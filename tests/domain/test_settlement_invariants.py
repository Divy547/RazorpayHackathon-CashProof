"""Tests for settlement aggregation and refund netting invariants."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cashproof.domain.exceptions import (
    DuplicateRefundNettingError,
    EmptySettlementItemsError,
    RefundNettingMismatchError,
    SettlementAssociationError,
    SettlementItemSumMismatchError,
)
from cashproof.domain.source import (
    Refund,
    Settlement,
    SettlementItem,
    validate_refund_netting_invariant,
    validate_settlement_items_aggregation,
)
from cashproof.domain.types import Currency, RefundStatus


def test_settlement_items_aggregation_success() -> None:
    now = datetime.now(UTC)
    settlement = Settlement("set_100", 25000, Currency.INR, now)

    # Item 1: 15000 - 300 - 54 - 0 + 0 = 14646
    item1 = SettlementItem("item_1", "set_100", "p_1", 15000, 300, 54, 0, 0, 14646)
    # Item 2: 11000 - 200 - 36 - 500 + 90 = 10354
    item2 = SettlementItem("item_2", "set_100", "p_2", 11000, 200, 36, 500, 90, 10354)

    # Total: 14646 + 10354 = 25000
    validate_settlement_items_aggregation(settlement, [item1, item2])


def test_settlement_items_aggregation_empty_raises() -> None:
    now = datetime.now(UTC)
    settlement = Settlement("set_100", 25000, Currency.INR, now)
    with pytest.raises(EmptySettlementItemsError):
        validate_settlement_items_aggregation(settlement, [])


def test_settlement_items_aggregation_wrong_settlement_id_raises() -> None:
    now = datetime.now(UTC)
    settlement = Settlement("set_100", 25000, Currency.INR, now)
    item = SettlementItem("item_1", "set_999", "p_1", 25000, 0, 0, 0, 0, 25000)

    with pytest.raises(SettlementAssociationError, match="set_999"):
        validate_settlement_items_aggregation(settlement, [item])


def test_settlement_items_aggregation_sum_mismatch_raises() -> None:
    now = datetime.now(UTC)
    settlement = Settlement("set_100", 25000, Currency.INR, now)
    item = SettlementItem("item_1", "set_100", "p_1", 20000, 0, 0, 0, 0, 20000)

    with pytest.raises(SettlementItemSumMismatchError, match="does not equal items sum"):
        validate_settlement_items_aggregation(settlement, [item])


def test_refund_netting_invariant_success() -> None:
    now = datetime.now(UTC)
    # SettlementItem with netted_refund_minor = 1500
    item = SettlementItem("item_1", "set_1", "pay_10", 10000, 200, 36, 1500, 0, 8264)

    refund1 = Refund("rf_1", "pay_10", 1000, Currency.INR, now, RefundStatus.PROCESSED, True)
    refund2 = Refund("rf_2", "pay_10", 500, Currency.INR, now, RefundStatus.PROCESSED, True)
    # Refund not netted into settlement should be ignored
    refund3 = Refund("rf_3", "pay_10", 2000, Currency.INR, now, RefundStatus.PROCESSED, False)

    validate_refund_netting_invariant([item], [refund1, refund2, refund3])


def test_refund_netting_invariant_sum_mismatch_raises() -> None:
    now = datetime.now(UTC)
    item = SettlementItem("item_1", "set_1", "pay_10", 10000, 200, 36, 1500, 0, 8264)
    # Only 1000 netted instead of 1500
    refund1 = Refund("rf_1", "pay_10", 1000, Currency.INR, now, RefundStatus.PROCESSED, True)

    with pytest.raises(RefundNettingMismatchError, match="total claimed netted refund"):
        validate_refund_netting_invariant([item], [refund1])


def test_refund_netting_invariant_duplicate_claim_raises() -> None:
    now = datetime.now(UTC)
    # Two settlement items claiming the same netted refund
    item1 = SettlementItem("item_1", "set_1", "pay_1", 10000, 200, 36, 1000, 0, 8764)
    item2 = SettlementItem("item_2", "set_1", "pay_2", 10000, 200, 36, 1000, 0, 8764)

    refund = Refund("rf_1", "pay_1", 1000, Currency.INR, now, RefundStatus.PROCESSED, True)
    # Passing the same refund twice
    with pytest.raises(DuplicateRefundNettingError, match="claimed across multiple"):
        validate_refund_netting_invariant([item1, item2], [refund, refund])


def test_refund_netting_double_claim_same_payment_id_raises() -> None:
    now = datetime.now(UTC)
    # Two items with the SAME payment_id both claiming 1000 refund
    item1 = SettlementItem("item_1", "set_1", "pay_10", 10000, 200, 36, 1000, 0, 8764)
    item2 = SettlementItem("item_2", "set_1", "pay_10", 10000, 200, 36, 1000, 0, 8764)

    # Only one refund of 1000 exists
    refund = Refund("rf_1", "pay_10", 1000, Currency.INR, now, RefundStatus.PROCESSED, True)

    # Total claimed (2000) != total available (1000) -> must fail!
    with pytest.raises(RefundNettingMismatchError, match="total claimed netted refund"):
        validate_refund_netting_invariant([item1, item2], [refund])


def test_refund_netting_split_claim_across_items_success() -> None:
    now = datetime.now(UTC)
    # Two items sharing payment_id, splitting the 1000 refund as 600 + 400
    item1 = SettlementItem("item_1", "set_1", "pay_10", 10000, 200, 36, 600, 0, 9164)
    item2 = SettlementItem("item_2", "set_1", "pay_10", 10000, 200, 36, 400, 0, 9364)

    refund = Refund("rf_1", "pay_10", 1000, Currency.INR, now, RefundStatus.PROCESSED, True)

    # Total claimed (1000) == total available (1000) -> passes!
    validate_refund_netting_invariant([item1, item2], [refund])
