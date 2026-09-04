"""Confidence Calibration and Automation Quality Intelligence (Phase 8).

Evaluator-only analytics comparing match hypotheses and AI confidence against GroundTruth.
This module is isolated to packages/benchmark and must never be imported in production code.

Core thesis:
Confidence = hypothesis strength / belief.
Evidence = factual support.
Gate = safety and compliance authorization firewall.
Confidence NEVER authorizes a resolution.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from cashproof.application.investigation import InvestigationRunResult
from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.models import GroundTruth, Resolvability, ScenarioFamily
from cashproof.domain.source import Settlement
from cashproof.domain.types import Disposition, StopReason


@dataclass(frozen=True, slots=True)
class ConfidenceObservation:
    """Evaluator-side representation of a single confidence-bearing hypothesis."""

    source: str  # "DETERMINISTIC_MATCHER" | "AI_INVESTIGATION"
    case_id: str
    confidence: float
    predicted_target_ids: tuple[str, ...]
    actual_target_ids: tuple[str, ...]
    ground_truth_resolvable: bool
    prediction_correct: bool
    abstained: bool
    scenario_family: ScenarioFamily
    disposition: Disposition
    gate_passed: bool
    failing_check: str | None


@dataclass(frozen=True, slots=True)
class ConfidenceBucket:
    """A single confidence interval bucket for calibration diagnostics."""

    bin_lower: float
    bin_upper: float
    bin_label: str
    observation_count: int
    correct_count: int
    incorrect_count: int
    abstention_count: int
    empirical_accuracy: float
    average_confidence: float
    gate_pass_count: int
    gate_fail_count: int


@dataclass(frozen=True, slots=True)
class ThresholdMetric:
    """Analytical simulation of precision and coverage at a given confidence threshold."""

    threshold: float
    predictions_meeting_threshold: int
    correct_predictions: int
    incorrect_predictions: int
    precision: float
    coverage: float
    false_auto_count_if_trusted_alone: int


@dataclass(frozen=True, slots=True)
class GateConfidenceCell:
    """Cross-tabulation showing how deterministic Gate interacts with confidence tiers."""

    tier: str
    confidence_range: str
    total_count: int
    gate_pass_count: int
    gate_fail_count: int
    dominant_failing_checks: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ScenarioConfidenceMetric:
    """Scenario-level confidence diagnostics across S1 through S6."""

    scenario_family: ScenarioFamily
    observation_count: int
    average_confidence: float
    precision: float
    coverage: float
    gate_pass_rate: float
    abstention_rate: float


@dataclass(frozen=True, slots=True)
class SourceConfidenceMetric:
    """Separate confidence metrics for DETERMINISTIC_MATCHER and AI_INVESTIGATION."""

    source: str
    observation_count: int
    average_confidence: float
    precision: float
    coverage: float
    ece: float
    brier_score: float
    abstention_rate: float
    gate_pass_rate: float
    buckets: tuple[ConfidenceBucket, ...]


@dataclass(frozen=True, slots=True)
class AutomationOpportunity:
    """Benchmark-only metric tracking high-confidence, correct, but non-auto-resolved cases."""

    threshold: float
    opportunity_count: int
    affected_settlement_net_minor: int
    currency: str
    failing_gate_checks: tuple[tuple[str, int], ...]
    current_dispositions: tuple[tuple[str, int], ...]
    sample_case_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfidenceReport:
    """Comprehensive benchmark confidence calibration and automation quality report."""

    total_observations: int
    overall_ece: float
    overall_brier_score: float
    buckets: tuple[ConfidenceBucket, ...]
    thresholds: tuple[ThresholdMetric, ...]
    gate_matrix: tuple[GateConfidenceCell, ...]
    source_metrics: tuple[SourceConfidenceMetric, ...]
    scenario_metrics: tuple[ScenarioConfidenceMetric, ...]
    automation_opportunity: AutomationOpportunity
    observations: tuple[ConfidenceObservation, ...]

    @property
    def predictions_made(self) -> int:
        return sum(1 for o in self.observations if not o.abstained)

    @property
    def abstentions(self) -> int:
        return sum(1 for o in self.observations if o.abstained)

    @property
    def high_confidence_precision(self) -> float:
        for t in self.thresholds:
            if abs(t.threshold - 0.80) < 1e-4:
                return t.precision
        return 0.0

    @property
    def potential_automation_opportunities(self) -> int:
        return self.automation_opportunity.opportunity_count

    @property
    def potential_automation_volume_minor(self) -> int:
        return self.automation_opportunity.affected_settlement_net_minor


class ConfidenceEvaluator:
    """Authoritative evaluator for confidence calibration and automation quality."""

    BUCKET_BOUNDS = [
        (0.0, 0.1, "0.00 - 0.10"),
        (0.1, 0.2, "0.10 - 0.20"),
        (0.2, 0.3, "0.20 - 0.30"),
        (0.3, 0.4, "0.30 - 0.40"),
        (0.4, 0.5, "0.40 - 0.50"),
        (0.5, 0.6, "0.50 - 0.60"),
        (0.6, 0.7, "0.60 - 0.70"),
        (0.7, 0.8, "0.70 - 0.80"),
        (0.8, 0.9, "0.80 - 0.90"),
        (0.9, 1.0, "0.90 - 1.00"),
    ]

    THRESHOLDS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    def evaluate(
        self,
        results: Sequence[ReconciliationResult],
        ground_truths: Sequence[GroundTruth],
        settlements: Mapping[str, Settlement] | Sequence[Settlement] | None = None,
        ai_results: Sequence[InvestigationRunResult] | None = None,
    ) -> ConfidenceReport:
        gt_by_case = {gt.case_id: gt for gt in ground_truths}
        settlement_by_id = (
            settlements
            if isinstance(settlements, Mapping)
            else ({s.settlement_id: s for s in settlements} if settlements else {})
        )

        observations: list[ConfidenceObservation] = []

        # 1. Deterministic Matcher Hypotheses
        for res in results:
            case_id = res.case.case_id
            gt = gt_by_case.get(case_id)
            if gt is None:
                continue

            proposed_targets = res.gate_evaluation.target_ledger_entry_ids
            actual_targets = tuple(sorted(gt.exact_target_ledger_entry_ids))
            is_provable = gt.resolvability == Resolvability.PROVABLE

            if res.candidates:
                top_cand = res.candidates[0]
                if proposed_targets:
                    matching = [
                        c.score for c in res.candidates if c.ledger_entry_id in proposed_targets
                    ]
                    confidence = max(matching) if matching else top_cand.score
                    predicted_targets = tuple(sorted(proposed_targets))
                    abstained = False
                    # Exact set equality required
                    correct = is_provable and (
                        frozenset(predicted_targets) == gt.exact_target_ledger_entry_ids
                    )
                else:
                    # Multiple candidates or ambiguous tie: classifier abstained
                    confidence = top_cand.score
                    predicted_targets = ()
                    abstained = True
                    correct = False
            else:
                # No candidates found
                confidence = 0.0
                predicted_targets = ()
                abstained = True
                correct = False

            observations.append(
                ConfidenceObservation(
                    source="DETERMINISTIC_MATCHER",
                    case_id=case_id,
                    confidence=confidence,
                    predicted_target_ids=predicted_targets,
                    actual_target_ids=actual_targets,
                    ground_truth_resolvable=is_provable,
                    prediction_correct=correct,
                    abstained=abstained,
                    scenario_family=gt.scenario_family,
                    disposition=res.resolution.disposition,
                    gate_passed=res.gate_evaluation.passed,
                    failing_check=res.gate_evaluation.failing_check,
                )
            )

        # 2. AI Investigation Hypotheses (if executed)
        if ai_results:
            for inv_res in ai_results:
                case_id = inv_res.case_id
                gt = gt_by_case.get(case_id)
                if gt is None:
                    continue

                actual_targets = tuple(sorted(gt.exact_target_ledger_entry_ids))
                is_provable = gt.resolvability == Resolvability.PROVABLE

                if inv_res.proposal is not None:
                    confidence = inv_res.proposal.confidence
                    predicted_targets = tuple(sorted(inv_res.proposal.target_ledger_entry_ids))
                    abstained = False
                    correct = is_provable and (
                        inv_res.proposal.target_ledger_entry_ids == gt.exact_target_ledger_entry_ids
                    )
                else:
                    confidence = 0.0
                    predicted_targets = ()
                    # Intentional abstention vs provider failure
                    abstained = inv_res.investigation.stop_reason == StopReason.COMPLETED
                    correct = False

                gate_passed = inv_res.preview_gate.passed if inv_res.preview_gate else False
                failing_check = inv_res.preview_gate.failing_check if inv_res.preview_gate else None

                observations.append(
                    ConfidenceObservation(
                        source="AI_INVESTIGATION",
                        case_id=case_id,
                        confidence=confidence,
                        predicted_target_ids=predicted_targets,
                        actual_target_ids=actual_targets,
                        ground_truth_resolvable=is_provable,
                        prediction_correct=correct,
                        abstained=abstained,
                        scenario_family=gt.scenario_family,
                        disposition=Disposition.HUMAN_REVIEW,
                        gate_passed=gate_passed,
                        failing_check=failing_check,
                    )
                )

        # 3. Calibration Buckets (Overall)
        buckets = self._compute_buckets(observations)

        # 4. ECE & Brier Score (Overall)
        active_preds = [o for o in observations if not o.abstained]
        overall_ece = self._compute_ece(buckets, len(active_preds))
        overall_brier = self._compute_brier(active_preds)

        # 5. Threshold Analysis (Precision / Coverage Curve)
        thresholds = self._compute_thresholds(active_preds)

        # 6. Gate × Confidence Matrix
        gate_matrix = self._compute_gate_matrix(observations)

        # 7. Scenario Metrics
        scenario_metrics = self._compute_scenario_metrics(observations)

        # 8. Source Metrics (Separate DETERMINISTIC_MATCHER and AI_INVESTIGATION)
        source_metrics = self._compute_source_metrics(observations)

        # 9. Automation Opportunity Analysis
        automation_opportunity = self._compute_automation_opportunity(
            observations=observations,
            settlement_by_id=settlement_by_id,
            threshold=0.80,
        )

        return ConfidenceReport(
            total_observations=len(observations),
            overall_ece=round(overall_ece, 4),
            overall_brier_score=round(overall_brier, 4),
            buckets=tuple(buckets),
            thresholds=tuple(thresholds),
            gate_matrix=tuple(gate_matrix),
            source_metrics=tuple(source_metrics),
            scenario_metrics=tuple(scenario_metrics),
            automation_opportunity=automation_opportunity,
            observations=tuple(observations),
        )

    def _compute_buckets(
        self, observations: Sequence[ConfidenceObservation]
    ) -> list[ConfidenceBucket]:
        buckets: list[ConfidenceBucket] = []
        for low, high, label in self.BUCKET_BOUNDS:
            in_bucket = [
                o
                for o in observations
                if (low <= o.confidence <= high if high == 1.0 else low <= o.confidence < high)
            ]
            count = len(in_bucket)
            correct = sum(1 for o in in_bucket if o.prediction_correct)
            abstained = sum(1 for o in in_bucket if o.abstained)
            incorrect = sum(1 for o in in_bucket if not o.prediction_correct and not o.abstained)

            evaluated_count = correct + incorrect
            empirical_acc = (correct / evaluated_count) if evaluated_count > 0 else 0.0
            avg_conf = (
                (sum(o.confidence for o in in_bucket) / count) if count > 0 else (low + high) / 2.0
            )
            gate_pass = sum(1 for o in in_bucket if o.gate_passed)
            gate_fail = count - gate_pass

            buckets.append(
                ConfidenceBucket(
                    bin_lower=low,
                    bin_upper=high,
                    bin_label=label,
                    observation_count=count,
                    correct_count=correct,
                    incorrect_count=incorrect,
                    abstention_count=abstained,
                    empirical_accuracy=round(empirical_acc, 4),
                    average_confidence=round(avg_conf, 4),
                    gate_pass_count=gate_pass,
                    gate_fail_count=gate_fail,
                )
            )
        return buckets

    def _compute_ece(
        self, buckets: Sequence[ConfidenceBucket], total_active_predictions: int
    ) -> float:
        if total_active_predictions <= 0:
            return 0.0
        ece = 0.0
        for b in buckets:
            n_b = b.correct_count + b.incorrect_count
            if n_b > 0:
                weight = n_b / total_active_predictions
                error = abs(b.average_confidence - b.empirical_accuracy)
                ece += weight * error
        return ece

    def _compute_brier(self, active_preds: Sequence[ConfidenceObservation]) -> float:
        if not active_preds:
            return 0.0
        total_sq_error = sum(
            (o.confidence - (1.0 if o.prediction_correct else 0.0)) ** 2 for o in active_preds
        )
        return total_sq_error / len(active_preds)

    def _compute_thresholds(
        self, active_preds: Sequence[ConfidenceObservation]
    ) -> list[ThresholdMetric]:
        total_eligible = len(active_preds)
        metrics: list[ThresholdMetric] = []
        for t in self.THRESHOLDS:
            meeting = [o for o in active_preds if o.confidence >= t]
            m_count = len(meeting)
            correct = sum(1 for o in meeting if o.prediction_correct)
            incorrect = m_count - correct

            precision = (correct / m_count) if m_count > 0 else 1.0
            coverage = (m_count / total_eligible) if total_eligible > 0 else 0.0

            metrics.append(
                ThresholdMetric(
                    threshold=t,
                    predictions_meeting_threshold=m_count,
                    correct_predictions=correct,
                    incorrect_predictions=incorrect,
                    precision=round(precision, 4),
                    coverage=round(coverage, 4),
                    false_auto_count_if_trusted_alone=incorrect,
                )
            )
        return metrics

    def _compute_gate_matrix(
        self, observations: Sequence[ConfidenceObservation]
    ) -> list[GateConfidenceCell]:
        tiers_def: list[tuple[str, str, Callable[[float], bool]]] = [
            ("HIGH", "0.80 - 1.00", lambda c: c >= 0.8),
            ("MEDIUM", "0.50 - 0.80", lambda c: 0.5 <= c < 0.8),
            ("LOW", "0.00 - 0.50", lambda c: c < 0.5),
        ]

        matrix: list[GateConfidenceCell] = []
        for name, crange, predicate in tiers_def:
            tier_obs = [o for o in observations if predicate(o.confidence)]
            total = len(tier_obs)
            passed = sum(1 for o in tier_obs if o.gate_passed)
            failed = total - passed

            fail_counts: dict[str, int] = defaultdict(int)
            for o in tier_obs:
                if not o.gate_passed and o.failing_check:
                    fail_counts[o.failing_check] += 1

            sorted_fails = tuple(sorted(fail_counts.items(), key=lambda x: (-x[1], x[0])))
            matrix.append(
                GateConfidenceCell(
                    tier=name,
                    confidence_range=crange,
                    total_count=total,
                    gate_pass_count=passed,
                    gate_fail_count=failed,
                    dominant_failing_checks=sorted_fails,
                )
            )
        return matrix

    def _compute_scenario_metrics(
        self, observations: Sequence[ConfidenceObservation]
    ) -> list[ScenarioConfidenceMetric]:
        all_families = (
            ScenarioFamily.S1_STRUCTURED_EXACT,
            ScenarioFamily.S2_STRUCTURED_AMBIGUOUS,
            ScenarioFamily.S3_FINANCIAL_MISMATCH,
            ScenarioFamily.S4_EXTERNAL_REF_TEXT,
            ScenarioFamily.S5_NARRATION_ALIAS_TEXT,
            ScenarioFamily.S6_NON_PROVABLE_CONFLICT,
        )

        scenario_by_family: dict[ScenarioFamily, list[ConfidenceObservation]] = defaultdict(list)
        for o in observations:
            scenario_by_family[o.scenario_family].append(o)

        metrics: list[ScenarioConfidenceMetric] = []
        for fam in all_families:
            obs = scenario_by_family.get(fam, [])
            count = len(obs)
            if count == 0:
                metrics.append(
                    ScenarioConfidenceMetric(
                        scenario_family=fam,
                        observation_count=0,
                        average_confidence=0.0,
                        precision=0.0,
                        coverage=0.0,
                        gate_pass_rate=0.0,
                        abstention_rate=0.0,
                    )
                )
                continue

            avg_conf = sum(o.confidence for o in obs) / count
            active = [o for o in obs if not o.abstained]
            correct = sum(1 for o in active if o.prediction_correct)
            precision = (correct / len(active)) if active else 0.0
            coverage = (len(active) / count) if count > 0 else 0.0
            gate_pass = sum(1 for o in obs if o.gate_passed)
            gate_pass_rate = gate_pass / count
            abstained = sum(1 for o in obs if o.abstained)
            abstention_rate = abstained / count

            metrics.append(
                ScenarioConfidenceMetric(
                    scenario_family=fam,
                    observation_count=count,
                    average_confidence=round(avg_conf, 4),
                    precision=round(precision, 4),
                    coverage=round(coverage, 4),
                    gate_pass_rate=round(gate_pass_rate, 4),
                    abstention_rate=round(abstention_rate, 4),
                )
            )
        return metrics

    def _compute_source_metrics(
        self, observations: Sequence[ConfidenceObservation]
    ) -> list[SourceConfidenceMetric]:
        sources = sorted({o.source for o in observations})
        metrics: list[SourceConfidenceMetric] = []

        for src in sources:
            src_obs = [o for o in observations if o.source == src]
            count = len(src_obs)
            if count == 0:
                continue

            avg_conf = sum(o.confidence for o in src_obs) / count
            active = [o for o in src_obs if not o.abstained]
            correct = sum(1 for o in active if o.prediction_correct)
            precision = (correct / len(active)) if active else 0.0
            coverage = (len(active) / count) if count > 0 else 0.0
            abstained = sum(1 for o in src_obs if o.abstained)
            abstention_rate = abstained / count
            gate_pass = sum(1 for o in src_obs if o.gate_passed)
            gate_pass_rate = gate_pass / count

            src_buckets = self._compute_buckets(src_obs)
            src_ece = self._compute_ece(src_buckets, len(active))
            src_brier = self._compute_brier(active)

            metrics.append(
                SourceConfidenceMetric(
                    source=src,
                    observation_count=count,
                    average_confidence=round(avg_conf, 4),
                    precision=round(precision, 4),
                    coverage=round(coverage, 4),
                    ece=round(src_ece, 4),
                    brier_score=round(src_brier, 4),
                    abstention_rate=round(abstention_rate, 4),
                    gate_pass_rate=round(gate_pass_rate, 4),
                    buckets=tuple(src_buckets),
                )
            )
        return metrics

    def _compute_automation_opportunity(
        self,
        observations: Sequence[ConfidenceObservation],
        settlement_by_id: Mapping[str, Settlement],
        threshold: float = 0.80,
    ) -> AutomationOpportunity:
        # High confidence, currently not auto-resolved, but hypothesis target is actually correct!
        opportunity_cases = [
            o
            for o in observations
            if o.confidence >= threshold
            and o.disposition != Disposition.AUTO_RESOLVED
            and o.prediction_correct
        ]

        total_net = 0
        currency = "INR"
        failing_checks: dict[str, int] = defaultdict(int)
        dispositions: dict[str, int] = defaultdict(int)
        sample_ids: list[str] = []

        for o in opportunity_cases:
            s = settlement_by_id.get(o.case_id)
            if s:
                total_net += s.net_deposited_minor
                currency = s.currency.value

            if o.failing_check:
                failing_checks[o.failing_check] += 1
            dispositions[o.disposition.value] += 1
            if len(sample_ids) < 10:
                sample_ids.append(o.case_id)

        sorted_checks = tuple(sorted(failing_checks.items(), key=lambda x: (-x[1], x[0])))
        sorted_disps = tuple(sorted(dispositions.items(), key=lambda x: (-x[1], x[0])))

        return AutomationOpportunity(
            threshold=threshold,
            opportunity_count=len(opportunity_cases),
            affected_settlement_net_minor=total_net,
            currency=currency,
            failing_gate_checks=sorted_checks,
            current_dispositions=sorted_disps,
            sample_case_ids=tuple(sample_ids),
        )
