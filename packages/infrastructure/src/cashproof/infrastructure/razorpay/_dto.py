"""Razorpay API response DTOs (private).

Mirrors Razorpay's own JSON field names verbatim so `normalizer.py` has one
place to translate them into domain vocabulary. Nothing here is imported
outside this sub-package - `cashproof.domain`/`cashproof.application` must
never see a "pay_xxx" id, an "entity" key, or a bare paise `amount` field.

Field sets are intentionally permissive (`total=False`) since Razorpay's API
returns additional fields we don't use; only the ones the normalizer reads
are declared.
"""

from __future__ import annotations

from typing import Any, TypedDict


class RazorpayPaymentDTO(TypedDict, total=False):
    id: str
    entity: str
    amount: int
    currency: str
    status: str
    order_id: str | None
    international: bool
    method: str
    amount_refunded: int
    captured: bool
    email: str
    contact: str
    created_at: int


class RazorpayRefundDTO(TypedDict, total=False):
    id: str
    entity: str
    amount: int
    currency: str
    payment_id: str
    status: str
    created_at: int


class RazorpaySettlementDTO(TypedDict, total=False):
    id: str
    entity: str
    amount: int
    status: str
    fees: int
    tax: int
    utr: str
    created_at: int


class RazorpayReconEntryDTO(TypedDict, total=False):
    """One row of GET /settlements/recon/combined."""

    entity_id: str
    type: str  # "payment" | "adjustment" | "refund" | ...
    debit: int
    credit: int
    amount: int
    fee: int
    tax: int
    adjustment: int
    on_hold: bool
    settled: bool
    settlement_id: str | None
    order_id: str | None
    settled_at: int | None
    created_at: int


class RazorpayListResponseDTO(TypedDict, total=False):
    entity: str
    count: int
    items: list[dict[str, Any]]
