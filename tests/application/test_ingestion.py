"""Tests for IngestionService: idempotency, duplicate/conflict handling, storage.

Uses the REAL InMemoryCaseStore (not a fake) so these tests also prove
ingestion never triggers reconciliation, AI, or any GroundTruth-aware code
path - store.results (populated only by BatchReconciler) stays empty
throughout every test in this module.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cashproof.application.ingestion import (
    DuplicateSourceConflictError,
    IngestionService,
    IngestionValidationError,
)
from cashproof.application.ports import (
    ConnectorStatus,
    IngestionStatus,
    NormalizedSourceBatch,
    SourceConnectorPort,
)
from cashproof.application.store import InMemoryCaseStore
from cashproof.domain.source import LedgerEntry, Settlement
from cashproof.domain.types import Currency, Direction

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)


def _store() -> InMemoryCaseStore:
    return InMemoryCaseStore(
        run_id="ingestion-test",
        settlements={},
        items_by_settlement={},
        payments_by_settlement={},
        ledger_pool=[],
    )


def _ledger_entry(entry_id: str = "ledger_1", amount: int = 1000) -> LedgerEntry:
    return LedgerEntry(
        id=entry_id,
        amount_minor=amount,
        currency=Currency.INR,
        timestamp=FIXED_NOW,
        direction=Direction.CREDIT,
        payment_ref="setl_1",
    )


def _settlement(settlement_id: str = "setl_1", amount: int = 1000) -> Settlement:
    return Settlement(
        settlement_id=settlement_id,
        net_deposited_minor=amount,
        currency=Currency.INR,
        settled_at=FIXED_NOW,
    )


class ScriptedConnector:
    """Test double for SourceConnectorPort - never touches the network."""

    def __init__(
        self,
        *,
        configured: bool = True,
        batch: NormalizedSourceBatch | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._configured = configured
        self._batch = batch or NormalizedSourceBatch()
        self._raises = raises

    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_name="scripted", configured=self._configured, detail="test double"
        )

    def fetch(self, *, year: int, month: int) -> NormalizedSourceBatch:
        if self._raises is not None:
            raise self._raises
        return self._batch


def test_successful_ingestion_stores_accepted_records_and_never_reconciles() -> None:
    store = _store()
    service = IngestionService(store)
    batch = NormalizedSourceBatch(ledger_entries=(_ledger_entry(),), settlements=(_settlement(),))

    run = service.ingest_batch(source="test", batch=batch, fetched_count=2, now=FIXED_NOW)

    assert run.status == IngestionStatus.COMPLETED
    assert run.accepted_count == 2
    assert run.duplicate_count == 0
    assert "setl_1" in store.settlements
    assert len(store.ledger_pool) == 1
    assert store.results == {}  # no reconciliation was triggered


def test_ingestion_run_is_persisted_and_retrievable() -> None:
    store = _store()
    service = IngestionService(store)
    run = service.ingest_batch(
        source="test", batch=NormalizedSourceBatch(), fetched_count=0, now=FIXED_NOW
    )
    assert store.get_ingestion_run(run.run_id) is run
    assert run in store.list_ingestion_runs()


def test_repeated_ingestion_of_identical_record_is_idempotent() -> None:
    store = _store()
    service = IngestionService(store)
    batch = NormalizedSourceBatch(ledger_entries=(_ledger_entry(),))

    first = service.ingest_batch(source="test", batch=batch, fetched_count=1, now=FIXED_NOW)
    second = service.ingest_batch(source="test", batch=batch, fetched_count=1, now=FIXED_NOW)

    assert first.accepted_count == 1
    assert second.accepted_count == 0
    assert second.duplicate_count == 1
    assert len(store.ledger_pool) == 1  # not duplicated in storage


def test_conflicting_duplicate_raises_and_fails_closed() -> None:
    store = _store()
    service = IngestionService(store)
    service.ingest_batch(
        source="test",
        batch=NormalizedSourceBatch(ledger_entries=(_ledger_entry(amount=1000),)),
        fetched_count=1,
        now=FIXED_NOW,
    )

    conflicting_batch = NormalizedSourceBatch(ledger_entries=(_ledger_entry(amount=9999),))
    with pytest.raises(DuplicateSourceConflictError):
        service.ingest_batch(source="test", batch=conflicting_batch, fetched_count=1, now=FIXED_NOW)

    # The original, previously-accepted fact must be untouched.
    assert len(store.ledger_pool) == 1
    assert store.ledger_pool[0].amount_minor == 1000


def test_conflict_does_not_partially_accept_the_rest_of_the_batch() -> None:
    """Atomicity: a conflict anywhere in the batch must leave nothing new stored."""
    store = _store()
    service = IngestionService(store)
    service.ingest_batch(
        source="test",
        batch=NormalizedSourceBatch(ledger_entries=(_ledger_entry("ledger_1", 1000),)),
        fetched_count=1,
        now=FIXED_NOW,
    )

    mixed_batch = NormalizedSourceBatch(
        ledger_entries=(
            _ledger_entry("ledger_2", 500),  # would be a brand-new, valid record
            _ledger_entry("ledger_1", 9999),  # conflicts with what's already stored
        )
    )
    with pytest.raises(DuplicateSourceConflictError):
        service.ingest_batch(source="test", batch=mixed_batch, fetched_count=2, now=FIXED_NOW)

    assert store.get_ingested_fingerprint("ledger_2") is None
    assert len(store.ledger_pool) == 1


def test_record_validation_failure_is_recorded_as_a_failed_run() -> None:
    store = _store()
    service = IngestionService(store)
    error = IngestionValidationError(["bad row 1", "bad row 2"], fetched_count=2)

    run = service.record_validation_failure(source="bank_statement", error=error, now=FIXED_NOW)

    assert run.status == IngestionStatus.FAILED
    assert run.rejected_count == 2
    assert run.validation_errors == ("bad row 1", "bad row 2")
    assert store.get_ingestion_run(run.run_id) is run


def test_ingest_from_connector_fails_closed_when_unconfigured() -> None:
    store = _store()
    service = IngestionService(store)
    connector = ScriptedConnector(configured=False)

    run = service.ingest_from_connector(
        connector, source="razorpay", year=2024, month=1, now=FIXED_NOW
    )

    assert run.status == IngestionStatus.FAILED
    assert run.accepted_count == 0
    assert store.ledger_pool == []


def test_ingest_from_connector_fails_closed_on_fetch_exception_without_crashing() -> None:
    store = _store()
    service = IngestionService(store)
    connector = ScriptedConnector(raises=RuntimeError("network exploded"))

    run = service.ingest_from_connector(
        connector, source="razorpay", year=2024, month=1, now=FIXED_NOW
    )

    assert run.status == IngestionStatus.FAILED
    assert "network exploded" in (run.failure_reason or "")


def test_ingest_from_connector_success_path_stores_batch() -> None:
    store = _store()
    service = IngestionService(store)
    connector = ScriptedConnector(batch=NormalizedSourceBatch(ledger_entries=(_ledger_entry(),)))

    run = service.ingest_from_connector(
        connector, source="razorpay", year=2024, month=1, now=FIXED_NOW
    )

    assert run.status == IngestionStatus.COMPLETED
    assert run.accepted_count == 1
    assert len(store.ledger_pool) == 1


def test_source_connector_port_is_structurally_satisfied_by_scripted_double() -> None:
    connector: SourceConnectorPort = ScriptedConnector()
    assert connector.status().connector_name == "scripted"
