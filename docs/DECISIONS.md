# Locked Architecture Decisions

1. Deterministic financial truth.
2. Evidence-first decisions.
3. One bounded investigator; no multi-agent mesh.
4. No Celery/Redis initially.
5. Modular monolith.
6. INR-only MVP with explicit currency.
7. S4/S5 text/alias-derived links route to HUMAN_REVIEW.
8. AUTO_RESOLVED requires exact target-set equality.
9. GroundTruth is evaluator-only and technically isolated from production/AI ports.
10. AI confidence is never a gate input.
11. `case_id` identifies one case instance and is not reused across runs; `settlement_id` is the cross-run comparison key.
12. No exact LLM reproducibility claim.
13. Use `ResolutionProposal`.
14. Adjustment sign: positive increases net, negative decreases net.
15. Candidate windows: +/-7 days reference-backed; +/-3 days S4/S5.
16. Tax is stored as `tax_on_fee_minor`; generator computes 18% once with half-up rounding.
17. Partial grouped matches: exact set may auto-resolve; strict subset fails evidence completeness; default UNRESOLVED; full-set proposal with uniquely plausible unmatched members routes HUMAN_REVIEW.
18. LedgerEntry amount is an unsigned magnitude interpreted by direction.
19. Settlement deposited net equals the sum of settlement-item computed nets.
20. Netted refund total equals the included refunds for that payment.
21. A LedgerEntry may be the final target of at most one Resolution.
22. `rule_version` identifies the deterministic engine code revision used by a benchmark run.
23. Investigator budgets are enforced from the first AI implementation.
24. GroundTruth is available only through benchmark evaluator interfaces.
25. Evidence and failing gate checks must be visible to reviewers in the Exception Center.
26. Exception Intelligence: clustering is 100% deterministic, deriving hashable ExceptionFingerprint from operational exception type, failing gate check, candidate count bucket, dominant provenance, currency, and delta status.
27. GroundTruth isolation in Exception Intelligence: clustering operates strictly on production-visible facts (ReconciliationResult, Settlement) and never accesses evaluator GroundTruth or benchmark scenario definitions.
28. Monetary Aggregation in Exception Intelligence: affected settlement volume (affected_settlement_net_minor) and reconciliation discrepancy (affected_delta_minor) are tracked separately in integer minor units; delta is signed while volume is positive magnitude.
29. Gate Intelligence strictly read-only: Gate Intelligence never recomputes, replaces, or relaxes evaluate_gate(). Zero second gate; no AI in gate decisions.
30. Canonical Evaluation Precedence: Multiple gate evaluations per case (initial matching, AI preview, human review) are canonicalized using result.resolution.governing_gate_evaluation when a resolution exists, or the latest evaluation when pending review, preventing preview gate inflations.
31. Deterministic Explainability Catalog: All 9 mandatory gate checks have deterministic plain-text summaries, technical invariant descriptions, and concrete eligibility requirements ("What must change to become eligible"), fully separated from ground truth.
32. Confidence Separation: Confidence measures statistical hypothesis strength / belief; the deterministic GateEvaluation is the sole authorization mechanism. Confidence is never used as an authorization threshold (`if confidence > 0.9: AUTO_RESOLVE` is strictly forbidden).
33. Two-Tier Confidence Architecture: Evaluator calibration (ECE, Brier score, GroundTruth target set precision, threshold simulation) is strictly isolated within `cashproof.benchmark`; operational confidence distributions (10 standard bins, HIGH/MED/LOW gate tiers, blocker check confidence context) operate purely on production-visible facts in `cashproof.application.confidence` with zero imports of GroundTruth.
34. Automation Opportunity Governance: High-confidence hypotheses whose predicted targets strictly equal evaluator GroundTruth but fail Gate checks (e.g. S3 fee/tax discrepancies) are categorized as "Potential Automation Opportunities" with exact financial blocker attribution; they are never labeled "Safe to automate" and never bypass financial accounting invariants.
35. Razorpay Adapter Boundary: the Razorpay connector lives entirely in `packages/infrastructure/.../razorpay/`, uses httpx, and confines Razorpay-specific field names to a private `_dto` module. The public normalizer converts DTOs to existing domain objects; domain code has zero knowledge of Razorpay field names.
36. Bank Statement Adapter Boundary: CSV bank statement parsing lives in `packages/infrastructure/.../bank/` and is fail-closed - a single malformed row (missing column, invalid amount/timestamp/currency/direction, or a conflicting in-file duplicate) rejects the entire batch via `IngestionValidationError` rather than producing a partially valid, unsafe subset.
37. Ingestion Port (application-defined): `packages/application/ports.py` gains `SourceConnectorPort` (a read-only connector returning a `NormalizedSourceBatch` of existing domain objects) and `IngestionResultStore` (records ingestion run metadata). The application defines the contract; infrastructure provides the implementation.
38. Idempotency via External ID Fingerprint Registry: source records carry stable external IDs (Razorpay `pay_xxx`/`rfnd_xxx`/`setl_xxx`; bank CSV `transaction_id`). `InMemoryCaseStore` gains `ingested_source_fingerprints: dict[str, str]` (an id -> fingerprint-of-critical-fields registry, not a bare set, so a conflicting re-ingestion under the same id can be distinguished from an identical one). Re-ingesting the same external ID with an identical fingerprint is silently idempotent; conflicting data under the same ID raises `DuplicateSourceConflictError` rather than silently overwriting.
39. Ingestion Service (application layer): `cashproof.application.ingestion.IngestionService` orchestrates connector fetch (or an already-parsed batch) -> idempotency check -> accepted-record storage -> `IngestionRun` result. It never runs `BatchReconciler`, never evaluates the gate, never invokes AI, and never reads GroundTruth. Triggering reconciliation over ingested data is a separate, explicit action (`POST /api/reconcile`) against the same unmodified `BatchReconciler` used for synthetic data.
40. IngestionRun Result Model: `IngestionRun` is an application-level dataclass (not a domain entity - no financial invariants) with fields `run_id`, `source`, `status`, `fetched_count`, `accepted_count`, `rejected_count`, `duplicate_count`, `validation_errors`, `failure_reason`, `started_at`, `completed_at`, stored in `InMemoryCaseStore.ingestion_runs`.


