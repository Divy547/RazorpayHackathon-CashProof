"""Tests for the CashProof HTTP API adapter.

Builds a real InMemoryCaseStore from the real Phase 2 dataset run through the
real production pipeline (same pattern as tests/application/test_review.py),
then exercises the API purely through HTTP requests via FastAPI's TestClient -
proving the adapter correctly delegates to HumanReviewUseCase rather than
reimplementing any decision logic itself.
"""

from __future__ import annotations

import concurrent.futures
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest
from cashproof.api.app import create_app
from cashproof.application.batch import BatchReconciler
from cashproof.application.ports import InvestigationOutcome
from cashproof.application.store import InMemoryCaseStore
from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.generator import GeneratedDataset, generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import ScenarioFamily
from cashproof.domain.ai import Investigation, InvestigatorBudget, ResolutionProposal
from cashproof.domain.decision import GateEvaluation, Resolution, evaluate_gate
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.types import (
    Currency,
    Direction,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
    StopReason,
)
from fastapi.testclient import TestClient

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)
TEST_BUDGET = InvestigatorBudget(
    max_tool_calls=5,
    max_tokens=4000,
    timeout_seconds=30.0,
    temperature=0.0,
    model_version="fake-model",
)


class ScriptedInvestigator:
    """Test double for AIInvestigatorPort - never touches the network. Returns a
    fixed InvestigationOutcome for every call, exactly as a well-behaved
    AIInvestigatorPort implementation would (provider failures are already
    translated to stop_reason=TOOL_FAILURE inside the port - never raised).
    """

    def __init__(self, outcome: InvestigationOutcome) -> None:
        self._outcome = outcome
        self.calls: list[str] = []

    def investigate(
        self,
        *,
        case: ReconciliationCase,
        settlement: Settlement,
        items: Sequence[SettlementItem],
        candidates: Sequence[MatchCandidate],
        evidence: Sequence[Evidence],
        gate: GateEvaluation,
        ledger_entries_by_id: Mapping[str, LedgerEntry],
        budget: InvestigatorBudget,
        run_id: str,
    ) -> InvestigationOutcome:
        self.calls.append(case.case_id)
        return self._outcome


def _investigation(case_id: str, stop_reason: StopReason = StopReason.COMPLETED) -> Investigation:
    return Investigation(
        investigation_id="inv_api_test",
        case_id=case_id,
        run_id="api-test",
        budget=TEST_BUDGET,
        tool_calls=(),
        stop_reason=stop_reason,
        candidates_considered=(),
    )


def _build_batch_inputs(
    dataset: GeneratedDataset,
) -> tuple[dict[str, list[SettlementItem]], dict[str, list[Payment]]]:
    items_by_settlement: dict[str, list[SettlementItem]] = defaultdict(list)
    for item in dataset.settlement_items:
        items_by_settlement[item.settlement_id].append(item)

    payment_by_id = {p.id: p for p in dataset.payments}
    payments_by_settlement: dict[str, list[Payment]] = defaultdict(list)
    for item in dataset.settlement_items:
        payment = payment_by_id.get(item.payment_id)
        if payment is not None:
            payments_by_settlement[item.settlement_id].append(payment)
    return items_by_settlement, payments_by_settlement


@pytest.fixture(scope="module")
def dataset() -> GeneratedDataset:
    return generate_dataset(GeneratorConfig(seed=42, num_settlements=100))


def _make_client(dataset: GeneratedDataset, investigator: ScriptedInvestigator) -> TestClient:
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)
    summary = BatchReconciler().run(
        run_id="api-test",
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=FIXED_NOW,
    )
    store = InMemoryCaseStore(
        run_id="api-test",
        settlements={s.settlement_id: s for s in dataset.settlements},
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=list(dataset.ledger_entries),
    )
    for result in summary.results:
        store.put(result)
    return TestClient(create_app(store, investigator, TEST_BUDGET))


@pytest.fixture()
def client(dataset: GeneratedDataset) -> TestClient:
    default_investigator = ScriptedInvestigator(
        InvestigationOutcome(_investigation("unused"), None)
    )
    return _make_client(dataset, default_investigator)


def _case_id_for(dataset: GeneratedDataset, family: ScenarioFamily) -> str:
    gt_by_case = {gt.case_id: gt for gt in dataset.ground_truths}
    return next(cid for cid, gt in gt_by_case.items() if gt.scenario_family == family)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_cases_returns_full_batch(client: TestClient, dataset: GeneratedDataset) -> None:
    response = client.get("/api/cases")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 100
    assert {row["disposition"] for row in body} == {"AUTO_RESOLVED", "HUMAN_REVIEW", "UNRESOLVED"}


