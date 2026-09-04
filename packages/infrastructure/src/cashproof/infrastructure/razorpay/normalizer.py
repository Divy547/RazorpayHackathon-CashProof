"""Razorpay DTO -> Phase 1 domain object normalization.

Pure functions: no I/O. Converts paise (already integer minor units) as-is,
Unix epoch seconds to UTC datetimes, and ISO currency codes to the existing
Currency enum. Raises IngestionValidationError (application-defined, reused
here rather than inventing a parallel exception hierarchy) on any record that
cannot be safely mapped onto an existing domain invariant - normalization
never silently guesses or drops a field.
"""

from __future__ import annotations

from datetime import UTC, datetime

from cashproof.application.ingestion import IngestionValidationError
from cashproof.domain.money import calculate_settlement_item_net
from cashproof.domain.source import LedgerEntry, Payment, Refund, Settlement, SettlementItem
from cashproof.domain.types import Currency, Direction, PaymentStatus, RefundStatus
from cashproof.infrastructure.razorpay._dto import (
    RazorpayPaymentDTO,
    RazorpayReconEntryDTO,
    RazorpayRefundDTO,
    RazorpaySettlementDTO,
)


def normalize_currency(raw: str, *, context: str) -> Currency:
    try:
        return Currency(raw.upper())
    except ValueError as exc:
        raise IngestionValidationError([f"{context}: unsupported currency '{raw}'"]) from exc


def normalize_epoch_timestamp(epoch_seconds: int, *, context: str) -> datetime:
    try:
        return datetime.fromtimestamp(int(epoch_seconds), tz=UTC)
    except (TypeError, ValueError, OSError) as exc:
        raise IngestionValidationError(
            [f"{context}: invalid Unix epoch timestamp '{epoch_seconds}'"]
        ) from exc


def _map_payment_status(dto: RazorpayPaymentDTO) -> PaymentStatus:
    raw = str(dto.get("status", ""))
    amount = int(dto.get("amount", 0) or 0)
    refunded = int(dto.get("amount_refunded", 0) or 0)
    if refunded > 0 and refunded >= amount and amount > 0:
        return PaymentStatus.REFUNDED
    if refunded > 0:
        return PaymentStatus.PARTIALLY_REFUNDED
    if raw == "captured":
        return PaymentStatus.CAPTURED
    if raw == "failed":
        return PaymentStatus.FAILED
    raise IngestionValidationError(
        [
            f"Payment {dto.get('id', '<unknown>')}: unrecognized/non-terminal status "
            f"'{raw}' is not eligible for read-only reconciliation ingestion"
        ]
    )


def normalize_payment(dto: RazorpayPaymentDTO) -> Payment:
    payment_id = dto.get("id")
    if not payment_id:
        raise IngestionValidationError(["Payment record missing required field 'id'"])
    try:
        return Payment(
            id=payment_id,
            order_ref=dto.get("order_id") or payment_id,
            customer_ref=dto.get("contact") or dto.get("email") or payment_id,
            # Razorpay's read API exposes contact/email, not a display name;
            # email is the closest available proxy for customer_name.
            customer_name=dto.get("email") or "unknown@razorpay",
            gross_minor=int(dto["amount"]),
            currency=normalize_currency(str(dto["currency"]), context=f"Payment {payment_id}"),
            captured_at=normalize_epoch_timestamp(
                int(dto["created_at"]), context=f"Payment {payment_id}"
            ),
            status=_map_payment_status(dto),
        )
    except KeyError as exc:
        raise IngestionValidationError(
            [f"Payment {payment_id}: missing required field {exc}"]
        ) from exc
    except ValueError as exc:
        raise IngestionValidationError([f"Payment {payment_id}: {exc}"]) from exc


def _map_refund_status(raw: str) -> RefundStatus:
    mapping = {
        "processed": RefundStatus.PROCESSED,
        "pending": RefundStatus.PENDING,
        "failed": RefundStatus.FAILED,
    }
    try:
        return mapping[raw]
    except KeyError as exc:
        raise IngestionValidationError([f"Refund: unrecognized status '{raw}'"]) from exc


