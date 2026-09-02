"""Tests for derived reconciliation entities: Evidence, MatchCandidate, ReconciliationCase."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from cashproof.domain.derived import (
    Evidence,
    EvidencePointer,
    MatchCandidate,
    ReconciliationCase,
)
from cashproof.domain.exceptions import SettlementItemSumMismatchError
from cashproof.domain.source import Settlement, SettlementItem
from cashproof.domain.types import (
    Currency,
    EvidenceStance,
    ExceptionType,
    MatchProvenance,
    ProcessingState,
)


def test_evidence_pointer_and_evidence_creation() -> None:
    ptr = EvidencePointer("Payment", "pay_100", "order_ref")
    assert ptr.entity_type == "Payment"
    assert ptr.field == "order_ref"

    ev = Evidence(
        pointer=ptr,
        relevance=0.95,
        stance=EvidenceStance.SUPPORTS,
        decision_consumed=True,
    )
    assert ev.relevance == 0.95
    assert ev.stance == EvidenceStance.SUPPORTS
    assert ev.decision_consumed is True

    with pytest.raises(FrozenInstanceError):
        ev.relevance = 1.0  # type: ignore[misc]


def test_evidence_relevance_validation() -> None:
    ptr = EvidencePointer("Payment", "pay_100", "order_ref")
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        Evidence(pointer=ptr, relevance=1.5, stance=EvidenceStance.SUPPORTS)
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        Evidence(pointer=ptr, relevance=-0.1, stance=EvidenceStance.SUPPORTS)
    with pytest.raises(ValueError, match="finite float"):
        Evidence(pointer=ptr, relevance=float("nan"), stance=EvidenceStance.SUPPORTS)


def test_match_candidate_defensive_copying_and_validation() -> None:
    signals = ["exact_order_ref", "amount_match"]
    traces = ["rule_1_ref_match"]

    candidate = MatchCandidate(
        case_id="case_1",
        ledger_entry_id="le_100",
        score=0.98,
        matched_signals=signals,
        rule_trace=traces,
        provenance=MatchProvenance.STRUCTURED_REFERENCE,
        engine_version="v1.0.0",
        run_id="run_1",
    )

    assert candidate.matched_signals == ("exact_order_ref", "amount_match")
    # Mutating caller collection does not mutate candidate
    signals.append("mutated_signal")
    assert candidate.matched_signals == ("exact_order_ref", "amount_match")

    with pytest.raises(FrozenInstanceError):
        candidate.score = 0.5  # type: ignore[misc]

    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        MatchCandidate(
            "case_1", "le_1", 1.2, (), (), MatchProvenance.STRUCTURED_REFERENCE, "v1", "r1"
        )


def test_reconciliation_case_factory_success() -> None:
    now = datetime.now(UTC)
    settlement = Settlement("set_10", 10000, Currency.INR, now)
    item = SettlementItem("it_1", "set_10", "p_1", 10000, 0, 0, 0, 0, 10000)

    case = ReconciliationCase.create(
        case_id="case_10",
        settlement=settlement,
        items=[item],
        observed_ledger_total=8000,
        exception_type=ExceptionType.AMOUNT_MISMATCH,
        run_id="run_1",
    )

    assert case.case_id == "case_10"
    assert case.settlement_id == "set_10"
    assert case.expected_net == 10000
    assert case.observed_ledger_total == 8000
    assert case.delta == 2000
    assert case.exception_type == ExceptionType.AMOUNT_MISMATCH
    assert case.processing_state == ProcessingState.INGESTED


def test_reconciliation_case_factory_validates_items() -> None:
    now = datetime.now(UTC)
    settlement = Settlement("set_10", 10000, Currency.INR, now)
    # Item net is 8000, but settlement net is 10000
    item = SettlementItem("it_1", "set_10", "p_1", 8000, 0, 0, 0, 0, 8000)

    with pytest.raises(SettlementItemSumMismatchError):
        ReconciliationCase.create(
            case_id="case_10",
            settlement=settlement,
            items=[item],
            observed_ledger_total=8000,
            exception_type=ExceptionType.AMOUNT_MISMATCH,
            run_id="run_1",
        )
