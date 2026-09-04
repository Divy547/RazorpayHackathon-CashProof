"""ReconcileSettlementUseCase: the deterministic vertical-slice pipeline.

source records -> candidate matching -> evidence -> classification ->
deterministic hypothesis -> evaluate_gate() -> Resolution factory -> AuditEvents

The gate remains the sole financial firewall: this use case never fabricates a
GateEvaluation and never bypasses evaluate_gate().
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime

from cashproof.application.classifier import classify_exception
from cashproof.application.evidence import EvidenceBuilder
from cashproof.application.matcher import CandidateMatcher
from cashproof.application.observation import compute_observed_ledger_state
from cashproof.domain.decision import AuditEvent, GateEvaluation, Resolution, evaluate_gate
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.state import transition_state
from cashproof.domain.types import (
    AuditActor,
    ExceptionType,
    HypothesisSource,
    ProcessingState,
)


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    """Full outcome of reconciling a single settlement."""

    case: ReconciliationCase
    candidates: tuple[MatchCandidate, ...]
    evidence: tuple[Evidence, ...]
    gate_evaluation: GateEvaluation
    resolution: Resolution
    audit_events: tuple[AuditEvent, ...]


class ReconcileSettlementUseCase:
    """Orchestrates one settlement through the full deterministic reconciliation pipeline."""

    def __init__(
        self,
        matcher: CandidateMatcher | None = None,
        evidence_builder: EvidenceBuilder | None = None,
        engine_version: str = "cashproof-matcher-1.0.0",
    ) -> None:
        self._matcher = matcher or CandidateMatcher(engine_version=engine_version)
        self._evidence_builder = evidence_builder or EvidenceBuilder()

    def execute(
        self,
        run_id: str,
        settlement: Settlement,
        items: Sequence[SettlementItem],
        payments: Sequence[Payment],
        ledger_pool: Sequence[LedgerEntry],
        already_resolved_target_ids: frozenset[str],
        now: datetime,
    ) -> ReconciliationResult:
        case_id = settlement.settlement_id
        events: list[AuditEvent] = []
        counter = 0

        def emit(entity_type: str, event_type: str, metadata: dict[str, str]) -> None:
            nonlocal counter
            counter += 1
            events.append(
                AuditEvent(
                    event_id=f"audit_{case_id}_{counter}",
                    case_id=case_id,
                    run_id=run_id,
                    entity_type=entity_type,
                    entity_id=case_id,
                    event_type=event_type,
                    actor=AuditActor.SYSTEM,
                    timestamp=now,
                    metadata=metadata,
                )
            )

        candidates = self._matcher.find_candidates(
            case_id=case_id,
            run_id=run_id,
            settlement=settlement,
            payments=payments,
            ledger_entries=ledger_pool,
        )
        emit("MatchCandidate", "CANDIDATES_GENERATED", {"candidate_count": str(len(candidates))})

        exception_type, proposed_target_ids = classify_exception(candidates)

        # Hypothesis-scoped: exactly the entries the classifier proposes as the
        # target. Used ONLY for evidence-building and as the gate hypothesis
        # below - never for the case-level observed ledger state.
        ledger_by_id = {entry.id: entry for entry in ledger_pool}
        target_entries = tuple(ledger_by_id[tid] for tid in sorted(proposed_target_ids))

        # Hypothesis-independent: what the ledger itself structurally claims
        # belongs to this settlement, regardless of which (if any) candidate
        # the classifier was willing to propose.
        observed_total = compute_observed_ledger_state(settlement, ledger_pool)

        case = ReconciliationCase.create(
            case_id=case_id,
            settlement=settlement,
            items=items,
            observed_ledger_total=observed_total,
            exception_type=exception_type,
            run_id=run_id,
        )
        emit("ReconciliationCase", "CASE_INGESTED", {"exception_type": exception_type.value})

        next_state = transition_state(case.processing_state, ProcessingState.RECONCILED)
        case = replace(case, processing_state=next_state)
        next_state = transition_state(case.processing_state, ProcessingState.CLASSIFIED)
        case = replace(case, processing_state=next_state)
        emit(
            "ReconciliationCase",
            "CASE_CLASSIFIED",
            {"processing_state": case.processing_state.value},
        )

        evidence = self._evidence_builder.build(
            settlement=settlement, target_entries=target_entries, candidates=candidates
        )

        gate = evaluate_gate(
            case=case,
            settlement=settlement,
            items=items,
            hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
            proposed_target_ids=proposed_target_ids,
            target_ledger_entries=target_entries,
            deterministic_candidates=candidates,
            evidence=evidence,
            already_resolved_target_ids=already_resolved_target_ids,
        )
        emit(
            "GateEvaluation",
            "GATE_EVALUATED",
            {"passed": str(gate.passed), "failing_check": gate.failing_check or "NONE"},
        )

        case = replace(
            case, processing_state=transition_state(case.processing_state, ProcessingState.GATED)
        )

        if gate.passed:
            resolution = Resolution.create_auto_resolved(gate)
        elif exception_type == ExceptionType.MISSING_RECORD:
            resolution = Resolution.create_unresolved(gate)
        else:
            resolution = Resolution.create_human_review_pending(gate)

        case = replace(
            case, processing_state=transition_state(case.processing_state, ProcessingState.CLOSED)
        )
        emit("Resolution", "RESOLUTION_RECORDED", {"disposition": resolution.disposition.value})

        return ReconciliationResult(
            case=case,
            candidates=candidates,
            evidence=evidence,
            gate_evaluation=gate,
            resolution=resolution,
            audit_events=tuple(events),
        )
