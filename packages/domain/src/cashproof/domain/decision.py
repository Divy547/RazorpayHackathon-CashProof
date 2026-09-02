"""CashProof Governance Decision Models and Deterministic Resolution Gates.

Implements protected GateEvaluation derivation, validated Resolution construction,
global target exclusivity checking, and immutable AuditEvents.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.exceptions import (
    CurrencyMismatchError,
    DirectConstructionForbiddenError,
    LedgerEntryAlreadyResolvedError,
    ResolutionGateViolationError,
    ResolutionGovernanceError,
    ResolutionScopeMismatchError,
    ResolutionTargetMismatchError,
)
from cashproof.domain.money import aggregate_ledger_total
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem
from cashproof.domain.types import (
    AuditActor,
    Disposition,
    EvidenceStance,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
    ReviewOutcome,
)


@dataclass(frozen=True, slots=True)
class GateCheckOutcome:
    """Outcome of a single deterministic gate check."""

    check_name: str
    passed: bool
    reason: str
    is_mandatory: bool = True

    def __post_init__(self) -> None:
        if not self.check_name.strip():
            raise ValueError("check_name must not be empty.")


@dataclass(frozen=True, slots=True)
class BridgeSnapshot:
    """Point-in-time financial reconciliation bridge snapshot."""

    gross_minor: int
    fee_minor: int
    tax_on_fee_minor: int
    netted_refund_minor: int
    adjustment_minor: int
    computed_net_minor: int
    expected_net_minor: int
    observed_net_minor: int | None
    delta_minor: int | None


@dataclass(frozen=True, slots=True)
class GateEvaluation:
    """Immutable evaluation of a resolution hypothesis.

    Constructed solely through evaluate_gate() from authoritative raw domain inputs.
    Direct construction is forbidden.
    """

    case_id: str
    run_id: str
    hypothesis_source: HypothesisSource
    target_ledger_entry_ids: frozenset[str]
    check_outcomes: tuple[GateCheckOutcome, ...]
    bridge_snapshot: BridgeSnapshot
    passed: bool
    failing_check: str | None

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise DirectConstructionForbiddenError(
            "GateEvaluation cannot be constructed directly. Use evaluate_gate()."
        )

    @classmethod
    def evaluate(
        cls,
        case: ReconciliationCase,
        settlement: Settlement,
        items: Sequence[SettlementItem] | SettlementItem,
        hypothesis_source: HypothesisSource,
        proposed_target_ids: frozenset[str] | Iterable[str],
        target_ledger_entries: Sequence[LedgerEntry],
        deterministic_candidates: Sequence[MatchCandidate],
        evidence: Sequence[Evidence],
        already_resolved_target_ids: frozenset[str] | Iterable[str],
    ) -> GateEvaluation:
        """Authoritative factory for GateEvaluation."""
        return evaluate_gate(
            case=case,
            settlement=settlement,
            items=items,
            hypothesis_source=hypothesis_source,
            proposed_target_ids=proposed_target_ids,
            target_ledger_entries=target_ledger_entries,
            deterministic_candidates=deterministic_candidates,
            evidence=evidence,
            already_resolved_target_ids=already_resolved_target_ids,
        )


def evaluate_gate(
    case: ReconciliationCase,
    settlement: Settlement,
    items: Sequence[SettlementItem] | SettlementItem,
    hypothesis_source: HypothesisSource,
    proposed_target_ids: frozenset[str] | Iterable[str],
    target_ledger_entries: Sequence[LedgerEntry],
    deterministic_candidates: Sequence[MatchCandidate],
    evidence: Sequence[Evidence],
    already_resolved_target_ids: frozenset[str] | Iterable[str],
) -> GateEvaluation:
    """Authoritative factory for GateEvaluation that executes all mandatory checks internally."""
    clean_proposed_ids = frozenset(proposed_target_ids)
    clean_resolved_ids = frozenset(already_resolved_target_ids)
    clean_targets = tuple(target_ledger_entries)
    clean_candidates = tuple(deterministic_candidates)
    clean_evidence = tuple(evidence)

    clean_items: tuple[SettlementItem, ...] = (
        (items,) if isinstance(items, SettlementItem) else tuple(items)
    )

    # 1. Compute settlement-wide bridge totals
    gross_minor = sum(i.gross_minor for i in clean_items)
    fee_minor = sum(i.fee_minor for i in clean_items)
    tax_on_fee_minor = sum(i.tax_on_fee_minor for i in clean_items)
    netted_refund_minor = sum(i.netted_refund_minor for i in clean_items)
    adjustment_minor = sum(i.adjustment_minor for i in clean_items)
    computed_net_minor = sum(i.computed_net_minor for i in clean_items)

    # 2. Currency check & observed ledger calculation
    currency_mismatches = [e.id for e in clean_targets if e.currency != settlement.currency]

    observed_total: int | None = None
    delta: int | None = None

    if not currency_mismatches:
        try:
            observed_total = aggregate_ledger_total(clean_targets, settlement.currency)
            delta = case.expected_net - observed_total
        except CurrencyMismatchError:
            observed_total = None
            delta = None

    bridge_snapshot = BridgeSnapshot(
        gross_minor=gross_minor,
        fee_minor=fee_minor,
        tax_on_fee_minor=tax_on_fee_minor,
        netted_refund_minor=netted_refund_minor,
        adjustment_minor=adjustment_minor,
        computed_net_minor=computed_net_minor,
        expected_net_minor=case.expected_net,
        observed_net_minor=observed_total,
        delta_minor=delta,
    )

    # 3. Execute 9 mandatory checks internally
    outcomes: list[GateCheckOutcome] = []

    # Check 1: IDENTITY
    target_entry_ids = {e.id for e in clean_targets}
    if not clean_proposed_ids:
        outcomes.append(GateCheckOutcome("IDENTITY", False, "Proposed target set is empty."))
    elif clean_proposed_ids != target_entry_ids:
        missing = sorted(clean_proposed_ids - target_entry_ids)
        extra = sorted(target_entry_ids - clean_proposed_ids)
        outcomes.append(
            GateCheckOutcome(
                "IDENTITY",
                False,
                f"Target entries mismatch: missing={missing}, extra={extra}",
            )
        )
    else:
        outcomes.append(
            GateCheckOutcome("IDENTITY", True, "All target entries exist and match proposed IDs.")
        )

    # Check 2: CURRENCY
    if currency_mismatches:
        outcomes.append(
            GateCheckOutcome(
                "CURRENCY",
                False,
                f"Ledger entries {currency_mismatches} mismatch settlement {settlement.currency}.",
            )
        )
    else:
        outcomes.append(GateCheckOutcome("CURRENCY", True, "Currency consistency verified."))

    # Check 3: BRIDGE (Settlement / Case level)
    if currency_mismatches or observed_total is None or delta is None:
        outcomes.append(
            GateCheckOutcome(
                "BRIDGE",
                False,
                "Monetary bridge unavailable due to currency mismatch.",
            )
        )
    elif observed_total != case.expected_net or delta != 0:
        outcomes.append(
            GateCheckOutcome(
                "BRIDGE",
                False,
                f"Monetary bridge mismatch: observed_total={observed_total}, "
                f"expected_net={case.expected_net}, delta={delta}",
            )
        )
    else:
        outcomes.append(GateCheckOutcome("BRIDGE", True, "Monetary bridge balances to zero delta."))

    # Check 4: UNIQUENESS
    if len(clean_targets) != len(clean_proposed_ids):
        outcomes.append(
            GateCheckOutcome("UNIQUENESS", False, "Duplicate entries detected in target set.")
        )
    else:
        conflicts = clean_proposed_ids & clean_resolved_ids
        if conflicts:
            outcomes.append(
                GateCheckOutcome(
                    "UNIQUENESS",
                    False,
                    f"Target entries {sorted(conflicts)} are already resolved in other cases.",
                )
            )
        else:
            outcomes.append(
                GateCheckOutcome(
                    "UNIQUENESS",
                    True,
                    "Target entries are unique and globally exclusive.",
                )
            )

    # Check 5: EVIDENCE_COMPLETENESS (Entity type LedgerEntry matching target ID)
    consumed_ledger_entry_pointers = {
        e.pointer.entity_id
        for e in clean_evidence
        if e.decision_consumed
        and e.stance == EvidenceStance.SUPPORTS
        and e.pointer.entity_type == "LedgerEntry"
    }
    uncovered_targets = clean_proposed_ids - consumed_ledger_entry_pointers
    if uncovered_targets and clean_proposed_ids:
        outcomes.append(
            GateCheckOutcome(
                "EVIDENCE_COMPLETENESS",
                False,
                f"Targets {sorted(uncovered_targets)} lack supporting LedgerEntry evidence.",
            )
        )
    else:
        outcomes.append(
            GateCheckOutcome("EVIDENCE_COMPLETENESS", True, "Evidence chain is complete.")
        )

    # Check 6: CONFLICT
    conflicting_evidence = [
        e for e in clean_evidence if e.stance == EvidenceStance.CONTRADICTS and e.decision_consumed
    ]
    if conflicting_evidence:
        outcomes.append(
            GateCheckOutcome(
                "CONFLICT",
                False,
                f"Detected {len(conflicting_evidence)} contradicting evidence items.",
            )
        )
    else:
        outcomes.append(GateCheckOutcome("CONFLICT", True, "No conflicting evidence detected."))

    # Check 7: POLICY (Aggregate candidate provenances per target)
    candidate_provenances: dict[str, set[MatchProvenance]] = {}
    for c in clean_candidates:
        candidate_provenances.setdefault(c.ledger_entry_id, set()).add(c.provenance)

    unstructured_targets = [
        t_id
        for t_id in clean_proposed_ids
        if MatchProvenance.EXTERNAL_REFERENCE_TEXT in candidate_provenances.get(t_id, set())
        or MatchProvenance.NARRATION_ALIAS_TEXT in candidate_provenances.get(t_id, set())
    ]
    if unstructured_targets:
        outcomes.append(
            GateCheckOutcome(
                "POLICY",
                False,
                f"Targets {sorted(unstructured_targets)} derive from unstructured/narration text. "
                "Policy requires HUMAN_REVIEW.",
            )
        )
    else:
        outcomes.append(GateCheckOutcome("POLICY", True, "Targets satisfy auto-resolution policy."))

    # Check 8: STATE_TRANSITION
    if case.processing_state not in (ProcessingState.INVESTIGATED, ProcessingState.CLASSIFIED):
        outcomes.append(
            GateCheckOutcome(
                "STATE_TRANSITION",
                False,
                f"Invalid case processing_state '{case.processing_state}' for gate evaluation.",
            )
        )
    else:
        outcomes.append(
            GateCheckOutcome("STATE_TRANSITION", True, "Case state is valid for gating.")
        )

    # Check 9: TARGET_SET_EQUALITY
    deterministic_candidate_ids = frozenset(c.ledger_entry_id for c in clean_candidates)
    if clean_proposed_ids != deterministic_candidate_ids:
        missing_cands = sorted(deterministic_candidate_ids - clean_proposed_ids)
        extra_cands = sorted(clean_proposed_ids - deterministic_candidate_ids)
        outcomes.append(
            GateCheckOutcome(
                "TARGET_SET_EQUALITY",
                False,
                f"Target set mismatch: missing={missing_cands}, extra={extra_cands}",
            )
        )
    else:
        outcomes.append(
            GateCheckOutcome("TARGET_SET_EQUALITY", True, "Exact target-set equality verified.")
        )

    mandatory_failed = [c for c in outcomes if c.is_mandatory and not c.passed]
    passed = len(mandatory_failed) == 0
    failing_check = mandatory_failed[0].check_name if mandatory_failed else None

    # Construct immutable GateEvaluation instance
    obj = object.__new__(GateEvaluation)
    object.__setattr__(obj, "case_id", case.case_id)
    object.__setattr__(obj, "run_id", case.run_id)
    object.__setattr__(obj, "hypothesis_source", hypothesis_source)
    object.__setattr__(obj, "target_ledger_entry_ids", clean_proposed_ids)
    object.__setattr__(obj, "check_outcomes", tuple(outcomes))
    object.__setattr__(obj, "bridge_snapshot", bridge_snapshot)
    object.__setattr__(obj, "passed", passed)
    object.__setattr__(obj, "failing_check", failing_check)
    return obj


@dataclass(frozen=True, slots=True)
class Resolution:
    """Immutable final governance resolution for a case instance."""

    case_id: str
    run_id: str
    disposition: Disposition
    target_ledger_entry_ids: frozenset[str]
    governing_gate_evaluation: GateEvaluation
    reviewer: str | None = None
    review_outcome: ReviewOutcome | None = None
    reviewed_at: datetime | None = None

    def __init__(
        self,
        case_id: str,
        run_id: str,
        disposition: Disposition,
        target_ledger_entry_ids: Iterable[str],
        governing_gate_evaluation: GateEvaluation,
        reviewer: str | None = None,
        review_outcome: ReviewOutcome | None = None,
        reviewed_at: datetime | None = None,
    ) -> None:
        clean_targets = frozenset(target_ledger_entry_ids)

        if not isinstance(governing_gate_evaluation, GateEvaluation):
            raise ResolutionGovernanceError("Resolution requires a governing GateEvaluation.")

        if clean_targets != governing_gate_evaluation.target_ledger_entry_ids:
            raise ResolutionTargetMismatchError(
                f"Resolution target set {clean_targets} does not match "
                f"gate evaluation target set {governing_gate_evaluation.target_ledger_entry_ids}."
            )

        if (
            case_id != governing_gate_evaluation.case_id
            or run_id != governing_gate_evaluation.run_id
        ):
            raise ResolutionScopeMismatchError(
                "Resolution case_id or run_id does not match governing GateEvaluation."
            )

        if disposition == Disposition.AUTO_RESOLVED:
            if not governing_gate_evaluation.passed:
                raise ResolutionGateViolationError(
                    f"AUTO_RESOLVED requires a passing GateEvaluation "
                    f"(failed: {governing_gate_evaluation.failing_check})."
                )
            if reviewer is not None or review_outcome is not None or reviewed_at is not None:
                raise ResolutionGovernanceError(
                    "AUTO_RESOLVED cannot contain human reviewer fields."
                )

        elif disposition == Disposition.HUMAN_REVIEW:
            if review_outcome not in (ReviewOutcome.PENDING, ReviewOutcome.APPROVED):
                raise ResolutionGovernanceError(
                    f"HUMAN_REVIEW requires PENDING or APPROVED, got {review_outcome}"
                )
            if review_outcome == ReviewOutcome.APPROVED:
                if not reviewer or not reviewed_at:
                    raise ResolutionGovernanceError(
                        "APPROVED human review requires reviewer and reviewed_at."
                    )
            elif review_outcome == ReviewOutcome.PENDING:
                if reviewer is not None or reviewed_at is not None:
                    raise ResolutionGovernanceError(
                        "PENDING human review cannot have reviewer or reviewed_at set."
                    )

        elif disposition == Disposition.UNRESOLVED:
            if review_outcome == ReviewOutcome.REJECTED:
                if not reviewer or not reviewed_at:
                    raise ResolutionGovernanceError(
                        "REJECTED human review requires reviewer and reviewed_at."
                    )
            elif review_outcome is None:
                if reviewer is not None or reviewed_at is not None:
                    raise ResolutionGovernanceError(
                        "Deterministic UNRESOLVED cannot have reviewer fields."
                    )
            else:
                raise ResolutionGovernanceError(
                    f"UNRESOLVED disposition cannot have review_outcome {review_outcome}."
                )

        object.__setattr__(self, "case_id", case_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "disposition", disposition)
        object.__setattr__(self, "target_ledger_entry_ids", clean_targets)
        object.__setattr__(self, "governing_gate_evaluation", governing_gate_evaluation)
        object.__setattr__(self, "reviewer", reviewer)
        object.__setattr__(self, "review_outcome", review_outcome)
        object.__setattr__(self, "reviewed_at", reviewed_at)

    @classmethod
    def create_auto_resolved(cls, gate: GateEvaluation) -> Resolution:
        """Create an AUTO_RESOLVED resolution from a passing GateEvaluation."""
        return cls(
            case_id=gate.case_id,
            run_id=gate.run_id,
            disposition=Disposition.AUTO_RESOLVED,
            target_ledger_entry_ids=gate.target_ledger_entry_ids,
            governing_gate_evaluation=gate,
            reviewer=None,
            review_outcome=None,
            reviewed_at=None,
        )

    @classmethod
    def create_human_review_pending(cls, gate: GateEvaluation) -> Resolution:
        """Create an open HUMAN_REVIEW resolution with review_outcome=PENDING."""
        return cls(
            case_id=gate.case_id,
            run_id=gate.run_id,
            disposition=Disposition.HUMAN_REVIEW,
            target_ledger_entry_ids=gate.target_ledger_entry_ids,
            governing_gate_evaluation=gate,
            reviewer=None,
            review_outcome=ReviewOutcome.PENDING,
            reviewed_at=None,
        )

    @classmethod
    def create_human_reviewed(
        cls,
        gate: GateEvaluation,
        reviewer: str,
        review_outcome: ReviewOutcome,
        reviewed_at: datetime,
    ) -> Resolution:
        """Create a completed human review resolution (APPROVED or REJECTED)."""
        if review_outcome == ReviewOutcome.APPROVED:
            disposition = Disposition.HUMAN_REVIEW
        elif review_outcome == ReviewOutcome.REJECTED:
            disposition = Disposition.UNRESOLVED
        else:
            raise ValueError("create_human_reviewed requires APPROVED or REJECTED outcome.")

        return cls(
            case_id=gate.case_id,
            run_id=gate.run_id,
            disposition=disposition,
            target_ledger_entry_ids=gate.target_ledger_entry_ids,
            governing_gate_evaluation=gate,
            reviewer=reviewer,
            review_outcome=review_outcome,
            reviewed_at=reviewed_at,
        )

    @classmethod
    def create_unresolved(cls, gate: GateEvaluation) -> Resolution:
        """Create a deterministic UNRESOLVED resolution."""
        return cls(
            case_id=gate.case_id,
            run_id=gate.run_id,
            disposition=Disposition.UNRESOLVED,
            target_ledger_entry_ids=gate.target_ledger_entry_ids,
            governing_gate_evaluation=gate,
            reviewer=None,
            review_outcome=None,
            reviewed_at=None,
        )


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Immutable, append-only audit event for tracking domain transitions and decisions."""

    event_id: str
    case_id: str
    run_id: str
    entity_type: str
    entity_id: str
    event_type: str
    actor: AuditActor
    timestamp: datetime
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __init__(
        self,
        event_id: str,
        case_id: str,
        run_id: str,
        entity_type: str,
        entity_id: str,
        event_type: str,
        actor: AuditActor,
        timestamp: datetime,
        metadata: Mapping[str, str] | Iterable[tuple[str, str]] = (),
    ) -> None:
        if not event_id.strip():
            raise ValueError("event_id must not be empty.")
        if not case_id.strip():
            raise ValueError("case_id must not be empty.")
        if not run_id.strip():
            raise ValueError("run_id must not be empty.")
        if not entity_type.strip():
            raise ValueError("entity_type must not be empty.")
        if not entity_id.strip():
            raise ValueError("entity_id must not be empty.")
        if not event_type.strip():
            raise ValueError("event_type must not be empty.")

        if isinstance(metadata, Mapping):
            frozen_meta = tuple(sorted((str(k), str(v)) for k, v in metadata.items()))
        else:
            frozen_meta = tuple((str(k), str(v)) for k, v in metadata)

        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "case_id", case_id)
        object.__setattr__(self, "run_id", run_id)
        object.__setattr__(self, "entity_type", entity_type)
        object.__setattr__(self, "entity_id", entity_id)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "actor", actor)
        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "metadata", frozen_meta)


def validate_ledger_target_exclusivity(
    candidate_target_ids: frozenset[str] | Iterable[str],
    already_resolved_target_ids: frozenset[str] | Iterable[str],
) -> None:
    """Enforce that a LedgerEntry may be the final target of at most one Resolution."""
    candidates = frozenset(candidate_target_ids)
    resolved = frozenset(already_resolved_target_ids)
    conflicts = candidates & resolved
    if conflicts:
        raise LedgerEntryAlreadyResolvedError(
            f"Ledger entries already resolved in another case: {sorted(conflicts)}"
        )
