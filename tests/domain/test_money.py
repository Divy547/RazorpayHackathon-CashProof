"""Tests for pure financial calculations and arithmetic invariants."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cashproof.domain.exceptions import CurrencyMismatchError
from cashproof.domain.money import (
    aggregate_ledger_total,
    calculate_gst_on_fee,
    calculate_ledger_signed_amount,
    calculate_settlement_item_net,
    compute_case_delta,
)
from cashproof.domain.source import LedgerEntry
from cashproof.domain.types import Currency, Direction


def test_calculate_settlement_item_net_standard() -> None:
    # 10000 gross - 200 fee - 36 tax - 1000 refund + 50 adj = 8814
    net = calculate_settlement_item_net(
        gross_minor=10000,
        fee_minor=200,
        tax_on_fee_minor=36,
        netted_refund_minor=1000,
        adjustment_minor=50,
    )
    assert net == 8814


def test_calculate_settlement_item_net_negative_adjustment() -> None:
    # negative adjustment decreases net
    net = calculate_settlement_item_net(
        gross_minor=10000,
        fee_minor=200,
        tax_on_fee_minor=36,
        netted_refund_minor=0,
        adjustment_minor=-150,
    )
    assert net == 10000 - 200 - 36 - 150  # 9614


def test_calculate_gst_on_fee_half_up_rounding() -> None:
    # 18% GST with half-up paise rounding
    assert calculate_gst_on_fee(100) == 18  # exactly 18.00
    assert calculate_gst_on_fee(105) == 19  # 18.9 -> 19
    assert calculate_gst_on_fee(0) == 0
    assert calculate_gst_on_fee(1) == 0  # 0.18 -> 0
    assert calculate_gst_on_fee(3) == 1  # 0.54 -> 1
    assert calculate_gst_on_fee(10000) == 1800


def test_calculate_gst_on_fee_negative_raises() -> None:
    with pytest.raises(ValueError, match="fee_minor must be non-negative"):
        calculate_gst_on_fee(-10)


def test_calculate_ledger_signed_amount() -> None:
    assert calculate_ledger_signed_amount(5000, Direction.CREDIT) == 5000
    assert calculate_ledger_signed_amount(5000, Direction.DEBIT) == -5000
    assert calculate_ledger_signed_amount(0, Direction.CREDIT) == 0


def test_calculate_ledger_signed_amount_negative_raises() -> None:
    with pytest.raises(ValueError, match="non-negative magnitude"):
        calculate_ledger_signed_amount(-500, Direction.CREDIT)


def test_aggregate_ledger_total() -> None:
    now = datetime.now(UTC)
    entries = [
        LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT),
        LedgerEntry("le_2", 2000, Currency.INR, now, Direction.DEBIT),
        LedgerEntry("le_3", 500, Currency.INR, now, Direction.CREDIT),
    ]
    # 10000 - 2000 + 500 = 8500
    assert aggregate_ledger_total(entries, Currency.INR) == 8500


def test_aggregate_ledger_total_currency_mismatch_raises() -> None:
    now = datetime.now(UTC)
    entries = [
        LedgerEntry("le_1", 10000, Currency.INR, now, Direction.CREDIT),
        LedgerEntry("le_2", 2000, Currency.USD, now, Direction.CREDIT),
    ]
    with pytest.raises(CurrencyMismatchError, match="currency"):
        aggregate_ledger_total(entries, Currency.INR)


def test_compute_case_delta() -> None:
    assert compute_case_delta(10000, 10000) == 0
    assert compute_case_delta(10000, 8000) == 2000
    assert compute_case_delta(10000, 12000) == -2000
