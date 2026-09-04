"""CashProof Benchmark Evaluator Models.

Evaluator-only models: GroundTruth, Resolvability, ScenarioFamily, and BenchmarkRun.
These models are technically isolated and must never be imported by production code.
"""

from __future__ import annotations

import enum
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cashproof.benchmark.confidence import ConfidenceReport

from cashproof.domain.ai import InvestigatorBudget
from cashproof.domain.derived import EvidencePointer
from cashproof.domain.types import Disposition


class Resolvability(enum.StrEnum):
    """Evaluator provability classification."""

    PROVABLE = "PROVABLE"
    NOT_PROVABLE = "NOT_PROVABLE"


class ScenarioFamily(enum.StrEnum):
    """Benchmark top-level scenario taxonomy."""

    S1_STRUCTURED_EXACT = "S1"
    S2_STRUCTURED_AMBIGUOUS = "S2"
    S3_FINANCIAL_MISMATCH = "S3"
    S4_EXTERNAL_REF_TEXT = "S4"
    S5_NARRATION_ALIAS_TEXT = "S5"
    S6_NON_PROVABLE_CONFLICT = "S6"


@dataclass(frozen=True, slots=True)
class GroundTruth:
    """Evaluator-only ground truth for benchmark cases.

    Contains true targets, scenario labels, and provability justifications.
    Production domain and application code cannot access this entity.
    """

    case_id: str
    resolvability: Resolvability
    exact_target_ledger_entry_ids: frozenset[str]
    justifying_evidence: tuple[EvidencePointer, ...]
    scenario_family: ScenarioFamily
    not_provable_reason: str | None = None

    def __init__(
        self,
        case_id: str,
        resolvability: Resolvability,
        exact_target_ledger_entry_ids: Iterable[str],
        justifying_evidence: Iterable[EvidencePointer],
        scenario_family: ScenarioFamily,
        not_provable_reason: str | None = None,
    ) -> None:
        if not case_id.strip():
            raise ValueError("case_id must not be empty.")
        if resolvability == Resolvability.NOT_PROVABLE and not not_provable_reason:
            raise ValueError("not_provable_reason is required when resolvability is NOT_PROVABLE.")

        object.__setattr__(self, "case_id", case_id)
        object.__setattr__(self, "resolvability", resolvability)
        object.__setattr__(
            self, "exact_target_ledger_entry_ids", frozenset(exact_target_ledger_entry_ids)
        )
        object.__setattr__(self, "justifying_evidence", tuple(justifying_evidence))
        object.__setattr__(self, "scenario_family", scenario_family)
        object.__setattr__(self, "not_provable_reason", not_provable_reason)


@dataclass(frozen=True, slots=True)
class OverallMetrics:
    """Core benchmark metrics and invariants."""

    total_cases: int
    auto_resolved: int
    human_review: int
    unresolved: int
    resolution_rate: float
    auto_resolution_rate: float
    human_review_rate: float
    unresolved_rate: float
    correct_auto_resolutions: int
    false_auto_resolutions: int
    exact_target_set_accuracy: float
    zero_false_auto_resolution: bool
    safety_gate_passed: bool
    false_auto_resolution_count: int
    correct_auto_resolution_count: int
    auto_resolution_count: int
    records_per_minute: float

    def as_dict(self) -> dict[str, float]:
        """Convert scalar metric values to float dictionary."""
        return {
            "total_cases": float(self.total_cases),
            "auto_resolved": float(self.auto_resolved),
            "human_review": float(self.human_review),
            "unresolved": float(self.unresolved),
            "resolution_rate": self.resolution_rate,
            "auto_resolution_rate": self.auto_resolution_rate,
            "human_review_rate": self.human_review_rate,
            "unresolved_rate": self.unresolved_rate,
            "correct_auto_resolutions": float(self.correct_auto_resolutions),
            "false_auto_resolutions": float(self.false_auto_resolutions),
            "exact_target_set_accuracy": self.exact_target_set_accuracy,
            "zero_false_auto_resolution": 1.0 if self.zero_false_auto_resolution else 0.0,
            "safety_gate_passed": 1.0 if self.safety_gate_passed else 0.0,
            "false_auto_resolution_count": float(self.false_auto_resolution_count),
            "correct_auto_resolution_count": float(self.correct_auto_resolution_count),
            "auto_resolution_count": float(self.auto_resolution_count),
            "records_per_minute": self.records_per_minute,
        }


@dataclass(frozen=True, slots=True)
class ScenarioMetrics:
    """Scenario matrix row for S1 through S6."""

    scenario_family: ScenarioFamily
    total: int
    auto_resolved: int
    human_review: int
    unresolved: int
    correct_outcomes: int
    false_auto_resolutions: int


@dataclass(frozen=True, slots=True)
class AIMetrics:
    """AI investigation performance and budget counters."""

    investigations_started: int = 0
    investigations_completed: int = 0
    investigations_failed: int = 0
    investigations_abstained: int = 0
    proposals_generated: int = 0
    proposals_gate_passed: int = 0
    proposals_gate_failed: int = 0
    total_tool_calls: int = 0
    token_usage: int = 0
    timeout_count: int = 0
    budget_exhaustion_count: int = 0
    malformed_output_count: int = 0
    tool_failure_count: int = 0

    def as_dict(self) -> dict[str, float]:
        """Convert counter metrics to float dictionary."""
        return {
            "ai_investigations_started": float(self.investigations_started),
            "ai_investigations_completed": float(self.investigations_completed),
            "ai_investigations_failed": float(self.investigations_failed),
            "ai_investigations_abstained": float(self.investigations_abstained),
            "ai_proposals_generated": float(self.proposals_generated),
            "ai_proposals_gate_passed": float(self.proposals_gate_passed),
            "ai_proposals_gate_failed": float(self.proposals_gate_failed),
            "ai_total_tool_calls": float(self.total_tool_calls),
            "ai_token_usage": float(self.token_usage),
            "ai_timeout_count": float(self.timeout_count),
            "ai_budget_exhaustion_count": float(self.budget_exhaustion_count),
            "ai_malformed_output_count": float(self.malformed_output_count),
            "ai_tool_failure_count": float(self.tool_failure_count),
        }


