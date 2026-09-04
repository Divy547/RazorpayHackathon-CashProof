"""Presentation shaping: application/domain objects -> API-boundary Pydantic models.

Pure formatting only. Every value here already comes from cashproof.application
or benchmark evaluation output - no decision logic lives in this module.
"""

from __future__ import annotations

from typing import Any

from cashproof.api.schemas import (
    AIMetricOut,
    AuditEventOut,
    AutomationBlockerOut,
    AutomationOpportunityOut,
    BenchmarkConfidenceResponse,
    BenchmarkRunOut,
    BenchmarkTimingOut,
    BridgeOut,
    CandidateOut,
    CaseDetail,
    CaseEvaluationOut,
    CaseSummary,
    CheckConfidenceContextOut,
    ConfidenceBucketOut,
    ControllerGateOutcomeOut,
    EvidenceOut,
    ExceptionClusterDetailOut,
    ExceptionClusterSummaryOut,
    ExceptionFingerprintOut,
    ExceptionIntelligenceResponse,
    FamilyConfidenceMetricOut,
    FamilyMetricOut,
    GateCheckBreakdownOut,
    GateCheckOut,
    GateConfidenceCellOut,
    GateExplanationOut,
    GateIntelligenceResponse,
    GateOut,
    GateTierSummaryOut,
    InvestigationOut,
    OperationalConfidenceBucketOut,
    OperationalConfidenceResponse,
    ProposalOut,
    ResolutionOut,
    SourceConfidenceMetricOut,
    ThresholdMetricOut,
    ToolCallOut,
)
from cashproof.api.schemas import (
    InvestigationResult as InvestigationResultOut,
)
from cashproof.application.confidence import OperationalConfidenceSummary
from cashproof.application.gate_intelligence import (
    AutomationBlocker,
    ControllerGateOutcome,
    GateCheckBreakdown,
    GateExplanation,
    GateIntelligenceSummary,
)
from cashproof.application.intelligence import (
    ExceptionCluster,
    ExceptionFingerprint,
    ExceptionIntelligenceSummary,
)
from cashproof.application.investigation import InvestigationRunResult
from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import Evidence
from cashproof.domain.source import Settlement, SettlementItem


def case_summary(result: ReconciliationResult) -> CaseSummary:
    case = result.case
    return CaseSummary(
        settlement_id=case.case_id,
        expected_net_minor=case.expected_net,
        observed_net_minor=case.observed_ledger_total,
        delta_minor=case.delta,
        exception_type=case.exception_type.value,
        candidate_count=len(result.candidates),
        disposition=result.resolution.disposition.value,
    )


def _serialize_evidence(e: Evidence) -> EvidenceOut:
    return EvidenceOut(
        entity_type=e.pointer.entity_type,
        entity_id=e.pointer.entity_id,
        field=e.pointer.field,
        relevance=e.relevance,
        stance=e.stance.value,
        decision_consumed=e.decision_consumed,
    )


def _serialize_gate(gate: GateEvaluation) -> GateOut:
    snapshot = gate.bridge_snapshot
    return GateOut(
        passed=gate.passed,
        failing_check=gate.failing_check,
        checks=[
            GateCheckOut(
                name=c.check_name, passed=c.passed, reason=c.reason, is_mandatory=c.is_mandatory
            )
            for c in gate.check_outcomes
        ],
        proposed_target_ids=sorted(gate.target_ledger_entry_ids),
        proposed_target_net_minor=snapshot.observed_net_minor,
        variance_minor=snapshot.delta_minor,
    )


def _bridge(items: list[SettlementItem], settlement: Settlement) -> BridgeOut:
    return BridgeOut(
        gross_minor=sum(i.gross_minor for i in items),
        fee_minor=sum(i.fee_minor for i in items),
        tax_on_fee_minor=sum(i.tax_on_fee_minor for i in items),
        netted_refund_minor=sum(i.netted_refund_minor for i in items),
        adjustment_minor=sum(i.adjustment_minor for i in items),
        computed_net_minor=sum(i.computed_net_minor for i in items),
        expected_net_minor=settlement.net_deposited_minor,
    )


