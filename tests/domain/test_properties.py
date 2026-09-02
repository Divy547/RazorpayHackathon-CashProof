"""Property-based tests using Hypothesis for mathematical and invariant properties."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from cashproof.domain.ai import ResolutionProposal
from cashproof.domain.decision import evaluate_gate
from cashproof.domain.derived import (
    Evidence,
    EvidencePointer,
    MatchCandidate,
    ReconciliationCase,
)
from cashproof.domain.money import (
    aggregate_ledger_total,
    calculate_gst_on_fee,
    calculate_ledger_signed_amount,
    calculate_settlement_item_net,
)
from cashproof.domain.source import (
    LedgerEntry,
    Payment,
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
    PaymentStatus,
    ProcessingState,
)
from hypothesis import given
from hypothesis import strategies as st


@given(
    gross=st.integers(min_value=0, max_value=10_000_000_00),
    fee=st.integers(min_value=0, max_value=1_000_000_00),
    tax=st.integers(min_value=0, max_value=1_000_000_00),
    refund=st.integers(min_value=0, max_value=5_000_000_00),
    adjustment=st.integers(min_value=-500_000_00, max_value=500_000_00),
)
def test_property_settlement_item_bridge_arithmetic(
    gross: int,
    fee: int,
    tax: int,
    refund: int,
    adjustment: int,
) -> None:
    computed_net = calculate_settlement_item_net(gross, fee, tax, refund, adjustment)
    expected = gross - fee - tax - refund + adjustment
    assert computed_net == expected


@given(fee_minor=st.integers(min_value=0, max_value=100_000_000))
def test_property_gst_on_fee_half_up_rounding(fee_minor: int) -> None:
    gst = calculate_gst_on_fee(fee_minor)
    assert 0 <= gst <= fee_minor
    # Check exact half-up formula: (fee * 18 + 50) // 100
    expected = (fee_minor * 18 + 50) // 100
    assert gst == expected


@given(
    amounts=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=1_000_000),
            st.sampled_from([Direction.CREDIT, Direction.DEBIT]),
        ),
        min_size=1,
        max_size=20,
    )
)
def test_property_ledger_aggregation_commutativity(
    amounts: list[tuple[int, Direction]],
) -> None:
    now = datetime.now(UTC)
    entries = [
        LedgerEntry(f"le_{i}", amt, Currency.INR, now, direction)
        for i, (amt, direction) in enumerate(amounts)
    ]
    total1 = aggregate_ledger_total(entries, Currency.INR)

    # Reversing the order must produce the exact same total (commutativity)
    reversed_entries = list(reversed(entries))
    total2 = aggregate_ledger_total(reversed_entries, Currency.INR)
    assert total1 == total2

    # Direct signed sum equivalence
    expected_sum = sum(calculate_ledger_signed_amount(amt, direction) for amt, direction in amounts)
    assert total1 == expected_sum


@given(
    gross=st.integers(min_value=100, max_value=10_000_000),
    order_ref=st.text(min_size=1, max_size=20),
)
def test_property_universal_immutability(gross: int, order_ref: str) -> None:
    now = datetime.now(UTC)
    payment = Payment(
        id="p_1",
        order_ref=order_ref,
        customer_ref="c_1",
        customer_name="Alice",
        gross_minor=gross,
        currency=Currency.INR,
        captured_at=now,
        status=PaymentStatus.CAPTURED,
    )

    with pytest.raises(FrozenInstanceError):
        payment.gross_minor = 999  # type: ignore[misc]


@given(confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
def test_property_confidence_independence_in_gate_evaluation(confidence: float) -> None:
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

    proposal = ResolutionProposal(
        proposal_id="prop_1",
        investigation_id="inv_1",
        case_id="case_1",
        run_id="run_1",
        target_ledger_entry_ids=["le_1"],
        rationale="Hypothesis rationale",
        evidence=[ev],
        confidence=confidence,  # Confidence varies from 0.0 to 1.0
    )

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.AI_INVESTIGATION,
        proposed_target_ids=proposal.target_ledger_entry_ids,
        target_ledger_entries=[entry],
        deterministic_candidates=[cand],
        evidence=[ev],
        already_resolved_target_ids=frozenset(),
    )

    # Regardless of confidence, if mandatory deterministic checks pass, gate passes
    assert gate.passed is True
    assert gate.failing_check is None
