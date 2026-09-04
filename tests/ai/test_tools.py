"""Tests for the bounded, read-only investigation tools.

Each tool is exercised in isolation with hand-built ToolContext fixtures - no
network, no generator. The core safety property under test: get_ledger_entry
refuses any id outside this case's own candidate pool, and ToolContext never
exposes data beyond what the caller explicitly scoped into it (no cross-case
or cross-settlement access is even representable).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from cashproof.ai.tools import (
    READ_TOOL_NAMES,
    TOOL_SCHEMAS,
    ToolContext,
    ToolExecutionError,
    dispatch_tool,
    get_bridge_breakdown,
    get_candidates,
    get_case_context,
    get_evidence,
    get_gate_result,
    get_ledger_entry,
)
from cashproof.domain.decision import evaluate_gate
from cashproof.domain.derived import Evidence as EvidenceCls
from cashproof.domain.derived import EvidencePointer, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem
from cashproof.domain.types import (
    Currency,
    Direction,
    EvidenceStance,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
)

NOW = datetime(2026, 8, 1, tzinfo=UTC)


def _context() -> ToolContext:
    settlement = Settlement("set_1", 10_000, Currency.INR, NOW)
    items = (SettlementItem("item_1", "set_1", "pay_1", 10_000, 0, 0, 0, 0, 10_000),)
    case = ReconciliationCase(
        "set_1",
        "set_1",
        "run_1",
        10_000,
        9_500,
        500,
        ExceptionType.AMOUNT_MISMATCH,
        ProcessingState.CLASSIFIED,
    )
    entry = LedgerEntry(
        "le_1",
        9_500,
        Currency.INR,
        NOW,
        Direction.CREDIT,
        payment_ref="set_1",
        narration="NEFT-RZPX-set_1-PAYOUT",
    )
    candidate = MatchCandidate(
        "set_1",
        "le_1",
        0.8,
        ("payment_ref_exact_match",),
        (),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "run_1",
    )
    evidence = (
        EvidenceCls(
            EvidencePointer("LedgerEntry", "le_1", "amount_minor"),
            1.0,
            EvidenceStance.CONTRADICTS,
            True,
        ),
    )
    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=items,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry],
        deterministic_candidates=[candidate],
        evidence=evidence,
        already_resolved_target_ids=frozenset(),
    )
    return ToolContext(
        case=case,
        settlement=settlement,
        items=items,
        candidates=(candidate,),
        evidence=evidence,
        gate=gate,
        ledger_entries_by_id={"le_1": entry},
    )


def test_get_case_context_returns_scalars_only() -> None:
    ctx = _context()
    payload = json.loads(get_case_context(ctx))
    assert payload == {
        "case_id": "set_1",
        "expected_net_minor": 10_000,
        "observed_net_minor": 9_500,
        "delta_minor": 500,
        "exception_type": "AMOUNT_MISMATCH",
        "currency": "INR",
    }


def test_get_bridge_breakdown() -> None:
    ctx = _context()
    payload = json.loads(get_bridge_breakdown(ctx))
    assert payload["settlement_net_deposited_minor"] == 10_000
    assert payload["items"][0]["item_id"] == "item_1"


def test_get_candidates_matches_context() -> None:
    ctx = _context()
    payload = json.loads(get_candidates(ctx))
    assert payload == [
        {
            "ledger_entry_id": "le_1",
            "score": 0.8,
            "matched_signals": ["payment_ref_exact_match"],
            "provenance": "STRUCTURED_REFERENCE",
        }
    ]


def test_get_ledger_entry_returns_full_fields_for_in_pool_id() -> None:
    ctx = _context()
    payload = json.loads(get_ledger_entry(ctx, "le_1"))
    assert payload["id"] == "le_1"
    assert payload["amount_minor"] == 9_500
    assert payload["narration"] == "NEFT-RZPX-set_1-PAYOUT"


def test_get_ledger_entry_rejects_out_of_pool_id() -> None:
    ctx = _context()
    with pytest.raises(ToolExecutionError, match="not among this case's candidates"):
        get_ledger_entry(ctx, "le_from_another_case")


def test_get_ledger_entry_rejects_id_not_in_scoped_map_even_if_syntactically_plausible() -> None:
    """A context that was scoped without a given entry cannot leak it, even if a
    caller somehow got a candidate list referencing it (defense in depth for a
    caller bug - the tool must still refuse rather than KeyError/leak).
    """
    ctx = _context()
    candidate = MatchCandidate(
        "set_1", "le_ghost", 0.5, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    ghost_ctx = ToolContext(
        case=ctx.case,
        settlement=ctx.settlement,
        items=ctx.items,
        candidates=(*ctx.candidates, candidate),
        evidence=ctx.evidence,
        gate=ctx.gate,
        ledger_entries_by_id=ctx.ledger_entries_by_id,  # deliberately NOT containing le_ghost
    )
    with pytest.raises(ToolExecutionError, match="not found"):
        get_ledger_entry(ghost_ctx, "le_ghost")


def test_get_evidence() -> None:
    ctx = _context()
    payload = json.loads(get_evidence(ctx))
    assert payload[0]["stance"] == "CONTRADICTS"
    assert payload[0]["field"] == "amount_minor"


def test_get_gate_result_reflects_original_failing_check() -> None:
    ctx = _context()
    payload = json.loads(get_gate_result(ctx))
    assert payload["passed"] is False
    assert payload["failing_check"] == "BRIDGE"
    assert any(c["name"] == "BRIDGE" and c["passed"] is False for c in payload["checks"])


def test_dispatch_tool_routes_to_correct_function() -> None:
    ctx = _context()
    result = dispatch_tool("get_case_context", ctx, {})
    assert json.loads(result)["case_id"] == "set_1"


def test_dispatch_tool_unknown_name_raises() -> None:
    ctx = _context()
    with pytest.raises(ToolExecutionError, match="Unknown tool"):
        dispatch_tool("delete_everything", ctx, {})


def test_read_tool_names_matches_dispatchable_set() -> None:
    for name in READ_TOOL_NAMES:
        dispatch_tool(name, _context(), {"ledger_entry_id": "le_1"})


def test_tool_schemas_cover_all_read_tools_plus_terminal_actions() -> None:
    schema_names = {schema["name"] for schema in TOOL_SCHEMAS}
    assert READ_TOOL_NAMES <= schema_names
    assert {"submit_proposal", "abstain"} <= schema_names


def test_tool_schemas_contain_no_write_or_filesystem_or_database_tools() -> None:
    forbidden_markers = ("delete", "write", "sql", "file", "exec", "database", "shell")
    for schema in TOOL_SCHEMAS:
        name_lower = schema["name"].lower()
        assert not any(marker in name_lower for marker in forbidden_markers)
