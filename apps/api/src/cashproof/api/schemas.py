"""API-boundary-only Pydantic request/response models.

These shape HTTP JSON in and out; they carry no domain/application logic
themselves - all decisions are made by cashproof.application before a
response model is ever constructed.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CaseSummary(BaseModel):
    settlement_id: str
    expected_net_minor: int
    observed_net_minor: int
    delta_minor: int
    exception_type: str
    candidate_count: int
    disposition: str


class CandidateOut(BaseModel):
    ledger_entry_id: str
    score: float
    matched_signals: list[str]
    rule_trace: list[str]
    provenance: str


class EvidenceOut(BaseModel):
    entity_type: str
    entity_id: str
    field: str
    relevance: float
    stance: str
    decision_consumed: bool


class GateCheckOut(BaseModel):
    name: str
    passed: bool
    reason: str
    is_mandatory: bool


class GateOut(BaseModel):
    passed: bool
    failing_check: str | None
    checks: list[GateCheckOut]
    proposed_target_ids: list[str]
    proposed_target_net_minor: int | None
    variance_minor: int | None


class BridgeOut(BaseModel):
    gross_minor: int
    fee_minor: int
    tax_on_fee_minor: int
    netted_refund_minor: int
    adjustment_minor: int
    computed_net_minor: int
    expected_net_minor: int


class ResolutionOut(BaseModel):
    disposition: str
    target_ledger_entry_ids: list[str]
    reviewer: str | None
    review_outcome: str | None
    reviewed_at: str | None


class AuditEventOut(BaseModel):
    event_id: str
    entity_type: str
    event_type: str
    actor: str
    timestamp: str
    metadata: dict[str, str]


class CaseDetail(CaseSummary):
    currency: str
    settled_at: str
    bridge: BridgeOut
    candidates: list[CandidateOut]
    evidence: list[EvidenceOut]
    gate: GateOut
    resolution: ResolutionOut
    audit_events: list[AuditEventOut]


class ReviewRequest(BaseModel):
    decision: Literal["approve", "reject", "pending"]
    selected_target_ids: list[str] = Field(default_factory=list)
    reviewer: str


class ToolCallOut(BaseModel):
    tool_name: str
    arguments: dict[str, str]
    response_summary: str
    duration_ms: int


class InvestigationOut(BaseModel):
    investigation_id: str
    stop_reason: str
    tool_calls: list[ToolCallOut]
    candidates_considered: list[str]


class ProposalOut(BaseModel):
    proposal_id: str
    target_ledger_entry_ids: list[str]
    rationale: str
    confidence: float
    evidence: list[EvidenceOut]


class InvestigationResult(BaseModel):
    case_id: str
    investigation: InvestigationOut
    proposal: ProposalOut | None
    preview_gate: GateOut | None


class ErrorResponse(BaseModel):
    detail: str


# Phase 9: Ingestion schemas
class ConnectorStatusResponse(BaseModel):
    connector_name: str
    configured: bool
    detail: str


class IngestionStatusResponse(BaseModel):
    connectors: list[ConnectorStatusResponse]


class IngestionTriggerRequest(BaseModel):
    year: int
    month: int


class IngestionRunOut(BaseModel):
    run_id: str
    source: str
    status: str
    fetched_count: int
    accepted_count: int
    rejected_count: int
    duplicate_count: int
    validation_errors: list[str]
    failure_reason: str | None
    started_at: str
    completed_at: str


class BankStatementIngestionResponse(IngestionRunOut):
    """Same shape as IngestionRunOut; named separately per the bank upload contract."""


class BenchmarkRunRequest(BaseModel):
    seed: int = 42
    num_settlements: int = 100
    run_id: str | None = None
    arm: str = "deterministic"


class FamilyMetricOut(BaseModel):
    scenario_family: str
    total: int
    auto_resolved: int
    human_review: int
    unresolved: int
    correct_outcomes: int
    false_auto_resolutions: int


class AIMetricOut(BaseModel):
    investigations_started: int = 0
    investigations_completed: int = 0
    investigations_failed: int = 0
    investigations_abstained: int = 0
    proposals_generated: int = 0
    proposals_gate_passed: int = 0
    proposals_gate_failed: int = 0
    total_tool_calls: int = 0
    token_usage: int = 0
    timeout_count: int = 0
    budget_exhaustion_count: int = 0
    malformed_output_count: int = 0
    tool_failure_count: int = 0


class CaseEvaluationOut(BaseModel):
    case_id: str
    scenario_family: str
    resolvability: str
    disposition: str
    gate_passed: bool
    failing_check: str | None
    actual_target_ids: list[str]
    expected_target_ids: list[str]
    is_correct_auto_resolution: bool
    is_false_auto_resolution: bool
    is_correct_outcome: bool
    notes: str | None = None


class BenchmarkTimingOut(BaseModel):
    pipeline_duration_seconds: float
    timing_boundary: str


class BenchmarkRunOut(BaseModel):
    run_id: str
    seed: int
    dataset_version: str
    rule_version: str
    code_revision: str
    model_version: str | None
    prompt_version: str | None
    policy_version: str
    arm: str
    total_cases: int
    auto_resolved: int
    human_review: int
    unresolved: int
    resolution_rate: float
    auto_resolution_rate: float
    human_review_rate: float
    unresolved_rate: float
    correct_auto_resolutions: int
    false_auto_resolutions: int
    exact_target_set_accuracy: float
    zero_false_auto_resolution: bool
    safety_gate_passed: bool
    false_auto_resolution_count: int
    correct_auto_resolution_count: int
    auto_resolution_count: int
    records_per_minute: float
    metrics: dict[str, float]
    timing: BenchmarkTimingOut
    scenario_matrix: list[FamilyMetricOut]
    ai_metrics: AIMetricOut
    case_evaluations: list[CaseEvaluationOut]


class ExceptionFingerprintOut(BaseModel):
    exception_type: str
    failing_check: str | None
    operational_category: str
    candidate_count_bucket: str
    dominant_provenance: str | None
    currency: str
    has_delta: bool
    disposition: str
    fingerprint_key: str


class ExceptionClusterSummaryOut(BaseModel):
    cluster_key: str
    cluster_name: str
    operational_category: str
    case_count: int
    percentage_of_exceptions: float
    affected_settlement_net_minor: int
    affected_delta_minor: int
    currency: str
    first_seen: str
    last_seen: str
    is_recurring: bool
    dominant_classification: str
    dominant_failing_gate: str | None
    disposition_counts: dict[str, int]
    representative_case_ids: list[str]
    description: str
    suggested_remediation: str


class ExceptionClusterDetailOut(ExceptionClusterSummaryOut):
    fingerprint: ExceptionFingerprintOut
    case_ids: list[str]


class ExceptionIntelligenceResponse(BaseModel):
    total_settlements: int
    total_exceptions: int
    total_clusters: int
    recurring_clusters: int
    total_affected_settlement_net_minor: int
    total_affected_delta_minor: int
    currency: str
    clusters: list[ExceptionClusterSummaryOut]


class CaseClusterOut(BaseModel):
    settlement_id: str
    cluster_key: str
    cluster_name: str
    operational_category: str
    case_count: int
    is_recurring: bool


# Phase 7: Gate Intelligence Schemas
class GateExplanationOut(BaseModel):
    check_name: str
    summary: str
    description: str
    eligibility_requirement: str
    is_automation_blocker: bool


class AutomationBlockerOut(BaseModel):
    rank: int
    check_name: str
    failure_count: int
    affected_cases: int
    affected_settlement_net_minor: int
    affected_delta_minor: int
    currency: str
    percentage_of_blocked_cases: float
    explanation: GateExplanationOut
    top_cluster_name: str | None
    top_cluster_key: str | None
    representative_case_ids: list[str]


class GateCheckBreakdownOut(BaseModel):
    check_name: str
    evaluation_count: int
    failure_count: int
    failure_rate: float
    affected_case_count: int
    affected_settlement_net_minor: int
    affected_delta_minor: int
    currency: str
    disposition_counts: dict[str, int]
    explanation: GateExplanationOut
    related_cluster_keys: list[str]
    representative_case_ids: list[str]


class ControllerGateOutcomeOut(BaseModel):
    case_id: str
    settlement_id: str
    run_id: str
    disposition: str
    passed: bool
    failing_check: str | None
    hypothesis_source: str
    expected_settlement_net_minor: int
    observed_ledger_net_minor: int | None
    delta_minor: int
    currency: str
    cluster_key: str | None
    operational_category: str | None
    explanation: GateExplanationOut | None
    failure_reason: str | None


class GateIntelligenceResponse(BaseModel):
    total_evaluations: int
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    fail_rate: float
    total_settlement_net_minor: int
    total_affected_settlement_net_minor: int
    total_affected_delta_minor: int
    currency: str
    disposition_breakdown: dict[str, int]
    automation_blockers: list[AutomationBlockerOut]
    check_breakdowns: list[GateCheckBreakdownOut]
    top_blocker: str | None


# Phase 8: Confidence Calibration & Automation Quality Schemas
class OperationalConfidenceBucketOut(BaseModel):
    bin_lower: float
    bin_upper: float
    bin_label: str
    hypothesis_count: int
    average_confidence: float
    gate_pass_count: int
    gate_fail_count: int


class GateTierSummaryOut(BaseModel):
    tier: str
    confidence_range: str
    total_count: int
    gate_pass_count: int
    gate_fail_count: int
    pass_rate_pct: float
    failing_check_counts: list[tuple[str, int]]


class CheckConfidenceContextOut(BaseModel):
    check_name: str
    case_count: int
    average_confidence: float
    min_confidence: float
    max_confidence: float


class OperationalConfidenceResponse(BaseModel):
    total_cases: int
    hypotheses_evaluated: int
    average_confidence: float
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    high_confidence_gate_blocked_count: int
    buckets: list[OperationalConfidenceBucketOut]
    gate_tiers: list[GateTierSummaryOut]
    check_contexts: list[CheckConfidenceContextOut]


class ConfidenceBucketOut(BaseModel):
    bin_lower: float
    bin_upper: float
    bin_label: str
    observation_count: int
    correct_count: int
    incorrect_count: int
    abstention_count: int
    empirical_accuracy: float
    average_confidence: float
    gate_pass_count: int
    gate_fail_count: int


class ThresholdMetricOut(BaseModel):
    threshold: float
    predictions_meeting_threshold: int
    correct_predictions: int
    incorrect_predictions: int
    precision: float
    coverage: float
    false_auto_count_if_trusted_alone: int


class GateConfidenceCellOut(BaseModel):
    tier: str
    confidence_range: str
    total_count: int
    gate_pass_count: int
    gate_fail_count: int
    dominant_failing_checks: list[tuple[str, int]]


class FamilyConfidenceMetricOut(BaseModel):
    scenario_family: str
    observation_count: int
    average_confidence: float
    precision: float
    coverage: float
    gate_pass_rate: float
    abstention_rate: float


class SourceConfidenceMetricOut(BaseModel):
    source: str
    observation_count: int
    average_confidence: float
    precision: float
    coverage: float
    ece: float
    brier_score: float
    abstention_rate: float
    gate_pass_rate: float
    buckets: list[ConfidenceBucketOut]


class AutomationOpportunityOut(BaseModel):
    threshold: float
    opportunity_count: int
    affected_settlement_net_minor: int
    currency: str
    failing_gate_checks: list[tuple[str, int]]
    current_dispositions: list[tuple[str, int]]
    sample_case_ids: list[str]


class BenchmarkConfidenceResponse(BaseModel):
    run_id: str
    total_observations: int
    overall_ece: float
    overall_brier_score: float
    buckets: list[ConfidenceBucketOut]
    thresholds: list[ThresholdMetricOut]
    gate_matrix: list[GateConfidenceCellOut]
    source_metrics: list[SourceConfidenceMetricOut]
    scenario_metrics: list[FamilyConfidenceMetricOut]
    automation_opportunity: AutomationOpportunityOut
