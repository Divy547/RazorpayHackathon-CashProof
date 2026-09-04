"""Bank statement CSV -> LedgerEntry parsing.

Fail-closed by design: every row is validated before anything is returned. If
ANY row has a critical error (missing required column, invalid amount,
invalid/missing transaction_id, invalid timestamp, invalid currency, invalid
direction, or an in-file duplicate transaction_id whose data conflicts), the
ENTIRE batch is rejected via IngestionValidationError - never a partially
valid, unsafe subset.

Cross-run idempotency (the same transaction_id re-uploaded in a later file) is
NOT this module's concern - that is IngestionService's job, using the same
fingorint-based comparison it applies to every other source. This module only
detects and refuses *within-file* duplicate conflicts.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime

from cashproof.application.ingestion import IngestionValidationError
from cashproof.domain.source import LedgerEntry
from cashproof.domain.types import Currency, Direction

REQUIRED_COLUMNS = ("transaction_id", "timestamp", "amount_minor", "currency", "direction")
OPTIONAL_COLUMNS = ("payment_ref", "external_ref", "narration", "customer_name")


@dataclass(frozen=True, slots=True)
class BankCsvParseResult:
    ledger_entries: tuple[LedgerEntry, ...]
    row_count: int
    duplicate_in_file_count: int


def _parse_row(row: dict[str, str], *, row_num: int, errors: list[str]) -> LedgerEntry | None:
    transaction_id = (row.get("transaction_id") or "").strip()
    if not transaction_id:
        errors.append(f"Row {row_num}: missing required transaction_id")
        return None

    raw_timestamp = (row.get("timestamp") or "").strip()
    timestamp: datetime | None = None
    try:
        timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"Row {row_num} ({transaction_id}): invalid timestamp '{raw_timestamp}'")

    raw_amount = (row.get("amount_minor") or "").strip()
    amount_minor: int | None = None
    try:
        amount_minor = int(raw_amount)
        if amount_minor < 0:
            errors.append(f"Row {row_num} ({transaction_id}): amount_minor must be non-negative")
            amount_minor = None
    except ValueError:
        errors.append(f"Row {row_num} ({transaction_id}): invalid amount_minor '{raw_amount}'")

    raw_currency = (row.get("currency") or "").strip().upper()
    currency: Currency | None = None
    try:
        currency = Currency(raw_currency)
    except ValueError:
        errors.append(f"Row {row_num} ({transaction_id}): invalid currency '{raw_currency}'")

    raw_direction = (row.get("direction") or "").strip().upper()
    direction: Direction | None = None
    try:
        direction = Direction(raw_direction)
    except ValueError:
        errors.append(f"Row {row_num} ({transaction_id}): invalid direction '{raw_direction}'")

    if timestamp is None or amount_minor is None or currency is None or direction is None:
        return None

    def _optional(name: str) -> str | None:
        value = (row.get(name) or "").strip()
        return value or None

    try:
        return LedgerEntry(
            id=transaction_id,
            amount_minor=amount_minor,
            currency=currency,
            timestamp=timestamp,
            direction=direction,
            payment_ref=_optional("payment_ref"),
            external_ref=_optional("external_ref"),
            narration=_optional("narration"),
            customer_name=_optional("customer_name"),
        )
    except ValueError as exc:
        errors.append(f"Row {row_num} ({transaction_id}): {exc}")
        return None


def _fingerprint(entry: LedgerEntry) -> str:
    return (
        f"{entry.amount_minor}:{entry.currency}:{entry.direction}:"
        f"{entry.timestamp.isoformat()}:{entry.payment_ref}"
    )


def parse_bank_statement(csv_bytes: bytes) -> BankCsvParseResult:
    try:
        text = csv_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionValidationError([f"File is not valid UTF-8 text: {exc}"]) from exc

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing_columns:
        raise IngestionValidationError(
            [f"CSV is missing required column(s): {', '.join(missing_columns)}"]
        )

    errors: list[str] = []
    entries_by_id: dict[str, LedgerEntry] = {}
    duplicate_count = 0
    row_count = 0

    for row_num, row in enumerate(reader, start=2):
        row_count += 1
        entry = _parse_row(row, row_num=row_num, errors=errors)
        if entry is None:
            continue

        existing = entries_by_id.get(entry.id)
        if existing is None:
            entries_by_id[entry.id] = entry
        elif _fingerprint(existing) == _fingerprint(entry):
            duplicate_count += 1
        else:
            errors.append(
                f"Row {row_num}: transaction_id '{entry.id}' appears earlier in this file "
                "with different amount/currency/direction/timestamp/payment_ref"
            )

    if errors:
        raise IngestionValidationError(errors, fetched_count=row_count)

    return BankCsvParseResult(
        ledger_entries=tuple(entries_by_id.values()),
        row_count=row_count,
        duplicate_in_file_count=duplicate_count,
    )
