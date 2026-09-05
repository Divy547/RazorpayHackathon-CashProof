"""GeminiInvestigator: a second, independent implementation of AIInvestigatorPort.

Implements cashproof.application.ports.AIInvestigatorPort using the Gemini API
(google-genai SDK) instead of Anthropic. Mirrors AnthropicInvestigator's
safety semantics exactly (budget enforcement in code, candidate-pool
boundary, stop-reason mapping, never trusting model-asserted evidence) but
owns its own Gemini-native Content/Part/function_call/function_response wire
format, since Gemini's tool-calling protocol is not compatible with
Anthropic's tool_use/tool_result block shape. All Gemini SDK types stay
inside this file - the rest of the codebase only ever sees the same
provider-neutral ChatResponse, Investigation, and InvestigationOutcome types
AnthropicInvestigator already produces.

Never constructs a Resolution, never trusts model-asserted evidence or
confidence as authorization - it only ever produces an Investigation and,
optionally, a ResolutionProposal for the caller (AIInvestigationUseCase) to
independently re-verify through the unmodified deterministic gate.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from cashproof.ai.investigator import (
    ChatResponse,
    _flatten_args,
    _validate_submit_proposal,
)
from cashproof.ai.prompts import SYSTEM_PROMPT
from cashproof.ai.tools import (
    TOOL_SCHEMAS,
    ToolContext,
    ToolExecutionError,
    dispatch_tool,
)
from cashproof.application.ports import InvestigationOutcome
from cashproof.domain.ai import (
    Investigation,
    InvestigatorBudget,
    ResolutionProposal,
    ToolCallRecord,
)
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem
from cashproof.domain.types import StopReason
from google.genai import types

# Gemini's "thinking" models draw internal thought tokens from the SAME
# max_output_tokens ceiling as the visible function-call/text output (unlike
# Anthropic, which has no such shared budget - see
# _DEFAULT_MAX_RESPONSE_TOKENS in investigator.py, kept at 1024 there).
# Real traces showed usage.thoughts_token_count reaching ~979 tokens in a
# single turn, leaving too little room for a complete function call and
# producing a truncated/malformed response. This constant is Gemini-specific
# and deliberately does not touch Anthropic's value.
_GEMINI_MAX_RESPONSE_TOKENS = 4096

# Reused verbatim from tools.py: the same 6 read tools + submit_proposal +
# abstain, converted to Gemini's function-declaration shape. TOOL_SCHEMAS'
# input_schema values are already plain JSON Schema, which
# FunctionDeclaration.parameters_json_schema accepts directly - no
# hand-written schema translation, so there is no second place that can
# silently drift from the Anthropic tool definitions.
_GEMINI_FUNCTION_DECLARATIONS: tuple[types.FunctionDeclaration, ...] = tuple(
    types.FunctionDeclaration(
        name=schema["name"],
        description=schema["description"],
        parameters_json_schema=schema["input_schema"],
    )
    for schema in TOOL_SCHEMAS
)
_GEMINI_TOOLS: tuple[types.Tool, ...] = (
    types.Tool(function_declarations=list(_GEMINI_FUNCTION_DECLARATIONS)),
)

# Without this, Gemini's default FunctionCallingConfigMode.AUTO lets the model
# return plain text instead of a function call on any turn - observed live as
# a MALFORMED_OUTPUT-triggering free-text response mid-investigation. mode=ANY
# over the full declared name set forces every turn to be SOME function call
# (still the model's free choice of which one) - it never narrows investigative
# freedom, and MALFORMED_OUTPUT below remains as defense-in-depth regardless.
_GEMINI_ALLOWED_FUNCTION_NAMES: tuple[str, ...] = tuple(schema["name"] for schema in TOOL_SCHEMAS)
_GEMINI_TOOL_CONFIG = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode=types.FunctionCallingConfigMode.ANY,
        allowed_function_names=list(_GEMINI_ALLOWED_FUNCTION_NAMES),
    )
)


class GeminiChatClient(Protocol):
    """Minimal seam over one Gemini generate_content call.

    GoogleGenAIChatClient wraps the real google-genai SDK to this shape;
    tests inject a fake implementing just this method - no SDK mocking
    required. Returns the SAME provider-neutral ChatResponse
    AnthropicChatClient returns, so everything downstream of this seam
    (budget accounting, tool dispatch, proposal validation) is identical
    across providers.
    """

    def generate(
        self,
        *,
        model: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> ChatResponse: ...


class GoogleGenAIChatClient:
    """Thin adapter wrapping the real google-genai SDK client to the GeminiChatClient seam.

    The real genai.Client() validates API key presence at CONSTRUCTION time
    (unlike anthropic.Anthropic(), which only fails when a call is actually
    made) - so construction is deferred to the first generate() call. This
    lets the API server boot normally with GEMINI_API_KEY unset; only an
    actual investigation attempt fails, and it fails closed via the same
    broad exception handling GeminiInvestigator.investigate() already applies
    to every provider call, mapping to StopReason.TOOL_FAILURE.
    """

    def __init__(self, client: Any | None = None, *, api_key: str | None = None) -> None:
        self._client = client
        self._api_key = api_key

    def generate(
        self,
        *,
        model: str,
        contents: list[types.Content],
        config: types.GenerateContentConfig,
    ) -> ChatResponse:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)

        response: Any = self._client.models.generate_content(
            model=model, contents=contents, config=config
        )
        blocks: list[dict[str, Any]] = []
        candidates = response.candidates or []
        parts = candidates[0].content.parts if candidates and candidates[0].content else None
        for part in parts or []:
            if part.text is not None:
                blocks.append({"type": "text", "text": part.text})
            elif part.function_call is not None:
                blocks.append(
                    {
                        "type": "tool_use",
                        # Gemini does not reliably supply its own call id; this id is
                        # purely an internal bookkeeping label for ToolCallRecord/audit
                        # purposes and is never sent back to Gemini (see
                        # _model_turn_content below - function results are matched by
                        # request order, not by id).
                        "id": f"call_{uuid.uuid4().hex[:16]}",
                        "name": part.function_call.name or "",
                        "input": dict(part.function_call.args or {}),
                        # "Thinking" Gemini models (e.g. gemini-3.x) reject the next
                        # turn with 400 INVALID_ARGUMENT if a function_call part's
                        # thought_signature isn't echoed back verbatim - opaque to us,
                        # never inspected, only round-tripped (see _model_turn_content).
                        "thought_signature": part.thought_signature,
                    }
                )
        usage = response.usage_metadata
        return ChatResponse(
            content_blocks=tuple(blocks),
            input_tokens=int(getattr(usage, "prompt_token_count", 0) or 0),
            output_tokens=int(getattr(usage, "candidates_token_count", 0) or 0),
        )


def _model_turn_content(blocks: Sequence[Mapping[str, Any]]) -> types.Content:
    """Rebuild a Gemini model-turn Content from a normalized ChatResponse's blocks.

    Deliberately omits FunctionCall.id (see GoogleGenAIChatClient.generate) -
    the synthetic id in `blocks` is internal-only and must never be fed back
    into the wire protocol as if Gemini had issued it. thought_signature IS
    echoed back, verbatim and opaque, on the Part itself - required by
    "thinking" Gemini models (see GoogleGenAIChatClient.generate) or the next
    turn is rejected with 400 INVALID_ARGUMENT.
    """
    parts: list[types.Part] = []
    for block in blocks:
        if block.get("type") == "text":
            parts.append(types.Part(text=str(block.get("text", ""))))
        elif block.get("type") == "tool_use":
            parts.append(
                types.Part(
                    function_call=types.FunctionCall(
                        name=str(block.get("name", "")),
                        args=dict(block.get("input") or {}),
                    ),
                    thought_signature=block.get("thought_signature"),
                )
            )
    return types.Content(role="model", parts=parts)


class GeminiInvestigator:
    """Bounded AI investigator backed by the Gemini API. Implements AIInvestigatorPort.

    Mirrors AnthropicInvestigator.investigate()'s control flow (budget
    checks, stop-reason mapping, candidate-pool re-validation) turn for turn;
    only the wire-format construction differs, because Gemini's
    Content/Part/function_call/function_response shape is not compatible
    with Anthropic's tool_use/tool_result blocks.
    """

    def __init__(self, chat_client: GeminiChatClient | None = None) -> None:
        self._chat_client = chat_client or GoogleGenAIChatClient(
            api_key=os.environ.get("GEMINI_API_KEY")
        )

    def investigate(
        self,
        *,
        case: ReconciliationCase,
        settlement: Settlement,
        items: Sequence[SettlementItem],
        candidates: Sequence[MatchCandidate],
        evidence: Sequence[Evidence],
        gate: GateEvaluation,
        ledger_entries_by_id: Mapping[str, LedgerEntry],
        budget: InvestigatorBudget,
        run_id: str,
    ) -> InvestigationOutcome:
        ctx = ToolContext(
            case=case,
            settlement=settlement,
            items=tuple(items),
            candidates=tuple(candidates),
            evidence=tuple(evidence),
            gate=gate,
            ledger_entries_by_id=ledger_entries_by_id,
        )
        investigation_id = f"inv_{uuid.uuid4().hex[:16]}"
        deadline = time.monotonic() + budget.timeout_seconds
        tool_calls: list[ToolCallRecord] = []
        candidates_considered: list[str] = []

        contents: list[types.Content] = [
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=(
                            f"Investigate reconciliation case {case.case_id}. Use the "
                            "available tools to gather evidence, then call "
                            "submit_proposal or abstain."
                        )
                    )
                ],
            )
        ]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=budget.temperature,
            max_output_tokens=_GEMINI_MAX_RESPONSE_TOKENS,
            tools=list(_GEMINI_TOOLS),
            tool_config=_GEMINI_TOOL_CONFIG,
        )

        stop_reason = StopReason.MALFORMED_OUTPUT
        proposal: ResolutionProposal | None = None
        total_tokens_used = 0

        while True:
            if time.monotonic() >= deadline:
                stop_reason = StopReason.TIMEOUT
                break
            if len(tool_calls) >= budget.max_tool_calls:
                stop_reason = StopReason.BUDGET_EXHAUSTED
                break

            try:
                response = self._chat_client.generate(
                    model=budget.model_version, contents=contents, config=config
                )
            except Exception:  # noqa: BLE001 - any SDK/network failure fails closed
                stop_reason = StopReason.TOOL_FAILURE
                break

            total_tokens_used += response.input_tokens + response.output_tokens
            if total_tokens_used > budget.max_tokens:
                stop_reason = StopReason.BUDGET_EXHAUSTED
                break

            tool_use_blocks = [b for b in response.content_blocks if b.get("type") == "tool_use"]
            if not tool_use_blocks:
                stop_reason = StopReason.MALFORMED_OUTPUT
                break

            contents.append(_model_turn_content(response.content_blocks))

            tool_result_parts: list[types.Part] = []
            terminal_stop: StopReason | None = None

            for block in tool_use_blocks:
                name = str(block.get("name", ""))
                tool_input = dict(block.get("input") or {})
                started = time.monotonic()

                if name == "submit_proposal":
                    validation = _validate_submit_proposal(
                        tool_input,
                        ctx,
                        investigation_id=investigation_id,
                        case=case,
                        run_id=run_id,
                    )
                    tool_calls.append(
                        ToolCallRecord(
                            tool_name=name,
                            arguments=_flatten_args(tool_input),
                            response_summary=validation.summary,
                            duration_ms=int((time.monotonic() - started) * 1000),
                        )
                    )
                    if validation.proposal is not None:
                        proposal = validation.proposal
                        terminal_stop = StopReason.COMPLETED
                    else:
                        terminal_stop = StopReason.MALFORMED_OUTPUT
                    break

                if name == "abstain":
                    reason = str(tool_input.get("reason", ""))
                    tool_calls.append(
                        ToolCallRecord(
                            tool_name=name,
                            arguments=_flatten_args(tool_input),
                            response_summary=f"Abstained: {reason}",
                            duration_ms=int((time.monotonic() - started) * 1000),
                        )
                    )
                    terminal_stop = StopReason.COMPLETED
                    break

                try:
                    result_text = dispatch_tool(name, ctx, tool_input)
                    if name == "get_ledger_entry":
                        lid = tool_input.get("ledger_entry_id")
                        if isinstance(lid, str) and lid in ctx.candidate_ids:
                            candidates_considered.append(lid)
                except ToolExecutionError as exc:
                    result_text = f"ERROR: {exc}"

                tool_calls.append(
                    ToolCallRecord(
                        tool_name=name,
                        arguments=_flatten_args(tool_input),
                        response_summary=result_text,
                        duration_ms=int((time.monotonic() - started) * 1000),
                    )
                )
                tool_result_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=name, response={"result": result_text}
                        )
                    )
                )

                if len(tool_calls) >= budget.max_tool_calls:
                    terminal_stop = StopReason.BUDGET_EXHAUSTED
                    break

            if terminal_stop is not None:
                stop_reason = terminal_stop
                break

            contents.append(types.Content(role="user", parts=tool_result_parts))

        investigation = Investigation(
            investigation_id=investigation_id,
            case_id=case.case_id,
            run_id=run_id,
            budget=budget,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            candidates_considered=tuple(dict.fromkeys(candidates_considered)),
        )
        if stop_reason != StopReason.COMPLETED:
            proposal = None
        return InvestigationOutcome(investigation=investigation, proposal=proposal)
