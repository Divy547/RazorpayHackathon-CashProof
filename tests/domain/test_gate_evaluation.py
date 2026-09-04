"""Dedicated test suite for deterministic GateEvaluation and mandatory governance checks."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cashproof.domain.decision import (
    GateEvaluation,
    Resolution,
    evaluate_gate,
)
from cashproof.domain.derived import (
    Evidence,
    EvidencePointer,
    MatchCandidate,
    ReconciliationCase,
)
from cashproof.domain.exceptions import (
    DirectConstructionForbiddenError,
    ResolutionGateViolationError,
)
from cashproof.domain.source import (
    LedgerEntry,
    Settlement,
    SettlementItem,
)
from cashproof.domain.types import (
    Currency,
    Direction,
    EvidenceStance,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
)


def _fixture_case_and_settlement(
    amount: int = 10000,
    processing_state: ProcessingState = ProcessingState.INVESTIGATED,
) -> tuple[ReconciliationCase, Settlement, SettlementItem]:
    now = datetime.now(UTC)
    settlement = Settlement("set_1", amount, Currency.INR, now)
    item = SettlementItem("item_1", "set_1", "pay_1", amount, 0, 0, 0, 0, amount)
    case = ReconciliationCase(
        case_id="case_1",
        settlement_id="set_1",
        run_id="run_1",
        expected_net=amount,
        observed_ledger_total=amount,
        delta=0,
        exception_type=ExceptionType.CLEAN_MATCH,
        processing_state=processing_state,
    )
    return case, settlement, item


def test_gate_evaluation_direct_construction_forbidden() -> None:
    with pytest.raises(DirectConstructionForbiddenError, match="cannot be constructed directly"):
        GateEvaluation()


def test_evaluate_gate_all_checks_pass() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    candidate = MatchCandidate(
        "case_1",
        "le_1",
        1.0,
        ("ref_match",),
        ("rule_1",),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "run_1",
    )
    ev = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry],
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )

    assert gate.passed is True
    assert gate.failing_check is None
    assert gate.target_ledger_entry_ids == frozenset({"le_1"})
    assert gate.bridge_snapshot.delta_minor == 0
    assert all(c.passed for c in gate.check_outcomes)


def test_evaluate_gate_identity_check_fails_when_empty() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset(),
        target_ledger_entries=[],
        deterministic_candidates=[],
        evidence=[],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    assert gate.failing_check == "IDENTITY"


def test_evaluate_gate_bridge_check_fails_on_amount_mismatch() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    # Target entry is 8000 instead of 10000
    entry = LedgerEntry("le_1", 8000, Currency.INR, now, Direction.CREDIT)
    candidate = MatchCandidate(
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
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    assert gate.failing_check == "BRIDGE"


def test_evaluate_gate_currency_check_fails() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.USD, now, Direction.CREDIT)
    candidate = MatchCandidate(
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
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    assert gate.failing_check == "CURRENCY"


def test_evaluate_gate_uniqueness_check_fails_on_already_resolved() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    candidate = MatchCandidate(
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
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset({"le_1"}),  # Already resolved!
    )
    assert gate.passed is False
    assert gate.failing_check == "UNIQUENESS"


def test_evaluate_gate_evidence_completeness_fails() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    candidate = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    # No consumed evidence
    ev = Evidence(
        EvidencePointer("LedgerEntry", "le_1", "id"),
        1.0,
        EvidenceStance.SUPPORTS,
        decision_consumed=False,
    )

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry],
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    assert gate.failing_check == "EVIDENCE_COMPLETENESS"


def test_evaluate_gate_conflict_check_fails() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    candidate = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    ev1 = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)
    # Contradicting consumed evidence item
    ev2 = Evidence(
        EvidencePointer("LedgerEntry", "le_1", "customer_ref"),
        1.0,
        EvidenceStance.CONTRADICTS,
        True,
    )

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry],
        deterministic_candidates=[candidate],
        evidence=[ev1, ev2],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    assert gate.failing_check == "CONFLICT"


def test_evaluate_gate_policy_blocks_unstructured_text() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    # Provenance is EXTERNAL_REFERENCE_TEXT (S4)
    candidate = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.EXTERNAL_REFERENCE_TEXT, "v1", "run_1"
    )
    ev = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.AI_INVESTIGATION,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry],
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    assert gate.failing_check == "POLICY"


def test_evaluate_gate_state_transition_fails_on_ingested_case() -> None:
    case, settlement, item = _fixture_case_and_settlement(
        10000,
        processing_state=ProcessingState.INGESTED,
    )
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    candidate = MatchCandidate(
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
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    assert gate.failing_check == "STATE_TRANSITION"


def test_evaluate_gate_target_set_equality_fails_on_missing_candidate() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry1 = LedgerEntry("le_1", 5000, Currency.INR, now, Direction.CREDIT)
    cand1 = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    cand2 = MatchCandidate(
        "case_1", "le_2", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    ev1 = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    # Proposal only proposes le_1 (missing le_2 from candidate set)
    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry1],
        deterministic_candidates=[cand1, cand2],
        evidence=[ev1],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    failed_checks = [c.check_name for c in gate.check_outcomes if not c.passed]
    assert "TARGET_SET_EQUALITY" in failed_checks


def test_failed_gate_cannot_produce_auto_resolved() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 8000, Currency.INR, now, Direction.CREDIT)
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
    assert gate.passed is False

    with pytest.raises(ResolutionGateViolationError, match="requires a passing GateEvaluation"):
        Resolution.create_auto_resolved(gate)


def test_evaluate_gate_human_review_policy_passes_for_unstructured_text() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    candidate = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.EXTERNAL_REFERENCE_TEXT, "v1", "run_1"
    )
    ev = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.HUMAN_REVIEW,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry],
        deterministic_candidates=[candidate],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is True
    assert gate.failing_check is None
    policy_check = next(c for c in gate.check_outcomes if c.check_name == "POLICY")
    assert policy_check.passed is True
    assert "Explicit human review satisfies policy" in policy_check.reason


def test_evaluate_gate_human_review_target_set_equality_allows_subset() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry1 = LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT)
    cand1 = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    cand2 = MatchCandidate(
        "case_1", "le_2", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    ev1 = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    # Human selects subset {le_1} from pool {le_1, le_2}
    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.HUMAN_REVIEW,
        proposed_target_ids=frozenset({"le_1"}),
        target_ledger_entries=[entry1],
        deterministic_candidates=[cand1, cand2],
        evidence=[ev1],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is True
    tse_check = next(c for c in gate.check_outcomes if c.check_name == "TARGET_SET_EQUALITY")
    assert tse_check.passed is True


def test_evaluate_gate_human_review_target_set_equality_rejects_extra_candidate() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    now = datetime.now(UTC)
    entry_extra = LedgerEntry("le_extra", 10000, Currency.INR, now, Direction.CREDIT)
    cand1 = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    cand2 = MatchCandidate(
        "case_1", "le_2", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    ev = Evidence(
        EvidencePointer("LedgerEntry", "le_extra", "id"), 1.0, EvidenceStance.SUPPORTS, True
    )

    # Human proposes entry outside the candidate pool
    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.HUMAN_REVIEW,
        proposed_target_ids=frozenset({"le_extra"}),
        target_ledger_entries=[entry_extra],
        deterministic_candidates=[cand1, cand2],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    tse_check = next(c for c in gate.check_outcomes if c.check_name == "TARGET_SET_EQUALITY")
    assert tse_check.passed is False
    assert "entries outside candidate pool" in tse_check.reason


def test_evaluate_gate_human_review_target_set_equality_rejects_empty_set() -> None:
    case, settlement, item = _fixture_case_and_settlement(10000)
    cand1 = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )

    # Human proposes empty target set
    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.HUMAN_REVIEW,
        proposed_target_ids=frozenset(),
        target_ledger_entries=[],
        deterministic_candidates=[cand1],
        evidence=[],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False
    tse_check = next(c for c in gate.check_outcomes if c.check_name == "TARGET_SET_EQUALITY")
    assert tse_check.passed is False
    assert "Human review target set is empty" in tse_check.reason
