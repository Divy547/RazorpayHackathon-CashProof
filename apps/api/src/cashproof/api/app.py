"""CashProof HTTP API composition root.

Thin adapter only: every route parses/validates at the Pydantic boundary,
delegates the actual decision to cashproof.application or benchmark evaluation,
and serializes the result back out. No domain/application logic is duplicated here.

This module must never import cashproof.benchmark - the store and benchmark service
it operates on are injected by a composition root (see scripts/run_api.py).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, Protocol

from cashproof.api.schemas import (
    BenchmarkConfidenceResponse,
    BenchmarkRunOut,
    BenchmarkRunRequest,
    CaseClusterOut,
    CaseDetail,
    CaseSummary,
    ControllerGateOutcomeOut,
    ExceptionClusterDetailOut,
    ExceptionIntelligenceResponse,
    GateCheckBreakdownOut,
    GateIntelligenceResponse,
    InvestigationResult,
    OperationalConfidenceResponse,
    ReviewRequest,
)
from cashproof.api.serializers import (
    case_detail,
    case_summary,
    investigation_result,
    serialize_benchmark_confidence,
    serialize_benchmark_run,
    serialize_cluster_detail,
    serialize_controller_gate_outcome,
    serialize_exception_intelligence,
    serialize_gate_check_breakdown,
    serialize_gate_intelligence,
    serialize_operational_confidence,
)
from cashproof.application.confidence import OperationalConfidenceService
from cashproof.application.gate_intelligence import GateIntelligenceService
from cashproof.application.intelligence import ExceptionIntelligenceService
from cashproof.application.investigation import AIInvestigationUseCase
from cashproof.application.ports import AIInvestigatorPort
from cashproof.application.review import (
    HumanReviewUseCase,
    InvalidCandidateSelectionError,
    ReviewNotApplicableError,
)
from cashproof.application.store import InMemoryCaseStore
from cashproof.domain.ai import InvestigatorBudget
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


class BenchmarkServiceProtocol(Protocol):
    """Abstract protocol for benchmark execution and retrieval."""

    def run_benchmark(
        self,
        seed: int = 42,
        num_settlements: int = 100,
        run_id: str | None = None,
        arm: str = "deterministic",
    ) -> Any: ...

    def get_benchmark(self, run_id: str) -> Any | None: ...

    def list_benchmarks(self) -> list[Any]: ...


def create_app(
    store: InMemoryCaseStore,
    investigator: AIInvestigatorPort,
    investigator_budget: InvestigatorBudget,
    benchmark_service: BenchmarkServiceProtocol | None = None,
) -> FastAPI:
    app = FastAPI(title="CashProof API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    review_use_case = HumanReviewUseCase()
    investigation_use_case = AIInvestigationUseCase(investigator)
    intelligence_service = ExceptionIntelligenceService()
    gate_intelligence_service = GateIntelligenceService(intelligence_service)
    operational_confidence_service = OperationalConfidenceService()

    @app.get("/api/cases", response_model=list[CaseSummary])
    def list_cases() -> list[CaseSummary]:
        return [
            case_summary(result)
            for result in sorted(store.results.values(), key=lambda r: r.case.case_id)
        ]

    @app.get("/api/cases/{settlement_id}", response_model=CaseDetail)
    def get_case(settlement_id: str) -> CaseDetail:
        result = store.get(settlement_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Case {settlement_id} not found.")
        settlement = store.settlements[settlement_id]
        items = store.items_by_settlement.get(settlement_id, [])
        return case_detail(result, settlement, items)

    @app.post("/api/cases/{settlement_id}/review", response_model=CaseDetail)
    def submit_review(settlement_id: str, request: ReviewRequest) -> CaseDetail:
        if not request.reviewer.strip():
            raise HTTPException(status_code=422, detail="reviewer must not be empty.")

        with store.lock:
            result = store.get(settlement_id)
            if result is None:
                raise HTTPException(status_code=404, detail=f"Case {settlement_id} not found.")

            settlement = store.settlements[settlement_id]
            items = store.items_by_settlement.get(settlement_id, [])

            try:
                updated = review_use_case.submit_review(
                    result=result,
                    settlement=settlement,
                    items=items,
                    ledger_pool=store.ledger_pool,
                    decision=request.decision,
                    selected_target_ids=frozenset(request.selected_target_ids),
                    reviewer=request.reviewer,
                    now=datetime.now(UTC),
                    already_resolved_target_ids=store.already_resolved_target_ids(
                        exclude_case_id=settlement_id
                    ),
                )
            except InvalidCandidateSelectionError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            except ReviewNotApplicableError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

            store.put(updated)
            return case_detail(updated, settlement, items)

    @app.post("/api/cases/{settlement_id}/investigate", response_model=InvestigationResult)
    def investigate_case(settlement_id: str) -> InvestigationResult:
        result = store.get(settlement_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Case {settlement_id} not found.")

        settlement = store.settlements[settlement_id]
        items = store.items_by_settlement.get(settlement_id, [])
        payments = store.payments_by_settlement.get(settlement_id, [])

        try:
            run_result = investigation_use_case.run_investigation(
                result=result,
                settlement=settlement,
                items=items,
                payments=payments,
                ledger_pool=store.ledger_pool,
                budget=investigator_budget,
                run_id=store.run_id,
                now=datetime.now(UTC),
                already_resolved_target_ids=store.already_resolved_target_ids(
                    exclude_case_id=settlement_id
                ),
            )
        except ReviewNotApplicableError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        store.put_investigation(run_result)
        return investigation_result(run_result)

    @app.get("/api/cases/{settlement_id}/investigation", response_model=InvestigationResult)
    def get_investigation(settlement_id: str) -> InvestigationResult:
        if store.get(settlement_id) is None:
            raise HTTPException(status_code=404, detail=f"Case {settlement_id} not found.")
        run_result = store.get_investigation(settlement_id)
        if run_result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No investigation has been run yet for case {settlement_id}.",
            )
        return investigation_result(run_result)

    # Benchmark endpoints (Phase 4)
    @app.post("/api/benchmarks", response_model=BenchmarkRunOut)
    def create_benchmark(request: BenchmarkRunRequest) -> BenchmarkRunOut:
        if benchmark_service is None:
            raise HTTPException(status_code=503, detail="Benchmark service is not configured.")
        if request.num_settlements < 50:
            raise HTTPException(
                status_code=422,
                detail="num_settlements must be >= 50 to satisfy benchmark scale requirements.",
            )

        try:
            run = benchmark_service.run_benchmark(
                seed=request.seed,
                num_settlements=request.num_settlements,
                run_id=request.run_id,
                arm=request.arm,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        return serialize_benchmark_run(run)

    @app.get("/api/benchmarks/{run_id}", response_model=BenchmarkRunOut)
    def get_benchmark(run_id: str) -> BenchmarkRunOut:
        if benchmark_service is None:
            raise HTTPException(status_code=503, detail="Benchmark service is not configured.")
        run = benchmark_service.get_benchmark(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Benchmark run '{run_id}' not found.")
        return serialize_benchmark_run(run)

    # Exception Intelligence endpoints (Phase 6)
    @app.get("/api/exceptions/clusters", response_model=ExceptionIntelligenceResponse)
    def get_exception_clusters(
        category: str | None = None,
        failing_gate: str | None = None,
        disposition: str | None = None,
    ) -> ExceptionIntelligenceResponse:
        summary = intelligence_service.cluster_exceptions(
            list(store.results.values()), store.settlements
        )
        clusters = summary.clusters
        if category:
            clusters = tuple(c for c in clusters if c.operational_category.value == category)
        if failing_gate:
            clusters = tuple(c for c in clusters if c.dominant_failing_gate == failing_gate)
        if disposition:
            clusters = tuple(
                c
                for c in clusters
                if any(disp == disposition for disp, cnt in c.disposition_counts if cnt > 0)
            )

        filtered_summary = replace(summary, clusters=clusters)
        return serialize_exception_intelligence(filtered_summary)

    @app.get("/api/exceptions/clusters/{cluster_key}", response_model=ExceptionClusterDetailOut)
    def get_exception_cluster_detail(cluster_key: str) -> ExceptionClusterDetailOut:
        summary = intelligence_service.cluster_exceptions(
            list(store.results.values()), store.settlements
        )
        for cluster in summary.clusters:
            if cluster.cluster_key == cluster_key:
                return serialize_cluster_detail(cluster)
        raise HTTPException(status_code=404, detail=f"Exception cluster '{cluster_key}' not found.")

    @app.get("/api/cases/{settlement_id}/cluster", response_model=CaseClusterOut)
    def get_case_cluster(settlement_id: str) -> CaseClusterOut:
        result = store.get(settlement_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Case {settlement_id} not found.")

        summary = intelligence_service.cluster_exceptions(
            list(store.results.values()), store.settlements
        )
        for cluster in summary.clusters:
            if settlement_id in cluster.case_ids:
                return CaseClusterOut(
                    settlement_id=settlement_id,
                    cluster_key=cluster.cluster_key,
                    cluster_name=cluster.cluster_name,
                    operational_category=cluster.operational_category.value,
                    case_count=cluster.case_count,
                    is_recurring=cluster.is_recurring,
                )

        raise HTTPException(
            status_code=404,
            detail=(
                f"Case {settlement_id} does not belong to any exception cluster "
                "(resolved or clean)."
            ),
        )

    # Gate Intelligence & Controller Explainability endpoints (Phase 7)
    @app.get("/api/gate/intelligence", response_model=GateIntelligenceResponse)
    def get_gate_intelligence(
        check: str | None = None,
        disposition: str | None = None,
    ) -> GateIntelligenceResponse:
        summary = gate_intelligence_service.analyze_gate(
            list(store.results.values()), store.settlements
        )
        blockers = summary.automation_blockers
        check_breakdowns = summary.check_breakdowns

        if check:
            blockers = tuple(b for b in blockers if b.check_name == check)
            check_breakdowns = tuple(b for b in check_breakdowns if b.check_name == check)
        if disposition:
            check_breakdowns = tuple(
                b
                for b in check_breakdowns
                if any(disp == disposition for disp, cnt in b.disposition_counts if cnt > 0)
            )

        filtered_summary = replace(
            summary, automation_blockers=blockers, check_breakdowns=check_breakdowns
        )
        return serialize_gate_intelligence(filtered_summary)

    @app.get("/api/gate/intelligence/{check}", response_model=GateCheckBreakdownOut)
    def get_gate_check_detail(check: str) -> GateCheckBreakdownOut:
        summary = gate_intelligence_service.analyze_gate(
            list(store.results.values()), store.settlements
        )
        for b in summary.check_breakdowns:
            if b.check_name == check:
                return serialize_gate_check_breakdown(b)
        raise HTTPException(status_code=404, detail=f"Gate check '{check}' not found.")

    @app.get("/api/cases/{settlement_id}/gate-outcome", response_model=ControllerGateOutcomeOut)
    def get_case_gate_outcome(settlement_id: str) -> ControllerGateOutcomeOut:
        result = store.get(settlement_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Case {settlement_id} not found.")

        summary = gate_intelligence_service.analyze_gate(
            list(store.results.values()), store.settlements
        )
        for outcome in summary.case_outcomes:
            if outcome.case_id == settlement_id:
                return serialize_controller_gate_outcome(outcome)

        raise HTTPException(
            status_code=404, detail=f"Gate outcome for case {settlement_id} not found."
        )

    # Confidence Calibration & Automation Quality endpoints (Phase 8)
    @app.get("/api/confidence", response_model=OperationalConfidenceResponse)
    def get_operational_confidence() -> OperationalConfidenceResponse:
        summary = operational_confidence_service.analyze(
            list(store.results.values()), store.settlements
        )
        return serialize_operational_confidence(summary)

    @app.get("/api/benchmarks/{run_id}/confidence", response_model=BenchmarkConfidenceResponse)
    def get_benchmark_confidence(run_id: str) -> BenchmarkConfidenceResponse:
        if benchmark_service is None:
            raise HTTPException(status_code=503, detail="Benchmark service is not configured.")
        run = benchmark_service.get_benchmark(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Benchmark run '{run_id}' not found.")
        if getattr(run, "confidence_report", None) is None:
            raise HTTPException(
                status_code=404, detail=f"Confidence report for run '{run_id}' not found."
            )
        return serialize_benchmark_confidence(run.run_id, run.confidence_report)

    @app.get("/api/benchmark/confidence", response_model=BenchmarkConfidenceResponse)
    def get_default_benchmark_confidence() -> BenchmarkConfidenceResponse:
        if benchmark_service is None:
            raise HTTPException(status_code=503, detail="Benchmark service is not configured.")
        runs = (
            benchmark_service.list_benchmarks()
            if hasattr(benchmark_service, "list_benchmarks")
            else []
        )
        if runs and getattr(runs[-1], "confidence_report", None) is not None:
            run = runs[-1]
        else:
            run = benchmark_service.run_benchmark(seed=42, num_settlements=100, arm="deterministic")

        if getattr(run, "confidence_report", None) is None:
            raise HTTPException(
                status_code=500, detail="Default benchmark did not produce a confidence report."
            )
        return serialize_benchmark_confidence(run.run_id, run.confidence_report)

    return app
