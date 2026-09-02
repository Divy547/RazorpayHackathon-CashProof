"""Benchmark package baseline and evaluator model tests."""

from dataclasses import FrozenInstanceError

import cashproof.benchmark
import pytest
from cashproof.benchmark.models import (
    BenchmarkRun,
    GroundTruth,
    Resolvability,
    ScenarioFamily,
)
from cashproof.domain.ai import InvestigatorBudget
from cashproof.domain.derived import EvidencePointer


def test_benchmark_package_import() -> None:
    assert cashproof.benchmark.__version__ == "0.1.0"


def test_ground_truth_creation_and_immutability() -> None:
    ptr = EvidencePointer("Payment", "pay_1", "id")
    gt = GroundTruth(
        case_id="case_1",
        resolvability=Resolvability.PROVABLE,
        exact_target_ledger_entry_ids=["le_10"],
        justifying_evidence=[ptr],
        scenario_family=ScenarioFamily.S1_STRUCTURED_EXACT,
    )
    assert gt.case_id == "case_1"
    assert gt.resolvability == Resolvability.PROVABLE
    assert gt.exact_target_ledger_entry_ids == frozenset({"le_10"})
    assert gt.scenario_family == ScenarioFamily.S1_STRUCTURED_EXACT

    with pytest.raises(FrozenInstanceError):
        gt.scenario_family = ScenarioFamily.S2_STRUCTURED_AMBIGUOUS  # type: ignore[misc]


def test_ground_truth_not_provable_requires_reason() -> None:
    with pytest.raises(ValueError, match="not_provable_reason is required"):
        GroundTruth(
            case_id="case_2",
            resolvability=Resolvability.NOT_PROVABLE,
            exact_target_ledger_entry_ids=[],
            justifying_evidence=[],
            scenario_family=ScenarioFamily.S6_NON_PROVABLE_CONFLICT,
            not_provable_reason="",
        )


def test_benchmark_run_creation() -> None:
    budget = InvestigatorBudget(5, 2048, 30.0, 0.0, "v1")
    run = BenchmarkRun(
        run_id="run_100",
        seed=42,
        dataset_version="v1.0",
        rule_version="sha_abc",
        code_revision="rev_xyz",
        model_version="claude-3-5-sonnet",
        prompt_version="p_v1",
        policy_version="pol_v1",
        arm="ai_investigator",
        metrics={"precision": 1.0, "recall": 0.95},
        ai_budget=budget,
    )
    assert run.run_id == "run_100"
    assert run.seed == 42
    assert run.metrics == (("precision", 1.0), ("recall", 0.95))