def case_detail(
    result: ReconciliationResult,
    settlement: Settlement,
    items: list[SettlementItem],
) -> CaseDetail:
    summary = case_summary(result)
    return CaseDetail(
        **summary.model_dump(),
        currency=settlement.currency.value,
        settled_at=settlement.settled_at.isoformat(),
        bridge=_bridge(items, settlement),
        candidates=[
            CandidateOut(
                ledger_entry_id=c.ledger_entry_id,
                score=c.score,
                matched_signals=list(c.matched_signals),
                rule_trace=list(c.rule_trace),
                provenance=c.provenance.value,
            )
            for c in result.candidates
        ],
        evidence=[_serialize_evidence(e) for e in result.evidence],
        gate=_serialize_gate(result.gate_evaluation),
        resolution=ResolutionOut(
            disposition=result.resolution.disposition.value,
            target_ledger_entry_ids=sorted(result.resolution.target_ledger_entry_ids),
            reviewer=result.resolution.reviewer,
            review_outcome=(
                result.resolution.review_outcome.value if result.resolution.review_outcome else None
            ),
            reviewed_at=(
                result.resolution.reviewed_at.isoformat() if result.resolution.reviewed_at else None
            ),
        ),
        audit_events=[
            AuditEventOut(
                event_id=e.event_id,
                entity_type=e.entity_type,
                event_type=e.event_type,
                actor=e.actor.value,
                timestamp=e.timestamp.isoformat(),
                metadata=dict(e.metadata),
            )
            for e in result.audit_events
        ],
    )


def investigation_result(run_result: InvestigationRunResult) -> InvestigationResultOut:
    investigation = run_result.investigation
    proposal = run_result.proposal
    return InvestigationResultOut(
        case_id=run_result.case_id,
        investigation=InvestigationOut(
            investigation_id=investigation.investigation_id,
            stop_reason=investigation.stop_reason.value,
            tool_calls=[
                ToolCallOut(
                    tool_name=tc.tool_name,
                    arguments=dict(tc.arguments),
                    response_summary=tc.response_summary,
                    duration_ms=tc.duration_ms,
                )
                for tc in investigation.tool_calls
            ],
            candidates_considered=list(investigation.candidates_considered),
        ),
        proposal=(
            ProposalOut(
                proposal_id=proposal.proposal_id,
                target_ledger_entry_ids=sorted(proposal.target_ledger_entry_ids),
                rationale=proposal.rationale,
                confidence=proposal.confidence,
                evidence=[_serialize_evidence(e) for e in proposal.evidence],
            )
            if proposal is not None
            else None
        ),
        preview_gate=(
            _serialize_gate(run_result.preview_gate)
            if run_result.preview_gate is not None
            else None
        ),
    )


