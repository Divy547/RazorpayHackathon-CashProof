"""Tests for CashProof BenchmarkRunner.

Verifies:
- Reproducibility of benchmark runs given the same seed and configuration.
- Preservation and honesty of metadata (seed, versions, code revision).
- Honest wall-clock timing boundary and KPI throughput.
"""

from __future__ import annotations

from datetime import UTC, datetime

from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.runner import BenchmarkRunner

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)


def test_runner_reproducibility() -> None:
    config = GeneratorConfig(seed=123, num_settlements=50)
    runner = BenchmarkRunner()

    run1 = runner.run(config=config, run_id="run_rep_1", now=FIXED_NOW)
    run2 = runner.run(config=config, run_id="run_rep_2", now=FIXED_NOW)

    assert run1.seed == run2.seed == 123
    assert run1.overall_metrics is not None
    assert run2.overall_metrics is not None

    assert run1.overall_metrics.total_cases == run2.overall_metrics.total_cases == 50
    assert run1.overall_metrics.auto_resolved == run2.overall_metrics.auto_resolved
    assert run1.overall_metrics.human_review == run2.overall_metrics.human_review
    assert run1.overall_metrics.unresolved == run2.overall_metrics.unresolved
    assert (
        run1.overall_metrics.correct_auto_resolutions
        == run2.overall_metrics.correct_auto_resolutions
    )
    assert (
        run1.overall_metrics.false_auto_resolutions
        == run2.overall_metrics.false_auto_resolutions
        == 0
    )
    assert (
        run1.overall_metrics.safety_gate_passed == run2.overall_metrics.safety_gate_passed is True
    )

    # Scenario matrix rows match exactly
    for row1, row2 in zip(run1.scenario_matrix, run2.scenario_matrix, strict=True):
        assert row1.scenario_family == row2.scenario_family
        assert row1.total == row2.total
        assert row1.auto_resolved == row2.auto_resolved
        assert row1.human_review == row2.human_review
        assert row1.unresolved == row2.unresolved
        assert row1.correct_outcomes == row2.correct_outcomes
        assert row1.false_auto_resolutions == row2.false_auto_resolutions


def test_runner_metadata_and_timing_boundary() -> None:
    config = GeneratorConfig(seed=42, num_settlements=50)
    runner = BenchmarkRunner()

    run = runner.run(
        config=config,
        run_id="run_meta_test",
        rule_version="rules_v1",
        policy_version="policy_v1",
        now=FIXED_NOW,
    )

    assert run.run_id == "run_meta_test"
    assert run.seed == 42
    assert run.rule_version == "rules_v1"
    assert run.policy_version == "policy_v1"
    assert run.dataset_version == config.generator_version
    assert run.code_revision != ""
    assert run.timing is not None
    assert run.timing.pipeline_duration_seconds > 0.0
    assert "BatchReconciler.run execution wall-clock" in run.timing.timing_boundary
    assert run.records_per_minute > 0.0
