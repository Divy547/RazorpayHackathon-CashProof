"""Operational Confidence Service (Phase 8).

Computes production-visible operational confidence metrics from ReconciliationResults.
Strictly isolated from GroundTruth and benchmark scenario labels:
contains ZERO imports of cashproof.benchmark.

Core principle:
Confidence = hypothesis strength / belief.
Gate = safety and compliance firewall.
Confidence never authorizes automatic resolution.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.source import Settlement
from cashproof.domain.types import Disposition


@dataclass(frozen=True, slots=True)
class OperationalHypothesis:
    """Production-visible summary of a single case's match hypothesis confidence."""

    case_id: str
    source: str
    confidence: float
    target_count: int
    gate_passed: bool
    failing_check: str | None
    disposition: Disposition
    is_proposed: bool


@dataclass(frozen=True, slots=True)
class OperationalConfidenceBucket:
    """A confidence interval bucket for active production hypotheses."""

    bin_lower: float
    bin_upper: float
    bin_label: str
    hypothesis_count: int
    average_confidence: float
    gate_pass_count: int
    gate_fail_count: int


@dataclass(frozen=True, slots=True)
class GateTierSummary:
    """Cross-tabulation of a confidence tier against deterministic gate outcomes."""

    tier: str
    confidence_range: str
    total_count: int
    gate_pass_count: int
    gate_fail_count: int
    pass_rate_pct: float
    failing_check_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class CheckConfidenceContext:
    """Average hypothesis confidence context for a specific gate check blocker."""

    check_name: str
    case_count: int
    average_confidence: float
    min_confidence: float
    max_confidence: float


@dataclass(frozen=True, slots=True)
class OperationalConfidenceSummary:
    """Aggregated operational confidence diagnostics across a batch of cases."""

    total_cases: int
    hypotheses_evaluated: int
    average_confidence: float
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    high_confidence_gate_blocked_count: int
    buckets: tuple[OperationalConfidenceBucket, ...]
    gate_tiers: tuple[GateTierSummary, ...]
    check_contexts: tuple[CheckConfidenceContext, ...]