def serialize_benchmark_run(run: Any) -> BenchmarkRunOut:
    """Safely converts a benchmark run dataclass into the API output schema.

    Uses structural introspection to avoid importing benchmark models directly.
    """
    if isinstance(run, BenchmarkRunOut):
        return run

    overall = getattr(run, "overall_metrics", None)
    timing = getattr(run, "timing", None)
    ai = getattr(run, "ai_metrics", None)
    matrix = getattr(run, "scenario_matrix", ())
    cases = getattr(run, "case_evaluations", ())

    metrics_dict: dict[str, float] = {}
    if hasattr(run, "metrics_dict"):
        metrics_dict = run.metrics_dict
    elif hasattr(run, "metrics"):
        metrics_dict = dict(run.metrics)

    family_rows: list[FamilyMetricOut] = []
    for m in matrix:
        fam_val = (
            m.scenario_family.value
            if hasattr(m.scenario_family, "value")
            else str(m.scenario_family)
        )
        family_rows.append(
            FamilyMetricOut(
                scenario_family=fam_val,
                total=m.total,
                auto_resolved=m.auto_resolved,
                human_review=m.human_review,
                unresolved=m.unresolved,
                correct_outcomes=m.correct_outcomes,
                false_auto_resolutions=m.false_auto_resolutions,
            )
        )

    ai_out = AIMetricOut(
        investigations_started=getattr(ai, "investigations_started", 0),
        investigations_completed=getattr(ai, "investigations_completed", 0),
        investigations_failed=getattr(ai, "investigations_failed", 0),
        investigations_abstained=getattr(ai, "investigations_abstained", 0),
        proposals_generated=getattr(ai, "proposals_generated", 0),
        proposals_gate_passed=getattr(ai, "proposals_gate_passed", 0),
        proposals_gate_failed=getattr(ai, "proposals_gate_failed", 0),
        total_tool_calls=getattr(ai, "total_tool_calls", 0),
        token_usage=getattr(ai, "token_usage", 0),
        timeout_count=getattr(ai, "timeout_count", 0),
        budget_exhaustion_count=getattr(ai, "budget_exhaustion_count", 0),
        malformed_output_count=getattr(ai, "malformed_output_count", 0),
        tool_failure_count=getattr(ai, "tool_failure_count", 0),
    )

    timing_out = BenchmarkTimingOut(
        pipeline_duration_seconds=getattr(timing, "pipeline_duration_seconds", 0.0),
        timing_boundary=getattr(timing, "timing_boundary", "N/A"),
    )

    case_eval_outs: list[CaseEvaluationOut] = []
    for c in cases:
        fam_val = (
            c.scenario_family.value
            if hasattr(c.scenario_family, "value")
            else str(c.scenario_family)
        )
        res_val = (
            c.resolvability.value if hasattr(c.resolvability, "value") else str(c.resolvability)
        )
        disp_val = c.disposition.value if hasattr(c.disposition, "value") else str(c.disposition)
        case_eval_outs.append(
            CaseEvaluationOut(
                case_id=c.case_id,
                scenario_family=fam_val,
                resolvability=res_val,
                disposition=disp_val,
                gate_passed=c.gate_passed,
                failing_check=c.failing_check,
                actual_target_ids=list(c.actual_target_ids),
                expected_target_ids=list(c.expected_target_ids),
                is_correct_auto_resolution=c.is_correct_auto_resolution,
                is_false_auto_resolution=c.is_false_auto_resolution,
                is_correct_outcome=c.is_correct_outcome,
                notes=c.notes,
            )
        )

    return BenchmarkRunOut(
        run_id=run.run_id,
        seed=run.seed,
        dataset_version=run.dataset_version,
        rule_version=run.rule_version,
        code_revision=run.code_revision,
        model_version=run.model_version,
        prompt_version=run.prompt_version,
        policy_version=run.policy_version,
        arm=run.arm,
        total_cases=getattr(overall, "total_cases", int(metrics_dict.get("total_cases", 0))),
        auto_resolved=getattr(overall, "auto_resolved", int(metrics_dict.get("auto_resolved", 0))),
        human_review=getattr(overall, "human_review", int(metrics_dict.get("human_review", 0))),
        unresolved=getattr(overall, "unresolved", int(metrics_dict.get("unresolved", 0))),
        resolution_rate=getattr(
            overall, "resolution_rate", float(metrics_dict.get("resolution_rate", 0.0))
        ),
        auto_resolution_rate=getattr(
            overall, "auto_resolution_rate", float(metrics_dict.get("auto_resolution_rate", 0.0))
        ),
        human_review_rate=getattr(
            overall, "human_review_rate", float(metrics_dict.get("human_review_rate", 0.0))
        ),
        unresolved_rate=getattr(
            overall, "unresolved_rate", float(metrics_dict.get("unresolved_rate", 0.0))
        ),
        correct_auto_resolutions=getattr(
            overall,
            "correct_auto_resolutions",
            int(metrics_dict.get("correct_auto_resolutions", 0)),
        ),
        false_auto_resolutions=getattr(
            overall, "false_auto_resolutions", int(metrics_dict.get("false_auto_resolutions", 0))
        ),
        exact_target_set_accuracy=getattr(
            overall,
            "exact_target_set_accuracy",
            float(metrics_dict.get("exact_target_set_accuracy", 1.0)),
        ),
        zero_false_auto_resolution=getattr(
            overall,
            "zero_false_auto_resolution",
            bool(metrics_dict.get("zero_false_auto_resolution", 1.0)),
        ),
        safety_gate_passed=getattr(
            overall, "safety_gate_passed", bool(metrics_dict.get("safety_gate_passed", 1.0))
        ),
        false_auto_resolution_count=getattr(
            overall,
            "false_auto_resolution_count",
            int(metrics_dict.get("false_auto_resolution_count", 0)),
        ),
        correct_auto_resolution_count=getattr(
            overall,
            "correct_auto_resolution_count",
            int(metrics_dict.get("correct_auto_resolution_count", 0)),
        ),
        auto_resolution_count=getattr(
            overall, "auto_resolution_count", int(metrics_dict.get("auto_resolution_count", 0))
        ),
        records_per_minute=getattr(
            overall, "records_per_minute", float(metrics_dict.get("records_per_minute", 0.0))
        ),
        metrics=metrics_dict,
        timing=timing_out,
        scenario_matrix=family_rows,
        ai_metrics=ai_out,
        case_evaluations=case_eval_outs,
    )


