"""CashProof Pure Financial Calculations.

Pure functions owning deterministic monetary truth: bridge calculation, GST rounding,
ledger direction signs, and delta computation. All amounts in integer minor units.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from cashproof.domain.exceptions import CurrencyMismatchError
from cashproof.domain.types import Currency, Direction

if TYPE_CHECKING:
    from cashproof.domain.source import LedgerEntry


def calculate_settlement_item_net(
    gross_minor: int,
    fee_minor: int,
    tax_on_fee_minor: int,
    netted_refund_minor: int,
    adjustment_minor: int,
) -> int:
    """Compute the deterministic settlement item net amount.

    Bridge formula:
        computed_net = gross - fee - tax_on_fee - netted_refund + adjustment
    """
    return gross_minor - fee_minor - tax_on_fee_minor - netted_refund_minor + adjustment_minor


def calculate_gst_on_fee(fee_minor: int) -> int:
    """Calculate 18% GST on fee using half-up rounding on integer paise.

    Formula: (fee_minor * 18 + 50) // 100
    """
    if fee_minor < 0:
        raise ValueError(f"fee_minor must be non-negative, got {fee_minor}")
    return (fee_minor * 18 + 50) // 100


def calculate_ledger_signed_amount(amount_minor: int, direction: Direction) -> int:
    """Convert unsigned magnitude and direction into a signed integer contribution.

    CREDIT contributes +amount_minor, DEBIT contributes -amount_minor.
    """
    if amount_minor < 0:
        raise ValueError(f"amount_minor must be a non-negative magnitude, got {amount_minor}")
    if direction == Direction.CREDIT:
        return amount_minor
    if direction == Direction.DEBIT:
        return -amount_minor
    raise ValueError(f"Invalid direction: {direction}")


def aggregate_ledger_total(
    entries: Sequence[LedgerEntry],
    expected_currency: Currency,
) -> int:
    """Aggregate signed contributions from ledger entries, verifying single-currency consistency."""
    total = 0
    for entry in entries:
        if entry.currency != expected_currency:
            raise CurrencyMismatchError(
                f"LedgerEntry {entry.id} currency {entry.currency} != {expected_currency}"
            )
        total += calculate_ledger_signed_amount(entry.amount_minor, entry.direction)
    return total


def compute_case_delta(expected_net: int, observed_ledger_total: int) -> int:
    """Compute discrepancy delta: expected_net - observed_ledger_total."""
    return expected_net - observed_ledger_total
