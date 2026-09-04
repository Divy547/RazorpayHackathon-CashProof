"""Tests for RazorpayConnector and RazorpayClient - all HTTP traffic is mocked
via httpx.MockTransport. No real network access occurs in this test module.
"""

from __future__ import annotations

import httpx
import pytest
from cashproof.infrastructure.razorpay import client as client_module
from cashproof.infrastructure.razorpay.client import RazorpayClient, RazorpayClientError
from cashproof.infrastructure.razorpay.connector import (
    RazorpayConnector,
    RazorpayConnectorUnconfiguredError,
)

SETTLEMENT_DTO = {"id": "setl_1", "entity": "settlement", "amount": 97500, "created_at": 1704067200}
RECON_ENTRY = {
    "entity_id": "pay_1",
    "type": "payment",
    "credit": 100000,
    "fee": 2000,
    "tax": 500,
    "settlement_id": "setl_1",
}
PAYMENT_DTO = {
    "id": "pay_1",
    "amount": 100000,
    "currency": "INR",
    "status": "captured",
    "amount_refunded": 0,
    "created_at": 1704067200,
    "email": "a@b.com",
}


def test_status_unconfigured_when_no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)
    connector = RazorpayConnector()
    status = connector.status()
    assert status.configured is False
    assert "RAZORPAY_KEY_ID" in status.detail


def test_status_configured_never_exposes_credential_values() -> None:
    connector = RazorpayConnector(key_id="rzp_test_secretid", key_secret="supersecretvalue")
    status = connector.status()
    assert status.configured is True
    assert "supersecretvalue" not in status.detail
    assert "rzp_test_secretid" not in status.detail


def test_fetch_raises_when_unconfigured_rather_than_crashing() -> None:
    connector = RazorpayConnector(key_id=None, key_secret=None)
    with pytest.raises(RazorpayConnectorUnconfiguredError):
        connector.fetch(year=2024, month=1)


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/v1/settlements":
        return httpx.Response(
            200, json={"entity": "collection", "count": 1, "items": [SETTLEMENT_DTO]}
        )
    if path == "/v1/settlements/recon/combined":
        return httpx.Response(
            200, json={"entity": "collection", "count": 1, "items": [RECON_ENTRY]}
        )
    if path == "/v1/payments/pay_1":
        return httpx.Response(200, json=PAYMENT_DTO)
    if path == "/v1/payments/pay_1/refunds":
        return httpx.Response(200, json={"entity": "collection", "count": 0, "items": []})
    return httpx.Response(404, json={"error": "not found"})


def _connector_with_mock_transport(transport: httpx.MockTransport) -> RazorpayConnector:
    return RazorpayConnector(
        key_id="test_key_id",
        key_secret="test_key_secret",
        client_factory=lambda key_id, key_secret: RazorpayClient(
            key_id, key_secret, transport=transport
        ),
    )


def test_fetch_builds_full_normalized_batch() -> None:
    connector = _connector_with_mock_transport(httpx.MockTransport(_handler))
    batch = connector.fetch(year=2024, month=1)

    assert len(batch.settlements) == 1
    assert batch.settlements[0].settlement_id == "setl_1"
    assert len(batch.settlement_items) == 1
    assert batch.settlement_items[0].payment_id == "pay_1"
    assert len(batch.payments) == 1
    assert batch.payments[0].id == "pay_1"
    assert len(batch.ledger_entries) == 1
    assert batch.ledger_entries[0].payment_ref == "setl_1"
    assert batch.refunds == ()


def test_fetch_filters_settlements_outside_requested_month() -> None:
    connector = _connector_with_mock_transport(httpx.MockTransport(_handler))
    batch = connector.fetch(year=2023, month=12)
    assert batch.settlements == ()
    assert batch.settlement_items == ()
    assert batch.payments == ()


def test_http_failure_raises_client_error_without_crashing() -> None:
    def failing_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"description": "boom"}})

    client = RazorpayClient("id", "secret", transport=httpx.MockTransport(failing_handler))
    with pytest.raises(RazorpayClientError):
        client.get_settlements()


def test_timeout_raises_client_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    client = RazorpayClient("id", "secret", transport=httpx.MockTransport(handler))
    with pytest.raises(RazorpayClientError):
        client.get_settlements()


def test_pagination_follows_every_full_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module, "MAX_PAGE_SIZE", 2)
    pages = {0: [{"id": "a"}, {"id": "b"}], 2: [{"id": "c"}]}

    def handler(request: httpx.Request) -> httpx.Response:
        skip = int(request.url.params.get("skip", "0"))
        items = pages.get(skip, [])
        return httpx.Response(
            200, json={"entity": "collection", "count": len(items), "items": items}
        )

    client = RazorpayClient("id", "secret", transport=httpx.MockTransport(handler))
    items = client.get_payments()
    assert [i["id"] for i in items] == ["a", "b", "c"]
