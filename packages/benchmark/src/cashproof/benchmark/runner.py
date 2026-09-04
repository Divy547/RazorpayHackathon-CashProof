"""BenchmarkRunner: orchestrates synthetic dataset generation, executes the production
reconciliation pipeline, and evaluates results against GroundTruth.

Rules:
- NEVER creates alternate reconciliation logic.
- Uses real production BatchReconciler directly.
- GroundTruth is passed ONLY to BenchmarkEvaluator.
"""

from __future__ import annotations

import subprocess
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from cashproof.application.batch import BatchReconciler
from cashproof.application.investigation import AIInvestigationUseCase, InvestigationRunResult
from cashproof.application.ports import AIInvestigatorPort
from cashproof.benchmark.confidence import ConfidenceEvaluator
from cashproof.benchmark.evaluator import BenchmarkEvaluator
from cashproof.benchmark.generator import generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import (
    AIMetrics,
    BenchmarkRun,
)
from cashproof.domain.ai import InvestigatorBudget
from cashproof.domain.source import Payment, SettlementItem
from cashproof.domain.types import Disposition, StopReason

DEFAULT_BUDGET = InvestigatorBudget(
    max_tool_calls=6,
    max_tokens=8000,
    timeout_seconds=60.0,
    temperature=0.0,
    model_version="claude-sonnet-5",
)


