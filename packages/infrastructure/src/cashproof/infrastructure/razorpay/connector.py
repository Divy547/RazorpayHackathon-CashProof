"""RazorpayConnector: implements cashproof.application.ports.SourceConnectorPort.

Read-only. Orchestrates: settlements -> recon-combined breakdown -> per-payment
detail -> per-payment refunds, then normalizes everything into a single
NormalizedSourceBatch of Phase 1 domain objects. Never reconciles, never
evaluates the gate, never touches AI or GroundTruth.

If RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET are not configured, status() reports
UNCONFIGURED and fetch() raises rather than silently returning an empty
batch - callers (IngestionService) are expected to check status() first.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from cashproof.application.ports import ConnectorStatus, NormalizedSourceBatch
from cashproof.domain.source import Payment, Refund
from cashproof.infrastructure.razorpay._dto import (
    RazorpayPaymentDTO,
    RazorpayReconEntryDTO,
    RazorpayRefundDTO,
    RazorpaySettlementDTO,
)
from cashproof.infrastructure.razorpay.client import RazorpayClient
from cashproof.infrastructure.razorpay.normalizer import (
    normalize_payment,
    normalize_refund,
    normalize_settlement,
    normalize_settlement_items,
    normalize_settlement_ledger_entry,
)

CONNECTOR_NAME = "razorpay"


class RazorpayConnectorUnconfiguredError(Exception):
    """Raised by fetch() when called while the connector reports UNCONFIGURED."""


class RazorpayConnector:
    """Read-only Razorpay test-mode connector."""

    def __init__(
        self,
        key_id: str | None = None,
        key_secret: str | None = None,
        *,
        client_factory: Callable[[str, str], RazorpayClient] = RazorpayClient,
    ) -> None:
        self._key_id = key_id if key_id is not None else os.environ.get("RAZORPAY_KEY_ID")
        self._key_secret = (
            key_secret if key_secret is not None else os.environ.get("RAZORPAY_KEY_SECRET")
        )
        self._client_factory = client_factory

    def status(self) -> ConnectorStatus:
        if self._key_id and self._key_secret:
            return ConnectorStatus(
                connector_name=CONNECTOR_NAME,
                configured=True,
                detail="RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are set.",
            )
        return ConnectorStatus(
            connector_name=CONNECTOR_NAME,
            configured=False,
            detail=(
                "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET are not set. Set both environment "
                "variables (test-mode key pair) to enable Razorpay ingestion."
            ),
        )

    def fetch(self, *, year: int, month: int) -> NormalizedSourceBatch:
        status = self.status()
        if not status.configured:
            raise RazorpayConnectorUnconfiguredError(status.detail)
        assert self._key_id is not None
        assert self._key_secret is not None

        client = self._client_factory(self._key_id, self._key_secret)
        try:
            settlement_dtos: list[RazorpaySettlementDTO] = [
                cast(RazorpaySettlementDTO, dto)
                for dto in client.get_settlements()
                if _in_month(int(dto.get("created_at", 0)), year=year, month=month)
            ]
            settlements = [normalize_settlement(dto) for dto in settlement_dtos]

            recon_entries = cast(
                list[RazorpayReconEntryDTO],
                client.get_settlement_recon_combined(year=year, month=month),
            )

            settlement_items = []
            for settlement in settlements:
                settlement_items.extend(
                    normalize_settlement_items(recon_entries, settlement=settlement)
                )

            payment_ids = sorted({item.payment_id for item in settlement_items})
            payments: list[Payment] = []
            refunds: list[Refund] = []
            for payment_id in payment_ids:
                payment_dto = cast(RazorpayPaymentDTO, client.get_payment(payment_id))
                payments.append(normalize_payment(payment_dto))

                refund_dtos = cast(list[RazorpayRefundDTO], client.get_payment_refunds(payment_id))
                refunds.extend(
                    normalize_refund(dto, netted_into_settlement=True) for dto in refund_dtos
                )

            ledger_entries = [normalize_settlement_ledger_entry(s) for s in settlements]

            return NormalizedSourceBatch(
                payments=tuple(payments),
                refunds=tuple(refunds),
                settlements=tuple(settlements),
                settlement_items=tuple(settlement_items),
                ledger_entries=tuple(ledger_entries),
            )
        finally:
            client.close()


def _in_month(epoch_seconds: int, *, year: int, month: int) -> bool:
    if not epoch_seconds:
        return False
    dt = datetime.fromtimestamp(epoch_seconds, tz=UTC)
    return dt.year == year and dt.month == month
