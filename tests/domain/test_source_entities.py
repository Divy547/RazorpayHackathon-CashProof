"""Tests for source financial entities and their self-contained invariants."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from cashproof.domain.exceptions import SettlementItemBridgeError
from cashproof.domain.source import (
    LedgerEntry,
    Payment,
    Refund,
    Settlement,
    SettlementItem,
)
from cashproof.domain.types import (
    Currency,
    Direction,
    PaymentStatus,
    RefundStatus,
)


def test_payment_creation_and_immutability() -> None:
    now = datetime.now(UTC)
    payment = Payment(
        id="pay_123",
        order_ref="ord_456",
        customer_ref="cust_789",
        customer_name="Alice Smith",
        gross_minor=50000,
        currency=Currency.INR,
        captured_at=now,
        status=PaymentStatus.CAPTURED,
    )
    assert payment.id == "pay_123"
    assert payment.gross_minor == 50000

    with pytest.raises(FrozenInstanceError):
        payment.gross_minor = 60000  # type: ignore[misc]


def test_payment_validation() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="id must not be empty"):
        Payment("", "ord_1", "cust_1", "Alice", 100, Currency.INR, now, PaymentStatus.CAPTURED)
    with pytest.raises(ValueError, match="gross_minor must be non-negative"):
        Payment("p_1", "ord_1", "cust_1", "Alice", -10, Currency.INR, now, PaymentStatus.CAPTURED)


def test_refund_creation_and_validation() -> None:
    now = datetime.now(UTC)
    refund = Refund(
        refund_id="rf_1",
        payment_id="pay_1",
        amount_minor=5000,
        currency=Currency.INR,
        created_at=now,
        status=RefundStatus.PROCESSED,
        netted_into_settlement=True,
    )
    assert refund.amount_minor == 5000

    with pytest.raises(FrozenInstanceError):
        refund.amount_minor = 6000  # type: ignore[misc]

    with pytest.raises(ValueError, match="amount_minor must be non-negative"):
        Refund("rf_2", "pay_1", -50, Currency.INR, now, RefundStatus.PROCESSED, True)


def test_settlement_item_bridge_enforcement() -> None:
    # 10000 - 200 - 36 - 1000 + 50 = 8814
    item = SettlementItem(
        item_id="item_1",
        settlement_id="set_1",
        payment_id="pay_1",
        gross_minor=10000,
        fee_minor=200,
        tax_on_fee_minor=36,
        netted_refund_minor=1000,
        adjustment_minor=50,
        computed_net_minor=8814,
    )
    assert item.computed_net_minor == 8814

    # Bridge mismatch raises SettlementItemBridgeError
    with pytest.raises(SettlementItemBridgeError, match="bridge violation"):
        SettlementItem(
            item_id="item_1",
            settlement_id="set_1",
            payment_id="pay_1",
            gross_minor=10000,
            fee_minor=200,
            tax_on_fee_minor=36,
            netted_refund_minor=1000,
            adjustment_minor=50,
            computed_net_minor=9000,  # Wrong!
        )


def test_settlement_creation_and_immutability() -> None:
    now = datetime.now(UTC)
    settlement = Settlement(
        settlement_id="set_1",
        net_deposited_minor=100000,
        currency=Currency.INR,
        settled_at=now,
    )
    assert settlement.settlement_id == "set_1"

    with pytest.raises(FrozenInstanceError):
        settlement.net_deposited_minor = 200000  # type: ignore[misc]


def test_ledger_entry_creation_and_validation() -> None:
    now = datetime.now(UTC)
    entry = LedgerEntry(
        id="le_1",
        amount_minor=50000,
        currency=Currency.INR,
        timestamp=now,
        direction=Direction.CREDIT,
        payment_ref="ord_123",
        external_ref="ext_456",
        narration="Test Narration",
        customer_name="Bob Jones",
    )
    assert entry.amount_minor == 50000
    assert entry.direction == Direction.CREDIT

    with pytest.raises(FrozenInstanceError):
        entry.amount_minor = 60000  # type: ignore[misc]

    with pytest.raises(ValueError, match="amount_minor must be non-negative"):
        LedgerEntry("le_2", -100, Currency.INR, now, Direction.CREDIT)
