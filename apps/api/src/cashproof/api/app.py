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
    ConnectorStatusResponse,
    ControllerGateOutcomeOut,
    ExceptionClusterDetailOut,
    ExceptionIntelligenceResponse,
    GateCheckBreakdownOut,
    GateIntelligenceResponse,
    IngestionRunOut,
    IngestionStatusResponse,
    IngestionTriggerRequest,
    InvestigationResult,
    OperationalConfidenceResponse,
    ReconcileResponse,
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
    serialize_ingestion_run,
    serialize_operational_confidence,
    serialize_settlement_reconciliation_error,
)
from cashproof.application.batch import BatchReconciler
from cashproof.application.confidence import OperationalConfidenceService
from cashproof.application.gate_intelligence import GateIntelligenceService
from cashproof.application.ingestion import (
    DuplicateSourceConflictError,
    IngestionService,
    IngestionValidationError,
)
from cashproof.application.intelligence import ExceptionIntelligenceService
from cashproof.application.investigation import AIInvestigationUseCase
from cashproof.application.ports import (
    AIInvestigatorPort,
    ConnectorStatus,
    NormalizedSourceBatch,
    SourceConnectorPort,
)
from cashproof.application.review import (
    HumanReviewUseCase,
    InvalidCandidateSelectionError,
    ReviewNotApplicableError,
)
from cashproof.application.store import InMemoryCaseStore
from cashproof.domain.ai import InvestigatorBudget
from cashproof.infrastructure.bank.csv_parser import parse_bank_statement
from fastapi import FastAPI, HTTPException, UploadFile
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


class _UnconfiguredConnector:
    """Default Razorpay connector stub used when the caller wires none in.

    Reports UNCONFIGURED (no secrets involved) rather than making create_app()
    require a connector argument every existing caller/test would otherwise
    need to pass.
    """

    def status(self) -> ConnectorStatus:
        return ConnectorStatus(
            connector_name="razorpay",
            configured=False,
            detail="No Razorpay connector was wired into this API instance.",
        )

    def fetch(self, *, year: int, month: int) -> NormalizedSourceBatch:
        raise RuntimeError("Razorpay connector is not configured for this API instance.")


def create_app(
    store: InMemoryCaseStore,
    investigator: AIInvestigatorPort,
    investigator_budget: InvestigatorBudget,
    benchmark_service: BenchmarkServiceProtocol | None = None,
    razorpay_connector: SourceConnectorPort | None = None,
) -> FastAPI:
    app = FastAPI(title="CashProof API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://razorpay-hackathon-cash-proof-yy6i.vercel.app",
        ],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    review_use_case = HumanReviewUseCase()
    investigation_use_case = AIInvestigationUseCase(investigator)
    intelligence_service = ExceptionIntelligenceService()
    gate_intelligence_service = GateIntelligenceService(intelligence_service)
    operational_confidence_service = OperationalConfidenceService()
    connector: SourceConnectorPort = razorpay_connector or _UnconfiguredConnector()
    ingestion_service = IngestionService(store)

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

    # Ingestion endpoints (Phase 9)
    @app.get("/api/ingestion/status", response_model=IngestionStatusResponse)
    def ingestion_status() -> IngestionStatusResponse:
        rp = connector.status()
        return IngestionStatusResponse(
            connectors=[
                ConnectorStatusResponse(
                    connector_name=rp.connector_name, configured=rp.configured, detail=rp.detail
                ),
                ConnectorStatusResponse(
                    connector_name="bank_statement",
                    configured=True,
                    detail="CSV upload endpoint; no external credentials required.",
                ),
            ]
        )

    @app.post("/api/ingestion/razorpay", response_model=IngestionRunOut)
    def ingest_razorpay(request: IngestionTriggerRequest) -> IngestionRunOut:
        with store.lock:
            try:
                run = ingestion_service.ingest_from_connector(
                    connector,
                    source="razorpay",
                    year=request.year,
                    month=request.month,
                    now=datetime.now(UTC),
                )
            except DuplicateSourceConflictError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
        return serialize_ingestion_run(run)

    @app.post("/api/ingestion/bank-statement", response_model=IngestionRunOut)
    async def ingest_bank_statement(file: UploadFile) -> IngestionRunOut:
        content = await file.read()
        with store.lock:
            try:
                parse_result = parse_bank_statement(content)
            except IngestionValidationError as exc:
                run = ingestion_service.record_validation_failure(
                    source="bank_statement", error=exc, now=datetime.now(UTC)
                )
                return serialize_ingestion_run(run)

            batch = NormalizedSourceBatch(ledger_entries=parse_result.ledger_entries)
            try:
                run = ingestion_service.ingest_batch(
                    source="bank_statement",
                    batch=batch,
                    fetched_count=parse_result.row_count,
                    now=datetime.now(UTC),
                )
            except DuplicateSourceConflictError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
        return serialize_ingestion_run(run)

    @app.get("/api/ingestion/runs", response_model=list[IngestionRunOut])
    def list_ingestion_runs() -> list[IngestionRunOut]:
        return [serialize_ingestion_run(r) for r in store.list_ingestion_runs()]

    @app.get("/api/ingestion/runs/{run_id}", response_model=IngestionRunOut)
    def get_ingestion_run(run_id: str) -> IngestionRunOut:
        run = store.get_ingestion_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"Ingestion run '{run_id}' not found.")
        return serialize_ingestion_run(run)

    @app.post("/api/reconcile", response_model=ReconcileResponse)
    def reconcile() -> ReconcileResponse:
        """Re-runs the EXISTING, unmodified BatchReconciler over every currently
        stored source record (synthetic + ingested). Cases a human has already
        finalized (APPROVED/REJECTED) are left untouched rather than reset back
        to a fresh pending gate outcome.

        A settlement whose own source records fail a domain invariant (e.g. no
        settlement items yet, or items that don't sum to net_deposited_minor)
        never aborts the batch: BatchReconciler reports it as a
        SettlementReconciliationError instead of a case, and every other
        settlement still reconciles normally. Nothing is fabricated in its
        place - it simply has no case, gate evaluation, or resolution.
        """
        with store.lock:
            summary = BatchReconciler().run(
                run_id=store.run_id,
                settlements=list(store.settlements.values()),
                items_by_settlement=store.items_by_settlement,
                payments_by_settlement=store.payments_by_settlement,
                ledger_pool=store.ledger_pool,
                now=datetime.now(UTC),
            )
            for result in summary.results:
                existing = store.get(result.case.case_id)
                if existing is not None and existing.resolution.review_outcome in (
                    "APPROVED",
                    "REJECTED",
                ):
                    continue
                store.put(result)

            cases = [
                case_summary(store.results[case_id])
                for case_id in sorted(r.case.case_id for r in summary.results)
            ]
            failed_settlements = [
                serialize_settlement_reconciliation_error(e) for e in summary.failed_settlements
            ]
            return ReconcileResponse(cases=cases, failed_settlements=failed_settlements)

    return app