def test_get_case_detail_for_s3(client: TestClient, dataset: GeneratedDataset) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)
    response = client.get(f"/api/cases/{case_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["settlement_id"] == case_id
    assert body["disposition"] == "HUMAN_REVIEW"
    assert body["gate"]["failing_check"] == "BRIDGE"
    assert len(body["candidates"]) == 1


def test_get_case_detail_not_found(client: TestClient) -> None:
    response = client.get("/api/cases/not_a_real_settlement")
    assert response.status_code == 404


def test_post_review_s2_single_candidate_approved(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    detail = client.get(f"/api/cases/{case_id}").json()
    chosen = [detail["candidates"][0]["ledger_entry_id"]]

    response = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "approve", "selected_target_ids": chosen, "reviewer": "rev_alice"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["gate"]["passed"] is True
    assert body["gate"]["failing_check"] is None
    assert body["resolution"]["disposition"] == "HUMAN_REVIEW"
    assert body["resolution"]["review_outcome"] == "APPROVED"
    assert body["resolution"]["reviewer"] == "rev_alice"
    assert body["resolution"]["target_ledger_entry_ids"] == chosen


def test_post_review_s2_both_candidates_rejected_by_bridge(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    detail = client.get(f"/api/cases/{case_id}").json()
    both = [c["ledger_entry_id"] for c in detail["candidates"]]

    response = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "approve", "selected_target_ids": both, "reviewer": "rev_alice"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["gate"]["passed"] is False
    assert body["gate"]["failing_check"] == "BRIDGE"
    assert body["resolution"]["review_outcome"] == "PENDING"


def test_post_review_s4_approval_passes_policy(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S4_EXTERNAL_REF_TEXT)
    detail = client.get(f"/api/cases/{case_id}").json()
    chosen = [detail["candidates"][0]["ledger_entry_id"]]

    response = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "approve", "selected_target_ids": chosen, "reviewer": "rev_alice"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["gate"]["passed"] is True
    assert body["gate"]["failing_check"] is None
    assert body["resolution"]["disposition"] == "HUMAN_REVIEW"
    assert body["resolution"]["review_outcome"] == "APPROVED"


def test_post_review_invalid_candidate_selection_returns_422(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)
    response = client.post(
        f"/api/cases/{case_id}/review",
        json={
            "decision": "approve",
            "selected_target_ids": ["le_not_a_real_candidate"],
            "reviewer": "rev_alice",
        },
    )
    assert response.status_code == 422


def test_post_review_empty_reviewer_returns_422(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)
    response = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "reject", "selected_target_ids": [], "reviewer": "   "},
    )
    assert response.status_code == 422


def test_post_review_reject_becomes_unresolved(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S4_EXTERNAL_REF_TEXT)
    response = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "reject", "selected_target_ids": [], "reviewer": "rev_bob"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["resolution"]["disposition"] == "UNRESOLVED"
    assert body["resolution"]["review_outcome"] == "REJECTED"
    assert body["resolution"]["reviewer"] == "rev_bob"

    # Reflected on a subsequent GET too (store was updated).
    follow_up = client.get(f"/api/cases/{case_id}")
    assert follow_up.json()["resolution"]["disposition"] == "UNRESOLVED"


def test_post_review_not_applicable_to_auto_resolved_returns_409(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S1_STRUCTURED_EXACT)
    response = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "reject", "selected_target_ids": [], "reviewer": "rev_alice"},
    )
    assert response.status_code == 409


def test_post_review_already_approved_returns_409(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S5_NARRATION_ALIAS_TEXT)
    detail = client.get(f"/api/cases/{case_id}").json()
    chosen = [detail["candidates"][0]["ledger_entry_id"]]

    # First review approves it
    first_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "approve", "selected_target_ids": chosen, "reviewer": "rev_alice"},
    )
    assert first_resp.status_code == 200
    assert first_resp.json()["resolution"]["review_outcome"] == "APPROVED"

    # Second review (approve) returns 409 Conflict
    second_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "approve", "selected_target_ids": chosen, "reviewer": "rev_bob"},
    )
    assert second_resp.status_code == 409
    assert "APPROVED" in second_resp.json()["detail"]

    # Third review (reject) returns 409 Conflict
    third_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "reject", "selected_target_ids": [], "reviewer": "rev_bob"},
    )
    assert third_resp.status_code == 409
    assert "APPROVED" in third_resp.json()["detail"]


