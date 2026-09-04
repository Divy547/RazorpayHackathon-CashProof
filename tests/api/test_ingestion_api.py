"""Tests for the ingestion HTTP API: connector status, bank upload, run history,
Razorpay trigger, and /api/reconcile invoking the existing BatchReconciler.

Follows the same pattern as tests/api/test_api.py: exercises the API purely
through HTTP requests via FastAPI's TestClient, proving the adapter delegates
to cashproof.application.ingestion.IngestionService rather than reimplementing
any ingestion logic itself.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from cashproof.api.app import create_app
from cashproof.application.ports import (
    ConnectorStatus,
    InvestigationOutcome,
    NormalizedSourceBatch,
)
from cashproof.application.store import InMemoryCaseStore
from cashproof.domain.ai import InvestigatorBudget
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.types import Currency, Direction, PaymentStatus
from fastapi.testclient import TestClient

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)
TEST_BUDGET = InvestigatorBudget(
    max_tool_calls=5,
    max_tokens=4000,
    timeout_seconds=30.0,
    temperature=0.0,
    model_version="fake-model",
)

HEADER = (
    "transaction_id,timestamp,amount_minor,currency,direction,"
    "payment_ref,external_ref,narration,customer_name"
)


class _NoOpInvestigator:
    """Minimal AIInvestigatorPort stub - never invoked by these tests."""

    def investigate(
        self,
        *,
        case: ReconciliationCase,
        settlement: Settlement,
        items: Sequence[SettlementItem],
        candidates: Sequence[MatchCandidate],
        evidence: Sequence[Evidence],
        gate: GateEvaluation,
        ledger_entries_by_id: Mapping[str, LedgerEntry],
        budget: InvestigatorBudget,
        run_id: str,
    ) -> InvestigationOutcome:
        raise NotImplementedError


class ScriptedConnector:
    """Test double for SourceConnectorPort - never touches the network."""

    def __init__(
        self,
        *,
        configured: bool = True,
        batches: list[NormalizedSourceBatch] | None = None,
    ) -> None:
        self._configured = configured
        self._batches = batches if batches is not None else [NormalizedSourceBatch()]
        self._call_count = 0

    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_name="razorpay",
            configured=self._configured,
            detail="scripted test double" if self._configured else "not configured (test double)",
        )

    def fetch(self, *, year: int, month: int) -> NormalizedSourceBatch:
        batch = self._batches[min(self._call_count, len(self._batches) - 1)]
        self._call_count += 1
        return batch


def _empty_store() -> InMemoryCaseStore:
    return InMemoryCaseStore(
        run_id="ingestion-api-test",
        settlements={},
        items_by_settlement={},
        payments_by_settlement={},
        ledger_pool=[],
    )


def _make_client(
    store: InMemoryCaseStore, connector: ScriptedConnector | None = None
) -> TestClient:
    app = create_app(
        store,
        _NoOpInvestigator(),
        TEST_BUDGET,
        razorpay_connector=connector or ScriptedConnector(configured=False),
    )
    return TestClient(app)


def test_ingestion_status_reports_configured_and_unconfigured_without_secrets() -> None:
    store = _empty_store()
    client = _make_client(store, ScriptedConnector(configured=False))

    response = client.get("/api/ingestion/status")
    assert response.status_code == 200
    body = response.json()
    razorpay = next(c for c in body["connectors"] if c["connector_name"] == "razorpay")
    bank = next(c for c in body["connectors"] if c["connector_name"] == "bank_statement")
    assert razorpay["configured"] is False
    assert bank["configured"] is True
    assert "secret" not in response.text.lower()
    assert "key_secret" not in response.text.lower()


def test_bank_statement_upload_accepts_valid_csv() -> None:
    store = _empty_store()
    client = _make_client(store)
    csv_bytes = (
        f"{HEADER}\ntxn_api_1,2024-01-05T09:30:00+00:00,100000,INR,CREDIT,setl_1,,,\n"
    ).encode()

    response = client.post(
        "/api/ingestion/bank-statement",
        files={"file": ("statement.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["accepted_count"] == 1
    assert len(store.ledger_pool) == 1


def test_bank_statement_upload_rejects_malformed_csv_as_failed_run() -> None:
    store = _empty_store()
    client = _make_client(store)
    csv_bytes = f"{HEADER}\ntxn_bad,2024-01-05T09:30:00+00:00,-1,INR,CREDIT,,,,\n".encode()

    response = client.post(
        "/api/ingestion/bank-statement",
        files={"file": ("statement.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["accepted_count"] == 0
    assert len(body["validation_errors"]) > 0
    assert store.ledger_pool == []


def test_ingestion_runs_are_listed_and_individually_retrievable() -> None:
    store = _empty_store()
    client = _make_client(store)
    csv_bytes = f"{HEADER}\ntxn_hist,2024-01-05T09:30:00+00:00,1000,INR,CREDIT,,,,\n".encode()
    upload = client.post(
        "/api/ingestion/bank-statement", files={"file": ("s.csv", csv_bytes, "text/csv")}
    )
    run_id = upload.json()["run_id"]

    listed = client.get("/api/ingestion/runs")
    assert listed.status_code == 200
    assert any(r["run_id"] == run_id for r in listed.json())

    fetched = client.get(f"/api/ingestion/runs/{run_id}")
    assert fetched.status_code == 200
    assert fetched.json()["run_id"] == run_id


def test_get_ingestion_run_not_found_returns_404() -> None:
    store = _empty_store()
    client = _make_client(store)
    response = client.get("/api/ingestion/runs/does_not_exist")
    assert response.status_code == 404


def test_razorpay_trigger_fails_closed_when_unconfigured_without_crashing() -> None:
    store = _empty_store()
    client = _make_client(store, ScriptedConnector(configured=False))
    response = client.post("/api/ingestion/razorpay", json={"year": 2024, "month": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["accepted_count"] == 0


def test_razorpay_trigger_success_stores_batch() -> None:
    ledger_entry = LedgerEntry(
        id="rp_ledger_1",
        amount_minor=5000,
        currency=Currency.INR,
        timestamp=FIXED_NOW,
        direction=Direction.CREDIT,
        payment_ref="setl_rp_1",
    )
    store = _empty_store()
    connector = ScriptedConnector(
        configured=True, batches=[NormalizedSourceBatch(ledger_entries=(ledger_entry,))]
    )
    client = _make_client(store, connector)

    response = client.post("/api/ingestion/razorpay", json={"year": 2024, "month": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["accepted_count"] == 1
    assert len(store.ledger_pool) == 1


def test_razorpay_trigger_conflicting_duplicate_returns_409() -> None:
    entry_a = LedgerEntry(
        id="rp_ledger_conflict",
        amount_minor=1000,
        currency=Currency.INR,
        timestamp=FIXED_NOW,
        direction=Direction.CREDIT,
        payment_ref="setl_rp_2",
    )
    entry_b = LedgerEntry(
        id="rp_ledger_conflict",
        amount_minor=9999,
        currency=Currency.INR,
        timestamp=FIXED_NOW,
        direction=Direction.CREDIT,
        payment_ref="setl_rp_2",
    )
    store = _empty_store()
    connector = ScriptedConnector(
        configured=True,
        batches=[
            NormalizedSourceBatch(ledger_entries=(entry_a,)),
            NormalizedSourceBatch(ledger_entries=(entry_b,)),
        ],
    )
    client = _make_client(store, connector)

    first = client.post("/api/ingestion/razorpay", json={"year": 2024, "month": 1})
    assert first.status_code == 200
    second = client.post("/api/ingestion/razorpay", json={"year": 2024, "month": 1})
    assert second.status_code == 409


def test_reconcile_endpoint_invokes_existing_batch_reconciler_over_ingested_data() -> None:
    settlement_id = "setl_ingested_1"
    settlement = Settlement(
        settlement_id=settlement_id,
        net_deposited_minor=100000,
        currency=Currency.INR,
        settled_at=FIXED_NOW,
    )
    item = SettlementItem(
        item_id="item_ingested_1",
        settlement_id=settlement_id,
        payment_id="pay_ingested_1",
        gross_minor=100000,
        fee_minor=0,
        tax_on_fee_minor=0,
        netted_refund_minor=0,
        adjustment_minor=0,
        computed_net_minor=100000,
    )
    payment_record = Payment(
        id="pay_ingested_1",
        order_ref="order_ingested_1",
        customer_ref="cust_1",
        customer_name="Test Customer",
        gross_minor=100000,
        currency=Currency.INR,
        captured_at=FIXED_NOW,
        status=PaymentStatus.CAPTURED,
    )
    ledger_entry = LedgerEntry(
        id="ledger_ingested_1",
        amount_minor=100000,
        currency=Currency.INR,
        timestamp=FIXED_NOW,
        direction=Direction.CREDIT,
        payment_ref=settlement_id,
    )

    store = _empty_store()
    connector = ScriptedConnector(
        configured=True,
        batches=[
            NormalizedSourceBatch(
                settlements=(settlement,),
                settlement_items=(item,),
                payments=(payment_record,),
                ledger_entries=(ledger_entry,),
            )
        ],
    )
    client = _make_client(store, connector)

    ingest_response = client.post("/api/ingestion/razorpay", json={"year": 2024, "month": 1})
    assert ingest_response.status_code == 200
    assert ingest_response.json()["status"] == "COMPLETED"

    # Before reconciling, the ingested settlement must not yet be a case.
    assert client.get("/api/cases").json() == []

    reconcile_response = client.post("/api/reconcile")
    assert reconcile_response.status_code == 200
    case_ids = [c["settlement_id"] for c in reconcile_response.json()]
    assert settlement_id in case_ids

    detail = client.get(f"/api/cases/{settlement_id}")
    assert detail.status_code == 200
    assert detail.json()["settlement_id"] == settlement_id