def get_git_revision() -> str:
    """Safely retrieves current git commit hash or returns a fallback revision."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, timeout=2
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "rev_production"


class BenchmarkRunner:
    """Executes end-to-end benchmark evaluation over the real production pipeline."""

    def __init__(
        self,
        reconciler: BatchReconciler | None = None,
        evaluator: BenchmarkEvaluator | None = None,
        confidence_evaluator: ConfidenceEvaluator | None = None,
    ) -> None:
        self._reconciler = reconciler or BatchReconciler()
        self._evaluator = evaluator or BenchmarkEvaluator()
        self._confidence_evaluator = confidence_evaluator or ConfidenceEvaluator()

    def run(
        self,
        config: GeneratorConfig,
        run_id: str | None = None,
        investigator: AIInvestigatorPort | None = None,
        ai_budget: InvestigatorBudget | None = None,
        arm: str | None = None,
        rule_version: str = "cashproof-matcher-1.0.0",
        code_revision: str | None = None,
        policy_version: str = "pol_cashproof_v1",
        model_version: str | None = None,
        prompt_version: str | None = None,
        now: datetime | None = None,
    ) -> BenchmarkRun:
        exec_now = now or datetime.now(UTC)
        run_identifier = run_id or f"bench_{int(exec_now.timestamp())}_{config.seed}"
        code_rev = code_revision or get_git_revision()
        chosen_budget = ai_budget or DEFAULT_BUDGET
        chosen_arm = arm or ("ai_investigator" if investigator is not None else "deterministic")
        chosen_model_version = model_version or (
            chosen_budget.model_version if investigator is not None else None
        )

        # 1. Deterministic synthetic dataset generation (Phase 2 generator)
        dataset = generate_dataset(config)

        # 2. Ingestion / indexing for production BatchReconciler
        items_by_settlement: dict[str, list[SettlementItem]] = defaultdict(list)
        for item in dataset.settlement_items:
            items_by_settlement[item.settlement_id].append(item)

        payment_by_id = {p.id: p for p in dataset.payments}
        payments_by_settlement: dict[str, list[Payment]] = defaultdict(list)
        for item in dataset.settlement_items:
            payment = payment_by_id.get(item.payment_id)
            if payment is not None:
                payments_by_settlement[item.settlement_id].append(payment)

        # 3. Honest timing boundary: measured strictly around production pipeline execution
        start_time = time.perf_counter()
        summary = self._reconciler.run(
            run_id=run_identifier,
            settlements=dataset.settlements,
            items_by_settlement=items_by_settlement,
            payments_by_settlement=payments_by_settlement,
            ledger_pool=dataset.ledger_entries,
            now=exec_now,
        )
        end_time = time.perf_counter()
        pipeline_duration = max(end_time - start_time, 1e-6)

        # 4. Optional AI investigation for HUMAN_REVIEW cases
        ai_metrics = AIMetrics()
        ai_run_results: list[InvestigationRunResult] | None = None
        if investigator is not None:
            ai_metrics, ai_run_results = self._run_ai_investigations(
                summary_results=summary.results,
                dataset=dataset,
                items_by_settlement=items_by_settlement,
                payments_by_settlement=payments_by_settlement,
                investigator=investigator,
                budget=chosen_budget,
                run_id=run_identifier,
                now=exec_now,
            )

        # 5. Benchmark Evaluator (GroundTruth is isolated and consumed only here)
        overall, scenario_matrix, case_evaluations, timing = self._evaluator.evaluate(
            results=summary.results,
            ground_truths=dataset.ground_truths,
            pipeline_duration_seconds=pipeline_duration,
            ai_metrics=ai_metrics,
        )

        # 6. Confidence Calibration Evaluator (GroundTruth is isolated and consumed only here)
        confidence_report = self._confidence_evaluator.evaluate(
            results=summary.results,
            ground_truths=dataset.ground_truths,
            settlements=dataset.settlements,
            ai_results=ai_run_results,
        )

        # 7. Combined metrics dictionary
        combined_metrics = overall.as_dict()
        combined_metrics["confidence_ece"] = confidence_report.overall_ece
        combined_metrics["confidence_brier_score"] = confidence_report.overall_brier_score
        if investigator is not None:
            combined_metrics.update(ai_metrics.as_dict())

        return BenchmarkRun(
            run_id=run_identifier,
            seed=config.seed,
            dataset_version=config.generator_version,
            rule_version=rule_version,
            code_revision=code_rev,
            model_version=chosen_model_version,
            prompt_version=prompt_version,
            policy_version=policy_version,
            arm=chosen_arm,
            metrics=combined_metrics,
            ai_budget=chosen_budget,
            overall_metrics=overall,
            scenario_matrix=scenario_matrix,
            ai_metrics=ai_metrics,
            case_evaluations=case_evaluations,
            timing=timing,
            confidence_report=confidence_report,
        )

    def _run_ai_investigations(
        self,
        summary_results: Sequence[Any],
        dataset: Any,
        items_by_settlement: Mapping[str, Sequence[SettlementItem]],
        payments_by_settlement: Mapping[str, Sequence[Payment]],
        investigator: AIInvestigatorPort,
        budget: InvestigatorBudget,
        run_id: str,
        now: datetime,
    ) -> tuple[AIMetrics, list[InvestigationRunResult]]:
        use_case = AIInvestigationUseCase(investigator)
        investigation_results: list[InvestigationRunResult] = []

        settlement_by_id = {s.settlement_id: s for s in dataset.settlements}

        for result in summary_results:
            if result.resolution.disposition == Disposition.HUMAN_REVIEW:
                settlement = settlement_by_id[result.case.case_id]
                items = items_by_settlement.get(settlement.settlement_id, ())
                payments = payments_by_settlement.get(settlement.settlement_id, ())
                try:
                    inv_res = use_case.run_investigation(
                        result=result,
                        settlement=settlement,
                        items=items,
                        payments=payments,
                        ledger_pool=dataset.ledger_entries,
                        budget=budget,
                        run_id=run_id,
                        now=now,
                        already_resolved_target_ids=frozenset(),
                    )
                    investigation_results.append(inv_res)
                except Exception:
                    # Investigating fails closed
                    pass

        # Aggregate AI metrics
        started = len(investigation_results)
        completed = 0
        abstained = 0
        failed = 0
        proposals_gen = 0
        proposals_passed = 0
        proposals_failed = 0
        total_calls = 0
        timeouts = 0
        budgets_exhausted = 0
        malformed = 0
        tool_failures = 0

        for r in investigation_results:
            inv = r.investigation
            total_calls += len(inv.tool_calls)
            if inv.stop_reason == StopReason.TIMEOUT:
                timeouts += 1
                failed += 1
            elif inv.stop_reason == StopReason.BUDGET_EXHAUSTED:
                budgets_exhausted += 1
                failed += 1
            elif inv.stop_reason == StopReason.MALFORMED_OUTPUT:
                malformed += 1
                failed += 1
            elif inv.stop_reason == StopReason.TOOL_FAILURE:
                tool_failures += 1
                failed += 1
            elif inv.stop_reason == StopReason.COMPLETED:
                if r.proposal is not None:
                    completed += 1
                else:
                    abstained += 1

            if r.proposal is not None:
                proposals_gen += 1
                if r.preview_gate is not None:
                    if r.preview_gate.passed:
                        proposals_passed += 1
                    else:
                        proposals_failed += 1

        metrics = AIMetrics(
            investigations_started=started,
            investigations_completed=completed,
            investigations_failed=failed,
            investigations_abstained=abstained,
            proposals_generated=proposals_gen,
            proposals_gate_passed=proposals_passed,
            proposals_gate_failed=proposals_failed,
            total_tool_calls=total_calls,
            token_usage=0,  # Token usage if tracked on budget/provider
            timeout_count=timeouts,
            budget_exhaustion_count=budgets_exhausted,
            malformed_output_count=malformed,
            tool_failure_count=tool_failures,
        )
        return metrics, investigation_results
