"""Thin, read-only httpx client over the Razorpay REST API.

Owns HTTP concerns only: auth, pagination, timeouts, and translating
transport/HTTP failures into RazorpayClientError. Never parses a response
into a domain object (see normalizer.py) and never exposes credentials in an
error message or log line.

Read-only by construction: this module defines no method that issues a
POST/PATCH/DELETE against a mutating Razorpay endpoint.
"""

from __future__ import annotations

from typing import Any

import httpx

RAZORPAY_BASE_URL = "https://api.razorpay.com/v1/"
DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_PAGE_SIZE = 100


class RazorpayClientError(Exception):
    """Raised on any HTTP/transport failure. Never includes key_id/key_secret."""


class RazorpayClient:
    """Read-only Razorpay API client. Every method is a GET."""

    def __init__(
        self,
        key_id: str,
        key_secret: str,
        *,
        base_url: str = RAZORPAY_BASE_URL,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            auth=httpx.BasicAuth(key_id, key_secret),
            timeout=timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> RazorpayClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RazorpayClientError(f"Razorpay request to {path!r} timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise RazorpayClientError(
                f"Razorpay request to {path!r} failed with HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RazorpayClientError(f"Razorpay request to {path!r} failed: {exc}") from exc

        data: Any = response.json()
        if not isinstance(data, dict):
            raise RazorpayClientError(f"Razorpay response for {path!r} was not a JSON object")
        return data

    def _paginate(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Pulls every page of a Razorpay list endpoint via count/skip."""
        items: list[dict[str, Any]] = []
        skip = 0
        base_params = dict(params or {})
        while True:
            page = self._get(path, {**base_params, "count": MAX_PAGE_SIZE, "skip": skip})
            page_items = page.get("items", [])
            if not isinstance(page_items, list):
                raise RazorpayClientError(f"Razorpay list response for {path!r} malformed")
            items.extend(page_items)
            if len(page_items) < MAX_PAGE_SIZE:
                break
            skip += MAX_PAGE_SIZE
        return items

    def get_payments(self) -> list[dict[str, Any]]:
        return self._paginate("payments")

    def get_payment(self, payment_id: str) -> dict[str, Any]:
        return self._get(f"payments/{payment_id}")

    def get_refunds(self) -> list[dict[str, Any]]:
        return self._paginate("refunds")

    def get_payment_refunds(self, payment_id: str) -> list[dict[str, Any]]:
        return self._paginate(f"payments/{payment_id}/refunds")

    def get_settlements(self) -> list[dict[str, Any]]:
        return self._paginate("settlements")

    def get_settlement(self, settlement_id: str) -> dict[str, Any]:
        return self._get(f"settlements/{settlement_id}")

    def get_settlement_recon_combined(self, *, year: int, month: int) -> list[dict[str, Any]]:
        return self._paginate("settlements/recon/combined", {"year": year, "month": f"{month:02d}"})
