"""CashProof Ingestion CLI.

Demonstrates Phase 9 ingestion as a standalone operational tool: connector
status, bank statement CSV ingestion, and reconciling freshly ingested data
through the EXISTING, unmodified BatchReconciler. This module contains no
business logic of its own - every decision is delegated to
cashproof.application.ingestion.IngestionService and
cashproof.application.batch.BatchReconciler.

Run with: uv run python -m cashproof.cli.ingestion <subcommand>
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from cashproof.application.batch import BatchReconciler
from cashproof.application.ingestion import (
    DuplicateSourceConflictError,
    IngestionService,
    IngestionValidationError,
)
from cashproof.application.ports import IngestionRun, NormalizedSourceBatch
from cashproof.application.store import InMemoryCaseStore
from cashproof.domain.source import Payment, SettlementItem
from cashproof.infrastructure.bank.csv_parser import parse_bank_statement
from cashproof.infrastructure.razorpay import RazorpayConnector

SAMPLE_STATEMENT_PATH = (
    Path(__file__).resolve().parents[5]
    / "packages"
    / "infrastructure"
    / "src"
    / "cashproof"
    / "infrastructure"
    / "bank"
    / "sample_statement.csv"
)


def _empty_store() -> InMemoryCaseStore:
    return InMemoryCaseStore(
        run_id="cli-ingestion-run",
        settlements={},
        items_by_settlement={},
        payments_by_settlement={},
        ledger_pool=[],
    )


def _print_run(run: IngestionRun) -> None:
    print(f"  run_id:      {run.run_id}")
    print(f"  source:      {run.source}")
    print(f"  status:      {run.status.value}")
    print(f"  fetched:     {run.fetched_count}")
    print(f"  accepted:    {run.accepted_count}")
    print(f"  rejected:    {run.rejected_count}")
    print(f"  duplicate:   {run.duplicate_count}")
    if run.failure_reason:
        print(f"  failure:     {run.failure_reason}")
    for err in run.validation_errors:
        print(f"    - {err}")


def _cmd_status(_args: argparse.Namespace) -> int:
    connector = RazorpayConnector()
    status = connector.status()
    print("Razorpay connector status")
    print(f"  configured: {status.configured}")
    print(f"  detail:     {status.detail}")
    return 0


def _cmd_ingest_bank(args: argparse.Namespace) -> int:
    file_path = Path(args.file) if args.file else SAMPLE_STATEMENT_PATH
    store = _empty_store()
    ingestion_service = IngestionService(store)
    now = datetime.now(UTC)

    csv_bytes = file_path.read_bytes()
    print(f"Ingesting bank statement: {file_path}")
    try:
        parse_result = parse_bank_statement(csv_bytes)
    except IngestionValidationError as exc:
        run = ingestion_service.record_validation_failure(
            source="bank_statement", error=exc, now=now
        )
        _print_run(run)
        return 1

    batch = NormalizedSourceBatch(ledger_entries=parse_result.ledger_entries)
    try:
        run = ingestion_service.ingest_batch(
            source="bank_statement",
            batch=batch,
            fetched_count=parse_result.row_count,
            now=now,
        )
    except DuplicateSourceConflictError as exc:
        print(f"FAILED: {exc}")
        return 1

    _print_run(run)

    if args.reconcile:
        print()
        print("Reconciling ingested source records via the existing BatchReconciler...")
        _reconcile_store(store)
    return 0


def _cmd_ingest_razorpay(args: argparse.Namespace) -> int:
    connector = RazorpayConnector()
    store = _empty_store()
    ingestion_service = IngestionService(store)
    now = datetime.now(UTC)

    run = ingestion_service.ingest_from_connector(
        connector, source="razorpay", year=args.year, month=args.month, now=now
    )
    print("Razorpay ingestion result")
    _print_run(run)

    if args.reconcile and run.status.value == "COMPLETED":
        print()
        print("Reconciling ingested source records via the existing BatchReconciler...")
        _reconcile_store(store)
    return 0 if run.status.value == "COMPLETED" else 1


def _reconcile_store(store: InMemoryCaseStore) -> None:
    items_by_settlement: dict[str, list[SettlementItem]] = defaultdict(
        list, store.items_by_settlement
    )
    payments_by_settlement: dict[str, list[Payment]] = defaultdict(
        list, store.payments_by_settlement
    )

    summary = BatchReconciler().run(
        run_id=store.run_id,
        settlements=list(store.settlements.values()),
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=store.ledger_pool,
        now=datetime.now(UTC),
    )
    print(f"  settlements reconciled: {summary.total_settlements}")
    print(f"  AUTO_RESOLVED:          {summary.auto_resolved_count}")
    print(f"  HUMAN_REVIEW:           {summary.human_review_count}")
    print(f"  UNRESOLVED:             {summary.unresolved_count}")
    if summary.failed_settlements:
        print(f"  FAILED (rejected):      {len(summary.failed_settlements)}")
        for failure in summary.failed_settlements:
            print(f"    - {failure.settlement_id}: {failure.error_type}: {failure.message}")


def run_cli() -> int:
    parser = argparse.ArgumentParser(description="CashProof Ingestion CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Show Razorpay connector configuration status")

    ingest_bank = subparsers.add_parser("ingest-bank", help="Ingest a bank statement CSV")
    ingest_bank.add_argument(
        "--file", type=str, default=None, help="Path to a bank statement CSV (default: sample)"
    )
    ingest_bank.add_argument(
        "--reconcile",
        action="store_true",
        help="Run BatchReconciler over the ingested records afterward",
    )

    ingest_razorpay = subparsers.add_parser(
        "ingest-razorpay", help="Trigger read-only Razorpay test-mode ingestion"
    )
    ingest_razorpay.add_argument("--year", type=int, required=True)
    ingest_razorpay.add_argument("--month", type=int, required=True)
    ingest_razorpay.add_argument(
        "--reconcile",
        action="store_true",
        help="Run BatchReconciler over the ingested records afterward",
    )

    args = parser.parse_args()

    if args.command == "status":
        return _cmd_status(args)
    if args.command == "ingest-bank":
        return _cmd_ingest_bank(args)
    if args.command == "ingest-razorpay":
        return _cmd_ingest_razorpay(args)
    return 1  # pragma: no cover - argparse enforces valid subcommands


if __name__ == "__main__":
    sys.exit(run_cli())
