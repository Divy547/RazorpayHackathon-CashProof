"""Deterministic batch reconciliation orchestration over Phase 2 source records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from cashproof.application.use_case import ReconcileSettlementUseCase, ReconciliationResult
from cashproof.domain.exceptions import DomainError
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.types import Disposition


@dataclass(frozen=True, slots=True)
class SettlementReconciliationError:
    """Records that one settlement could not be reconciled at all.

    Raised only for a domain-level data-quality failure on the settlement's
    OWN source records (e.g. no settlement items, or items that don't sum to
    the settlement's net_deposited_minor) - never fabricated in place of a
    real ReconciliationCase/GateEvaluation/Resolution. This settlement simply
    has no case, no gate evaluation, and no resolution for this run; it is
    surfaced here so the caller can see it was rejected rather than silently
    dropped or allowed to abort the rest of the batch.
    """

    settlement_id: str
    error_type: str
    message: str


@dataclass(frozen=True, slots=True)
class BatchReconciliationSummary:
    """Aggregate outcome of running the pipeline across every settlement in a batch."""

    total_settlements: int
    auto_resolved_count: int
    human_review_count: int
    unresolved_count: int
    results: tuple[ReconciliationResult, ...]
    failed_settlements: tuple[SettlementReconciliationError, ...] = ()


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
        failed_settlements: list[SettlementReconciliationError] = []

        for settlement in ordered_settlements:
            try:
                result = self._use_case.execute(
                    run_id=run_id,
                    settlement=settlement,
                    items=items_by_settlement.get(settlement.settlement_id, ()),
                    payments=payments_by_settlement.get(settlement.settlement_id, ()),
                    ledger_pool=ledger_pool,
                    already_resolved_target_ids=frozenset(already_resolved_target_ids),
                    now=now,
                )
            except DomainError as exc:
                # A domain-level invariant on THIS settlement's own source
                # records failed (e.g. no settlement items, or items that
                # don't sum to net_deposited_minor). This settlement gets no
                # case, no gate evaluation, and no resolution - nothing is
                # fabricated in its place. Every other settlement in the
                # batch must still be reconciled normally.
                failed_settlements.append(
                    SettlementReconciliationError(
                        settlement_id=settlement.settlement_id,
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )
                continue

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
            failed_settlements=tuple(failed_settlements),
        )
