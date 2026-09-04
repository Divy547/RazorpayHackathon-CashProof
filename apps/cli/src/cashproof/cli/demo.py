"""CashProof end-to-end reconciliation demo.

Composition root: generates a Phase 2 synthetic dataset and runs it through the
production Phase 1+application reconciliation pipeline (matcher -> evidence ->
classifier -> evaluate_gate() -> Resolution -> AuditEvents).

ScenarioFamily/GroundTruth are used ONLY here, in the reporting layer, to label
representative examples for the demo printout. The production pipeline
(cashproof.application) never sees them.

Run with: uv run python -m cashproof.cli.demo
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from cashproof.application.batch import BatchReconciler, BatchReconciliationSummary
from cashproof.benchmark.generator import generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import GroundTruth, ScenarioFamily
from cashproof.domain.source import Payment, Settlement, SettlementItem


def run_demo(num_settlements: int = 100, seed: int = 42) -> None:
    config = GeneratorConfig(seed=seed, num_settlements=num_settlements)
    dataset = generate_dataset(config)

    items_by_settlement: dict[str, list[SettlementItem]] = defaultdict(list)
    for item in dataset.settlement_items:
        items_by_settlement[item.settlement_id].append(item)

    payment_by_id: dict[str, Payment] = {p.id: p for p in dataset.payments}
    payments_by_settlement: dict[str, list[Payment]] = defaultdict(list)
    for item in dataset.settlement_items:
        payment = payment_by_id.get(item.payment_id)
        if payment is not None:
            payments_by_settlement[item.settlement_id].append(payment)

    reconciler = BatchReconciler()
    now = datetime.now(UTC)
    summary: BatchReconciliationSummary = reconciler.run(
        run_id="demo-run-001",
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=now,
    )

    print("=" * 60)
    print("CashProof Reconciliation")
    print("=" * 60)
    print(f"Settlements: {summary.total_settlements}")
    print()
    print(f"AUTO_RESOLVED: {summary.auto_resolved_count}")
    print(f"HUMAN_REVIEW:  {summary.human_review_count}")
    print(f"UNRESOLVED:    {summary.unresolved_count}")
    print()

    # Demo-only correlation layer: map case_id -> scenario family purely for
    # human-readable labeling. The production pipeline above never used this.
    scenario_by_case: dict[str, GroundTruth] = {gt.case_id: gt for gt in dataset.ground_truths}
    settlement_by_id: dict[str, Settlement] = {s.settlement_id: s for s in dataset.settlements}

    shown: set[ScenarioFamily] = set()
    print("-" * 60)
    print("Representative examples (one per scenario family)")
    print("-" * 60)
    for result in summary.results:
        gt = scenario_by_case.get(result.case.case_id)
        if gt is None or gt.scenario_family in shown:
            continue
        shown.add(gt.scenario_family)
        settlement = settlement_by_id[result.case.case_id]
        gate = result.gate_evaluation
        print(f"[{gt.scenario_family.value}] settlement={settlement.settlement_id}")
        print(f"    expected_amount   = {settlement.net_deposited_minor}")
        print(f"    candidate_count   = {len(result.candidates)}")
        print(f"    exception_type    = {result.case.exception_type.value}")
        print(f"    gate_passed       = {gate.passed}")
        print(f"    failing_check     = {gate.failing_check}")
        print(f"    disposition       = {result.resolution.disposition.value}")
        print()

    print("=" * 60)


if __name__ == "__main__":
    run_demo()
