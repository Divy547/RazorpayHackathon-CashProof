"""Integration tests proving BenchmarkRunner invokes the real production BatchReconciler.

Verifies:
- No alternate or shortcut reconciliation path is used in benchmark evaluation.
- Real production BatchReconciler is called with real source records.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from cashproof.application.batch import BatchReconciler, BatchReconciliationSummary
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.runner import BenchmarkRunner
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)


class SpyBatchReconciler(BatchReconciler):
    """Spy wrapper around production BatchReconciler to verify execution flow."""

    def __init__(self) -> None:
        super().__init__()
        self.call_count = 0
        self.recorded_settlements: list[Settlement] = []

    def run(
        self,
        run_id: str,
        settlements: Sequence[Settlement],
        items_by_settlement: Mapping[str, Sequence[SettlementItem]],
        payments_by_settlement: Mapping[str, Sequence[Payment]],
        ledger_pool: Sequence[LedgerEntry],
        now: datetime,
    ) -> BatchReconciliationSummary:
        self.call_count += 1
        self.recorded_settlements = list(settlements)
        # Delegates directly to the real BatchReconciler implementation
        return super().run(
            run_id=run_id,
            settlements=settlements,
            items_by_settlement=items_by_settlement,
            payments_by_settlement=payments_by_settlement,
            ledger_pool=ledger_pool,
            now=now,
        )


def test_benchmark_runner_uses_real_production_batch_reconciler() -> None:
    spy = SpyBatchReconciler()
    runner = BenchmarkRunner(reconciler=spy)
    config = GeneratorConfig(seed=42, num_settlements=50)

    run = runner.run(config=config, run_id="integration_test_run", now=FIXED_NOW)

    # 1. Proves production BatchReconciler.run was invoked
    assert spy.call_count == 1
    assert len(spy.recorded_settlements) == 50

    # 2. Proves real production results were evaluated
    assert run.overall_metrics is not None
    assert run.overall_metrics.total_cases == 50
    assert run.overall_metrics.safety_gate_passed is True
    assert run.case_evaluations is not None
    assert len(run.case_evaluations) == 50
