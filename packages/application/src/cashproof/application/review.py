"""HumanReviewUseCase: apply a reviewer's decision to a HUMAN_REVIEW case.

Pipeline: reviewer selection -> EvidenceBuilder -> evaluate_gate() -> Resolution
-> AuditEvent(actor=REVIEWER). The deterministic gate remains the sole
financial firewall: this use case never fabricates a GateEvaluation, never
bypasses evaluate_gate(), and never lets a reviewer author a target set that
extends beyond the candidates the deterministic matcher already surfaced for
this case.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from typing import Literal

from cashproof.application.evidence import EvidenceBuilder
from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.decision import AuditEvent, Resolution, evaluate_gate
from cashproof.domain.derived import ReconciliationCase
from cashproof.domain.exceptions import ResolutionGateViolationError
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem
from cashproof.domain.state import transition_state
from cashproof.domain.types import (
    AuditActor,
    Disposition,
    HypothesisSource,
    ProcessingState,
    ReviewOutcome,
)

ReviewDecision = Literal["approve", "reject", "pending"]


class InvalidCandidateSelectionError(Exception):
    """Raised when a reviewer selects ledger entry ids that are not among this
    case's existing MatchCandidate pool, or selects none at all for an
    approval. Reviewers may only choose from candidates the deterministic
    matcher already surfaced for this case - never arbitrary ledger entry ids.
    """


class ReviewNotApplicableError(Exception):
    """Raised when a review action is attempted on a case whose current
    disposition is not HUMAN_REVIEW (e.g. already AUTO_RESOLVED, or a
    deterministic UNRESOLVED case with zero candidates).
    """


class HumanReviewUseCase:
    """Applies one reviewer decision to one case's current ReconciliationResult."""

    def __init__(self, evidence_builder: EvidenceBuilder | None = None) -> None:
        self._evidence_builder = evidence_builder or EvidenceBuilder()

    def submit_review(
        self,
        result: ReconciliationResult,
        settlement: Settlement,
        items: Sequence[SettlementItem],
        ledger_pool: Sequence[LedgerEntry],
        decision: ReviewDecision,
        selected_target_ids: frozenset[str],
        reviewer: str,
        now: datetime,
        already_resolved_target_ids: frozenset[str],
    ) -> ReconciliationResult:
        if not reviewer.strip():
            raise ValueError("reviewer must not be empty.")
        if (
            result.resolution.disposition != Disposition.HUMAN_REVIEW
            or result.resolution.review_outcome != ReviewOutcome.PENDING
        ):
            status_desc = (
                result.resolution.review_outcome.value
                if result.resolution.review_outcome
                else result.resolution.disposition.value
            )
            raise ReviewNotApplicableError(
                f"Case {result.case.case_id} has review status "
                f"{status_desc}, not PENDING; no review action is applicable."
            )

        case_id = result.case.case_id
        events: list[AuditEvent] = list(result.audit_events)
        counter = len(events)

        def emit(entity_type: str, event_type: str, metadata: dict[str, str]) -> None:
            nonlocal counter
            counter += 1
            events.append(
                AuditEvent(
                    event_id=f"audit_{case_id}_review_{counter}",
                    case_id=case_id,
                    run_id=result.case.run_id,
                    entity_type=entity_type,
                    entity_id=case_id,
                    event_type=event_type,
                    actor=AuditActor.REVIEWER,
                    timestamp=now,
                    metadata={**metadata, "reviewer": reviewer},
                )
            )

        if decision == "pending":
            emit("Resolution", "REVIEW_LEFT_PENDING", {})
            return replace(result, audit_events=tuple(events))

        if decision == "reject":
            resolution = Resolution.create_human_reviewed(
                gate=result.gate_evaluation,
                reviewer=reviewer,
                review_outcome=ReviewOutcome.REJECTED,
                reviewed_at=now,
            )
            emit(
                "Resolution",
                "RESOLUTION_RECORDED",
                {"disposition": resolution.disposition.value, "review_outcome": "REJECTED"},
            )
            return replace(result, resolution=resolution, audit_events=tuple(events))

        if decision != "approve":
            raise ValueError(f"Unknown review decision: {decision!r}")

        candidate_ids = frozenset(c.ledger_entry_id for c in result.candidates)
        invalid = selected_target_ids - candidate_ids
        if invalid:
            raise InvalidCandidateSelectionError(
                f"Selected target ids {sorted(invalid)} are not among this case's "
                f"deterministic candidates {sorted(candidate_ids)}."
            )
        if not selected_target_ids:
            raise InvalidCandidateSelectionError(
                "At least one existing candidate must be selected to approve."
            )

        ledger_by_id = {entry.id: entry for entry in ledger_pool}
        target_entries = tuple(ledger_by_id[tid] for tid in sorted(selected_target_ids))

        evidence = self._evidence_builder.build(
            settlement=settlement,
            target_entries=target_entries,
            candidates=result.candidates,
        )
        emit(
            "MatchCandidate",
            "REVIEW_TARGET_SELECTED",
            {"selected_target_ids": ",".join(sorted(selected_target_ids))},
        )

        # Case-level facts (expected_net, observed_ledger_total, exception_type) are
        # authoritative production facts a reviewer cannot redefine - carried over
        # unchanged. A fresh ReconciliationCase is constructed and walked through the
        # SAME allowed state transitions the original pipeline uses, because the
        # original case object is already terminal (CLOSED) and CLOSED has no
        # further legal transitions in the domain's own state machine.
        review_case = ReconciliationCase.create(
            case_id=case_id,
            settlement=settlement,
            items=items,
            observed_ledger_total=result.case.observed_ledger_total,
            exception_type=result.case.exception_type,
            run_id=result.case.run_id,
        )
        review_case = replace(
            review_case,
            processing_state=transition_state(
                review_case.processing_state, ProcessingState.RECONCILED
            ),
        )
        review_case = replace(
            review_case,
            processing_state=transition_state(
                review_case.processing_state, ProcessingState.CLASSIFIED
            ),
        )

        gate = evaluate_gate(
            case=review_case,
            settlement=settlement,
            items=items,
            hypothesis_source=HypothesisSource.HUMAN_REVIEW,
            proposed_target_ids=selected_target_ids,
            target_ledger_entries=target_entries,
            deterministic_candidates=result.candidates,
            evidence=evidence,
            already_resolved_target_ids=already_resolved_target_ids,
        )
        emit(
            "GateEvaluation",
            "REVIEW_GATE_EVALUATED",
            {"passed": str(gate.passed), "failing_check": gate.failing_check or "NONE"},
        )

        review_case = replace(
            review_case,
            processing_state=transition_state(review_case.processing_state, ProcessingState.GATED),
        )
        review_case = replace(
            review_case,
            processing_state=transition_state(review_case.processing_state, ProcessingState.CLOSED),
        )

        try:
            resolution = Resolution.create_human_reviewed(
                gate=gate,
                reviewer=reviewer,
                review_outcome=ReviewOutcome.APPROVED,
                reviewed_at=now,
            )
            emit(
                "Resolution",
                "RESOLUTION_RECORDED",
                {"disposition": resolution.disposition.value, "review_outcome": "APPROVED"},
            )
        except ResolutionGateViolationError as exc:
            # Deterministic gate refused the reviewer's selection: the case remains
            # open for human review rather than silently advancing. Never falls back
            # to AUTO_RESOLVED or any other disposition - the gate's refusal stands.
            emit("Resolution", "REVIEW_APPROVAL_REJECTED_BY_GATE", {"reason": str(exc)})
            resolution = Resolution.create_human_review_pending(gate)

        return ReconciliationResult(
            case=review_case,
            candidates=result.candidates,
            evidence=evidence,
            gate_evaluation=gate,
            resolution=resolution,
            audit_events=tuple(events),
        )
