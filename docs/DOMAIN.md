# CashProof Domain Model

## Source

### Payment
Immutable: id, order_ref, customer_ref, customer_name, gross_minor, currency, captured_at, status.

### Refund
Immutable: refund_id, payment_id, amount_minor, currency, created_at, status, netted_into_settlement.

### Settlement
Immutable: settlement_id, net_deposited_minor, currency, settled_at.

Invariant:
`net_deposited_minor == sum(SettlementItem.computed_net_minor)`.

### SettlementItem
Immutable: item_id, settlement_id, payment_id, gross_minor, fee_minor, tax_on_fee_minor, netted_refund_minor, adjustment_minor, computed_net_minor.

Invariant:
`gross - fee - tax_on_fee - netted_refund + adjustment == computed_net`.

### LedgerEntry
Immutable: id, amount_minor, currency, timestamp, direction, payment_ref, external_ref, narration, customer_name.

`amount_minor` is a non-negative magnitude.
`direction` is `CREDIT` or `DEBIT`.
When aggregating an entry into `observed_ledger_total`, CREDIT contributes `+amount_minor` and DEBIT contributes `-amount_minor`.

No truth/decoy/noise/scenario flags exist on source records.

### Refund/SettlementItem invariant
For each payment:
`SettlementItem.netted_refund_minor == sum(Refund.amount_minor)` for refunds belonging to that payment with `netted_into_settlement=true` and included in that settlement item.

## Derived

### ReconciliationCase
Fields: case_id, settlement_id, expected_net, observed_ledger_total, delta, exception_type, processing_state, run_id.

One settlement produces one case instance per run.
`expected_net` is sourced from Settlement.net_deposited_minor.
`delta` is recomputed as `expected_net - observed_ledger_total`.

### MatchCandidate
Fields: case_id, ledger_entry_id, score, matched_signals, rule_trace, engine_version, run_id.

Immutable. Candidate scores never authorize resolution.

### Evidence
Field-level source pointer `(entity_type, entity_id, field)`, relevance, supports/contradicts, decision_consumed.

Immutable.

## AI

### Investigation
Fields include case_id, tool_calls, budget, stop_reason, candidates_considered.

Read-only over source data and may produce zero proposals.

### ResolutionProposal
Fields include investigation_id, target ledger-entry set, rationale, evidence, confidence.

Immutable. It references existing records and does not supply authoritative monetary amounts.

## Decisions

### GateEvaluation
Immutable evaluation of a resolution hypothesis.

Contains case_id, hypothesis source, target set, check outcomes, bridge snapshot, pass/fail, failing check.

Every Resolution path passes through GateEvaluation.

Mandatory checks:
- identity
- bridge
- currency
- uniqueness
- evidence completeness
- conflict
- policy
- state transition
- exact target-set equality

### Resolution
Fields: case_id, disposition, final target set, governing gate evaluation, reviewer, review outcome, reviewed_at.

One final Resolution per case/run.

A LedgerEntry may be the final target of at most one Resolution across the system.

For AUTO_RESOLVED, reviewer/review outcome/reviewed_at are null because no human review occurred.

Disposition derives only from deterministic GateEvaluation and policy.

### AuditEvent
Append-only: entity type/id, event type, actor, timestamp, metadata.

Actors: SYSTEM, AI, REVIEWER.

## Benchmark

### GroundTruth
Evaluator-only: case_id, resolvability, exact target set, justifying evidence pointer, scenario label, not-provable reason.

### BenchmarkRun
run_id, seed, dataset/rule/model/prompt/policy versions, code/rule revision, arm, metrics, AI budget/decoding metadata.

## Scenario taxonomy

The benchmark uses exactly six top-level scenario families:

| Label | Scenario | Meaning | Default disposition |
|---|---|---|---|
| S1 | Structured Exact | Strong structured reference evidence uniquely identifies the correct ledger target and the bridge balances. | AUTO_RESOLVED eligible |
| S2 | Structured Ambiguous | Structured references produce multiple plausible candidates or otherwise fail uniqueness. | HUMAN_REVIEW / UNRESOLVED |
| S3 | Financial Mismatch | Candidate relationship exists, but amount, fee, tax, refund, bridge, or other deterministic financial validation fails. | HUMAN_REVIEW / UNRESOLVED |
| S4 | External-Reference Text | Resolution depends on unstructured/external-reference text rather than a trusted structured payment reference. | HUMAN_REVIEW |
| S5 | Narration/Alias Text | Resolution depends on narration, customer-name aliasing, or other unstructured textual relationship. | HUMAN_REVIEW |
| S6 | Non-Provable / Conflict | Evidence is missing, contradictory, duplicated, malformed, or insufficient to establish one valid target set. | UNRESOLVED |

The detailed exception types in BENCHMARK.md map into these families. S4 and S5 always use the unstructured +/-3-day candidate window.

## Lifecycle

INGESTED -> RECONCILED -> CLASSIFIED -> [INVESTIGATED] -> GATED -> CLOSED

If no investigation is needed, CLASSIFIED transitions directly to GATED and an audit event records that investigation was skipped.

RESOLUTION_PROPOSED is the existence of ResolutionProposal.

Human review:
- APPROVED closes the case with the reviewed resolution.
- REJECTED closes the current attempt as rejected.
- PENDING means review is still open.

## Partial grouped match

- exact target set + passing bridge => AUTO eligible
- strict subset => evidence completeness failure
- default => UNRESOLVED
- if every unmatched member has exactly one plausible candidate and a proposal covers the full set => HUMAN_REVIEW
