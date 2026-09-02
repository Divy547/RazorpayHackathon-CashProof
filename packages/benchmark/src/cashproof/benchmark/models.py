"""CashProof Benchmark Evaluator Models.

Evaluator-only models: GroundTruth, Resolvability, ScenarioFamily, and BenchmarkRun.
These models are technically isolated and must never be imported by production code.
"""

from __future__ import annotations

import enum
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from cashproof.domain.ai import InvestigatorBudget
from cashproof.domain.derived import EvidencePointer


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
class BenchmarkRun:
    """Benchmark execution metadata and reproducibility parameters."""

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
