"""Tests for Resolution governance semantics and global target exclusivity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cashproof.domain.decision import (
    GateEvaluation,
    Resolution,
    evaluate_gate,
    validate_ledger_target_exclusivity,
)
from cashproof.domain.derived import (
    Evidence,
    EvidencePointer,
    MatchCandidate,
    ReconciliationCase,
)
from cashproof.domain.exceptions import (
    LedgerEntryAlreadyResolvedError,
    ResolutionGovernanceError,
    ResolutionScopeMismatchError,
    ResolutionTargetMismatchError,
)
from cashproof.domain.source import (
    LedgerEntry,
    Settlement,
    SettlementItem,
)
from cashproof.domain.types import (
    Currency,
    Direction,
    Disposition,
    EvidenceStance,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
    ReviewOutcome,
)


def _passing_gate() -> tuple[ReconciliationCase, GateEvaluation]:
    now = datetime.now(UTC)
    settlement = Settlement("set_1", 10000, Currency.INR, now)
    item = SettlementItem("item_1", "set_1", "pay_1", 10000, 0, 0, 0, 0, 10000)
    case = ReconciliationCase(
        "case_1",
        "set_1",
        "run_1",
        10000,
        10000,
        0,
        ExceptionType.CLEAN_MATCH,
        ProcessingState.INVESTIGATED,
    )
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    cand = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    ev = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry],
        deterministic_candidates=[cand],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    return case, gate


def test_resolution_auto_resolved_factory() -> None:
    _, gate = _passing_gate()
    res = Resolution.create_auto_resolved(gate)

    assert res.disposition == Disposition.AUTO_RESOLVED
    assert res.target_ledger_entry_ids == frozenset({"le_1"})
    assert res.reviewer is None
    assert res.review_outcome is None
    assert res.reviewed_at is None


def test_resolution_human_review_pending_factory() -> None:
    _, gate = _passing_gate()
    res = Resolution.create_human_review_pending(gate)

    assert res.disposition == Disposition.HUMAN_REVIEW
    assert res.review_outcome == ReviewOutcome.PENDING
    assert res.reviewer is None
    assert res.reviewed_at is None


def test_resolution_human_reviewed_approved_factory() -> None:
    _, gate = _passing_gate()
    now = datetime.now(UTC)
    res = Resolution.create_human_reviewed(
        gate=gate,
        reviewer="rev_alice",
        review_outcome=ReviewOutcome.APPROVED,
        reviewed_at=now,
    )

    assert res.disposition == Disposition.HUMAN_REVIEW
    assert res.review_outcome == ReviewOutcome.APPROVED
    assert res.reviewer == "rev_alice"
    assert res.reviewed_at == now


def test_resolution_human_reviewed_rejected_factory() -> None:
    # Shape B: Unresolved via rejected human review
    _, gate = _passing_gate()
    now = datetime.now(UTC)
    res = Resolution.create_human_reviewed(
        gate=gate,
        reviewer="rev_bob",
        review_outcome=ReviewOutcome.REJECTED,
        reviewed_at=now,
    )

    assert res.disposition == Disposition.UNRESOLVED
    assert res.review_outcome == ReviewOutcome.REJECTED
    assert res.reviewer == "rev_bob"
    assert res.reviewed_at == now


def test_resolution_unresolved_deterministic_factory() -> None:
    # Shape A: Deterministic unresolved
    _, gate = _passing_gate()
    res = Resolution.create_unresolved(gate)

    assert res.disposition == Disposition.UNRESOLVED
    assert res.review_outcome is None
    assert res.reviewer is None
    assert res.reviewed_at is None


def test_resolution_target_mismatch_raises() -> None:
    _, gate = _passing_gate()
    with pytest.raises(ResolutionTargetMismatchError, match="target set"):
        Resolution(
            case_id=gate.case_id,
            run_id=gate.run_id,
            disposition=Disposition.AUTO_RESOLVED,
            target_ledger_entry_ids={"le_diff"},  # Mismatched target!
            governing_gate_evaluation=gate,
        )


def test_resolution_scope_mismatch_raises() -> None:
    _, gate = _passing_gate()
    with pytest.raises(ResolutionScopeMismatchError, match="case_id or run_id"):
        Resolution(
            case_id="case_other",
            run_id=gate.run_id,
            disposition=Disposition.AUTO_RESOLVED,
            target_ledger_entry_ids=gate.target_ledger_entry_ids,
            governing_gate_evaluation=gate,
        )


def test_resolution_auto_resolved_with_reviewer_raises() -> None:
    _, gate = _passing_gate()
    with pytest.raises(ResolutionGovernanceError, match="cannot contain human reviewer"):
        Resolution(
            case_id=gate.case_id,
            run_id=gate.run_id,
            disposition=Disposition.AUTO_RESOLVED,
            target_ledger_entry_ids=gate.target_ledger_entry_ids,
            governing_gate_evaluation=gate,
            reviewer="Alice",
        )


def test_validate_ledger_target_exclusivity() -> None:
    # No conflict
    validate_ledger_target_exclusivity({"le_1", "le_2"}, {"le_3", "le_4"})

    # Conflict
    with pytest.raises(LedgerEntryAlreadyResolvedError, match="already resolved"):
        validate_ledger_target_exclusivity({"le_1", "le_2"}, {"le_2", "le_3"})
