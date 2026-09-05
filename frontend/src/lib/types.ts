export type Disposition = "AUTO_RESOLVED" | "HUMAN_REVIEW" | "UNRESOLVED";

export type ScenarioFamily = "S1" | "S2" | "S3" | "S4" | "S5" | "S6";

export type Stance = "SUPPORTS" | "CONTRADICTS";

export type Provenance =
  | "STRUCTURED_REFERENCE"
  | "EXTERNAL_REFERENCE_TEXT"
  | "NARRATION_ALIAS_TEXT";

export interface CaseRow {
  settlement_id: string;
  expected_net_minor: number;
  observed_net_minor: number;
  delta_minor: number;
  exception_type: string;
  candidate_count: number;
  disposition: Disposition;
  /**
   * Demo/evaluator-only label, present only in the static demo-data.json snapshot
   * (Overview/Cases/Scenarios pages). The live review API never returns this -
   * production code must never expose ScenarioFamily/GroundTruth.
   */
  scenario_family?: ScenarioFamily | null;
}

export interface Candidate {
  ledger_entry_id: string;
  score: number;
  matched_signals: string[];
  rule_trace: string[];
  provenance: Provenance;
}

export interface EvidenceItem {
  entity_type: string;
  entity_id: string;
  field: string;
  relevance: number;
  stance: Stance;
  decision_consumed: boolean;
}

export interface GateCheck {
  name: string;
  passed: boolean;
  reason: string;
  is_mandatory: boolean;
}

export interface GateResult {
  passed: boolean;
  failing_check: string | null;
  checks: GateCheck[];
  /** Gate-level observation: entries actually proposed as the hypothesis target. */
  proposed_target_ids: string[];
  /** Gate-level observation: net amount of the proposed target set (evaluate_gate's own bridge). */
  proposed_target_net_minor: number | null;
  /** Gate-level observation: expected net minus proposed_target_net_minor. */
  variance_minor: number | null;
}

export interface Bridge {
  gross_minor: number;
  fee_minor: number;
  tax_on_fee_minor: number;
  netted_refund_minor: number;
  adjustment_minor: number;
  computed_net_minor: number;
  expected_net_minor: number;
}

export interface AuditEvent {
  event_id: string;
  entity_type: string;
  event_type: string;
  actor: string;
  timestamp: string;
  metadata: Record<string, string>;
}

export interface CaseDetail extends CaseRow {
  currency: string;
  settled_at: string;
  bridge: Bridge;
  candidates: Candidate[];
  evidence: EvidenceItem[];
  gate: GateResult;
  resolution: {
    disposition: Disposition;
    target_ledger_entry_ids: string[];
    reviewer?: string | null;
    review_outcome?: "APPROVED" | "REJECTED" | "PENDING" | null;
    reviewed_at?: string | null;
  };
  audit_events: AuditEvent[];
}

export type StopReason =
  | "COMPLETED"
  | "BUDGET_EXHAUSTED"
  | "TIMEOUT"
  | "TOOL_FAILURE"
  | "MALFORMED_OUTPUT";

export interface ToolCall {
  tool_name: string;
  arguments: Record<string, string>;
  response_summary: string;
  duration_ms: number;
}

export interface Investigation {
  investigation_id: string;
  stop_reason: StopReason;
  tool_calls: ToolCall[];
  candidates_considered: string[];
}

export interface ResolutionProposal {
  proposal_id: string;
  target_ledger_entry_ids: string[];
  rationale: string;
  confidence: number;
  evidence: EvidenceItem[];
}

export interface InvestigationResult {
  case_id: string;
  investigation: Investigation;
  proposal: ResolutionProposal | null;
  preview_gate: GateResult | null;
}

export interface Overview {
  total_settlements: number;
  auto_resolved: number;
  human_review: number;
  unresolved: number;
  false_auto_resolutions: number;
}

export interface DemoData {
  meta: {
    run_id: string;
    generated_at: string;
    seed: number;
    num_settlements: number;
    generator_version: string | null;
  };
  overview: Overview;
  cases: CaseRow[];
  case_detail: Record<string, CaseDetail>;
  scenario_examples: Record<ScenarioFamily, string>;
}

// Phase 4: Benchmark Evaluator Types
export interface ScenarioMetric {
  scenario_family: ScenarioFamily;
  total: number;
  auto_resolved: number;
  human_review: number;
  unresolved: number;
  correct_outcomes: number;
  false_auto_resolutions: number;
}

export interface AIMetric {
  investigations_started: number;
  investigations_completed: number;
  investigations_failed: number;
  investigations_abstained: number;
  proposals_generated: number;
  proposals_gate_passed: number;
  proposals_gate_failed: number;
  total_tool_calls: number;
  token_usage: number;
  timeout_count: number;
  budget_exhaustion_count: number;
  malformed_output_count: number;
  tool_failure_count: number;
}

