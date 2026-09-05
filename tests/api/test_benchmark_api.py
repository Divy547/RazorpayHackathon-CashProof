"""Tests for live benchmark endpoints in CashProof API.

Verifies:
- POST /api/benchmarks (run creation and response serialization)
- GET /api/benchmarks/{run_id} (fetching stored benchmark run)
- 404 on missing benchmark run
- 422 on invalid benchmark scale request (< 50 settlements)
- Serialization of safety gate failure when false auto-resolutions occur
"""

from __future__ import annotations

from typing import Any

from cashproof.api.app import create_app
from cashproof.api.schemas import (
    AIMetricOut,
    BenchmarkRunOut,
    BenchmarkTimingOut,
    FamilyMetricOut,
)
from cashproof.application.ports import AIInvestigatorPort, InvestigationOutcome
from cashproof.application.store import InMemoryCaseStore
from cashproof.benchmark.service import InMemoryBenchmarkService
from cashproof.domain.ai import InvestigatorBudget
from fastapi.testclient import TestClient

BUDGET = InvestigatorBudget(
    max_tool_calls=5,
    max_tokens=4000,
    timeout_seconds=30.0,
    temperature=0.0,
    model_version="fake-model",
)


class DummyInvestigator(AIInvestigatorPort):
    def investigate(self, **kwargs: Any) -> InvestigationOutcome:
        raise NotImplementedError("Not needed for benchmark API tests")


class MockFailingBenchmarkService:
    """Mock service that returns a benchmark run with a safety gate failure."""

    def __init__(self) -> None:
        self.runs: dict[str, Any] = {}

    def run_benchmark(
        self,
        seed: int = 42,
        num_settlements: int = 50,
        run_id: str | None = None,
        arm: str = "deterministic",
    ) -> Any:
        rid = run_id or "failing_run_01"
        out = BenchmarkRunOut(
            run_id=rid,
            seed=seed,
            dataset_version="1.0.0",
            rule_version="rules_v1",
            code_revision="rev_test",
            model_version=None,
            prompt_version=None,
            policy_version="pol_v1",
            arm=arm,
            total_cases=50,
            auto_resolved=25,
            human_review=20,
            unresolved=5,
            resolution_rate=0.5,
            auto_resolution_rate=0.5,
            human_review_rate=0.4,
            unresolved_rate=0.1,
            correct_auto_resolutions=23,
            false_auto_resolutions=2,
            exact_target_set_accuracy=23 / 25,
            zero_false_auto_resolution=False,
            safety_gate_passed=False,
            false_auto_resolution_count=2,
            correct_auto_resolution_count=23,
            auto_resolution_count=25,
            records_per_minute=1380.0,
            metrics={"records_per_minute": 1380.0, "safety_gate_passed": 0.0},
            timing=BenchmarkTimingOut(
                pipeline_duration_seconds=1.0, timing_boundary="test boundary"
            ),
            scenario_matrix=[
                FamilyMetricOut(
                    scenario_family="S2",
                    total=5,
                    auto_resolved=2,
                    human_review=3,
                    unresolved=0,
                    correct_outcomes=3,
                    false_auto_resolutions=2,
                )
            ],
            ai_metrics=AIMetricOut(),
            case_evaluations=[],
        )
        self.runs[rid] = out
        return out

    def get_benchmark(self, run_id: str) -> Any | None:
        return self.runs.get(run_id)


def _make_client(service: Any | None = None) -> TestClient:
    store = InMemoryCaseStore(
        run_id="test_api_store",
        settlements={},
        items_by_settlement={},
        payments_by_settlement={},
        ledger_pool=[],
    )
    bench_service = service or InMemoryBenchmarkService()
    app = create_app(
        store=store,
        investigator=DummyInvestigator(),
        investigator_budget=BUDGET,
        benchmark_service=bench_service,
    )
    return TestClient(app)