def serialize_fingerprint(fp: ExceptionFingerprint) -> ExceptionFingerprintOut:
    return ExceptionFingerprintOut(
        exception_type=fp.exception_type.value,
        failing_check=fp.failing_check,
        operational_category=fp.operational_category.value,
        candidate_count_bucket=fp.candidate_count_bucket,
        dominant_provenance=fp.dominant_provenance.value if fp.dominant_provenance else None,
        currency=fp.currency.value,
        has_delta=fp.has_delta,
        disposition=fp.disposition.value,
        fingerprint_key=fp.fingerprint_key,
    )


def serialize_cluster_summary(cluster: ExceptionCluster) -> ExceptionClusterSummaryOut:
    return ExceptionClusterSummaryOut(
        cluster_key=cluster.cluster_key,
        cluster_name=cluster.cluster_name,
        operational_category=cluster.operational_category.value,
        case_count=cluster.case_count,
        percentage_of_exceptions=cluster.percentage_of_exceptions,
        affected_settlement_net_minor=cluster.affected_settlement_net_minor,
        affected_delta_minor=cluster.affected_delta_minor,
        currency=cluster.currency.value,
        first_seen=cluster.first_seen.isoformat(),
        last_seen=cluster.last_seen.isoformat(),
        is_recurring=cluster.is_recurring,
        dominant_classification=cluster.dominant_classification.value,
        dominant_failing_gate=cluster.dominant_failing_gate,
        disposition_counts=dict(cluster.disposition_counts),
        representative_case_ids=list(cluster.representative_case_ids),
        description=cluster.description,
        suggested_remediation=cluster.suggested_remediation,
    )


def serialize_cluster_detail(cluster: ExceptionCluster) -> ExceptionClusterDetailOut:
    summary = serialize_cluster_summary(cluster)
    return ExceptionClusterDetailOut(
        **summary.model_dump(),
        fingerprint=serialize_fingerprint(cluster.fingerprint),
        case_ids=list(cluster.case_ids),
    )


def serialize_exception_intelligence(
    summary: ExceptionIntelligenceSummary,
) -> ExceptionIntelligenceResponse:
    return ExceptionIntelligenceResponse(
        total_settlements=summary.total_settlements,
        total_exceptions=summary.total_exceptions,
        total_clusters=summary.total_clusters,
        recurring_clusters=summary.recurring_clusters,
        total_affected_settlement_net_minor=summary.total_affected_settlement_net_minor,
        total_affected_delta_minor=summary.total_affected_delta_minor,
        currency=summary.currency.value,
        clusters=[serialize_cluster_summary(c) for c in summary.clusters],
    )


# Phase 7: Gate Intelligence Serializers
def serialize_gate_explanation(exp: GateExplanation) -> GateExplanationOut:
    return GateExplanationOut(
        check_name=exp.check_name,
        summary=exp.summary,
        description=exp.description,
        eligibility_requirement=exp.eligibility_requirement,
        is_automation_blocker=exp.is_automation_blocker,
    )


def serialize_automation_blocker(b: AutomationBlocker) -> AutomationBlockerOut:
    return AutomationBlockerOut(
        rank=b.rank,
        check_name=b.check_name,
        failure_count=b.failure_count,
        affected_cases=b.affected_cases,
        affected_settlement_net_minor=b.affected_settlement_net_minor,
        affected_delta_minor=b.affected_delta_minor,
        currency=b.currency.value,
        percentage_of_blocked_cases=b.percentage_of_blocked_cases,
        explanation=serialize_gate_explanation(b.explanation),
        top_cluster_name=b.top_cluster_name,
        top_cluster_key=b.top_cluster_key,
        representative_case_ids=list(b.representative_case_ids),
    )


