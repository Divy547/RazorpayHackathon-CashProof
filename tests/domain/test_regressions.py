"""Dedicated regression tests for adversarial review defects B1-B4 and I1-I2."""

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
    DuplicateRefundNettingError,
    RefundNettingMismatchError,
    ResolutionGateViolationError,
)
from cashproof.domain.source import (
    LedgerEntry,
    Refund,
    Settlement,
    SettlementItem,
    validate_refund_netting_invariant,
)
from cashproof.domain.types import (
    Currency,
    Direction,
    EvidenceStance,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
    RefundStatus,
)

# ==============================================================================
# B1: GateEvaluation Fabrication Vulnerability
# ==============================================================================


def test_regression_b1_gate_evaluation_fabrication_impossible() -> None:
    """Proves that direct GateEvaluation construction is impossible under any argument pattern."""
    # Attempt 1: Empty constructor
    with pytest.raises(DirectConstructionForbiddenError):
        GateEvaluation()

    # Attempt 2: Positional arguments fabrication
    with pytest.raises(DirectConstructionForbiddenError):
        GateEvaluation("case_1", "run_1", HypothesisSource.DETERMINISTIC_RULES)

    # Attempt 3: Keyword arguments fabrication attempt with passed=True
    with pytest.raises(DirectConstructionForbiddenError):
        GateEvaluation(
            case_id="case_1",
            run_id="run_1",
            passed=True,
        )


def test_regression_b1_resolution_cannot_bind_fabricated_or_failed_gate() -> None:
    """Proves Resolution.create_auto_resolved rejects failed gates."""
    now = datetime.now(UTC)
    settlement = Settlement("set_1", 10000, Currency.INR, now)
    item = SettlementItem("item_1", "set_1", "p_1", 10000, 0, 0, 0, 0, 10000)
    case = ReconciliationCase(
        "case_1",
        "set_1",
        "run_1",
        10000,
        8000,
        2000,
        ExceptionType.AMOUNT_MISMATCH,
        ProcessingState.INVESTIGATED,
    )

    # Failed gate due to amount mismatch
    entry = LedgerEntry("le_1", 8000, Currency.INR, now, Direction.CREDIT)
    cand = MatchCandidate(
        "case_1",
        "le_1",
        1.0,
        (),
        (),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "run_1",
    )
    ev = Evidence(
        EvidencePointer("LedgerEntry", "le_1", "id"),
        1.0,
        EvidenceStance.SUPPORTS,
        True,
    )

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids={"le_1"},
        target_ledger_entries=[entry],
        deterministic_candidates=[cand],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate.passed is False

    with pytest.raises(ResolutionGateViolationError):
        Resolution.create_auto_resolved(gate)


# ==============================================================================
# B2: Multi-Item Settlement BRIDGE Validation
# ==============================================================================


def test_regression_b2_multi_item_settlement_bridge_success() -> None:
    """Proves multi-item settlements validate bridge at whole-settlement level."""
    now = datetime.now(UTC)
    # Settlement total = 25000
    settlement = Settlement("set_100", 25000, Currency.INR, now)

    # Item 1: net 14646, Item 2: net 10354 -> sum = 25000
    item1 = SettlementItem("it_1", "set_100", "p_1", 15000, 300, 54, 0, 0, 14646)
    item2 = SettlementItem("it_2", "set_100", "p_2", 11000, 200, 36, 500, 90, 10354)

    case = ReconciliationCase(
        case_id="case_100",
        settlement_id="set_100",
        run_id="run_1",
        expected_net=25000,
        observed_ledger_total=25000,
        delta=0,
        exception_type=ExceptionType.CLEAN_MATCH,
        processing_state=ProcessingState.INVESTIGATED,
    )

    # 2 Ledger entries summing to 25000 (15000 + 10000)
    entry1 = LedgerEntry("le_1", 14646, Currency.INR, now, Direction.CREDIT)
    entry2 = LedgerEntry("le_2", 10354, Currency.INR, now, Direction.CREDIT)

    cand1 = MatchCandidate(
        "case_100", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    cand2 = MatchCandidate(
        "case_100", "le_2", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )

    ev1 = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)
    ev2 = Evidence(EvidencePointer("LedgerEntry", "le_2", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item1, item2],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids={"le_1", "le_2"},
        target_ledger_entries=[entry1, entry2],
        deterministic_candidates=[cand1, cand2],
        evidence=[ev1, ev2],
        already_resolved_target_ids=frozenset(),
    )

    assert gate.passed is True
    assert gate.failing_check is None
    assert gate.bridge_snapshot.observed_net_minor == 25000
    assert gate.bridge_snapshot.expected_net_minor == 25000
    assert gate.bridge_snapshot.delta_minor == 0


