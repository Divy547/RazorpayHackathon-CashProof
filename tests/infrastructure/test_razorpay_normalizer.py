"""Tests for Razorpay DTO -> domain normalization (pure functions, no network)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cashproof.application.ingestion import IngestionValidationError
from cashproof.domain.source import Settlement
from cashproof.domain.types import Currency, Direction, PaymentStatus, RefundStatus
from cashproof.infrastructure.razorpay.normalizer import (
    normalize_currency,
    normalize_epoch_timestamp,
    normalize_payment,
    normalize_refund,
    normalize_settlement,
    normalize_settlement_items,
    normalize_settlement_ledger_entry,
)


def test_normalize_currency_maps_iso_code() -> None:
    assert normalize_currency("inr", context="test") == Currency.INR


def test_normalize_currency_rejects_unsupported_code() -> None:
    with pytest.raises(IngestionValidationError):
        normalize_currency("GBP", context="test")


def test_normalize_epoch_timestamp_is_utc() -> None:
    dt = normalize_epoch_timestamp(1_700_000_000, context="test")
    assert dt.tzinfo == UTC


def test_normalize_epoch_timestamp_rejects_garbage() -> None:
    with pytest.raises(IngestionValidationError):
        normalize_epoch_timestamp("not-a-number", context="test")  # type: ignore[arg-type]


def test_normalize_payment_converts_paise_and_epoch() -> None:
    dto = {
        "id": "pay_ABC123",
        "amount": 500000,
        "currency": "INR",
        "status": "captured",
        "amount_refunded": 0,
        "created_at": 1_700_000_000,
        "order_id": "order_XYZ",
        "email": "buyer@example.com",
        "contact": "+911234567890",
    }
    payment = normalize_payment(dto)  # type: ignore[arg-type]
    assert payment.id == "pay_ABC123"
    assert payment.gross_minor == 500000
    assert payment.currency == Currency.INR
    assert payment.status == PaymentStatus.CAPTURED
    assert payment.order_ref == "order_XYZ"
    assert payment.captured_at.tzinfo == UTC


def test_normalize_payment_maps_partial_refund() -> None:
    dto = {
        "id": "pay_partial",
        "amount": 1000,
        "currency": "INR",
        "status": "captured",
        "amount_refunded": 400,
        "created_at": 1_700_000_000,
    }
    payment = normalize_payment(dto)  # type: ignore[arg-type]
    assert payment.status == PaymentStatus.PARTIALLY_REFUNDED


def test_normalize_payment_rejects_non_terminal_status() -> None:
    dto = {
        "id": "pay_created",
        "amount": 1000,
        "currency": "INR",
        "status": "created",
        "created_at": 1_700_000_000,
    }
    with pytest.raises(IngestionValidationError):
        normalize_payment(dto)  # type: ignore[arg-type]


def test_normalize_payment_missing_required_field_fails_closed() -> None:
    dto = {"id": "pay_missing_fields"}
    with pytest.raises(IngestionValidationError):
        normalize_payment(dto)  # type: ignore[arg-type]


def test_normalize_refund_links_to_payment() -> None:
    dto = {
        "id": "rfnd_ABC",
        "payment_id": "pay_ABC123",
        "amount": 20000,
        "currency": "INR",
        "status": "processed",
        "created_at": 1_700_000_500,
    }
    refund = normalize_refund(dto, netted_into_settlement=True)  # type: ignore[arg-type]
    assert refund.refund_id == "rfnd_ABC"
    assert refund.payment_id == "pay_ABC123"
    assert refund.amount_minor == 20000
    assert refund.status == RefundStatus.PROCESSED
    assert refund.netted_into_settlement is True


def test_normalize_settlement_maps_paise_amount() -> None:
    dto = {"id": "setl_XYZ", "amount": 999900, "created_at": 1_700_000_000}
    settlement = normalize_settlement(dto)  # type: ignore[arg-type]
    assert settlement.settlement_id == "setl_XYZ"
    assert settlement.net_deposited_minor == 999900
    assert settlement.currency == Currency.INR


def _settlement() -> Settlement:
    return Settlement(
        settlement_id="setl_XYZ",
        net_deposited_minor=98174,
        currency=Currency.INR,
        settled_at=datetime(2024, 1, 15, tzinfo=UTC),
    )


def test_normalize_settlement_items_computes_bridge() -> None:
    settlement = _settlement()
    recon_entries = [
        {
            "entity_id": "pay_ABC123",
            "type": "payment",
            "credit": 100000,
            "fee": 1600,
            "tax": 226,
            "settlement_id": "setl_XYZ",
        }
    ]
    items = normalize_settlement_items(recon_entries, settlement=settlement)  # type: ignore[arg-type]
    assert len(items) == 1
    item = items[0]
    assert item.payment_id == "pay_ABC123"
    assert item.gross_minor == 100000
    assert item.fee_minor == 1600
    assert item.tax_on_fee_minor == 226
    assert item.computed_net_minor == 100000 - 1600 - 226


def test_normalize_settlement_items_ignores_other_settlements_and_types() -> None:
    settlement = _settlement()
    recon_entries = [
        {
            "entity_id": "pay_other",
            "type": "payment",
            "credit": 1000,
            "settlement_id": "setl_OTHER",
        },
        {"entity_id": "adj_1", "type": "adjustment", "credit": 500, "settlement_id": "setl_XYZ"},
    ]
    items = normalize_settlement_items(recon_entries, settlement=settlement)  # type: ignore[arg-type]
    assert items == []


def test_normalize_settlement_items_rejects_missing_entity_id() -> None:
    settlement = _settlement()
    recon_entries = [{"type": "payment", "credit": 1000, "settlement_id": "setl_XYZ"}]
    with pytest.raises(IngestionValidationError):
        normalize_settlement_items(recon_entries, settlement=settlement)  # type: ignore[arg-type]


def test_normalize_settlement_ledger_entry_links_via_payment_ref() -> None:
    settlement = _settlement()
    entry = normalize_settlement_ledger_entry(settlement)
    assert entry.payment_ref == settlement.settlement_id
    assert entry.amount_minor == settlement.net_deposited_minor
    assert entry.direction == Direction.CREDIT
    assert entry.currency == settlement.currency