def test_post_benchmarks_valid_creates_and_returns_run() -> None:
    client = _make_client()
    response = client.post("/api/benchmarks", json={"seed": 42, "num_settlements": 50})
    assert response.status_code == 200
    data = response.json()

    assert data["seed"] == 42
    assert data["total_cases"] == 50
    assert data["safety_gate_passed"] is True
    assert data["false_auto_resolution_count"] == 0
    assert data["records_per_minute"] > 0
    assert len(data["scenario_matrix"]) == 6
    assert "timing" in data
    assert "pipeline_duration_seconds" in data["timing"]

    run_id = data["run_id"]

    # Verify GET retrieves the same run
    get_res = client.get(f"/api/benchmarks/{run_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["run_id"] == run_id
    assert get_data["total_cases"] == 50


def test_get_benchmark_not_found_returns_404() -> None:
    client = _make_client()
    response = client.get("/api/benchmarks/non_existent_run_id")
    assert response.status_code == 404


def test_post_benchmarks_under_minimum_scale_returns_422() -> None:
    client = _make_client()
    response = client.post("/api/benchmarks", json={"seed": 42, "num_settlements": 20})
    assert response.status_code == 422
    assert ">= 50" in response.json()["detail"]


def test_safety_gate_failure_serialization() -> None:
    client = _make_client(service=MockFailingBenchmarkService())
    response = client.post("/api/benchmarks", json={"seed": 42, "num_settlements": 50})
    assert response.status_code == 200
    data = response.json()

    assert data["safety_gate_passed"] is False
    assert data["zero_false_auto_resolution"] is False
    assert data["false_auto_resolution_count"] == 2
    assert data["false_auto_resolutions"] == 2


def test_get_benchmark_confidence_endpoints() -> None:
    client = _make_client()

    # 1. Default benchmark confidence triggers benchmark on the fly
    resp = client.get("/api/benchmark/confidence")
    assert resp.status_code == 200
    data = resp.json()

    assert "overall_ece" in data
    assert "overall_brier_score" in data
    assert data["total_observations"] == 100
    assert len(data["buckets"]) == 10
    assert len(data["thresholds"]) == 11
    assert len(data["gate_matrix"]) == 3
    assert data["automation_opportunity"]["opportunity_count"] == 15
    assert data["automation_opportunity"]["affected_settlement_net_minor"] == 17196914

    run_id = data["run_id"]

    # 2. Query by specific run_id
    run_resp = client.get(f"/api/benchmarks/{run_id}/confidence")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["run_id"] == run_id
    assert run_data["overall_ece"] == data["overall_ece"]

    # 3. 404 for unknown run_id
    not_found = client.get("/api/benchmarks/unknown_run_id_999/confidence")
    assert not_found.status_code == 404


def test_benchmark_confidence_response_matches_frontend_contract() -> None:
    """Regression test for the /confidence page crash (undefined 'thresholds').

    ConfidenceIntelligenceClient.tsx and BenchmarkConfidenceResponse (types.ts)
    require this exact top-level shape and these exact nested field names.
    A previous stale-server incident showed this endpoint missing several of
    these fields at runtime even though the source contract already declared
    them - this test pins the full, currently-agreed contract so any future
    source-level regression (a dropped/renamed field) fails CI immediately.
    """
    client = _make_client()
    response = client.get("/api/benchmark/confidence")
    assert response.status_code == 200
    data = response.json()

    top_level_fields = {
        "run_id",
        "total_observations",
        "predictions_made",
        "abstentions",
        "overall_ece",
        "overall_brier_score",
        "high_confidence_precision",
        "potential_automation_opportunities",
        "potential_automation_volume_minor",
        "currency",
        "buckets",
        "thresholds",
        "gate_matrix",
        "source_metrics",
        "scenario_metrics",
        "automation_opportunity",
    }
    assert top_level_fields <= set(data.keys())

    # The exact field the crash traced to: bm.thresholds (NOT threshold_curve),
    # a non-empty list whose entries expose the fields the threshold selector reads.
    assert isinstance(data["thresholds"], list)
    assert len(data["thresholds"]) > 0
    threshold_entry = data["thresholds"][0]
    assert {
        "threshold",
        "predictions_meeting_threshold",
        "correct_predictions",
        "incorrect_predictions",
        "precision",
        "coverage",
        "false_auto_count_if_trusted_alone",
    } <= set(threshold_entry.keys())

    assert isinstance(data["buckets"], list)
    bucket_entry = data["buckets"][0]
    assert {
        "bin_lower",
        "bin_upper",
        "bin_label",
        "observation_count",
        "empirical_accuracy",
        "average_confidence",
        "gate_pass_count",
        "gate_fail_count",
    } <= set(bucket_entry.keys())

    assert isinstance(data["gate_matrix"], list) and len(data["gate_matrix"]) > 0
    gate_cell = data["gate_matrix"][0]
    assert {
        "tier",
        "confidence_range",
        "total_count",
        "gate_pass_count",
        "gate_fail_count",
        "dominant_failing_checks",
    } <= set(gate_cell.keys())

    assert isinstance(data["scenario_metrics"], list) and len(data["scenario_metrics"]) > 0
    scenario_entry = data["scenario_metrics"][0]
    assert {
        "scenario_family",
        "observation_count",
        "average_confidence",
        "precision",
        "coverage",
        "gate_pass_rate",
        "abstention_rate",
    } <= set(scenario_entry.keys())

    automation = data["automation_opportunity"]
    assert {
        "threshold",
        "opportunity_count",
        "affected_settlement_net_minor",
        "currency",
        "failing_gate_checks",
        "current_dispositions",
        "sample_case_ids",
    } <= set(automation.keys())


def test_operational_confidence_response_matches_frontend_contract() -> None:
    """Pins the GET /api/confidence contract consumed by the same /confidence page."""
    client = _make_client()
    response = client.get("/api/confidence")
    assert response.status_code == 200
    data = response.json()

    assert {
        "total_cases",
        "hypotheses_evaluated",
        "average_confidence",
        "high_confidence_count",
        "medium_confidence_count",
        "low_confidence_count",
        "high_confidence_gate_blocked_count",
        "buckets",
        "gate_tiers",
        "check_contexts",
    } <= set(data.keys())

    assert isinstance(data["gate_tiers"], list) and len(data["gate_tiers"]) > 0
    tier_entry = data["gate_tiers"][0]
    assert {
        "tier",
        "confidence_range",
        "total_count",
        "gate_pass_count",
        "gate_fail_count",
        "pass_rate_pct",
        "failing_check_counts",
    } <= set(tier_entry.keys())
