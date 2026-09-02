"""CashProof Source Financial Entities.

Immutable domain representations of external source financial facts.
No truth/decoy/noise/scenario flags exist on source records.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from cashproof.domain.exceptions import (
    DuplicateRefundNettingError,
    EmptySettlementItemsError,
    RefundNettingMismatchError,
    SettlementAssociationError,
    SettlementItemBridgeError,
    SettlementItemSumMismatchError,
)
from cashproof.domain.money import calculate_settlement_item_net
from cashproof.domain.types import Currency, Direction, PaymentStatus, RefundStatus


@dataclass(frozen=True, slots=True)
class Payment:
    """Immutable source payment record."""

    id: str
    order_ref: str
    customer_ref: str
    customer_name: str
    gross_minor: int
    currency: Currency
    captured_at: datetime
    status: PaymentStatus

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Payment id must not be empty.")
        if self.gross_minor < 0:
            raise ValueError(f"Payment gross_minor must be non-negative, got {self.gross_minor}")


@dataclass(frozen=True, slots=True)
class Refund:
    """Immutable source refund record."""

    refund_id: str
    payment_id: str
    amount_minor: int
    currency: Currency
    created_at: datetime
    status: RefundStatus
    netted_into_settlement: bool

    def __post_init__(self) -> None:
        if not self.refund_id.strip():
            raise ValueError("Refund refund_id must not be empty.")
        if not self.payment_id.strip():
            raise ValueError("Refund payment_id must not be empty.")
        if self.amount_minor < 0:
            raise ValueError(f"Refund amount_minor must be non-negative, got {self.amount_minor}")


@dataclass(frozen=True, slots=True)
class SettlementItem:
    """Immutable source settlement breakdown item.

    SettlementItem intentionally does not store currency independently; it inherits currency
    from its parent Settlement.
    """

    item_id: str
    settlement_id: str
    payment_id: str
    gross_minor: int
    fee_minor: int
    tax_on_fee_minor: int
    netted_refund_minor: int
    adjustment_minor: int
    computed_net_minor: int

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("SettlementItem item_id must not be empty.")
        if not self.settlement_id.strip():
            raise ValueError("SettlementItem settlement_id must not be empty.")
        if not self.payment_id.strip():
            raise ValueError("SettlementItem payment_id must not be empty.")
        if self.gross_minor < 0:
            raise ValueError(f"gross_minor must be non-negative, got {self.gross_minor}")
        if self.fee_minor < 0:
            raise ValueError(f"fee_minor must be non-negative, got {self.fee_minor}")
        if self.tax_on_fee_minor < 0:
            raise ValueError(f"tax_on_fee_minor must be non-negative, got {self.tax_on_fee_minor}")
        if self.netted_refund_minor < 0:
            raise ValueError(
                f"netted_refund_minor must be non-negative, got {self.netted_refund_minor}"
            )

        expected_net = calculate_settlement_item_net(
            gross_minor=self.gross_minor,
            fee_minor=self.fee_minor,
            tax_on_fee_minor=self.tax_on_fee_minor,
            netted_refund_minor=self.netted_refund_minor,
            adjustment_minor=self.adjustment_minor,
        )
        if self.computed_net_minor != expected_net:
            raise SettlementItemBridgeError(
                f"SettlementItem {self.item_id} bridge violation: computed_net_minor "
                f"({self.computed_net_minor}) != expected ({expected_net})"
            )


@dataclass(frozen=True, slots=True)
class Settlement:
    """Immutable source settlement aggregate record."""

    settlement_id: str
    net_deposited_minor: int
    currency: Currency
    settled_at: datetime

    def __post_init__(self) -> None:
        if not self.settlement_id.strip():
            raise ValueError("Settlement settlement_id must not be empty.")


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """Immutable source bank/internal ledger entry record."""

    id: str
    amount_minor: int
    currency: Currency
    timestamp: datetime
    direction: Direction
    payment_ref: str | None = None
    external_ref: str | None = None
    narration: str | None = None
    customer_name: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("LedgerEntry id must not be empty.")
        if self.amount_minor < 0:
            raise ValueError(
                f"LedgerEntry amount_minor must be non-negative, got {self.amount_minor}"
            )


def validate_settlement_items_aggregation(
    settlement: Settlement,
    items: Sequence[SettlementItem],
) -> None:
    """Validate settlement items aggregation matches Settlement net_deposited_minor."""
    if not items:
        raise EmptySettlementItemsError(
            f"Settlement {settlement.settlement_id} contains no settlement items."
        )

    for item in items:
        if item.settlement_id != settlement.settlement_id:
            raise SettlementAssociationError(
                f"SettlementItem {item.item_id} has settlement_id '{item.settlement_id}', "
                f"expected '{settlement.settlement_id}'"
            )

    total_items_net = sum(item.computed_net_minor for item in items)
    if total_items_net != settlement.net_deposited_minor:
        raise SettlementItemSumMismatchError(
            f"Settlement {settlement.settlement_id} net_deposited_minor "
            f"({settlement.net_deposited_minor}) does not equal items sum ({total_items_net})"
        )


def validate_refund_netting_invariant(
    items: Sequence[SettlementItem],
    refunds: Sequence[Refund],
) -> None:
    """Validate that across all items, netted_refund_minor matches applicable refunds per payment.

    Enforces:
    - No single refund_id is duplicate in the refund list.
    - Total claimed netted refund for a payment equals available netted refunds for that payment.
    """
    seen_refund_ids: set[str] = set()
    available_by_payment: dict[str, int] = {}

    for r in refunds:
        if r.netted_into_settlement:
            if r.refund_id in seen_refund_ids:
                raise DuplicateRefundNettingError(
                    f"Refund {r.refund_id} is claimed across multiple settlement items."
                )
            seen_refund_ids.add(r.refund_id)
            available_by_payment[r.payment_id] = (
                available_by_payment.get(r.payment_id, 0) + r.amount_minor
            )

    claimed_by_payment: dict[str, int] = {}
    for item in items:
        claimed_by_payment[item.payment_id] = (
            claimed_by_payment.get(item.payment_id, 0) + item.netted_refund_minor
        )

    all_payments = set(claimed_by_payment.keys()) | set(available_by_payment.keys())
    for payment_id in all_payments:
        claimed = claimed_by_payment.get(payment_id, 0)
        available = available_by_payment.get(payment_id, 0)
        if claimed != available:
            raise RefundNettingMismatchError(
                f"Payment {payment_id} total claimed netted refund ({claimed}) "
                f"!= available netted refunds ({available})"
            )
