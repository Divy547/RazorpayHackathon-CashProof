"""Tests for AI investigation contracts, strongly-typed budgets, and resolution proposals."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from cashproof.domain.ai import (
    Investigation,
    InvestigatorBudget,
    ResolutionProposal,
    ToolCallRecord,
)
from cashproof.domain.derived import Evidence, EvidencePointer
from cashproof.domain.types import EvidenceStance, StopReason


def test_investigator_budget_validation() -> None:
    budget = InvestigatorBudget(
        max_tool_calls=5,
        max_tokens=2048,
        timeout_seconds=30.0,
        temperature=0.0,
        model_version="claude-3-5-sonnet",
    )
    assert budget.max_tool_calls == 5
    assert budget.temperature == 0.0

    with pytest.raises(ValueError, match="max_tool_calls must be positive"):
        InvestigatorBudget(0, 2048, 30.0, 0.0, "v1")
    with pytest.raises(ValueError, match="max_tokens must be positive"):
        InvestigatorBudget(5, -1, 30.0, 0.0, "v1")
    with pytest.raises(ValueError, match="timeout_seconds must be a positive"):
        InvestigatorBudget(5, 2048, 0.0, 0.0, "v1")
    with pytest.raises(ValueError, match="temperature must be between 0.0 and 1.0"):
        InvestigatorBudget(5, 2048, 30.0, 1.5, "v1")
    with pytest.raises(ValueError, match="model_version must not be empty"):
        InvestigatorBudget(5, 2048, 30.0, 0.0, "")


def test_tool_call_record_defensive_freeze() -> None:
    args_dict = {"query": "SELECT * FROM ledger", "limit": "10"}
    record = ToolCallRecord("sql_query", args_dict, "Returned 2 rows", 120)

    assert record.arguments == (("limit", "10"), ("query", "SELECT * FROM ledger"))
    # Mutating caller dictionary does not mutate record
    args_dict["injected"] = "malicious"
    assert "injected" not in [k for k, _ in record.arguments]

    with pytest.raises(FrozenInstanceError):
        record.duration_ms = 200  # type: ignore[misc]


def test_investigation_creation_and_immutability() -> None:
    budget = InvestigatorBudget(5, 2048, 30.0, 0.0, "v1")
    tools = [ToolCallRecord("lookup", {"id": "1"}, "found", 50)]
    candidates = ["le_1", "le_2"]

    inv = Investigation(
        investigation_id="inv_1",
        case_id="case_1",
        run_id="run_1",
        budget=budget,
        tool_calls=tools,
        stop_reason=StopReason.COMPLETED,
        candidates_considered=candidates,
    )

    assert len(inv.tool_calls) == 1
    assert inv.candidates_considered == ("le_1", "le_2")

    tools.append(ToolCallRecord("lookup2", {}, "", 10))
    candidates.append("le_3")
    assert len(inv.tool_calls) == 1
    assert inv.candidates_considered == ("le_1", "le_2")


def test_resolution_proposal_validation_and_immutability() -> None:
    ptr = EvidencePointer("Payment", "pay_1", "order_ref")
    ev = Evidence(ptr, 0.9, EvidenceStance.SUPPORTS, True)
    targets = ["le_10", "le_20"]
    ev_list = [ev]

    proposal = ResolutionProposal(
        proposal_id="prop_1",
        investigation_id="inv_1",
        case_id="case_1",
        run_id="run_1",
        target_ledger_entry_ids=targets,
        rationale="Order ref match confirmed across bank statement.",
        evidence=ev_list,
        confidence=0.92,
    )

    assert proposal.target_ledger_entry_ids == frozenset({"le_10", "le_20"})
    assert proposal.confidence == 0.92

    # Mutating caller collections
    targets.append("le_30_mutated")
    ev_list.clear()
    assert proposal.target_ledger_entry_ids == frozenset({"le_10", "le_20"})
    assert len(proposal.evidence) == 1

    # Confidence validation
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        ResolutionProposal("p2", "i1", "c1", "r1", ["le_1"], "rat", [], 1.5)
    with pytest.raises(ValueError, match="finite float"):
        ResolutionProposal("p2", "i1", "c1", "r1", ["le_1"], "rat", [], float("nan"))