def serialize_gate_check_breakdown(b: GateCheckBreakdown) -> GateCheckBreakdownOut:
    return GateCheckBreakdownOut(
        check_name=b.check_name,
        evaluation_count=b.evaluation_count,
        failure_count=b.failure_count,
        failure_rate=b.failure_rate,
        affected_case_count=b.affected_case_count,
        affected_settlement_net_minor=b.affected_settlement_net_minor,
        affected_delta_minor=b.affected_delta_minor,
        currency=b.currency.value,
        disposition_counts=dict(b.disposition_counts),
        explanation=serialize_gate_explanation(b.explanation),
        related_cluster_keys=list(b.related_cluster_keys),
        representative_case_ids=list(b.representative_case_ids),
    )


def serialize_controller_gate_outcome(o: ControllerGateOutcome) -> ControllerGateOutcomeOut:
    return ControllerGateOutcomeOut(
        case_id=o.case_id,
        settlement_id=o.settlement_id,
        run_id=o.run_id,
        disposition=o.disposition.value,
        passed=o.passed,
        failing_check=o.failing_check,
        hypothesis_source=o.hypothesis_source.value,
        expected_settlement_net_minor=o.expected_settlement_net_minor,
        observed_ledger_net_minor=o.observed_ledger_net_minor,
        delta_minor=o.delta_minor,
        currency=o.currency.value,
        cluster_key=o.cluster_key,
        operational_category=o.operational_category,
        explanation=serialize_gate_explanation(o.explanation) if o.explanation else None,
        failure_reason=o.failure_reason,
    )


def serialize_gate_intelligence(summary: GateIntelligenceSummary) -> GateIntelligenceResponse:
    return GateIntelligenceResponse(
        total_evaluations=summary.total_evaluations,
        total_cases=summary.total_cases,
        passed_cases=summary.passed_cases,
        failed_cases=summary.failed_cases,
        pass_rate=summary.pass_rate,
        fail_rate=summary.fail_rate,
        total_settlement_net_minor=summary.total_settlement_net_minor,
        total_affected_settlement_net_minor=summary.total_affected_settlement_net_minor,
        total_affected_delta_minor=summary.total_affected_delta_minor,
        currency=summary.currency.value,
        disposition_breakdown=dict(summary.disposition_breakdown),
        automation_blockers=[serialize_automation_blocker(b) for b in summary.automation_blockers],
        check_breakdowns=[serialize_gate_check_breakdown(b) for b in summary.check_breakdowns],
        top_blocker=summary.top_blocker,
    )


def serialize_operational_confidence(
    summary: OperationalConfidenceSummary,
) -> OperationalConfidenceResponse:
    return OperationalConfidenceResponse(
        total_cases=summary.total_cases,
        hypotheses_evaluated=summary.hypotheses_evaluated,
        average_confidence=summary.average_confidence,
        high_confidence_count=summary.high_confidence_count,
        medium_confidence_count=summary.medium_confidence_count,
        low_confidence_count=summary.low_confidence_count,
        high_confidence_gate_blocked_count=summary.high_confidence_gate_blocked_count,
        buckets=[
            OperationalConfidenceBucketOut(
                bin_lower=b.bin_lower,
                bin_upper=b.bin_upper,
                bin_label=b.bin_label,
                hypothesis_count=b.hypothesis_count,
                average_confidence=b.average_confidence,
                gate_pass_count=b.gate_pass_count,
                gate_fail_count=b.gate_fail_count,
            )
            for b in summary.buckets
        ],
        gate_tiers=[
            GateTierSummaryOut(
                tier=gt.tier,
                confidence_range=gt.confidence_range,
                total_count=gt.total_count,
                gate_pass_count=gt.gate_pass_count,
                gate_fail_count=gt.gate_fail_count,
                pass_rate_pct=gt.pass_rate_pct,
                failing_check_counts=list(gt.failing_check_counts),
            )
            for gt in summary.gate_tiers
        ],
        check_contexts=[
            CheckConfidenceContextOut(
                check_name=cc.check_name,
                case_count=cc.case_count,
                average_confidence=cc.average_confidence,
                min_confidence=cc.min_confidence,
                max_confidence=cc.max_confidence,
            )
            for cc in summary.check_contexts
        ],
    )


