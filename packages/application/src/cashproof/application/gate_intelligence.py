"""CashProof Gate Intelligence and Controller Explainability Engine.

This module provides deterministic observation, metrics aggregation, ranking, and
operator explainability for the CashProof GateEvaluation firewall.

Core architectural invariant:
The Gate (evaluate_gate) remains the sole authoritative decision firewall.
Gate Intelligence is strictly READ / ANALYZE: it never mutates financial facts,
never bypasses the gate, and never approves resolutions.

Canonical Evaluation Rule:
A case may undergo multiple gate evaluations (initial deterministic evaluation,
AI proposal preview, human review re-evaluation). To ensure case-level controller
integrity, Gate Intelligence resolves the canonical evaluation as the
governing_gate_evaluation of the case's recorded Resolution.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from cashproof.application.intelligence import (
    ExceptionCluster,
    ExceptionIntelligenceService,
)
from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.source import Settlement
from cashproof.domain.types import Currency, Disposition, HypothesisSource

# All 9 mandatory gate checks defined in cashproof.domain.decision
MANDATORY_GATE_CHECKS: tuple[str, ...] = (
    "IDENTITY",
    "CURRENCY",
    "BRIDGE",
    "UNIQUENESS",
    "EVIDENCE_COMPLETENESS",
    "CONFLICT",
    "POLICY",
    "STATE_TRANSITION",
    "TARGET_SET_EQUALITY",
)


@dataclass(frozen=True, slots=True)
class GateExplanation:
    """Deterministic operator explanation and remediation requirement for a GateCheck."""

    check_name: str
    summary: str
    description: str
    eligibility_requirement: str
    is_automation_blocker: bool = True


DETERMINISTIC_GATE_EXPLANATIONS: Mapping[str, GateExplanation] = {
    "IDENTITY": GateExplanation(
        check_name="IDENTITY",
        summary="Ledger identity could not be established with sufficient certainty.",
        description=(
            "Proposed target ledger set is empty or does not match authoritative ledger record IDs."
        ),
        eligibility_requirement=(
            "Provide or ingest a valid ledger entry whose identifier and reference match the "
            "settlement."
        ),
        is_automation_blocker=True,
    ),
    "CURRENCY": GateExplanation(
        check_name="CURRENCY",
        summary="Source records use incompatible currencies.",
        description=(
            "One or more proposed ledger entries have a currency that mismatches the settlement "
            "currency."
        ),
        eligibility_requirement=(
            "Ensure all candidate ledger entries are denominated in the exact settlement currency "
            "(e.g. INR)."
        ),
        is_automation_blocker=True,
    ),
    "BRIDGE": GateExplanation(
        check_name="BRIDGE",
        summary="The proposed ledger target does not reconcile to the expected settlement bridge.",
        description=(
            "The sum of proposed ledger entries does not match the expected net deposited amount "
            "(gross - fee - tax - refund + adj)."
        ),
        eligibility_requirement=(
            "Verify fee schedules, 18% GST calculation, and netted refund lines to balance the "
            "bridge delta to zero."
        ),
        is_automation_blocker=True,
    ),
    "UNIQUENESS": GateExplanation(
        check_name="UNIQUENESS",
        summary="Proposed ledger targets conflict with another resolution or are duplicated.",
        description=(
            "One or more proposed ledger entries are already resolved in another settlement or "
            "duplicated in the target set."
        ),
        eligibility_requirement=(
            "Select unique, unallocated ledger entries that have not been claimed by any existing "
            "resolution."
        ),
        is_automation_blocker=True,
    ),
    "EVIDENCE_COMPLETENESS": GateExplanation(
        check_name="EVIDENCE_COMPLETENESS",
        summary="Required supporting evidence pointers are missing.",
        description=(
            "Every proposed target ledger entry must have a supporting, decision-consumed evidence "
            "pointer."
        ),
        eligibility_requirement=(
            "Attach validated supporting evidence pointers linking the settlement item to the "
            "candidate ledger entry."
        ),
        is_automation_blocker=True,
    ),
    "CONFLICT": GateExplanation(
        check_name="CONFLICT",
        summary="Available evidence contains contradictory signals.",
        description=(
            "One or more decision-consumed evidence items have CONTRADICTS stance against the "
            "proposed hypothesis."
        ),
        eligibility_requirement=(
            "Investigate and resolve conflicting evidence sources before proposing the target set."
        ),
        is_automation_blocker=True,
    ),
    "POLICY": GateExplanation(
        check_name="POLICY",
        summary="The match may be valid, but policy requires explicit human verification.",
        description=(
            "Candidate derived from unstructured free text (external reference or narration "
            "alias), blocking automated resolution."
        ),
        eligibility_requirement=(
            "Obtain explicit human reviewer verification and approval through the Human Review "
            "workflow."
        ),
        is_automation_blocker=True,
    ),
    "STATE_TRANSITION": GateExplanation(
        check_name="STATE_TRANSITION",
        summary="The case lifecycle state is invalid for gating.",
        description=(
            "Case lifecycle state must be CLASSIFIED or INVESTIGATED to undergo gate evaluation."
        ),
        eligibility_requirement=(
            "Progress the case through the standard lifecycle pipeline before evaluating gates."
        ),
        is_automation_blocker=True,
    ),
    "TARGET_SET_EQUALITY": GateExplanation(
        check_name="TARGET_SET_EQUALITY",
        summary="Proposed target set does not satisfy candidate-set constraints.",
        description=(
            "For automated resolution, proposed targets must exactly equal the deterministic "
            "candidate pool; for human review, targets must be a subset of candidates."
        ),
        eligibility_requirement=(
            "For auto-resolution, eliminate ambiguous multiple candidates; for human review, "
            "select target entries strictly from the candidate pool."
        ),
        is_automation_blocker=True,
    ),
}


@dataclass(frozen=True, slots=True)
class ControllerGateOutcome:
    """Deterministic analytical projection representing the canonical gate outcome for one case."""

    case_id: str
    settlement_id: str
    run_id: str
    disposition: Disposition
    passed: bool
    failing_check: str | None
    hypothesis_source: HypothesisSource
    expected_settlement_net_minor: int
    observed_ledger_net_minor: int | None
    delta_minor: int
    currency: Currency
    cluster_key: str | None
    operational_category: str | None
    explanation: GateExplanation | None
    failure_reason: str | None


@dataclass(frozen=True, slots=True)
class GateCheckBreakdown:
    """Aggregated controller metrics for a single deterministic gate check."""

    check_name: str
    evaluation_count: int
    failure_count: int
    failure_rate: float
    affected_case_count: int
    affected_settlement_net_minor: int
    affected_delta_minor: int
    currency: Currency
    disposition_counts: tuple[tuple[str, int], ...]
    explanation: GateExplanation
    related_cluster_keys: tuple[str, ...]
    representative_case_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AutomationBlocker:
    """Ranked automation blocker impeding AUTO_RESOLVED disposition."""

    rank: int
    check_name: str
    failure_count: int
    affected_cases: int
    affected_settlement_net_minor: int
    affected_delta_minor: int
    currency: Currency
    percentage_of_blocked_cases: float
    explanation: GateExplanation
    top_cluster_name: str | None
    top_cluster_key: str | None
    representative_case_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GateIntelligenceSummary:
    """Comprehensive, deterministic controller gate intelligence and explainability report."""

    total_evaluations: int
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    fail_rate: float
    total_settlement_net_minor: int
    total_affected_settlement_net_minor: int
    total_affected_delta_minor: int
    currency: Currency
    disposition_breakdown: tuple[tuple[str, int], ...]
    automation_blockers: tuple[AutomationBlocker, ...]
    check_breakdowns: tuple[GateCheckBreakdown, ...]
    top_blocker: str | None
    case_outcomes: tuple[ControllerGateOutcome, ...]


def resolve_canonical_evaluation(result: ReconciliationResult) -> GateEvaluation:
    """Resolves the authoritative canonical GateEvaluation for a case.

    A case may have multiple GateEvaluations across its lifecycle:
    1. Initial deterministic pipeline evaluation
    2. AI investigation preview evaluation (advisory only)
    3. Human reviewer approval/refusal evaluation

    The canonical evaluation is the governing_gate_evaluation of the recorded
    Resolution, which authorizes the final or active case disposition.
    """
    if result.resolution and result.resolution.governing_gate_evaluation:
        return result.resolution.governing_gate_evaluation
    return result.gate_evaluation


class GateIntelligenceService:
    """Deterministic service for Gate observation, failure attribution, and explainability."""

    def __init__(self, intelligence_service: ExceptionIntelligenceService | None = None) -> None:
        self._intelligence_service = intelligence_service or ExceptionIntelligenceService()

    def get_explanation(self, check_name: str) -> GateExplanation:
        """Retrieves the deterministic explanation for a gate check."""
        return DETERMINISTIC_GATE_EXPLANATIONS.get(
            check_name,
            GateExplanation(
                check_name=check_name,
                summary=f"Gate check {check_name} failed.",
                description=f"Deterministic rule {check_name} failed validation.",
                eligibility_requirement="Satisfy all mandatory gate check constraints.",
                is_automation_blocker=True,
            ),
        )

    def analyze_gate(
        self,
        results: Sequence[ReconciliationResult],
        settlements: Mapping[str, Settlement],
        clusters: Sequence[ExceptionCluster] | None = None,
        total_evaluations_count: int | None = None,
    ) -> GateIntelligenceSummary:
        """Computes comprehensive gate intelligence across a batch of reconciliation results."""
        default_currency = Currency.INR
        total_cases = len(results)

        # Evaluation-level metric vs Case-level metric
        total_evals = (
            total_evaluations_count if total_evaluations_count is not None else total_cases
        )

        if total_cases == 0:
            return GateIntelligenceSummary(
                total_evaluations=0,
                total_cases=0,
                passed_cases=0,
                failed_cases=0,
                pass_rate=0.0,
                fail_rate=0.0,
                total_settlement_net_minor=0,
                total_affected_settlement_net_minor=0,
                total_affected_delta_minor=0,
                currency=default_currency,
                disposition_breakdown=(),
                automation_blockers=(),
                check_breakdowns=(),
                top_blocker=None,
                case_outcomes=(),
            )

        # Obtain exception clusters if not supplied
        if clusters is None:
            cluster_summary = self._intelligence_service.cluster_exceptions(results, settlements)
            clusters = cluster_summary.clusters

        # Map each case_id to its Phase 6 ExceptionCluster for cross-referencing
        case_to_cluster: dict[str, ExceptionCluster] = {}
        for c in clusters:
            for cid in c.case_ids:
                case_to_cluster[cid] = c

        # Project canonical outcomes for all cases (O(n))
        case_outcomes: list[ControllerGateOutcome] = []
        cases_by_failing_check: dict[str, list[ReconciliationResult]] = defaultdict(list)
        check_eval_counts: Counter[str] = Counter()
        disposition_counts: Counter[str] = Counter()

        total_settlement_net = 0
        total_affected_net = 0
        total_affected_delta = 0
        passed_cases = 0
        failed_cases = 0

        for r in results:
            settlement = settlements.get(r.case.case_id)
            curr = settlement.currency if settlement else Currency.INR
            canonical_gate = resolve_canonical_evaluation(r)
            failing_check = canonical_gate.failing_check

            total_settlement_net += r.case.expected_net
            disposition_counts[r.resolution.disposition.value] += 1

            for chk in canonical_gate.check_outcomes:
                check_eval_counts[chk.check_name] += 1

            cluster = case_to_cluster.get(r.case.case_id)
            explanation = self.get_explanation(failing_check) if failing_check else None

            # Get failure reason from the canonical GateCheckOutcome
            failure_reason = None
            if failing_check:
                for chk in canonical_gate.check_outcomes:
                    if chk.check_name == failing_check:
                        failure_reason = chk.reason
                        break

            outcome = ControllerGateOutcome(
                case_id=r.case.case_id,
                settlement_id=r.case.settlement_id,
                run_id=r.case.run_id,
                disposition=r.resolution.disposition,
                passed=canonical_gate.passed,
                failing_check=failing_check,
                hypothesis_source=canonical_gate.hypothesis_source,
                expected_settlement_net_minor=r.case.expected_net,
                observed_ledger_net_minor=canonical_gate.bridge_snapshot.observed_net_minor,
                delta_minor=r.case.delta,
                currency=curr,
                cluster_key=cluster.cluster_key if cluster else None,
                operational_category=cluster.operational_category.value if cluster else None,
                explanation=explanation,
                failure_reason=failure_reason,
            )
            case_outcomes.append(outcome)

            if canonical_gate.passed:
                passed_cases += 1
            else:
                failed_cases += 1
                total_affected_net += r.case.expected_net
                total_affected_delta += r.case.delta
                if failing_check:
                    cases_by_failing_check[failing_check].append(r)

        pass_rate = round((passed_cases / total_cases) * 100.0, 1)
        fail_rate = round((failed_cases / total_cases) * 100.0, 1)

        # Build GateCheckBreakdown for each check in MANDATORY_GATE_CHECKS
        check_breakdowns: list[GateCheckBreakdown] = []
        for check_name in MANDATORY_GATE_CHECKS:
            failing_results = cases_by_failing_check.get(check_name, [])
            failure_count = len(failing_results)
            fail_pct = round((failure_count / total_cases) * 100.0, 1)

            affected_net = sum(r.case.expected_net for r in failing_results)
            affected_delta = sum(r.case.delta for r in failing_results)

            disp_c = Counter(r.resolution.disposition.value for r in failing_results)
            disp_tuple = tuple(sorted(disp_c.items()))

            # Related clusters: clusters matching dominant_failing_gate or containing cases
            related_keys = tuple(
                sorted(
                    {
                        c.cluster_key
                        for c in clusters
                        if c.dominant_failing_gate == check_name
                        or any(r.case.case_id in c.case_ids for r in failing_results)
                    }
                )
            )

            # Deterministic representative cases (-abs(delta), -expected_net, case_id)
            sorted_reps = sorted(
                failing_results,
                key=lambda r: (-abs(r.case.delta), -r.case.expected_net, r.case.case_id),
            )
            rep_ids = tuple(r.case.case_id for r in sorted_reps[:3])

            check_breakdowns.append(
                GateCheckBreakdown(
                    check_name=check_name,
                    evaluation_count=check_eval_counts.get(check_name, total_cases),
                    failure_count=failure_count,
                    failure_rate=fail_pct,
                    affected_case_count=failure_count,
                    affected_settlement_net_minor=affected_net,
                    affected_delta_minor=affected_delta,
                    currency=default_currency,
                    disposition_counts=disp_tuple,
                    explanation=self.get_explanation(check_name),
                    related_cluster_keys=related_keys,
                    representative_case_ids=rep_ids,
                )
            )

        # Build ranked AutomationBlockers: failure_count desc, affected_volume desc, check_name asc
        failing_check_breakdowns = [b for b in check_breakdowns if b.failure_count > 0]
        sorted_blockers = sorted(
            failing_check_breakdowns,
            key=lambda b: (-b.failure_count, -b.affected_settlement_net_minor, b.check_name),
        )

        automation_blockers: list[AutomationBlocker] = []
        cluster_by_key = {c.cluster_key: c for c in clusters}
        for rank, b in enumerate(sorted_blockers, start=1):
            pct_blocked = (
                round((b.failure_count / max(1, failed_cases)) * 100.0, 1)
                if failed_cases > 0
                else 0.0
            )

            # Find top cluster associated with this blocker
            top_cluster_key = b.related_cluster_keys[0] if b.related_cluster_keys else None
            top_cluster_name = (
                cluster_by_key[top_cluster_key].cluster_name
                if top_cluster_key and top_cluster_key in cluster_by_key
                else None
            )

            automation_blockers.append(
                AutomationBlocker(
                    rank=rank,
                    check_name=b.check_name,
                    failure_count=b.failure_count,
                    affected_cases=b.affected_case_count,
                    affected_settlement_net_minor=b.affected_settlement_net_minor,
                    affected_delta_minor=b.affected_delta_minor,
                    currency=default_currency,
                    percentage_of_blocked_cases=pct_blocked,
                    explanation=b.explanation,
                    top_cluster_name=top_cluster_name,
                    top_cluster_key=top_cluster_key,
                    representative_case_ids=b.representative_case_ids,
                )
            )

        top_blocker = automation_blockers[0].check_name if automation_blockers else None

        return GateIntelligenceSummary(
            total_evaluations=total_evals,
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            pass_rate=pass_rate,
            fail_rate=fail_rate,
            total_settlement_net_minor=total_settlement_net,
            total_affected_settlement_net_minor=total_affected_net,
            total_affected_delta_minor=total_affected_delta,
            currency=default_currency,
            disposition_breakdown=tuple(sorted(disposition_counts.items())),
            automation_blockers=tuple(automation_blockers),
            check_breakdowns=tuple(check_breakdowns),
            top_blocker=top_blocker,
            case_outcomes=tuple(case_outcomes),
        )
