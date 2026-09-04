"""AIInvestigationUseCase: run a bounded AI investigation over a HUMAN_REVIEW case.

Pipeline: HumanReview-eligible case -> AIInvestigatorPort -> Investigation ->
(optional) ResolutionProposal -> EvidenceBuilder (deterministic rebuild,
never the model's own claimed evidence) -> the SAME unmodified evaluate_gate()
-> preview GateEvaluation.

This module MUST NEVER import cashproof.domain.decision.Resolution: it never
creates a Resolution and never changes a case's disposition. A gate-passing
AI proposal is only ever a pre-vetted recommendation - a human must still
approve it through the existing HumanReviewUseCase, which independently
re-runs evaluate_gate() a second time.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime

from cashproof.application.evidence import EvidenceBuilder
from cashproof.application.ports import AIInvestigatorPort
from cashproof.application.review import ReviewNotApplicableError
from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.ai import Investigation, InvestigatorBudget, ResolutionProposal
from cashproof.domain.decision import AuditEvent, GateEvaluation, evaluate_gate
from cashproof.domain.derived import ReconciliationCase
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.state import transition_state
from cashproof.domain.types import (
    AuditActor,
    Disposition,
    HypothesisSource,
    ProcessingState,
    StopReason,
)


@dataclass(frozen=True, slots=True)
class InvestigationRunResult:
    """Full outcome of one AI investigation run over a case.

    preview_gate is None whenever no proposal was produced (any non-COMPLETED
    stop reason, an explicit abstain, or a proposal this use case itself
    rejected as referencing ledger ids outside the case's own candidate pool).
    """

    case_id: str
    investigation: Investigation
    proposal: ResolutionProposal | None
    preview_gate: GateEvaluation | None
    audit_events: tuple[AuditEvent, ...]


class AIInvestigationUseCase:
    """Orchestrates one bounded AI investigation over a HUMAN_REVIEW case."""

    def __init__(
        self,
        investigator: AIInvestigatorPort,
        evidence_builder: EvidenceBuilder | None = None,
    ) -> None:
        self._investigator = investigator
        self._evidence_builder = evidence_builder or EvidenceBuilder()

    def run_investigation(
        self,
        result: ReconciliationResult,
        settlement: Settlement,
        items: Sequence[SettlementItem],
        payments: Sequence[Payment],
        ledger_pool: Sequence[LedgerEntry],
        budget: InvestigatorBudget,
        run_id: str,
        now: datetime,
        already_resolved_target_ids: frozenset[str],
    ) -> InvestigationRunResult:
        del payments  # not used by any bounded tool today; kept for signature symmetry
        if result.resolution.disposition != Disposition.HUMAN_REVIEW:
            raise ReviewNotApplicableError(
                f"Case {result.case.case_id} has disposition "
                f"{result.resolution.disposition.value}, not HUMAN_REVIEW; AI investigation "
                "is not applicable."
            )

        case_id = result.case.case_id
        events: list[AuditEvent] = []
        counter = 0

        def emit(entity_type: str, event_type: str, metadata: dict[str, str]) -> None:
            nonlocal counter
            counter += 1
            events.append(
                AuditEvent(
                    event_id=f"audit_{case_id}_ai_{counter}",
                    case_id=case_id,
                    run_id=run_id,
                    entity_type=entity_type,
                    entity_id=case_id,
                    event_type=event_type,
                    actor=AuditActor.AI,
                    timestamp=now,
                    metadata=metadata,
                )
            )

        ledger_entries_by_id = {
            c.ledger_entry_id: entry
            for c in result.candidates
            for entry in ledger_pool
            if entry.id == c.ledger_entry_id
        }

        outcome = self._investigator.investigate(
            case=result.case,
            settlement=settlement,
            items=items,
            candidates=result.candidates,
            evidence=result.evidence,
            gate=result.gate_evaluation,
            ledger_entries_by_id=ledger_entries_by_id,
            budget=budget,
            run_id=run_id,
        )

        investigation = outcome.investigation
        proposal = outcome.proposal
        preview_gate: GateEvaluation | None = None

        emit(
            "Investigation",
            "AI_INVESTIGATION_COMPLETED",
            {
                "stop_reason": investigation.stop_reason.value,
                "tool_call_count": str(len(investigation.tool_calls)),
            },
        )

        if proposal is not None:
            candidate_ids = frozenset(c.ledger_entry_id for c in result.candidates)
            out_of_pool = proposal.target_ledger_entry_ids - candidate_ids
            if not proposal.target_ledger_entry_ids or out_of_pool:
                # Belt-and-suspenders: never trust the port's own validation alone.
                # An out-of-pool proposal is downgraded to "no usable proposal" and
                # the investigation's own record is corrected to reflect that.
                investigation = replace(investigation, stop_reason=StopReason.MALFORMED_OUTPUT)
                emit(
                    "ResolutionProposal",
                    "AI_PROPOSAL_REJECTED_OUT_OF_POOL",
                    {"invalid_target_ids": ",".join(sorted(out_of_pool))},
                )
                proposal = None

        if proposal is not None:
            ledger_by_id = {entry.id: entry for entry in ledger_pool}
            target_entries = tuple(
                ledger_by_id[tid] for tid in sorted(proposal.target_ledger_entry_ids)
            )
            rebuilt_evidence = self._evidence_builder.build(
                settlement=settlement,
                target_entries=target_entries,
                candidates=result.candidates,
            )
            # Never the model's own claimed evidence - always the deterministic
            # rebuild, attached here for a consistent, trustworthy audit record.
            proposal = replace(proposal, evidence=rebuilt_evidence)
            emit(
                "ResolutionProposal",
                "AI_PROPOSAL_SUBMITTED",
                {
                    "target_ledger_entry_ids": ",".join(sorted(proposal.target_ledger_entry_ids)),
                    "confidence": str(proposal.confidence),
                },
            )

            review_case = ReconciliationCase.create(
                case_id=result.case.case_id,
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

            preview_gate = evaluate_gate(
                case=review_case,
                settlement=settlement,
                items=items,
                hypothesis_source=HypothesisSource.AI_INVESTIGATION,
                proposed_target_ids=proposal.target_ledger_entry_ids,
                target_ledger_entries=target_entries,
                deterministic_candidates=result.candidates,
                evidence=rebuilt_evidence,
                already_resolved_target_ids=already_resolved_target_ids,
            )
            emit(
                "GateEvaluation",
                "AI_PREVIEW_GATE_EVALUATED",
                {
                    "passed": str(preview_gate.passed),
                    "failing_check": preview_gate.failing_check or "NONE",
                },
            )

        return InvestigationRunResult(
            case_id=case_id,
            investigation=investigation,
            proposal=proposal,
            preview_gate=preview_gate,
            audit_events=tuple(events),
        )
