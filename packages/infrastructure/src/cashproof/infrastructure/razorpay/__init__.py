"""Razorpay test-mode read-only adapter.

Implements cashproof.application.ports.SourceConnectorPort. Razorpay-specific
field names/vocabulary (pay_xxx, entity, amount, fee, tax, ...) are confined
to this sub-package - RazorpayConnector.fetch() returns only existing Phase 1
domain objects (Payment, Refund, Settlement, SettlementItem, LedgerEntry).

Read-only: this adapter never creates payments, refunds, or settlements, and
never mutates anything at Razorpay.
"""

from __future__ import annotations

from cashproof.infrastructure.razorpay.client import RazorpayClient, RazorpayClientError
from cashproof.infrastructure.razorpay.connector import RazorpayConnector

__all__ = ["RazorpayConnector", "RazorpayClient", "RazorpayClientError"]