def test_regression_b2_multi_item_settlement_bridge_mismatch_fails() -> None:
    """Proves whole-settlement sum mismatch fails BRIDGE check."""
    now = datetime.now(UTC)
    settlement = Settlement("set_100", 25000, Currency.INR, now)
    item1 = SettlementItem("it_1", "set_100", "p_1", 15000, 300, 54, 0, 0, 14646)
    item2 = SettlementItem("it_2", "set_100", "p_2", 11000, 200, 36, 500, 90, 10354)

    case = ReconciliationCase(
        "case_100",
        "set_100",
        "run_1",
        25000,
        20000,
        5000,
        ExceptionType.AMOUNT_MISMATCH,
        ProcessingState.INVESTIGATED,
    )

    # Observed total only 20000
    entry = LedgerEntry("le_1", 20000, Currency.INR, now, Direction.CREDIT)
    cand = MatchCandidate(
        "case_100", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    ev = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item1, item2],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids={"le_1"},
        target_ledger_entries=[entry],
        deterministic_candidates=[cand],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )

    assert gate.passed is False
    assert gate.failing_check == "BRIDGE"


# ==============================================================================
# B3: MatchCandidate Provenance Ordering Vulnerability
# ==============================================================================


def test_regression_b3_candidate_provenance_ordering_invariance() -> None:
    """Proves candidate ordering cannot bypass POLICY check when unstructured candidate exists."""
    now = datetime.now(UTC)
    settlement = Settlement("set_1", 10000, Currency.INR, now)
    item = SettlementItem("it_1", "set_1", "p_1", 10000, 0, 0, 0, 0, 10000)
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
    ev = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    cand_struct = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    cand_alias = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.NARRATION_ALIAS_TEXT, "v1", "run_1"
    )

    # Order 1: [STRUCTURED_REFERENCE, NARRATION_ALIAS_TEXT] -> Must FAIL policy
    gate1 = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item],
        hypothesis_source=HypothesisSource.AI_INVESTIGATION,
        proposed_target_ids={"le_1"},
        target_ledger_entries=[entry],
        deterministic_candidates=[cand_struct, cand_alias],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate1.passed is False
    assert gate1.failing_check == "POLICY"

    # Order 2: [NARRATION_ALIAS_TEXT, STRUCTURED_REFERENCE] -> Must FAIL policy
    gate2 = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item],
        hypothesis_source=HypothesisSource.AI_INVESTIGATION,
        proposed_target_ids={"le_1"},
        target_ledger_entries=[entry],
        deterministic_candidates=[cand_alias, cand_struct],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate2.passed is False
    assert gate2.failing_check == "POLICY"

    # Structured only -> POLICY passes
    gate3 = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item],
        hypothesis_source=HypothesisSource.AI_INVESTIGATION,
        proposed_target_ids={"le_1"},
        target_ledger_entries=[entry],
        deterministic_candidates=[cand_struct],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )
    assert gate3.passed is True
    assert gate3.failing_check is None


# ==============================================================================
# B4: Refund Double-Claim Vulnerability
# ==============================================================================


def test_regression_b4_refund_double_claim_detected_and_rejected() -> None:
    """Proves two SettlementItems sharing a payment_id cannot double-claim the same refund pool."""
    now = datetime.now(UTC)
    item1 = SettlementItem("it_1", "set_1", "pay_shared", 10000, 200, 36, 1000, 0, 8764)
    item2 = SettlementItem("it_2", "set_1", "pay_shared", 10000, 200, 36, 1000, 0, 8764)

    refund = Refund("rf_1", "pay_shared", 1000, Currency.INR, now, RefundStatus.PROCESSED, True)

    with pytest.raises(RefundNettingMismatchError, match="total claimed netted refund"):
        validate_refund_netting_invariant([item1, item2], [refund])


