"""Regression tests for BatchReconciler resilience (final review finding H1).

POST /api/reconcile previously aborted the ENTIRE batch when one settlement's
own source records failed a domain invariant (no items, or items that don't
sum to net_deposited_minor) - a single malformed/incomplete ingested
settlement would take down reconciliation for every other settlement too,
including the synthetic demo dataset. BatchReconciler.run() must now report
such a settlement as a SettlementReconciliationError instead of raising,
while still reconciling every valid settlement normally and fabricating
nothing (no case, no gate evaluation, no resolution) for the failed one.
"""

from __future__ import annotations

from datetime import UTC, datetime

from cashproof.application.batch import BatchReconciler
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.types import Currency, Direction, PaymentStatus

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)


def _valid_settlement(
    settlement_id: str, amount: int
) -> tuple[Settlement, SettlementItem, Payment, LedgerEntry]:
    settlement = Settlement(
        settlement_id=settlement_id,
        net_deposited_minor=amount,
        currency=Currency.INR,
        settled_at=FIXED_NOW,
    )
    item = SettlementItem(
        item_id=f"item_{settlement_id}",
        settlement_id=settlement_id,
        payment_id=f"pay_{settlement_id}",
        gross_minor=amount,
        fee_minor=0,
        tax_on_fee_minor=0,
        netted_refund_minor=0,
        adjustment_minor=0,
        computed_net_minor=amount,
    )
    payment = Payment(
        id=f"pay_{settlement_id}",
        order_ref=f"order_{settlement_id}",
        customer_ref="cust_1",
        customer_name="Test Customer",
        gross_minor=amount,
        currency=Currency.INR,
        captured_at=FIXED_NOW,
        status=PaymentStatus.CAPTURED,
    )
    ledger_entry = LedgerEntry(
        id=f"ledger_{settlement_id}",
        amount_minor=amount,
        currency=Currency.INR,
        timestamp=FIXED_NOW,
        direction=Direction.CREDIT,
        payment_ref=settlement_id,
    )
    return settlement, item, payment, ledger_entry


def test_zero_item_settlement_does_not_abort_the_batch() -> None:
    valid_1 = _valid_settlement("setl_valid_1", 100_000)
    valid_2 = _valid_settlement("setl_valid_2", 250_000)
    empty_settlement = Settlement(
        settlement_id="setl_empty",
        net_deposited_minor=50_000,
        currency=Currency.INR,
        settled_at=FIXED_NOW,
    )

    summary = BatchReconciler().run(
        run_id="resilience-test-empty",
        settlements=[valid_1[0], valid_2[0], empty_settlement],
        items_by_settlement={
            valid_1[0].settlement_id: [valid_1[1]],
            valid_2[0].settlement_id: [valid_2[1]],
            empty_settlement.settlement_id: [],
        },
        payments_by_settlement={
            valid_1[0].settlement_id: [valid_1[2]],
            valid_2[0].settlement_id: [valid_2[2]],
        },
        ledger_pool=[valid_1[3], valid_2[3]],
        now=FIXED_NOW,
    )

    assert summary.total_settlements == 3
    assert {r.case.case_id for r in summary.results} == {"setl_valid_1", "setl_valid_2"}
    assert len(summary.failed_settlements) == 1
    failure = summary.failed_settlements[0]
    assert failure.settlement_id == "setl_empty"
    assert failure.error_type == "EmptySettlementItemsError"
    # No fabricated case/resolution for the failed settlement anywhere in results.
    assert "setl_empty" not in {r.case.case_id for r in summary.results}


def test_settlement_item_sum_mismatch_does_not_abort_the_batch() -> None:
    valid = _valid_settlement("setl_valid", 100_000)
    mismatched_settlement = Settlement(
        settlement_id="setl_mismatch",
        net_deposited_minor=99_999,
        currency=Currency.INR,
        settled_at=FIXED_NOW,
    )
    # Internally bridge-consistent item (50_000 - 0 - 0 - 0 + 0 == 50_000), but
    # its sum (50_000) does not equal the settlement's net_deposited_minor (99_999).
    mismatched_item = SettlementItem(
        item_id="item_mismatch",
        settlement_id="setl_mismatch",
        payment_id="pay_mismatch",
        gross_minor=50_000,
        fee_minor=0,
        tax_on_fee_minor=0,
        netted_refund_minor=0,
        adjustment_minor=0,
        computed_net_minor=50_000,
    )

    summary = BatchReconciler().run(
        run_id="resilience-test-mismatch",
        settlements=[valid[0], mismatched_settlement],
        items_by_settlement={
            valid[0].settlement_id: [valid[1]],
            mismatched_settlement.settlement_id: [mismatched_item],
        },
        payments_by_settlement={valid[0].settlement_id: [valid[2]]},
        ledger_pool=[valid[3]],
        now=FIXED_NOW,
    )

    assert summary.total_settlements == 2
    assert {r.case.case_id for r in summary.results} == {"setl_valid"}
    assert len(summary.failed_settlements) == 1
    failure = summary.failed_settlements[0]
    assert failure.settlement_id == "setl_mismatch"
    assert failure.error_type == "SettlementItemSumMismatchError"


def test_all_valid_settlements_produce_zero_failures() -> None:
    valid_1 = _valid_settlement("setl_all_valid_1", 10_000)
    valid_2 = _valid_settlement("setl_all_valid_2", 20_000)

    summary = BatchReconciler().run(
        run_id="resilience-test-all-valid",
        settlements=[valid_1[0], valid_2[0]],
        items_by_settlement={
            valid_1[0].settlement_id: [valid_1[1]],
            valid_2[0].settlement_id: [valid_2[1]],
        },
        payments_by_settlement={
            valid_1[0].settlement_id: [valid_1[2]],
            valid_2[0].settlement_id: [valid_2[2]],
        },
        ledger_pool=[valid_1[3], valid_2[3]],
        now=FIXED_NOW,
    )

    assert summary.failed_settlements == ()
    assert len(summary.results) == 2


def test_multiple_malformed_settlements_are_all_reported_independently() -> None:
    valid = _valid_settlement("setl_valid_only", 5_000)
    empty_1 = Settlement(
        settlement_id="setl_empty_1",
        net_deposited_minor=1_000,
        currency=Currency.INR,
        settled_at=FIXED_NOW,
    )
    empty_2 = Settlement(
        settlement_id="setl_empty_2",
        net_deposited_minor=2_000,
        currency=Currency.INR,
        settled_at=FIXED_NOW,
    )

    summary = BatchReconciler().run(
        run_id="resilience-test-multi",
        settlements=[valid[0], empty_1, empty_2],
        items_by_settlement={valid[0].settlement_id: [valid[1]]},
        payments_by_settlement={valid[0].settlement_id: [valid[2]]},
        ledger_pool=[valid[3]],
        now=FIXED_NOW,
    )

    assert {r.case.case_id for r in summary.results} == {"setl_valid_only"}
    failed_ids = {f.settlement_id for f in summary.failed_settlements}
    assert failed_ids == {"setl_empty_1", "setl_empty_2"}
    assert all(f.error_type == "EmptySettlementItemsError" for f in summary.failed_settlements)
