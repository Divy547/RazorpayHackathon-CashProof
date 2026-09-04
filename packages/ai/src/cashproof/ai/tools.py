"""Bounded, read-only investigation tools and their Anthropic tool-use schemas.

Every tool operates ONLY on data already scoped to one case by the caller
(ToolContext) - never a store, never another case/settlement, never
GroundTruth/ScenarioFamily, never the filesystem or a database. get_ledger_entry
is the one tool with a hard boundary check: it refuses any id outside this
case's own MatchCandidate pool.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem


class ToolExecutionError(Exception):
    """Raised by a bounded tool for invalid input (e.g. an out-of-pool ledger id).

    Never raised for "the answer is empty" - only for a request that violates
    this tool's boundary.
    """


@dataclass(frozen=True, slots=True)
class ToolContext:
    """Single-case-scoped read-only data available to the bounded tools."""

    case: ReconciliationCase
    settlement: Settlement
    items: tuple[SettlementItem, ...]
    candidates: tuple[MatchCandidate, ...]
    evidence: tuple[Evidence, ...]
    gate: GateEvaluation
    ledger_entries_by_id: Mapping[str, LedgerEntry]

    @property
    def candidate_ids(self) -> frozenset[str]:
        return frozenset(c.ledger_entry_id for c in self.candidates)


def get_case_context(ctx: ToolContext) -> str:
    return json.dumps(
        {
            "case_id": ctx.case.case_id,
            "expected_net_minor": ctx.case.expected_net,
            "observed_net_minor": ctx.case.observed_ledger_total,
            "delta_minor": ctx.case.delta,
            "exception_type": ctx.case.exception_type.value,
            "currency": ctx.settlement.currency.value,
        }
    )


def get_bridge_breakdown(ctx: ToolContext) -> str:
    return json.dumps(
        {
            "settlement_net_deposited_minor": ctx.settlement.net_deposited_minor,
            "items": [
                {
                    "item_id": item.item_id,
                    "gross_minor": item.gross_minor,
                    "fee_minor": item.fee_minor,
                    "tax_on_fee_minor": item.tax_on_fee_minor,
                    "netted_refund_minor": item.netted_refund_minor,
                    "adjustment_minor": item.adjustment_minor,
                    "computed_net_minor": item.computed_net_minor,
                }
                for item in ctx.items
            ],
        }
    )


def get_candidates(ctx: ToolContext) -> str:
    return json.dumps(
        [
            {
                "ledger_entry_id": c.ledger_entry_id,
                "score": c.score,
                "matched_signals": list(c.matched_signals),
                "provenance": c.provenance.value,
            }
            for c in ctx.candidates
        ]
    )


def get_ledger_entry(ctx: ToolContext, ledger_entry_id: str) -> str:
    if ledger_entry_id not in ctx.candidate_ids:
        raise ToolExecutionError(
            f"ledger_entry_id {ledger_entry_id!r} is not among this case's candidates "
            f"{sorted(ctx.candidate_ids)}. Only candidates returned by get_candidates may "
            "be inspected."
        )
    entry = ctx.ledger_entries_by_id.get(ledger_entry_id)
    if entry is None:
        raise ToolExecutionError(f"ledger_entry_id {ledger_entry_id!r} was not found.")
    return json.dumps(
        {
            "id": entry.id,
            "amount_minor": entry.amount_minor,
            "currency": entry.currency.value,
            "timestamp": entry.timestamp.isoformat(),
            "direction": entry.direction.value,
            "payment_ref": entry.payment_ref,
            "external_ref": entry.external_ref,
            "narration": entry.narration,
            "customer_name": entry.customer_name,
        }
    )


def get_evidence(ctx: ToolContext) -> str:
    return json.dumps(
        [
            {
                "entity_type": e.pointer.entity_type,
                "entity_id": e.pointer.entity_id,
                "field": e.pointer.field,
                "stance": e.stance.value,
                "relevance": e.relevance,
                "decision_consumed": e.decision_consumed,
            }
            for e in ctx.evidence
        ]
    )


def get_gate_result(ctx: ToolContext) -> str:
    return json.dumps(
        {
            "passed": ctx.gate.passed,
            "failing_check": ctx.gate.failing_check,
            "checks": [
                {"name": c.check_name, "passed": c.passed, "reason": c.reason}
                for c in ctx.gate.check_outcomes
            ],
        }
    )


_READ_TOOLS: dict[str, Callable[[ToolContext, Mapping[str, Any]], str]] = {
    "get_case_context": lambda ctx, args: get_case_context(ctx),
    "get_bridge_breakdown": lambda ctx, args: get_bridge_breakdown(ctx),
    "get_candidates": lambda ctx, args: get_candidates(ctx),
    "get_ledger_entry": (
        lambda ctx, args: get_ledger_entry(ctx, str(args.get("ledger_entry_id", "")))
    ),
    "get_evidence": lambda ctx, args: get_evidence(ctx),
    "get_gate_result": lambda ctx, args: get_gate_result(ctx),
}

READ_TOOL_NAMES: frozenset[str] = frozenset(_READ_TOOLS)


def dispatch_tool(name: str, ctx: ToolContext, args: Mapping[str, Any]) -> str:
    """Dispatch one of the 6 bounded read-only tools. Raises ToolExecutionError for
    an unknown tool name or a boundary violation (see get_ledger_entry).
    """
    fn = _READ_TOOLS.get(name)
    if fn is None:
        raise ToolExecutionError(f"Unknown tool: {name!r}")
    return fn(ctx, args)


TOOL_SCHEMAS: Sequence[dict[str, Any]] = (
    {
        "name": "get_case_context",
        "description": (
            "Get this case's expected settlement amount, observed ledger amount, delta, "
            "exception type, and currency."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_bridge_breakdown",
        "description": (
            "Get this case's settlement item breakdown (gross, fee, tax, refund, "
            "adjustment, computed net per item) - how the expected settlement amount "
            "was derived."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_candidates",
        "description": (
            "Get the deterministic matcher's candidate ledger entries for this case, "
            "with scores, matched signals, and provenance. This is the complete set of "
            "ledger entries you may investigate or propose - no others exist for this "
            "case."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_ledger_entry",
        "description": (
            "Get full details of one ledger entry, by id. The id MUST be one returned by "
            "get_candidates; any other id is refused."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"ledger_entry_id": {"type": "string"}},
            "required": ["ledger_entry_id"],
        },
    },
    {
        "name": "get_evidence",
        "description": "Get the field-level evidence already constructed for this case.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_gate_result",
        "description": (
            "Get the original deterministic gate evaluation for this case: which checks "
            "passed/failed and why. This is why the case needs investigation."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "submit_proposal",
        "description": (
            "Terminate the investigation with a resolution hypothesis. target_ledger_entry_ids "
            "MUST be drawn only from the ids returned by get_candidates. This does not resolve "
            "the case - it is independently re-verified by a deterministic gate you cannot see "
            "or influence, and a human must still approve it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_ledger_entry_ids": {"type": "array", "items": {"type": "string"}},
                "rationale": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "required": ["target_ledger_entry_ids", "rationale", "confidence"],
        },
    },
    {
        "name": "abstain",
        "description": (
            "Terminate the investigation without a proposal, because the evidence does not "
            "support one. Always safe and often correct."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    },
)

TERMINAL_TOOL_NAMES: frozenset[str] = frozenset({"submit_proposal", "abstain"})
