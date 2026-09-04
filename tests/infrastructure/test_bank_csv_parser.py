"""Tests for the bank statement CSV parser - fail-closed on any critical row error."""

from __future__ import annotations

from pathlib import Path

import pytest
from cashproof.application.ingestion import IngestionValidationError
from cashproof.domain.types import Currency, Direction
from cashproof.infrastructure.bank.csv_parser import parse_bank_statement

HEADER = (
    "transaction_id,timestamp,amount_minor,currency,direction,"
    "payment_ref,external_ref,narration,customer_name"
)


def _csv(*rows: str) -> bytes:
    return "\n".join([HEADER, *rows]).encode("utf-8")


def test_valid_csv_parses_all_rows() -> None:
    result = parse_bank_statement(
        _csv(
            "txn_1,2024-01-05T09:30:00+00:00,100000,INR,CREDIT,setl_1,,note,",
            "txn_2,2024-01-06T09:30:00+00:00,5000,INR,DEBIT,,ext_1,fee,",
        )
    )
    assert result.row_count == 2
    assert result.duplicate_in_file_count == 0
    assert len(result.ledger_entries) == 2
    entry = next(e for e in result.ledger_entries if e.id == "txn_1")
    assert entry.amount_minor == 100000
    assert entry.currency == Currency.INR
    assert entry.direction == Direction.CREDIT
    assert entry.payment_ref == "setl_1"


def test_missing_required_column_fails_closed() -> None:
    bad_header = "transaction_id,timestamp,amount_minor,currency"
    with pytest.raises(IngestionValidationError):
        parse_bank_statement(f"{bad_header}\ntxn_1,2024-01-05T00:00:00+00:00,100,INR".encode())


def test_invalid_amount_rejects_entire_batch() -> None:
    with pytest.raises(IngestionValidationError) as exc_info:
        parse_bank_statement(
            _csv(
                "txn_1,2024-01-05T09:30:00+00:00,100000,INR,CREDIT,,,,",
                "txn_2,2024-01-06T09:30:00+00:00,not-a-number,INR,DEBIT,,,,",
            )
        )
    assert any("amount_minor" in e for e in exc_info.value.errors)


def test_negative_amount_rejects_entire_batch() -> None:
    with pytest.raises(IngestionValidationError):
        parse_bank_statement(_csv("txn_1,2024-01-05T09:30:00+00:00,-100,INR,CREDIT,,,,"))


def test_invalid_timestamp_rejects_entire_batch() -> None:
    with pytest.raises(IngestionValidationError) as exc_info:
        parse_bank_statement(_csv("txn_1,not-a-date,100000,INR,CREDIT,,,,"))
    assert any("timestamp" in e for e in exc_info.value.errors)


def test_invalid_currency_rejects_entire_batch() -> None:
    with pytest.raises(IngestionValidationError) as exc_info:
        parse_bank_statement(_csv("txn_1,2024-01-05T09:30:00+00:00,100000,GBP,CREDIT,,,,"))
    assert any("currency" in e for e in exc_info.value.errors)


def test_invalid_direction_rejects_entire_batch() -> None:
    with pytest.raises(IngestionValidationError) as exc_info:
        parse_bank_statement(_csv("txn_1,2024-01-05T09:30:00+00:00,100000,INR,SIDEWAYS,,,,"))
    assert any("direction" in e for e in exc_info.value.errors)


def test_empty_transaction_id_rejects_entire_batch() -> None:
    with pytest.raises(IngestionValidationError):
        parse_bank_statement(_csv(",2024-01-05T09:30:00+00:00,100000,INR,CREDIT,,,,"))


def test_one_malformed_row_rejects_the_whole_valid_batch() -> None:
    """Fail-closed: a single bad row must not let the other, valid rows through."""
    with pytest.raises(IngestionValidationError):
        parse_bank_statement(
            _csv(
                "txn_good,2024-01-05T09:30:00+00:00,100000,INR,CREDIT,,,,",
                "txn_bad,2024-01-06T09:30:00+00:00,-1,INR,CREDIT,,,,",
            )
        )


def test_identical_duplicate_transaction_id_counted_not_rejected() -> None:
    row = "txn_dup,2024-01-05T09:30:00+00:00,100000,INR,CREDIT,setl_1,,,"
    result = parse_bank_statement(_csv(row, row))
    assert result.duplicate_in_file_count == 1
    assert len(result.ledger_entries) == 1


def test_conflicting_duplicate_transaction_id_rejects_entire_batch() -> None:
    with pytest.raises(IngestionValidationError):
        parse_bank_statement(
            _csv(
                "txn_dup,2024-01-05T09:30:00+00:00,100000,INR,CREDIT,,,,",
                "txn_dup,2024-01-05T09:30:00+00:00,999999,INR,CREDIT,,,,",
            )
        )


def test_sample_statement_file_is_deterministic_and_parses_cleanly() -> None:
    sample_path = (
        Path(__file__).resolve().parents[2]
        / "packages"
        / "infrastructure"
        / "src"
        / "cashproof"
        / "infrastructure"
        / "bank"
        / "sample_statement.csv"
    )
    csv_bytes = sample_path.read_bytes()
    result_a = parse_bank_statement(csv_bytes)
    result_b = parse_bank_statement(csv_bytes)
    assert result_a.row_count == result_b.row_count
    assert {e.id for e in result_a.ledger_entries} == {e.id for e in result_b.ledger_entries}
    assert result_a.row_count > 0