export interface CaseEvaluation {
  case_id: string;
  scenario_family: ScenarioFamily;
  resolvability: "PROVABLE" | "NOT_PROVABLE";
  disposition: Disposition;
  gate_passed: boolean;
  failing_check: string | null;
  actual_target_ids: string[];
  expected_target_ids: string[];
  is_correct_auto_resolution: boolean;
  is_false_auto_resolution: boolean;
  is_correct_outcome: boolean;
  notes: string | null;
}

export interface BenchmarkTiming {
  pipeline_duration_seconds: number;
  timing_boundary: string;
}

export interface BenchmarkRunResponse {
  run_id: string;
  seed: number;
  dataset_version: string;
  rule_version: string;
  code_revision: string;
  model_version: string | null;
  prompt_version: string | null;
  policy_version: string;
  arm: string;
  total_cases: number;
  auto_resolved: number;
  human_review: number;
  unresolved: number;
  resolution_rate: number;
  auto_resolution_rate: number;
  human_review_rate: number;
  unresolved_rate: number;
  correct_auto_resolutions: number;
  false_auto_resolutions: number;
  exact_target_set_accuracy: number;
  zero_false_auto_resolution: boolean;
  safety_gate_passed: boolean;
  false_auto_resolution_count: number;
  correct_auto_resolution_count: number;
  auto_resolution_count: number;
  records_per_minute: number;
  metrics: Record<string, number>;
  timing: BenchmarkTiming;
  scenario_matrix: ScenarioMetric[];
  ai_metrics: AIMetric;
  case_evaluations: CaseEvaluation[];
}

// Phase 6: Exception Intelligence & Clustering Types
export type OperationalCategory =
  | "REFERENCE_AMBIGUITY"
  | "AMOUNT_INCONSISTENCY"
  | "UNSTRUCTURED_REFERENCE"
  | "MISSING_RECORD"
  | "EVIDENCE_CONFLICT"
  | "POLICY_REVIEW"
  | "OTHER";

export interface ExceptionFingerprint {
  exception_type: string;
  failing_check: string | null;
  operational_category: OperationalCategory;
  candidate_count_bucket: string;
  dominant_provenance: string | null;
  currency: string;
  has_delta: boolean;
  disposition: Disposition;
  fingerprint_key: string;
}

export interface ExceptionClusterSummary {
  cluster_key: string;
  cluster_name: string;
  fingerprint: ExceptionFingerprint;
  operational_category: OperationalCategory;
  case_count: number;
  percentage_of_exceptions: number;
  affected_settlement_net_minor: number;
  affected_delta_minor: number;
  currency: string;
  first_seen: string;
  last_seen: string;
  is_recurring: boolean;
  dominant_classification: string;
  dominant_failing_gate: string | null;
  disposition_counts: Record<string, number>;
  representative_case_ids: string[];
}

export interface ExceptionClusterDetail extends ExceptionClusterSummary {
  description: string;
  suggested_remediation: string;
  case_ids: string[];
}

export interface ExceptionIntelligenceResponse {
  total_settlements: number;
  total_exceptions: number;
  total_clusters: number;
  recurring_clusters: number;
  total_affected_settlement_net_minor: number;
  total_affected_delta_minor: number;
  currency: string;
  clusters: ExceptionClusterSummary[];
}

export interface CaseCluster {
  settlement_id: string;
  cluster_key: string;
  cluster_name: string;
  operational_category: OperationalCategory;
  case_count: number;
  is_recurring: boolean;
}

// Phase 7: Gate Intelligence & Controller Explainability Types
export interface GateExplanation {
  check_name: string;
  summary: string;
  description: string;
  eligibility_requirement: string;
  is_automation_blocker: boolean;
}

export interface AutomationBlocker {
  rank: number;
  check_name: string;
  failure_count: number;
  affected_cases: number;
  affected_settlement_net_minor: number;
  affected_delta_minor: number;
  currency: string;
  percentage_of_blocked_cases: number;
  explanation: GateExplanation;
  top_cluster_name: string | null;
  top_cluster_key: string | null;
  representative_case_ids: string[];
}

export interface GateCheckBreakdown {
  check_name: string;
  evaluation_count: number;
  failure_count: number;
  failure_rate: number;
  affected_case_count: number;
  affected_settlement_net_minor: number;
  affected_delta_minor: number;
  currency: string;
  disposition_counts: Record<string, number>;
  explanation: GateExplanation;
  related_cluster_keys: string[];
  representative_case_ids: string[];
}

export interface ControllerGateOutcome {
  case_id: string;
  settlement_id: string;
  run_id: string;
  disposition: Disposition;
  passed: boolean;
  failing_check: string | null;
  hypothesis_source: string;
  expected_settlement_net_minor: number;
  observed_ledger_net_minor: number | null;
  delta_minor: number;
  currency: string;
  cluster_key: string | null;
  operational_category: string | null;
  explanation: GateExplanation | null;
  failure_reason: string | null;
}

