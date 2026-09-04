"""IngestionService: orchestrates connector fetch -> idempotency -> source storage.

This module is deliberately narrow. It NEVER:
- generates MatchCandidates
- classifies exceptions
- runs BatchReconciler / ReconcileSettlementUseCase
- calls evaluate_gate()
- invokes AI
- reads GroundTruth or ScenarioFamily

Ingestion and reconciliation are separate responsibilities. Once accepted
source records land in the store, they enter the exact same
ReconcileSettlementUseCase/BatchReconciler path as synthetic benchmark data -
this module has no idea that path exists.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import fields
from datetime import datetime

from cashproof.application.ports import (
    IngestionResultStore,
    IngestionRun,
    IngestionStatus,
    NormalizedSourceBatch,
    SourceConnectorPort,
)
from cashproof.domain.source import LedgerEntry, Payment, Refund, Settlement, SettlementItem


class IngestionValidationError(Exception):
    """Raised on a critical, fail-closed validation failure.

    Carries every structured error found (not just the first) so an operator
    can fix an entire malformed batch in one pass. Raising this means NOTHING
    from the batch was stored - partial-but-unsafe ingestion is never allowed.
    """

    def __init__(self, errors: Sequence[str], *, fetched_count: int = 0) -> None:
        self.errors = tuple(errors)
        self.fetched_count = fetched_count
        preview = "; ".join(self.errors[:5])
        super().__init__(f"{len(self.errors)} validation error(s): {preview}")


class DuplicateSourceConflictError(Exception):
    """Raised when an external ID already exists with conflicting critical data.

    Source records are immutable once accepted - re-ingesting the same
    external ID with identical data is silently idempotent (counted as a
    duplicate), but a *different* amount/currency/etc. under the same ID is
    refused rather than silently overwriting the previously accepted fact.
    """

    def __init__(self, external_id: str, reason: str) -> None:
        self.external_id = external_id
        super().__init__(f"Conflicting duplicate for source record '{external_id}': {reason}")


def _external_id_and_fingerprint(
    record: Payment | Refund | Settlement | SettlementItem | LedgerEntry,
) -> tuple[str, str]:
    """Stable external id + a fingerprint of the record's critical fields.

    The fingerprint is compared on re-ingestion: an identical fingerprint
    under the same id is an idempotent duplicate; a differing one is a
    conflict that must fail closed rather than silently overwrite.
    """
    if isinstance(record, Payment):
        return record.id, (
            f"payment:{record.gross_minor}:{record.currency}:{record.status}:"
            f"{record.captured_at.isoformat()}"
        )
    if isinstance(record, Refund):
        return record.refund_id, (
            f"refund:{record.payment_id}:{record.amount_minor}:{record.currency}:"
            f"{record.status}:{record.netted_into_settlement}"
        )
    if isinstance(record, Settlement):
        return record.settlement_id, (
            f"settlement:{record.net_deposited_minor}:{record.currency}:"
            f"{record.settled_at.isoformat()}"
        )
    if isinstance(record, SettlementItem):
        return record.item_id, (
            f"item:{record.settlement_id}:{record.payment_id}:{record.gross_minor}:"
            f"{record.fee_minor}:{record.tax_on_fee_minor}:{record.netted_refund_minor}:"
            f"{record.adjustment_minor}:{record.computed_net_minor}"
        )
    if isinstance(record, LedgerEntry):
        return record.id, (
            f"ledger:{record.amount_minor}:{record.currency}:{record.direction}:"
            f"{record.timestamp.isoformat()}:{record.payment_ref}"
        )
    raise TypeError(f"Unsupported source record type: {type(record)!r}")  # pragma: no cover


def _flatten(batch: NormalizedSourceBatch) -> list[tuple[str, object]]:
    return [(f.name, record) for f in fields(batch) for record in getattr(batch, f.name)]


def _rebuild(records: Sequence[tuple[str, object]]) -> NormalizedSourceBatch:
    grouped: dict[str, list[object]] = {f.name: [] for f in fields(NormalizedSourceBatch)}
    for field_name, record in records:
        grouped[field_name].append(record)
    return NormalizedSourceBatch(
        payments=tuple(grouped["payments"]),  # type: ignore[arg-type]
        refunds=tuple(grouped["refunds"]),  # type: ignore[arg-type]
        settlements=tuple(grouped["settlements"]),  # type: ignore[arg-type]
        settlement_items=tuple(grouped["settlement_items"]),  # type: ignore[arg-type]
        ledger_entries=tuple(grouped["ledger_entries"]),  # type: ignore[arg-type]
    )


class IngestionService:
    """Orchestrates one ingestion run: fetch/parse -> idempotency -> storage -> IngestionRun."""

    def __init__(self, store: IngestionResultStore) -> None:
        self._store = store

    def ingest_from_connector(
        self,
        connector: SourceConnectorPort,
        *,
        source: str,
        year: int,
        month: int,
        now: datetime,
    ) -> IngestionRun:
        """Fetch from a SourceConnectorPort (e.g. Razorpay) and ingest the result.

        Fails closed (returns a FAILED IngestionRun, never raises) when the
        connector is unconfigured or the fetch itself fails - a misconfigured
        or unreachable external connector must never crash the application.
        """
        run_id = f"ing_{source}_{uuid.uuid4().hex[:12]}"
        status = connector.status()
        if not status.configured:
            run = IngestionRun(
                run_id=run_id,
                source=source,
                status=IngestionStatus.FAILED,
                fetched_count=0,
                accepted_count=0,
                rejected_count=0,
                duplicate_count=0,
                validation_errors=(),
                failure_reason=f"Connector '{status.connector_name}' is not configured: "
                f"{status.detail}",
                started_at=now,
                completed_at=now,
            )
            self._store.record_ingestion_run(run)
            return run

        try:
            batch = connector.fetch(year=year, month=month)
        except Exception as exc:  # connector I/O failure - fail closed, never crash
            run = IngestionRun(
                run_id=run_id,
                source=source,
                status=IngestionStatus.FAILED,
                fetched_count=0,
                accepted_count=0,
                rejected_count=0,
                duplicate_count=0,
                validation_errors=(),
                failure_reason=f"Connector fetch failed: {exc}",
                started_at=now,
                completed_at=now,
            )
            self._store.record_ingestion_run(run)
            return run

        return self.ingest_batch(
            source=source,
            batch=batch,
            fetched_count=batch.record_count(),
            now=now,
            run_id=run_id,
        )

    def ingest_batch(
        self,
        *,
        source: str,
        batch: NormalizedSourceBatch,
        fetched_count: int,
        now: datetime,
        run_id: str | None = None,
    ) -> IngestionRun:
        """Idempotency-check and store an already-normalized batch as one ingestion run.

        Used directly by callers (e.g. the bank CSV upload route) that already
        parsed/normalized their source outside this service, and internally by
        ingest_from_connector(). Never runs reconciliation.
        """
        run_id = run_id or f"ing_{source}_{uuid.uuid4().hex[:12]}"
        started_at = now

        classified: list[tuple[str, object]] = []
        duplicate_count = 0
        for field_name, record in _flatten(batch):
            external_id, fingerprint = _external_id_and_fingerprint(record)  # type: ignore[arg-type]
            existing = self._store.get_ingested_fingerprint(external_id)
            if existing is None:
                classified.append((field_name, record))
            elif existing == fingerprint:
                duplicate_count += 1
            else:
                # Fail closed: nothing accepted so far has been written to the
                # store yet (add_source_records is only called after this
                # entire loop completes cleanly), so raising here leaves the
                # store untouched.
                run = IngestionRun(
                    run_id=run_id,
                    source=source,
                    status=IngestionStatus.FAILED,
                    fetched_count=fetched_count,
                    accepted_count=0,
                    rejected_count=0,
                    duplicate_count=0,
                    validation_errors=(
                        f"Conflicting duplicate for '{external_id}': previously ingested "
                        "with different critical field values.",
                    ),
                    failure_reason=f"DuplicateSourceConflictError: {external_id}",
                    started_at=started_at,
                    completed_at=now,
                )
                self._store.record_ingestion_run(run)
                raise DuplicateSourceConflictError(
                    external_id, "critical field values differ from the previously ingested record"
                )

        accepted_batch = _rebuild(classified)
        self._store.add_source_records(accepted_batch)
        for _field_name, record in classified:
            external_id, fingerprint = _external_id_and_fingerprint(record)  # type: ignore[arg-type]
            self._store.register_source_id(external_id, fingerprint)

        run = IngestionRun(
            run_id=run_id,
            source=source,
            status=IngestionStatus.COMPLETED,
            fetched_count=fetched_count,
            accepted_count=len(classified),
            rejected_count=0,
            duplicate_count=duplicate_count,
            validation_errors=(),
            failure_reason=None,
            started_at=started_at,
            completed_at=now,
        )
        self._store.record_ingestion_run(run)
        return run

    def record_validation_failure(
        self,
        *,
        source: str,
        error: IngestionValidationError,
        now: datetime,
    ) -> IngestionRun:
        """Records a fail-closed critical validation failure (e.g. malformed bank CSV) as a run.

        Called by the composition root when normalization/parsing (an
        infrastructure concern) raised IngestionValidationError before any
        record ever reached this service.
        """
        run_id = f"ing_{source}_{uuid.uuid4().hex[:12]}"
        run = IngestionRun(
            run_id=run_id,
            source=source,
            status=IngestionStatus.FAILED,
            fetched_count=error.fetched_count,
            accepted_count=0,
            rejected_count=len(error.errors),
            duplicate_count=0,
            validation_errors=error.errors,
            failure_reason=str(error),
            started_at=now,
            completed_at=now,
        )
        self._store.record_ingestion_run(run)
        return run