def test_post_review_already_rejected_returns_409(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)

    # First review rejects it
    first_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "reject", "selected_target_ids": [], "reviewer": "rev_alice"},
    )
    assert first_resp.status_code == 200
    assert first_resp.json()["resolution"]["review_outcome"] == "REJECTED"

    # Subsequent reviews return 409 Conflict
    second_resp = client.post(
        f"/api/cases/{case_id}/review",
        json={"decision": "reject", "selected_target_ids": [], "reviewer": "rev_bob"},
    )
    assert second_resp.status_code == 409
    assert "REJECTED" in second_resp.json()["detail"]


def test_post_review_not_found_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/cases/not_a_real_settlement/review",
        json={"decision": "reject", "selected_target_ids": [], "reviewer": "rev_alice"},
    )
    assert response.status_code == 404


def test_post_investigate_not_found_returns_404(client: TestClient) -> None:
    response = client.post("/api/cases/not_a_real_settlement/investigate")
    assert response.status_code == 404


def test_post_investigate_not_applicable_to_auto_resolved_returns_409(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S1_STRUCTURED_EXACT)
    response = client.post(f"/api/cases/{case_id}/investigate")
    assert response.status_code == 409


def test_post_investigate_successful_proposal_serializes_correctly(
    dataset: GeneratedDataset,
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)
    gt_by_case = {gt.case_id: gt for gt in dataset.ground_truths}
    assert gt_by_case[case_id].scenario_family == ScenarioFamily.S3_FINANCIAL_MISMATCH

    # We need the case's own candidate id, which is only known after the batch
    # run - fetch it via a throwaway client first, then build the scripted
    # investigator that references it.
    scratch_client = _make_client(
        dataset, ScriptedInvestigator(InvestigationOutcome(_investigation(case_id), None))
    )
    detail = scratch_client.get(f"/api/cases/{case_id}").json()
    target_id = detail["candidates"][0]["ledger_entry_id"]

    proposal = ResolutionProposal(
        proposal_id="prop_api_test",
        investigation_id="inv_api_test",
        case_id=case_id,
        run_id="api-test",
        target_ledger_entry_ids=frozenset({target_id}),
        rationale="the structured reference matches despite the amount mismatch",
        evidence=(),
        confidence=0.7,
    )
    outcome = InvestigationOutcome(_investigation(case_id), proposal)
    client = _make_client(dataset, ScriptedInvestigator(outcome))

    response = client.post(f"/api/cases/{case_id}/investigate")
    assert response.status_code == 200
    body = response.json()

    assert body["case_id"] == case_id
    assert body["investigation"]["stop_reason"] == "COMPLETED"
    assert body["proposal"]["target_ledger_entry_ids"] == [target_id]
    assert body["proposal"]["confidence"] == 0.7
    assert body["preview_gate"] is not None
    assert body["preview_gate"]["failing_check"] == "BRIDGE"  # honest: still fails, same as S3

    # GET reflects the stored investigation without re-running it.
    follow_up = client.get(f"/api/cases/{case_id}/investigation")
    assert follow_up.status_code == 200
    assert follow_up.json()["proposal"]["proposal_id"] == "prop_api_test"


def test_post_investigate_provider_failure_serializes_as_tool_failure(
    dataset: GeneratedDataset,
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)
    outcome = InvestigationOutcome(
        _investigation(case_id, stop_reason=StopReason.TOOL_FAILURE), None
    )
    client = _make_client(dataset, ScriptedInvestigator(outcome))

    response = client.post(f"/api/cases/{case_id}/investigate")
    assert response.status_code == 200
    body = response.json()
    assert body["investigation"]["stop_reason"] == "TOOL_FAILURE"
    assert body["proposal"] is None
    assert body["preview_gate"] is None


def test_post_investigate_malformed_output_yields_no_proposal(dataset: GeneratedDataset) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    outcome = InvestigationOutcome(
        _investigation(case_id, stop_reason=StopReason.MALFORMED_OUTPUT), None
    )
    client = _make_client(dataset, ScriptedInvestigator(outcome))

    response = client.post(f"/api/cases/{case_id}/investigate")
    assert response.status_code == 200
    body = response.json()
    assert body["investigation"]["stop_reason"] == "MALFORMED_OUTPUT"
    assert body["proposal"] is None


