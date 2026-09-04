"""Application-defined ports.

The application layer depends on these interfaces only; concrete
implementations live in packages/ai (or, for other ports, infrastructure).
Signatures are expressed entirely in Phase 1 domain types - no concrete AI
SDK type may appear here, and no infrastructure type may appear here.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from cashproof.domain.ai import Investigation, InvestigatorBudget, ResolutionProposal
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Payment, Refund, Settlement, SettlementItem


@dataclass(frozen=True, slots=True)
class InvestigationOutcome:
    """Raw output of one AI investigation session.

    proposal is None whenever the investigation did not cleanly complete with
    a submitted proposal (budget exhausted, timeout, provider failure,
    malformed output, or an explicit abstain).
    """

    investigation: Investigation
    proposal: ResolutionProposal | None


class AIInvestigatorPort(Protocol):
    """Port implemented by a concrete AI adapter (e.g. cashproof.ai.AnthropicInvestigator).

    Receives only data already scoped to one case by the caller - never a
    store, never cross-case/cross-settlement data, never GroundTruth or
    ScenarioFamily. Implementations must never mutate any argument.
    """

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
    ) -> InvestigationOutcome: ...


# ---------------------------------------------------------------------------
# Phase 9: ingestion ports
#
# Ingestion is a separate responsibility from reconciliation. A connector's
# only job is to fetch/parse external source data and normalize it into
# existing Phase 1 domain objects (Payment, Refund, Settlement,
# SettlementItem, LedgerEntry) - it must never generate candidates, evaluate
# the gate, invoke AI, or touch GroundTruth. Source-specific vocabulary
# (Razorpay field names, bank CSV column names) is confined to the concrete
# adapter in packages/infrastructure; only these generic, domain-typed
# contracts are visible here.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ConnectorStatus:
    """Read-only connector configuration/availability state.

    Never carries credential values - only whether the connector is usable
    and a human-readable, secret-free explanation.
    """

    connector_name: str
    configured: bool
    detail: str


@dataclass(frozen=True, slots=True)
class NormalizedSourceBatch:
    """A batch of already-normalized Phase 1 domain records from one ingestion fetch.

    Every field is a tuple of existing domain objects - a connector cannot
    introduce a new record shape. An empty batch (all fields default to
    ``()``) is valid or fewer than all record kinds).
    """

    payments: tuple[Payment, ...] = ()
    refunds: tuple[Refund, ...] = ()
    settlements: tuple[Settlement, ...] = ()
    settlement_items: tuple[SettlementItem, ...] = ()
    ledger_entries: tuple[LedgerEntry, ...] = ()

    def record_count(self) -> int:
        return (
            len(self.payments)
            + len(self.refunds)
            + len(self.settlements)
            + len(self.settlement_items)
            + len(self.ledger_entries)
        )


class SourceConnectorPort(Protocol):
    """Read-only connector to an external payment/settlement data source.

    Implementations (e.g. cashproof.infrastructure.razorpay.RazorpayConnector)
    perform only fetch + normalize. They must never reconcile, evaluate the
    gate, invoke AI, or read GroundTruth/ScenarioFamily.
    """

    def status(self) -> ConnectorStatus: ...

    def fetch(self, *, year: int, month: int) -> NormalizedSourceBatch: ...


class IngestionStatus(enum.StrEnum):
    """Terminal outcome of one ingestion run."""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class IngestionRun:
    """Application-level record of one ingestion attempt.

    Not a domain entity - it carries no financial invariants of its own. It
    exists purely to make ingestion lifecycle/idempotency observable
    (accepted/rejected/duplicate counts, validation errors, failure reason).
    """

    run_id: str
    source: str
    status: IngestionStatus
    fetched_count: int
    accepted_count: int
    rejected_count: int
    duplicate_count: int
    validation_errors: tuple[str, ...]
    failure_reason: str | None
    started_at: datetime
    completed_at: datetime


class IngestionResultStore(Protocol):
    """Application-defined persistence contract for ingestion lifecycle/idempotency.

    Implemented by cashproof.application.store.InMemoryCaseStore today; a
    future SQLAlchemy-backed store implements the same contract without any
    change to IngestionService.
    """

    def record_ingestion_run(self, run: IngestionRun) -> None: ...

    def get_ingestion_run(self, run_id: str) -> IngestionRun | None: ...

    def list_ingestion_runs(self) -> Sequence[IngestionRun]: ...

    def get_ingested_fingerprint(self, external_id: str) -> str | None: ...

    def register_source_id(self, external_id: str, fingerprint: str) -> None: ...

    def add_source_records(self, batch: NormalizedSourceBatch) -> None: ...