class OperationalConfidenceService:
    """Computes production-safe operational confidence distributions."""

    def analyze(
        self,
        results: Sequence[ReconciliationResult],
        settlements: Mapping[str, Settlement] | Sequence[Settlement] | None = None,
    ) -> OperationalConfidenceSummary:
        del settlements  # Unused for scalar confidence metrics, reserved for interface symmetry

        if not results:
            empty_buckets = tuple(
                OperationalConfidenceBucket(
                    bin_lower=round(i * 0.1, 1),
                    bin_upper=round((i + 1) * 0.1, 1),
                    bin_label=f"[{i * 0.1:.1f}, {(i + 1) * 0.1:.1f}{']' if i == 9 else ')'}",
                    hypothesis_count=0,
                    average_confidence=0.0,
                    gate_pass_count=0,
                    gate_fail_count=0,
                )
                for i in range(10)
            )
            empty_tiers = tuple(
                GateTierSummary(
                    tier=tier,
                    confidence_range=(
                        ">= 0.80"
                        if tier == "HIGH"
                        else ("0.50 - 0.80" if tier == "MEDIUM" else "< 0.50")
                    ),
                    total_count=0,
                    gate_pass_count=0,
                    gate_fail_count=0,
                    pass_rate_pct=0.0,
                    failing_check_counts=(),
                )
                for tier in ("HIGH", "MEDIUM", "LOW")
            )
            return OperationalConfidenceSummary(
                total_cases=0,
                hypotheses_evaluated=0,
                average_confidence=0.0,
                high_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
                high_confidence_gate_blocked_count=0,
                buckets=empty_buckets,
                gate_tiers=empty_tiers,
                check_contexts=(),
            )

        hypotheses: list[OperationalHypothesis] = []
        for res in results:
            case_id = res.case.case_id
            proposed_targets = res.gate_evaluation.target_ledger_entry_ids
            has_proposed = len(proposed_targets) > 0

            confidence = 0.0
            source = res.gate_evaluation.hypothesis_source.value

            if res.candidates:
                top_cand = res.candidates[0]
                if has_proposed:
                    # Find candidate score matching the proposed target
                    matching = [
                        c.score for c in res.candidates if c.ledger_entry_id in proposed_targets
                    ]
                    confidence = max(matching) if matching else top_cand.score
                else:
                    # Ambiguous or held back: top candidate score represents matcher strength
                    confidence = top_cand.score

            hypotheses.append(
                OperationalHypothesis(
                    case_id=case_id,
                    source=source,
                    confidence=confidence,
                    target_count=len(proposed_targets),
                    gate_passed=res.gate_evaluation.passed,
                    failing_check=res.gate_evaluation.failing_check,
                    disposition=res.resolution.disposition,
                    is_proposed=has_proposed,
                )
            )

        # 10 Standard Buckets [0.0, 0.1), ..., [0.9, 1.0]
        bucket_defs = [
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

        buckets: list[OperationalConfidenceBucket] = []
        for low, high, label in bucket_defs:
            in_bucket = [
                h
                for h in hypotheses
                if (low <= h.confidence <= high if high == 1.0 else low <= h.confidence < high)
            ]
            count = len(in_bucket)
            avg_conf = (
                (sum(h.confidence for h in in_bucket) / count) if count > 0 else (low + high) / 2.0
            )
            gate_pass = sum(1 for h in in_bucket if h.gate_passed)
            gate_fail = count - gate_pass

            buckets.append(
                OperationalConfidenceBucket(
                    bin_lower=low,
                    bin_upper=high,
                    bin_label=label,
                    hypothesis_count=count,
                    average_confidence=round(avg_conf, 4),
                    gate_pass_count=gate_pass,
                    gate_fail_count=gate_fail,
                )
            )

        # Confidence Tiers: HIGH (>= 0.8), MEDIUM (0.5 to 0.8), LOW (< 0.5)
        tiers_def: list[tuple[str, str, Callable[[float], bool]]] = [
            ("HIGH", ">= 0.80", lambda c: c >= 0.8),
            ("MEDIUM", "0.50 - 0.80", lambda c: 0.5 <= c < 0.8),
            ("LOW", "0.00 - 0.50", lambda c: c < 0.5),
        ]

        gate_tiers: list[GateTierSummary] = []
        for name, crange, predicate in tiers_def:
            tier_hyps = [h for h in hypotheses if predicate(h.confidence)]
            t_count = len(tier_hyps)
            t_pass = sum(1 for h in tier_hyps if h.gate_passed)
            t_fail = t_count - t_pass
            t_pct = (t_pass / t_count * 100.0) if t_count > 0 else 0.0

            fail_counts: dict[str, int] = defaultdict(int)
            for h in tier_hyps:
                if not h.gate_passed and h.failing_check:
                    fail_counts[h.failing_check] += 1

            sorted_fails = tuple(sorted(fail_counts.items(), key=lambda x: (-x[1], x[0])))
            gate_tiers.append(
                GateTierSummary(
                    tier=name,
                    confidence_range=crange,
                    total_count=t_count,
                    gate_pass_count=t_pass,
                    gate_fail_count=t_fail,
                    pass_rate_pct=round(t_pct, 2),
                    failing_check_counts=sorted_fails,
                )
            )

        # Check Context: average confidence per failing check
        check_to_hyps: dict[str, list[OperationalHypothesis]] = defaultdict(list)
        for h in hypotheses:
            if not h.gate_passed and h.failing_check:
                check_to_hyps[h.failing_check].append(h)

        check_contexts: list[CheckConfidenceContext] = []
        for check_name, c_hyps in sorted(check_to_hyps.items(), key=lambda x: -len(x[1])):
            confidences = [h.confidence for h in c_hyps]
            check_contexts.append(
                CheckConfidenceContext(
                    check_name=check_name,
                    case_count=len(c_hyps),
                    average_confidence=round(sum(confidences) / len(confidences), 4),
                    min_confidence=round(min(confidences), 4),
                    max_confidence=round(max(confidences), 4),
                )
            )

        total_hyps = len(hypotheses)
        overall_avg = sum(h.confidence for h in hypotheses) / total_hyps if total_hyps > 0 else 0.0
        high_conf = sum(1 for h in hypotheses if h.confidence >= 0.8)
        med_conf = sum(1 for h in hypotheses if 0.5 <= h.confidence < 0.8)
        low_conf = sum(1 for h in hypotheses if h.confidence < 0.5)
        high_blocked = sum(1 for h in hypotheses if h.confidence >= 0.8 and not h.gate_passed)

        return OperationalConfidenceSummary(
            total_cases=len(results),
            hypotheses_evaluated=total_hyps,
            average_confidence=round(overall_avg, 4),
            high_confidence_count=high_conf,
            medium_confidence_count=med_conf,
            low_confidence_count=low_conf,
            high_confidence_gate_blocked_count=high_blocked,
            buckets=tuple(buckets),
            gate_tiers=tuple(gate_tiers),
            check_contexts=tuple(check_contexts),
        )
