"""Bank statement CSV ingestion adapter.

Produces only existing Phase 1 LedgerEntry objects. Fail-closed: any row with
a critical error (missing column, invalid amount/timestamp/currency/direction,
or an in-file duplicate transaction_id with conflicting data) rejects the
entire batch rather than silently ingesting a partially valid, unsafe file.
"""

from __future__ import annotations

from cashproof.infrastructure.bank.csv_parser import BankCsvParseResult, parse_bank_statement

__all__ = ["BankCsvParseResult", "parse_bank_statement"]