def test_get_investigation_before_any_run_returns_404(
    client: TestClient, dataset: GeneratedDataset
) -> None:
    case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)
    response = client.get(f"/api/cases/{case_id}/investigation")
    assert response.status_code == 404


def test_concurrent_reviews_same_case(dataset: GeneratedDataset) -> None:
    client = _make_client(
        dataset, ScriptedInvestigator(InvestigationOutcome(_investigation("unused"), None))
    )
    case_id = _case_id_for(dataset, ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    detail = client.get(f"/api/cases/{case_id}").json()
    chosen = [detail["candidates"][0]["ledger_entry_id"]]

    def do_review(reviewer: str) -> Any:
        return client.post(
            f"/api/cases/{case_id}/review",
            json={"decision": "approve", "selected_target_ids": chosen, "reviewer": reviewer},
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(do_review, "reviewer_1")
        f2 = executor.submit(do_review, "reviewer_2")
        r1 = f1.result()
        r2 = f2.result()

    statuses = sorted([r1.status_code, r2.status_code])
    assert statuses == [200, 409]


def test_concurrent_reviews_competing_for_same_ledger_entry() -> None:
    now = FIXED_NOW
    entry = LedgerEntry(
        "le_shared_conc", 10_000, Currency.INR, now, Direction.CREDIT, payment_ref="shared_ref"
    )

    # Case A
    set_a = Settlement("set_conc_a", 10_000, Currency.INR, now)
    item_a = SettlementItem("item_conc_a", "set_conc_a", "pay_conc_a", 10_000, 0, 0, 0, 0, 10_000)
    cand_a = MatchCandidate(
        "set_conc_a",
        "le_shared_conc",
        1.0,
        ("payment_ref_exact_match", "amount_exact_match"),
        (),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "test_conc",
    )
    case_a = ReconciliationCase(
        "set_conc_a",
        "set_conc_a",
        "test_conc",
        10_000,
        0,
        10_000,
        ExceptionType.AMBIGUOUS_MATCH,
        ProcessingState.CLASSIFIED,
    )
    gate_a = evaluate_gate(
        case=case_a,
        settlement=set_a,
        items=[item_a],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset(),
        target_ledger_entries=[],
        deterministic_candidates=[cand_a],
        evidence=[],
        already_resolved_target_ids=frozenset(),
    )
    res_a = ReconciliationResult(
        case=replace(case_a, processing_state=ProcessingState.CLOSED),
        candidates=(cand_a,),
        evidence=(),
        gate_evaluation=gate_a,
        resolution=Resolution.create_human_review_pending(gate_a),
        audit_events=(),
    )

    # Case B
    set_b = Settlement("set_conc_b", 10_000, Currency.INR, now)
    item_b = SettlementItem("item_conc_b", "set_conc_b", "pay_conc_b", 10_000, 0, 0, 0, 0, 10_000)
    cand_b = MatchCandidate(
        "set_conc_b",
        "le_shared_conc",
        1.0,
        ("payment_ref_exact_match", "amount_exact_match"),
        (),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "test_conc",
    )
    case_b = ReconciliationCase(
        "set_conc_b",
        "set_conc_b",
        "test_conc",
        10_000,
        0,
        10_000,
        ExceptionType.AMBIGUOUS_MATCH,
        ProcessingState.CLASSIFIED,
    )
    gate_b = evaluate_gate(
        case=case_b,
        settlement=set_b,
        items=[item_b],
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset(),
        target_ledger_entries=[],
        deterministic_candidates=[cand_b],
        evidence=[],
        already_resolved_target_ids=frozenset(),
    )
    res_b = ReconciliationResult(
        case=replace(case_b, processing_state=ProcessingState.CLOSED),
        candidates=(cand_b,),
        evidence=(),
        gate_evaluation=gate_b,
        resolution=Resolution.create_human_review_pending(gate_b),
        audit_events=(),
    )

    store = InMemoryCaseStore(
        run_id="test_conc",
        settlements={"set_conc_a": set_a, "set_conc_b": set_b},
        items_by_settlement={"set_conc_a": [item_a], "set_conc_b": [item_b]},
        payments_by_settlement={"set_conc_a": [], "set_conc_b": []},
        ledger_pool=[entry],
    )
    store.put(res_a)
    store.put(res_b)

    client = TestClient(
        create_app(
            store,
            ScriptedInvestigator(InvestigationOutcome(_investigation("unused"), None)),
            TEST_BUDGET,
        )
    )

    def approve_case(case_id: str, reviewer: str) -> Any:
        return client.post(
            f"/api/cases/{case_id}/review",
            json={
                "decision": "approve",
                "selected_target_ids": ["le_shared_conc"],
                "reviewer": reviewer,
            },
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_a = executor.submit(approve_case, "set_conc_a", "reviewer_a")
        f_b = executor.submit(approve_case, "set_conc_b", "reviewer_b")
        resp_a = f_a.result()
        resp_b = f_b.result()

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    body_a = resp_a.json()
    body_b = resp_b.json()

    outcomes = [body_a["resolution"]["review_outcome"], body_b["resolution"]["review_outcome"]]
    assert "APPROVED" in outcomes
    assert "PENDING" in outcomes

    if body_a["resolution"]["review_outcome"] == "APPROVED":
        assert body_a["gate"]["passed"] is True
        assert body_b["gate"]["passed"] is False
        assert body_b["gate"]["failing_check"] == "UNIQUENESS"
    else:
        assert body_b["gate"]["passed"] is True
        assert body_a["gate"]["passed"] is False
        assert body_a["gate"]["failing_check"] == "UNIQUENESS"


def test_get_exception_clusters_list(client: TestClient) -> None:
    response = client.get("/api/exceptions/clusters")
    assert response.status_code == 200
    body = response.json()
    assert body["total_settlements"] == 100
    assert body["total_exceptions"] == 61
    assert body["total_clusters"] == 5
    assert body["recurring_clusters"] == 5
    assert len(body["clusters"]) == 5

    first = body["clusters"][0]
    assert "cluster_key" in first
    assert "cluster_name" in first
    assert "operational_category" in first
    assert "affected_settlement_net_minor" in first
    assert "representative_case_ids" in first
    assert len(first["representative_case_ids"]) <= 3
    assert "disposition_counts" in first
    assert isinstance(first["disposition_counts"], dict)
    assert not isinstance(first["disposition_counts"], list)
    assert len(first["disposition_counts"]) > 0
    for disp, cnt in first["disposition_counts"].items():
        assert isinstance(disp, str)
        assert isinstance(cnt, int)
        assert cnt > 0


def test_get_exception_clusters_filter(client: TestClient) -> None:
    response = client.get("/api/exceptions/clusters?category=AMOUNT_INCONSISTENCY")
    assert response.status_code == 200
    body = response.json()
    assert len(body["clusters"]) == 1
    assert body["clusters"][0]["operational_category"] == "AMOUNT_INCONSISTENCY"
    assert body["clusters"][0]["dominant_failing_gate"] == "BRIDGE"

    disp_resp = client.get("/api/exceptions/clusters?disposition=HUMAN_REVIEW")
    assert disp_resp.status_code == 200
    disp_body = disp_resp.json()
    assert len(disp_body["clusters"]) > 0
    for cluster in disp_body["clusters"]:
        assert "HUMAN_REVIEW" in cluster["disposition_counts"]
        assert cluster["disposition_counts"]["HUMAN_REVIEW"] > 0


def test_get_exception_cluster_detail(client: TestClient) -> None:
    # First list to get a cluster key
    list_resp = client.get("/api/exceptions/clusters")
    target_key = list_resp.json()["clusters"][0]["cluster_key"]

    response = client.get(f"/api/exceptions/clusters/{target_key}")
    assert response.status_code == 200
    body = response.json()
    assert body["cluster_key"] == target_key
    assert "description" in body
    assert "suggested_remediation" in body
    assert "case_ids" in body
    assert len(body["case_ids"]) > 0
    assert "disposition_counts" in body
    assert isinstance(body["disposition_counts"], dict)
    assert not isinstance(body["disposition_counts"], list)
    assert len(body["disposition_counts"]) > 0
    for disp, cnt in body["disposition_counts"].items():
        assert isinstance(disp, str)
        assert isinstance(cnt, int)
        assert cnt > 0

    # 404 for unknown key
    not_found = client.get("/api/exceptions/clusters/non_existent_key")
    assert not_found.status_code == 404


def test_get_case_cluster_endpoints(client: TestClient, dataset: GeneratedDataset) -> None:
    s2_case_id = _case_id_for(dataset, ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    s1_case_id = _case_id_for(dataset, ScenarioFamily.S1_STRUCTURED_EXACT)

    # Exception case belongs to a cluster
    resp = client.get(f"/api/cases/{s2_case_id}/cluster")
    assert resp.status_code == 200
    body = resp.json()
    assert body["settlement_id"] == s2_case_id
    assert body["operational_category"] == "REFERENCE_AMBIGUITY"
    assert body["is_recurring"] is True

    # S1 clean match does not belong to an exception cluster
    s1_resp = client.get(f"/api/cases/{s1_case_id}/cluster")
    assert s1_resp.status_code == 404

    # Non-existent case
    not_found = client.get("/api/cases/non_existent_case_id/cluster")
    assert not_found.status_code == 404


def test_get_gate_intelligence_endpoints(client: TestClient) -> None:
    # 1. Full gate intelligence summary
    resp = client.get("/api/gate/intelligence")
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_cases"] == 100
    assert body["passed_cases"] == 39
    assert body["failed_cases"] == 61
    assert body["pass_rate"] == 39.0
    assert body["fail_rate"] == 61.0
    assert body["top_blocker"] == "IDENTITY"
    assert len(body["automation_blockers"]) == 3
    assert len(body["check_breakdowns"]) == 9

    # Verify ranked automation blockers order
    blockers = body["automation_blockers"]
    assert blockers[0]["check_name"] == "IDENTITY"
    assert blockers[0]["failure_count"] == 25
    assert blockers[1]["check_name"] == "POLICY"
    assert blockers[1]["failure_count"] == 21
    assert blockers[2]["check_name"] == "BRIDGE"
    assert blockers[2]["failure_count"] == 15

    # 2. Filter by check
    filter_resp = client.get("/api/gate/intelligence?check=BRIDGE")
    assert filter_resp.status_code == 200
    filter_body = filter_resp.json()
    assert len(filter_body["automation_blockers"]) == 1
    assert filter_body["automation_blockers"][0]["check_name"] == "BRIDGE"

    # 3. Individual check detail endpoint
    check_resp = client.get("/api/gate/intelligence/BRIDGE")
    assert check_resp.status_code == 200
    check_body = check_resp.json()
    assert check_body["check_name"] == "BRIDGE"
    assert check_body["failure_count"] == 15
    assert "explanation" in check_body
    assert check_body["explanation"]["eligibility_requirement"] != ""

    # 404 for non-existent check
    not_found_check = client.get("/api/gate/intelligence/NON_EXISTENT_GATE")
    assert not_found_check.status_code == 404


def test_get_case_gate_outcome_endpoint(client: TestClient, dataset: GeneratedDataset) -> None:
    s3_case_id = _case_id_for(dataset, ScenarioFamily.S3_FINANCIAL_MISMATCH)
    s1_case_id = _case_id_for(dataset, ScenarioFamily.S1_STRUCTURED_EXACT)

    # Failed case
    resp = client.get(f"/api/cases/{s3_case_id}/gate-outcome")
    assert resp.status_code == 200
    body = resp.json()
    assert body["case_id"] == s3_case_id
    assert body["passed"] is False
    assert body["failing_check"] == "BRIDGE"
    assert body["explanation"] is not None
    assert body["explanation"]["check_name"] == "BRIDGE"
    assert body["failure_reason"] is not None

    # Passed case
    s1_resp = client.get(f"/api/cases/{s1_case_id}/gate-outcome")
    assert s1_resp.status_code == 200
    s1_body = s1_resp.json()
    assert s1_body["passed"] is True
    assert s1_body["failing_check"] is None

    # 404 for unknown case
    not_found = client.get("/api/cases/non_existent_case_123/gate-outcome")
    assert not_found.status_code == 404


def test_get_operational_confidence_endpoint(client: TestClient) -> None:
    resp = client.get("/api/confidence")
    assert resp.status_code == 200
    body = resp.json()

    assert "hypotheses_evaluated" in body
    assert body["hypotheses_evaluated"] == 100
    assert body["high_confidence_count"] > 0
    assert len(body["buckets"]) == 10
    assert len(body["gate_tiers"]) == 3

    # Check contexts
    checks = {c["check_name"]: c for c in body["check_contexts"]}
    assert "BRIDGE" in checks
    assert checks["BRIDGE"]["average_confidence"] >= 0.8


def test_get_benchmark_confidence_unconfigured_returns_503(client: TestClient) -> None:
    resp = client.get("/api/benchmark/confidence")
    assert resp.status_code == 503