def serialize_benchmark_confidence(run_id: str, report: Any) -> BenchmarkConfidenceResponse:
    """Safely serializes a Benchmark ConfidenceReport using introspection."""
    buckets_out = [
        ConfidenceBucketOut(
            bin_lower=b.bin_lower,
            bin_upper=b.bin_upper,
            bin_label=b.bin_label,
            observation_count=b.observation_count,
            correct_count=b.correct_count,
            incorrect_count=b.incorrect_count,
            abstention_count=b.abstention_count,
            empirical_accuracy=b.empirical_accuracy,
            average_confidence=b.average_confidence,
            gate_pass_count=b.gate_pass_count,
            gate_fail_count=b.gate_fail_count,
        )
        for b in getattr(report, "buckets", ())
    ]

    thresholds_out = [
        ThresholdMetricOut(
            threshold=t.threshold,
            predictions_meeting_threshold=t.predictions_meeting_threshold,
            correct_predictions=t.correct_predictions,
            incorrect_predictions=t.incorrect_predictions,
            precision=t.precision,
            coverage=t.coverage,
            false_auto_count_if_trusted_alone=t.false_auto_count_if_trusted_alone,
        )
        for t in getattr(report, "thresholds", ())
    ]

    gate_matrix_out = [
        GateConfidenceCellOut(
            tier=c.tier,
            confidence_range=c.confidence_range,
            total_count=c.total_count,
            gate_pass_count=c.gate_pass_count,
            gate_fail_count=c.gate_fail_count,
            dominant_failing_checks=list(c.dominant_failing_checks),
        )
        for c in getattr(report, "gate_matrix", ())
    ]

    source_metrics_out = []
    for s in getattr(report, "source_metrics", ()):
        src_buckets = [
            ConfidenceBucketOut(
                bin_lower=sb.bin_lower,
                bin_upper=sb.bin_upper,
                bin_label=sb.bin_label,
                observation_count=sb.observation_count,
                correct_count=sb.correct_count,
                incorrect_count=sb.incorrect_count,
                abstention_count=sb.abstention_count,
                empirical_accuracy=sb.empirical_accuracy,
                average_confidence=sb.average_confidence,
                gate_pass_count=sb.gate_pass_count,
                gate_fail_count=sb.gate_fail_count,
            )
            for sb in getattr(s, "buckets", ())
        ]
        source_metrics_out.append(
            SourceConfidenceMetricOut(
                source=s.source,
                observation_count=s.observation_count,
                average_confidence=s.average_confidence,
                precision=s.precision,
                coverage=s.coverage,
                ece=s.ece,
                brier_score=s.brier_score,
                abstention_rate=s.abstention_rate,
                gate_pass_rate=s.gate_pass_rate,
                buckets=src_buckets,
            )
        )

    scenario_metrics_out = [
        FamilyConfidenceMetricOut(
            scenario_family=(
                sc.scenario_family.value
                if hasattr(sc.scenario_family, "value")
                else str(sc.scenario_family)
            ),
            observation_count=sc.observation_count,
            average_confidence=sc.average_confidence,
            precision=sc.precision,
            coverage=sc.coverage,
            gate_pass_rate=sc.gate_pass_rate,
            abstention_rate=sc.abstention_rate,
        )
        for sc in getattr(report, "scenario_metrics", ())
    ]

    opp = getattr(report, "automation_opportunity", None)
    opp_out = AutomationOpportunityOut(
        threshold=getattr(opp, "threshold", 0.8),
        opportunity_count=getattr(opp, "opportunity_count", 0),
        affected_settlement_net_minor=getattr(opp, "affected_settlement_net_minor", 0),
        currency=getattr(opp, "currency", "INR"),
        failing_gate_checks=list(getattr(opp, "failing_gate_checks", ())),
        current_dispositions=list(getattr(opp, "current_dispositions", ())),
        sample_case_ids=list(getattr(opp, "sample_case_ids", ())),
    )

    return BenchmarkConfidenceResponse(
        run_id=run_id,
        total_observations=getattr(report, "total_observations", 0),
        overall_ece=getattr(report, "overall_ece", 0.0),
        overall_brier_score=getattr(report, "overall_brier_score", 0.0),
        buckets=buckets_out,
        thresholds=thresholds_out,
        gate_matrix=gate_matrix_out,
        source_metrics=source_metrics_out,
        scenario_metrics=scenario_metrics_out,
        automation_opportunity=opp_out,
    )
