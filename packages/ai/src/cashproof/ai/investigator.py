"""AnthropicInvestigator: the bounded AI investigator implementation.

Implements cashproof.application.ports.AIInvestigatorPort. Owns the model
tool-use loop, active budget enforcement, and StopReason mapping. Never
constructs a Resolution, never trusts model-asserted evidence or confidence
as authorization - it only ever produces an Investigation and, optionally, a
ResolutionProposal for the caller (AIInvestigationUseCase) to independently
re-verify through the unmodified deterministic gate.
"""

from __future__ import annotations

import math
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

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

_DEFAULT_MAX_RESPONSE_TOKENS = 1024


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """Normalized shape this module needs from one model turn."""

    content_blocks: tuple[Mapping[str, Any], ...]
    input_tokens: int
    output_tokens: int


class ChatClient(Protocol):
    """Minimal seam over one LLM chat-completion call.

    AnthropicChatClient wraps the real Anthropic SDK to this shape; tests
    inject a fake implementing just this method - no SDK mocking required.
    """

    def create_message(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: float,
        system: str,
        tools: Sequence[dict[str, Any]],
        messages: list[dict[str, Any]],
    ) -> ChatResponse: ...


class AnthropicChatClient:
    """Thin adapter wrapping the real Anthropic SDK client to the ChatClient seam."""

    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self._client = client

    def create_message(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: float,
        system: str,
        tools: Sequence[dict[str, Any]],
        messages: list[dict[str, Any]],
    ) -> ChatResponse:
        # NOTE: the installed anthropic SDK's Messages.create() does not accept a
        # top-level `temperature` kwarg (verified against the installed package;
        # confirm before changing if the SDK version changes). budget.temperature
        # is still captured and persisted on Investigation.budget for audit
        # purposes even though this adapter cannot forward it to the API call.
        # `tools`/`messages` are plain dicts matching the SDK's documented JSON
        # shape; the SDK's own param types are a large overloaded union we
        # deliberately do not depend on here (see ChatResponse normalization
        # below, which insulates the rest of this codebase from that union).
        del temperature
        response: Any = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=list(tools),  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )
        blocks: list[dict[str, Any]] = []
        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                blocks.append({"type": "text", "text": getattr(block, "text", "")})
            elif block_type == "tool_use":
                blocks.append(
                    {
                        "type": "tool_use",
                        "id": getattr(block, "id", ""),
                        "name": getattr(block, "name", ""),
                        "input": getattr(block, "input", {}),
                    }
                )
        usage = response.usage
        return ChatResponse(
            content_blocks=tuple(blocks),
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        )


def _flatten_args(data: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    flattened: list[tuple[str, str]] = []
    for key, value in data.items():
        if isinstance(value, (list, tuple)):
            flattened.append((key, ",".join(str(v) for v in value)))
        else:
            flattened.append((key, str(value)))
    return tuple(flattened)


@dataclass(frozen=True, slots=True)
class _ProposalValidation:
    proposal: ResolutionProposal | None
    summary: str


def _validate_submit_proposal(
    tool_input: Mapping[str, Any],
    ctx: ToolContext,
    *,
    investigation_id: str,
    case: ReconciliationCase,
    run_id: str,
) -> _ProposalValidation:
    raw_ids = tool_input.get("target_ledger_entry_ids")
    rationale = tool_input.get("rationale")
    confidence = tool_input.get("confidence")

    if not isinstance(raw_ids, list) or not raw_ids or not all(isinstance(x, str) for x in raw_ids):
        return _ProposalValidation(
            None, "Rejected: target_ledger_entry_ids must be a non-empty list of strings."
        )
    if not isinstance(rationale, str) or not rationale.strip():
        return _ProposalValidation(None, "Rejected: rationale must be a non-empty string.")
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or math.isnan(float(confidence))
        or math.isinf(float(confidence))
        or not (0.0 <= float(confidence) <= 1.0)
    ):
        return _ProposalValidation(
            None, "Rejected: confidence must be a finite number between 0.0 and 1.0."
        )

    target_ids = frozenset(raw_ids)
    invalid = target_ids - ctx.candidate_ids
    if invalid:
        return _ProposalValidation(
            None,
            f"Rejected: target ids {sorted(invalid)} are not among this case's candidates "
            f"{sorted(ctx.candidate_ids)}.",
        )

    proposal = ResolutionProposal(
        proposal_id=f"prop_{uuid.uuid4().hex[:16]}",
        investigation_id=investigation_id,
        case_id=case.case_id,
        run_id=run_id,
        target_ledger_entry_ids=target_ids,
        rationale=rationale,
        # Never the model's own claimed evidence - AIInvestigationUseCase rebuilds
        # this deterministically via EvidenceBuilder before it is ever trusted.
        evidence=(),
        confidence=float(confidence),
    )
    return _ProposalValidation(proposal, f"Accepted: proposal targeting {sorted(target_ids)}.")


class AnthropicInvestigator:
    """Bounded AI investigator. Implements AIInvestigatorPort."""

    def __init__(self, chat_client: ChatClient | None = None) -> None:
        self._chat_client = chat_client or AnthropicChatClient()

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

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    f"Investigate reconciliation case {case.case_id}. Use the available "
                    "tools to gather evidence, then call submit_proposal or abstain."
                ),
            }
        ]

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
                response = self._chat_client.create_message(
                    model=budget.model_version,
                    max_tokens=_DEFAULT_MAX_RESPONSE_TOKENS,
                    temperature=budget.temperature,
                    system=SYSTEM_PROMPT,
                    tools=TOOL_SCHEMAS,
                    messages=messages,
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

            messages.append({"role": "assistant", "content": list(response.content_blocks)})

            tool_results: list[dict[str, Any]] = []
            terminal_stop: StopReason | None = None

            for block in tool_use_blocks:
                name = str(block.get("name", ""))
                tool_input = dict(block.get("input") or {})
                block_id = str(block.get("id", ""))
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
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block_id, "content": result_text}
                )

                if len(tool_calls) >= budget.max_tool_calls:
                    terminal_stop = StopReason.BUDGET_EXHAUSTED
                    break

            if terminal_stop is not None:
                stop_reason = terminal_stop
                break

            messages.append({"role": "user", "content": tool_results})

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
