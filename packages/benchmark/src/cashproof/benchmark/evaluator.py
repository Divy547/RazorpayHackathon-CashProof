"""CashProof Benchmark Evaluator: Evaluates production reconciliation against GroundTruth.

GroundTruth is evaluator-only and technically isolated from production reconciliation code.
This module evaluates exact target set equality, primary safety invariants, disposition rates,
scenario matrices (S1-S6), and KPI throughput.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.models import (
    AIMetrics,
    BenchmarkTiming,
    CaseEvaluation,
    GroundTruth,
    OverallMetrics,
    Resolvability,
    ScenarioFamily,
    ScenarioMetrics,
)
from cashproof.domain.types import Disposition


class BenchmarkEvaluationError(Exception):
    """Raised when ground truth alignment or case join invariant fails."""


class BenchmarkEvaluator:
    """Authoritative evaluator comparing real production reconciliation results to GroundTruth.

    Enforces the primary safety invariant:
    - Zero false auto-resolutions across all cases.
    - Exact target set equality only (frozenset equality).
    - No confidence scoring, no heuristics.
    """

    def evaluate(
        self,
        results: Sequence[ReconciliationResult],
        ground_truths: Sequence[GroundTruth],
        pipeline_duration_seconds: float = 0.0,
        ai_metrics: AIMetrics | None = None,
        timing_boundary: str = (
            "BatchReconciler.run execution wall-clock (excluding generator and evaluation)"
        ),
    ) -> tuple[
        OverallMetrics,
        tuple[ScenarioMetrics, ...],
        tuple[CaseEvaluation, ...],
        BenchmarkTiming,
    ]:
        gt_by_case: dict[str, GroundTruth] = {gt.case_id: gt for gt in ground_truths}
        if len(gt_by_case) != len(ground_truths):
            raise BenchmarkEvaluationError("Duplicate case_id found in ground truths.")

        case_evaluations: list[CaseEvaluation] = []
        family_evals: dict[ScenarioFamily, list[CaseEvaluation]] = defaultdict(list)

        for result in results:
            case_id = result.case.case_id
            gt = gt_by_case.get(case_id)
            if gt is None:
                err_msg = (
                    f"Production reconciliation result for case '{case_id}' "
                    "has no matching GroundTruth."
                )
                raise BenchmarkEvaluationError(err_msg)

            disposition = result.resolution.disposition
            actual_targets = frozenset(result.resolution.target_ledger_entry_ids)
            expected_targets = gt.exact_target_ledger_entry_ids

            is_auto = disposition == Disposition.AUTO_RESOLVED
            exact_match = actual_targets == expected_targets

            # Primary safety invariant definition:
            # A false auto-resolution occurs when production emits AUTO_RESOLVED but:
            # 1. GroundTruth is NOT_PROVABLE, OR
            # 2. resolved target IDs are not exactly equal to GroundTruth target IDs.
            is_false_auto = is_auto and (
                gt.resolvability == Resolvability.NOT_PROVABLE or not exact_match
            )
            is_correct_auto = is_auto and (
                gt.resolvability == Resolvability.PROVABLE and exact_match
            )

            # Scenario outcome classification:
            is_correct_outcome = self._evaluate_scenario_outcome(
                family=gt.scenario_family,
                resolvability=gt.resolvability,
                disposition=disposition,
                is_correct_auto=is_correct_auto,
                is_false_auto=is_false_auto,
            )

            notes: str | None = None
            if is_false_auto:
                if gt.resolvability == Resolvability.NOT_PROVABLE:
                    reason_str = gt.not_provable_reason or "ambiguity/conflict"
                    notes = f"False auto-resolution on NOT_PROVABLE case ({reason_str})"
                else:
                    notes = (
                        f"Target mismatch: expected {sorted(expected_targets)}, "
                        f"got {sorted(actual_targets)}"
                    )

            evaluation = CaseEvaluation(
                case_id=case_id,
                scenario_family=gt.scenario_family,
                resolvability=gt.resolvability,
                disposition=disposition,
                gate_passed=result.gate_evaluation.passed,
                failing_check=result.gate_evaluation.failing_check,
                actual_target_ids=tuple(sorted(actual_targets)),
                expected_target_ids=tuple(sorted(expected_targets)),
                is_correct_auto_resolution=is_correct_auto,
                is_false_auto_resolution=is_false_auto,
                is_correct_outcome=is_correct_outcome,
                notes=notes,
            )
            case_evaluations.append(evaluation)
            family_evals[gt.scenario_family].append(evaluation)

        # Totals and counts
        total_cases = len(case_evaluations)
        auto_resolved = sum(
            1 for e in case_evaluations if e.disposition == Disposition.AUTO_RESOLVED
        )
        human_review = sum(1 for e in case_evaluations if e.disposition == Disposition.HUMAN_REVIEW)
        unresolved = sum(1 for e in case_evaluations if e.disposition == Disposition.UNRESOLVED)

        false_auto_count = sum(1 for e in case_evaluations if e.is_false_auto_resolution)
        correct_auto_count = sum(1 for e in case_evaluations if e.is_correct_auto_resolution)
        zero_false_auto = false_auto_count == 0
        safety_gate_passed = zero_false_auto

        # Rates
        resolution_rate = (auto_resolved / total_cases) if total_cases > 0 else 0.0
        auto_resolution_rate = (auto_resolved / total_cases) if total_cases > 0 else 0.0
        human_review_rate = (human_review / total_cases) if total_cases > 0 else 0.0
        unresolved_rate = (unresolved / total_cases) if total_cases > 0 else 0.0
        exact_target_set_accuracy = (
            (correct_auto_count / auto_resolved) if auto_resolved > 0 else 1.0
        )

        # Primary KPI: correctly resolved records per minute
        records_per_minute = (
            (correct_auto_count / pipeline_duration_seconds * 60.0)
            if pipeline_duration_seconds > 0
            else 0.0
        )

        overall = OverallMetrics(
            total_cases=total_cases,
            auto_resolved=auto_resolved,
            human_review=human_review,
            unresolved=unresolved,
            resolution_rate=resolution_rate,
            auto_resolution_rate=auto_resolution_rate,
            human_review_rate=human_review_rate,
            unresolved_rate=unresolved_rate,
            correct_auto_resolutions=correct_auto_count,
            false_auto_resolutions=false_auto_count,
            exact_target_set_accuracy=exact_target_set_accuracy,
            zero_false_auto_resolution=zero_false_auto,
            safety_gate_passed=safety_gate_passed,
            false_auto_resolution_count=false_auto_count,
            correct_auto_resolution_count=correct_auto_count,
            auto_resolution_count=auto_resolved,
            records_per_minute=records_per_minute,
        )

        # Scenario Matrix for S1 through S6
        all_families = (
            ScenarioFamily.S1_STRUCTURED_EXACT,
            ScenarioFamily.S2_STRUCTURED_AMBIGUOUS,
            ScenarioFamily.S3_FINANCIAL_MISMATCH,
            ScenarioFamily.S4_EXTERNAL_REF_TEXT,
            ScenarioFamily.S5_NARRATION_ALIAS_TEXT,
            ScenarioFamily.S6_NON_PROVABLE_CONFLICT,
        )
        scenario_matrix_rows: list[ScenarioMetrics] = []
        for fam in all_families:
            cases = family_evals.get(fam, [])
            f_total = len(cases)
            f_auto = sum(1 for c in cases if c.disposition == Disposition.AUTO_RESOLVED)
            f_hr = sum(1 for c in cases if c.disposition == Disposition.HUMAN_REVIEW)
            f_unres = sum(1 for c in cases if c.disposition == Disposition.UNRESOLVED)
            f_correct = sum(1 for c in cases if c.is_correct_outcome)
            f_false_auto = sum(1 for c in cases if c.is_false_auto_resolution)

            scenario_matrix_rows.append(
                ScenarioMetrics(
                    scenario_family=fam,
                    total=f_total,
                    auto_resolved=f_auto,
                    human_review=f_hr,
                    unresolved=f_unres,
                    correct_outcomes=f_correct,
                    false_auto_resolutions=f_false_auto,
                )
            )

        timing = BenchmarkTiming(
            pipeline_duration_seconds=pipeline_duration_seconds,
            timing_boundary=timing_boundary,
        )

        return overall, tuple(scenario_matrix_rows), tuple(case_evaluations), timing

    @staticmethod
    def _evaluate_scenario_outcome(
        family: ScenarioFamily,
        resolvability: Resolvability,
        disposition: Disposition,
        is_correct_auto: bool,
        is_false_auto: bool,
    ) -> bool:
        """Determines if the pipeline's outcome matches expected scenario semantics.

        - S1: Provable exact match -> must be AUTO_RESOLVED with exact target IDs.
        - S2: Ambiguous match -> must route to HUMAN_REVIEW without false auto-resolution.
        - S3: Financial mismatch -> must fail bridge and route to HUMAN_REVIEW.
        - S4: External ref text -> must route to HUMAN_REVIEW per Decision 7.
        - S5: Narration alias text -> must route to HUMAN_REVIEW per Decision 7.
        - S6: Non-provable missing record -> must route to UNRESOLVED.
        """
        if is_false_auto:
            return False

        if family == ScenarioFamily.S1_STRUCTURED_EXACT:
            return is_correct_auto
        if family == ScenarioFamily.S2_STRUCTURED_AMBIGUOUS:
            return disposition == Disposition.HUMAN_REVIEW
        if family == ScenarioFamily.S3_FINANCIAL_MISMATCH:
            return disposition == Disposition.HUMAN_REVIEW
        if family == ScenarioFamily.S4_EXTERNAL_REF_TEXT:
            return disposition == Disposition.HUMAN_REVIEW
        if family == ScenarioFamily.S5_NARRATION_ALIAS_TEXT:
            return disposition == Disposition.HUMAN_REVIEW
        if family == ScenarioFamily.S6_NON_PROVABLE_CONFLICT:
            return disposition == Disposition.UNRESOLVED

        # Default fallback
        if resolvability == Resolvability.PROVABLE and is_correct_auto:
            return True
        return not is_false_auto
