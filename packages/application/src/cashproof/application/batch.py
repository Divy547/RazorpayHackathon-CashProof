"""Deterministic batch reconciliation orchestration over Phase 2 source records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from cashproof.application.use_case import ReconcileSettlementUseCase, ReconciliationResult
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.types import Disposition


@dataclass(frozen=True, slots=True)
class BatchReconciliationSummary:
    """Aggregate outcome of running the pipeline across every settlement in a batch."""

    total_settlements: int
    auto_resolved_count: int
    human_review_count: int
    unresolved_count: int
    results: tuple[ReconciliationResult, ...]


class BatchReconciler:
    """Processes every settlement deterministically, preventing duplicate ledger resolution."""

    def __init__(self, use_case: ReconcileSettlementUseCase | None = None) -> None:
        self._use_case = use_case or ReconcileSettlementUseCase()

    def run(
        self,
        run_id: str,
        settlements: Sequence[Settlement],
        items_by_settlement: Mapping[str, Sequence[SettlementItem]],
        payments_by_settlement: Mapping[str, Sequence[Payment]],
        ledger_pool: Sequence[LedgerEntry],
        now: datetime,
    ) -> BatchReconciliationSummary:
        ordered_settlements = sorted(settlements, key=lambda s: s.settlement_id)
        already_resolved_target_ids: set[str] = set()
        results: list[ReconciliationResult] = []

        for settlement in ordered_settlements:
            result = self._use_case.execute(
                run_id=run_id,
                settlement=settlement,
                items=items_by_settlement.get(settlement.settlement_id, ()),
                payments=payments_by_settlement.get(settlement.settlement_id, ()),
                ledger_pool=ledger_pool,
                already_resolved_target_ids=frozenset(already_resolved_target_ids),
                now=now,
            )
            results.append(result)
            if result.resolution.disposition == Disposition.AUTO_RESOLVED:
                already_resolved_target_ids.update(result.resolution.target_ledger_entry_ids)

        auto_resolved = sum(
            1 for r in results if r.resolution.disposition == Disposition.AUTO_RESOLVED
        )
        human_review = sum(
            1 for r in results if r.resolution.disposition == Disposition.HUMAN_REVIEW
        )
        unresolved = sum(1 for r in results if r.resolution.disposition == Disposition.UNRESOLVED)

        return BatchReconciliationSummary(
            total_settlements=len(ordered_settlements),
            auto_resolved_count=auto_resolved,
            human_review_count=human_review,
            unresolved_count=unresolved,
            results=tuple(results),
        )
