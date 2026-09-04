"""In-memory, single-process store of reconciliation state for the review MVP.

Holds the batch's source records and the current ReconciliationResult per
case, so a human review action can be applied against live, correct state
with no persistence layer. This module never imports the benchmark package -
it is populated by a composition root (e.g. a CLI/script entry point) that is
allowed to touch Phase 2, and it exposes only Phase 1/3 domain and
application types.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from cashproof.application.investigation import InvestigationRunResult
from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.types import Disposition, ReviewOutcome


@dataclass(slots=True)
class InMemoryCaseStore:
    """Mutable, process-local store synchronized via a threading.Lock."""

    run_id: str
    settlements: dict[str, Settlement]
    items_by_settlement: dict[str, list[SettlementItem]]
    payments_by_settlement: dict[str, list[Payment]]
    ledger_pool: list[LedgerEntry]
    results: dict[str, ReconciliationResult] = field(default_factory=dict)
    investigations: dict[str, InvestigationRunResult] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def lock(self) -> threading.Lock:
        """Lock for synchronizing check-then-write operations across threads."""
        return self._lock

    def get(self, case_id: str) -> ReconciliationResult | None:
        return self.results.get(case_id)

    def put(self, result: ReconciliationResult) -> None:
        self.results[result.case.case_id] = result

    def get_investigation(self, case_id: str) -> InvestigationRunResult | None:
        return self.investigations.get(case_id)

    def put_investigation(self, run_result: InvestigationRunResult) -> None:
        self.investigations[run_result.case_id] = run_result

    def already_resolved_target_ids(self, exclude_case_id: str | None = None) -> frozenset[str]:
        """Ledger entries finalized as a Resolution's target elsewhere in the batch:
        every AUTO_RESOLVED case, plus every HUMAN_REVIEW case a reviewer has
        already APPROVED. Excludes the case currently under review so it never
        blocks itself.
        """
        claimed: set[str] = set()
        for case_id, result in self.results.items():
            if case_id == exclude_case_id:
                continue
            disposition = result.resolution.disposition
            if disposition == Disposition.AUTO_RESOLVED:
                claimed.update(result.resolution.target_ledger_entry_ids)
            elif (
                disposition == Disposition.HUMAN_REVIEW
                and result.resolution.review_outcome == ReviewOutcome.APPROVED
            ):
                claimed.update(result.resolution.target_ledger_entry_ids)
        return frozenset(claimed)