export interface GateIntelligenceResponse {
  total_evaluations: number;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  pass_rate: number;
  fail_rate: number;
  total_settlement_net_minor: number;
  total_affected_settlement_net_minor: number;
  total_affected_delta_minor: number;
  currency: string;
  disposition_breakdown: Record<string, number>;
  automation_blockers: AutomationBlocker[];
  check_breakdowns: GateCheckBreakdown[];
  top_blocker: string | null;
}

// Phase 8: Confidence Intelligence Types

export interface OperationalHypothesis {
  case_id: string;
  settlement_id: string;
  source: string;
  confidence: number;
  gate_passed: boolean;
  disposition: string;
  failing_check: string | null;
  currency: string;
  amount_minor: number;
}

export interface OperationalConfidenceBucket {
  bin_lower: number;
  bin_upper: number;
  bin_label: string;
  hypothesis_count: number;
  average_confidence: number;
  gate_pass_count: number;
  gate_fail_count: number;
}

export interface GateTierSummary {
  tier: string;
  confidence_range: string;
  total_count: number;
  gate_pass_count: number;
  gate_fail_count: number;
  pass_rate_pct: number;
  failing_check_counts: [string, number][];
}

export interface CheckConfidenceContext {
  check_name: string;
  case_count: number;
  average_confidence: number;
  min_confidence: number;
  max_confidence: number;
}

export interface OperationalConfidenceResponse {
  total_cases: number;
  hypotheses_evaluated: number;
  average_confidence: number;
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
  high_confidence_gate_blocked_count: number;
  buckets: OperationalConfidenceBucket[];
  gate_tiers: GateTierSummary[];
  check_contexts: CheckConfidenceContext[];
}

export interface ConfidenceBucket {
  bin_lower: number;
  bin_upper: number;
  bin_label: string;
  observation_count: number;
  correct_count: number;
  incorrect_count: number;
  abstention_count: number;
  empirical_accuracy: number;
  average_confidence: number;
  gate_pass_count: number;
  gate_fail_count: number;
}

export interface ThresholdMetric {
  threshold: number;
  predictions_meeting_threshold: number;
  correct_predictions: number;
  incorrect_predictions: number;
  precision: number;
  coverage: number;
  false_auto_count_if_trusted_alone: number;
}

export interface GateConfidenceCell {
  tier: string;
  confidence_range: string;
  total_count: number;
  gate_pass_count: number;
  gate_fail_count: number;
  dominant_failing_checks: [string, number][];
}

export interface FamilyConfidenceMetric {
  scenario_family: string;
  observation_count: number;
  average_confidence: number;
  precision: number;
  coverage: number;
  gate_pass_rate: number;
  abstention_rate: number;
}

export interface SourceConfidenceMetric {
  source: string;
  observation_count: number;
  average_confidence: number;
  precision: number;
  coverage: number;
  ece: number;
  brier_score: number;
  abstention_rate: number;
  gate_pass_rate: number;
  buckets: ConfidenceBucket[];
}

export interface AutomationOpportunity {
  threshold: number;
  opportunity_count: number;
  affected_settlement_net_minor: number;
  currency: string;
  failing_gate_checks: [string, number][];
  current_dispositions: [string, number][];
  sample_case_ids: string[];
}

// Phase 9: Ingestion Types
export interface ConnectorStatus {
  connector_name: string;
  configured: boolean;
  detail: string;
}

export interface IngestionStatusResponse {
  connectors: ConnectorStatus[];
}

export interface SettlementReconciliationError {
  settlement_id: string;
  error_type: string;
  message: string;
}

export interface ReconcileResponse {
  cases: CaseRow[];
  failed_settlements: SettlementReconciliationError[];
}

export interface IngestionRun {
  run_id: string;
  source: string;
  status: "COMPLETED" | "FAILED";
  fetched_count: number;
  accepted_count: number;
  rejected_count: number;
  duplicate_count: number;
  validation_errors: string[];
  failure_reason: string | null;
  started_at: string;
  completed_at: string;
}

export interface BenchmarkConfidenceResponse {
  run_id: string;
  total_observations: number;
  predictions_made: number;
  abstentions: number;
  overall_ece: number;
  overall_brier_score: number;
  high_confidence_precision: number;
  potential_automation_opportunities: number;
  potential_automation_volume_minor: number;
  currency: string;
  buckets: ConfidenceBucket[];
  thresholds: ThresholdMetric[];
  gate_matrix: GateConfidenceCell[];
  source_metrics: SourceConfidenceMetric[];
  scenario_metrics: FamilyConfidenceMetric[];
  automation_opportunity: AutomationOpportunity;
}