def test_regression_b4_refund_legitimate_split_and_duplicates() -> None:
    """Proves valid split refund passes and duplicate refund IDs fail."""
    now = datetime.now(UTC)
    item1 = SettlementItem("it_1", "set_1", "pay_shared", 10000, 200, 36, 600, 0, 9164)
    item2 = SettlementItem("it_2", "set_1", "pay_shared", 10000, 200, 36, 400, 0, 9364)

    refund = Refund("rf_1", "pay_shared", 1000, Currency.INR, now, RefundStatus.PROCESSED, True)

    # Valid split: 600 + 400 == 1000
    validate_refund_netting_invariant([item1, item2], [refund])

    # Duplicate refund object in input list
    with pytest.raises(DuplicateRefundNettingError, match="claimed across multiple"):
        validate_refund_netting_invariant([item1, item2], [refund, refund])


# ==============================================================================
# I1: Currency Mismatch Bridge Snapshot Safety
# ==============================================================================


def test_regression_i1_currency_mismatch_no_misleading_snapshot() -> None:
    """Proves mixed-currency entries do not produce a currency-blind sum in BridgeSnapshot."""
    now = datetime.now(UTC)
    settlement = Settlement("set_1", 10000, Currency.INR, now)
    item = SettlementItem("it_1", "set_1", "p_1", 10000, 0, 0, 0, 0, 10000)
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

    # One INR entry and one USD entry
    entry_inr = LedgerEntry("le_1", 5000, Currency.INR, now, Direction.CREDIT)
    entry_usd = LedgerEntry("le_2", 5000, Currency.USD, now, Direction.CREDIT)

    cand1 = MatchCandidate(
        "case_1", "le_1", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )
    cand2 = MatchCandidate(
        "case_1", "le_2", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )

    ev1 = Evidence(EvidencePointer("LedgerEntry", "le_1", "id"), 1.0, EvidenceStance.SUPPORTS, True)
    ev2 = Evidence(EvidencePointer("LedgerEntry", "le_2", "id"), 1.0, EvidenceStance.SUPPORTS, True)

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids={"le_1", "le_2"},
        target_ledger_entries=[entry_inr, entry_usd],
        deterministic_candidates=[cand1, cand2],
        evidence=[ev1, ev2],
        already_resolved_target_ids=frozenset(),
    )

    assert gate.passed is False
    assert gate.failing_check == "CURRENCY"
    # Check outcomes contain failing CURRENCY check
    currency_check = next(c for c in gate.check_outcomes if c.check_name == "CURRENCY")
    assert currency_check.passed is False

    # Bridge snapshot must NOT have a misleading 10000 currency-blind sum
    assert gate.bridge_snapshot.observed_net_minor is None
    assert gate.bridge_snapshot.delta_minor is None


# ==============================================================================
# I2: Evidence Completeness Entity Type & ID Collision
# ==============================================================================


def test_regression_i2_evidence_completeness_entity_type_collision() -> None:
    """Proves evidence referencing Payment with same ID does not satisfy LedgerEntry target."""
    now = datetime.now(UTC)
    settlement = Settlement("set_1", 10000, Currency.INR, now)
    item = SettlementItem("it_1", "set_1", "colliding_id", 10000, 0, 0, 0, 0, 10000)
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

    entry = LedgerEntry("colliding_id", 10000, Currency.INR, now, Direction.CREDIT)
    cand = MatchCandidate(
        "case_1", "colliding_id", 1.0, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "run_1"
    )

    # Evidence points to Payment 'colliding_id' instead of LedgerEntry
    ev_payment = Evidence(
        EvidencePointer("Payment", "colliding_id", "id"),
        1.0,
        EvidenceStance.SUPPORTS,
        True,
    )

    gate_fail = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids={"colliding_id"},
        target_ledger_entries=[entry],
        deterministic_candidates=[cand],
        evidence=[ev_payment],
        already_resolved_target_ids=frozenset(),
    )
    assert gate_fail.passed is False
    assert gate_fail.failing_check == "EVIDENCE_COMPLETENESS"

    # Evidence points to LedgerEntry 'colliding_id'
    ev_ledger = Evidence(
        EvidencePointer("LedgerEntry", "colliding_id", "id"),
        1.0,
        EvidenceStance.SUPPORTS,
        True,
    )

    gate_pass = evaluate_gate(
        case=case,
        settlement=settlement,
        items=[item],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids={"colliding_id"},
        target_ledger_entries=[entry],
        deterministic_candidates=[cand],
        evidence=[ev_ledger],
        already_resolved_target_ids=frozenset(),
    )
    assert gate_pass.passed is True
    assert gate_pass.failing_check is None