@dataclass(frozen=True, slots=True)
class BenchmarkTiming:
    """Timing metadata documenting the wall-clock boundary."""

    pipeline_duration_seconds: float
    timing_boundary: str = (
        "BatchReconciler.run execution wall-clock (excluding generator and evaluation)"
    )


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    """Detailed evaluation of a single case against GroundTruth."""

    case_id: str
    scenario_family: ScenarioFamily
    resolvability: Resolvability
    disposition: Disposition
    gate_passed: bool
    failing_check: str | None
    actual_target_ids: tuple[str, ...]
    expected_target_ids: tuple[str, ...]
    is_correct_auto_resolution: bool
    is_false_auto_resolution: bool
    is_correct_outcome: bool
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    """Benchmark execution metadata, reproducibility parameters, and evaluation results."""

    run_id: str
    seed: int
    dataset_version: str
    rule_version: str
    code_revision: str
    model_version: str | None
    prompt_version: str | None
    policy_version: str
    arm: str
    metrics: tuple[tuple[str, float], ...]
    ai_budget: InvestigatorBudget
    overall_metrics: OverallMetrics | None
    scenario_matrix: tuple[ScenarioMetrics, ...]
    ai_metrics: AIMetrics
    case_evaluations: tuple[CaseEvaluation, ...]
    timing: BenchmarkTiming | None
    confidence_report: ConfidenceReport | None = None

    def __init__(
        self,
        run_id: str,
        seed: int,
        dataset_version: str,
        rule_version: str,
        code_revision: str,
        model_version: str | None,
        prompt_version: str | None,
        policy_version: str,
        arm: str,
        metrics: Mapping[str, float] | Iterable[tuple[str, float]],
        ai_budget: InvestigatorBudget,
        overall_metrics: OverallMetrics | None = None,
        scenario_matrix: Sequence[ScenarioMetrics] = (),
        ai_metrics: AIMetrics | None = None,
        case_evaluations: Sequence[CaseEvaluation] = (),
        timing: BenchmarkTiming | None = None,
        confidence_report: ConfidenceReport | None = None,
    ) -> None:
        if not run_id.strip():
            raise ValueError("run_id must not be empty.")
        if not dataset_version.strip():
            raise ValueError("dataset_version must not be empty.")
        if not rule_version.strip():
            raise ValueError("rule_version must not be empty.")
        if not code_revision.strip():
            raise ValueError("code_revision must not be empty.")
        if not policy_version.strip():
            raise ValueError("policy_version must not be empty.")
        if not arm.strip():
            raise ValueError("arm must not be empty.")

        if isinstance(metrics, Mapping):
            frozen_metrics = tuple(sorted((str(k), float(v)) for k, v in metrics.items()))
        else:
            frozen_metrics = tuple((str(k), float(v)) for k, v in metrics)

        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "dataset_version", dataset_version)
        object.__setattr__(self, "rule_version", rule_version)
        object.__setattr__(self, "code_revision", code_revision)
        object.__setattr__(self, "model_version", model_version)
        object.__setattr__(self, "prompt_version", prompt_version)
        object.__setattr__(self, "policy_version", policy_version)
        object.__setattr__(self, "arm", arm)
        object.__setattr__(self, "metrics", frozen_metrics)
        object.__setattr__(self, "ai_budget", ai_budget)
        object.__setattr__(self, "overall_metrics", overall_metrics)
        object.__setattr__(self, "scenario_matrix", tuple(scenario_matrix))
        object.__setattr__(self, "ai_metrics", ai_metrics or AIMetrics())
        object.__setattr__(self, "case_evaluations", tuple(case_evaluations))
        object.__setattr__(self, "timing", timing)
        object.__setattr__(self, "confidence_report", confidence_report)

    @property
    def metrics_dict(self) -> dict[str, float]:
        """Return metrics as a dictionary."""
        return dict(self.metrics)

    @property
    def safety_gate_passed(self) -> bool:
        """Returns True iff zero false auto-resolutions were detected."""
        if self.overall_metrics is not None:
            return self.overall_metrics.safety_gate_passed
        val = self.metrics_dict.get("safety_gate_passed")
        return bool(val and val > 0.0)

    @property
    def records_per_minute(self) -> float:
        """Headline KPI: correctly resolved records per minute."""
        if self.overall_metrics is not None:
            return self.overall_metrics.records_per_minute
        return self.metrics_dict.get("records_per_minute", 0.0)

    def summary_dict(self) -> dict[str, Any]:
        """Serializable representation of the benchmark run."""
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "dataset_version": self.dataset_version,
            "rule_version": self.rule_version,
            "code_revision": self.code_revision,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
            "policy_version": self.policy_version,
            "arm": self.arm,
            "safety_gate_passed": self.safety_gate_passed,
            "records_per_minute": self.records_per_minute,
            "metrics": self.metrics_dict,
            "timing": (
                {
                    "pipeline_duration_seconds": self.timing.pipeline_duration_seconds,
                    "timing_boundary": self.timing.timing_boundary,
                }
                if self.timing
                else None
            ),
        }