def normalize_refund(dto: RazorpayRefundDTO, *, netted_into_settlement: bool) -> Refund:
    refund_id = dto.get("id")
    payment_id = dto.get("payment_id")
    if not refund_id or not payment_id:
        raise IngestionValidationError(["Refund record missing required id/payment_id"])
    try:
        return Refund(
            refund_id=refund_id,
            payment_id=payment_id,
            amount_minor=int(dto["amount"]),
            currency=normalize_currency(str(dto["currency"]), context=f"Refund {refund_id}"),
            created_at=normalize_epoch_timestamp(
                int(dto["created_at"]), context=f"Refund {refund_id}"
            ),
            status=_map_refund_status(str(dto.get("status", ""))),
            netted_into_settlement=netted_into_settlement,
        )
    except KeyError as exc:
        raise IngestionValidationError(
            [f"Refund {refund_id}: missing required field {exc}"]
        ) from exc
    except ValueError as exc:
        raise IngestionValidationError([f"Refund {refund_id}: {exc}"]) from exc


def normalize_settlement(dto: RazorpaySettlementDTO) -> Settlement:
    settlement_id = dto.get("id")
    if not settlement_id:
        raise IngestionValidationError(["Settlement record missing required field 'id'"])
    try:
        return Settlement(
            settlement_id=settlement_id,
            net_deposited_minor=int(dto["amount"]),
            # Razorpay settlement list responses do not carry an explicit
            # currency field (test-mode settlements are always INR); default
            # matches the MVP's INR-only scope per docs/DECISIONS.md #6.
            currency=normalize_currency(
                str(dto.get("currency", "INR")), context=f"Settlement {settlement_id}"
            ),
            settled_at=normalize_epoch_timestamp(
                int(dto["created_at"]), context=f"Settlement {settlement_id}"
            ),
        )
    except KeyError as exc:
        raise IngestionValidationError(
            [f"Settlement {settlement_id}: missing required field {exc}"]
        ) from exc
    except ValueError as exc:
        raise IngestionValidationError([f"Settlement {settlement_id}: {exc}"]) from exc


def normalize_settlement_items(
    recon_entries: list[RazorpayReconEntryDTO],
    *,
    settlement: Settlement,
) -> list[SettlementItem]:
    """Builds one SettlementItem per payment-type recon row for this settlement.

    Refuses (fail closed) rather than silently coercing when a row's own
    numbers don't satisfy the domain's bridge invariant
    (gross - fee - tax - refund + adjustment == computed_net) - that
    invariant is enforced again inside SettlementItem.__post_init__ regardless.
    """
    items: list[SettlementItem] = []
    for entry in recon_entries:
        if entry.get("type") != "payment":
            continue
        if entry.get("settlement_id") != settlement.settlement_id:
            continue
        payment_id = entry.get("entity_id")
        if not payment_id:
            raise IngestionValidationError(
                [f"Settlement {settlement.settlement_id}: recon entry missing entity_id"]
            )
        gross_minor = int(entry.get("credit", entry.get("amount", 0)) or 0)
        fee_minor = int(entry.get("fee", 0) or 0)
        tax_minor = int(entry.get("tax", 0) or 0)
        adjustment_minor = int(entry.get("adjustment", 0) or 0)
        # Recon-report entries embed net refunds already deducted from
        # `debit`; this adapter does not attempt to reverse-derive a
        # per-payment netted refund split from the combined report alone -
        # see docs/ARCHITECTURE.md Phase 9 limitations.
        netted_refund_minor = 0
        computed_net_minor = calculate_settlement_item_net(
            gross_minor=gross_minor,
            fee_minor=fee_minor,
            tax_on_fee_minor=tax_minor,
            netted_refund_minor=netted_refund_minor,
            adjustment_minor=adjustment_minor,
        )
        items.append(
            SettlementItem(
                item_id=f"item_{settlement.settlement_id}_{payment_id}",
                settlement_id=settlement.settlement_id,
                payment_id=payment_id,
                gross_minor=gross_minor,
                fee_minor=fee_minor,
                tax_on_fee_minor=tax_minor,
                netted_refund_minor=netted_refund_minor,
                adjustment_minor=adjustment_minor,
                computed_net_minor=computed_net_minor,
            )
        )
    return items


def normalize_settlement_ledger_entry(settlement: Settlement) -> LedgerEntry:
    """The settlement payout itself as a bank-side ledger fact.

    Razorpay settlements deposit into the merchant's bank account as one
    credit; `payment_ref` links it structurally to the settlement, mirroring
    exactly how the synthetic Phase 2 generator links a LedgerEntry to its
    settlement (see cashproof.application.observation).
    """
    return LedgerEntry(
        id=f"ledger_{settlement.settlement_id}",
        amount_minor=settlement.net_deposited_minor,
        currency=settlement.currency,
        timestamp=settlement.settled_at,
        direction=Direction.CREDIT,
        payment_ref=settlement.settlement_id,
        external_ref=None,
        narration=f"Razorpay settlement {settlement.settlement_id}",
        customer_name=None,
    )
