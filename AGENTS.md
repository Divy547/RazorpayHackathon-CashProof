# CashProof Agent Constitution

CashProof is an Evidence-First Settlement Controller for the Razorpay Buildathon 2026 AI Finance Controller track.

Core thesis: Use deterministic software for certainty. Use AI for ambiguity. Use evidence to explain the decision.

Core loop:
Ingest -> Normalize -> Reconcile -> Investigate -> Validate -> Resolve / Review -> Audit -> Benchmark

The core loop describes capabilities, not lifecycle states. Normalize is part of ingestion/reconciliation preparation. Classification assigns the case exception type. Validate is represented by deterministic GateEvaluation. Audit and Benchmark are cross-cutting concerns.

## Non-negotiable architecture

- Deterministic code owns monetary truth.
- AI investigates ambiguity only.
- Every material decision must be explainable through evidence and deterministic checks.
- The system fails closed.
- Domain code has zero framework/database/HTTP/LLM dependencies.
- Application depends on ports, never directly on infrastructure or AI implementations.
- Source financial facts are immutable.
- Derived decision artifacts are immutable.
- Ground truth is evaluator-only.
- Benchmark uses the same application use cases as production.
- Avoid distributed infrastructure until concretely needed.

## Financial rules

Amounts are integer minor units. MVP is INR, but currency is explicit everywhere.

Bridge:
gross - fee - tax_on_fee - netted_refund + adjustment = net

Positive adjustment increases net; negative adjustment decreases net.
Fee, tax, and refund are stored as positive magnitudes.

GST is 18% of the fee. The generator computes it once using half-up rounding on paise; reconciliation consumes stored tax and never recomputes it.

Settlement invariant:
Settlement.net_deposited_minor == sum(SettlementItem.computed_net_minor).

ReconciliationCase.expected_net is sourced from Settlement.net_deposited_minor.

Refund invariant:
For a payment, SettlementItem.netted_refund_minor equals the sum of Refund.amount_minor for that payment where netted_into_settlement=true.

Candidate windows:
- reference-backed: +/- 7 days
- unstructured S4/S5: +/- 3 days
Windows filter candidates; they are never proof.

## AI boundaries

AI may inspect allowed evidence, retrieve related source records, investigate ambiguity, classify exceptions, synthesize evidence, explain discrepancies, and propose a target record set.

AI may not redefine monetary truth, modify source facts, alter authoritative amounts, bypass deterministic validation, approve its own proposal, move money, issue refunds, post journals, write source data, access ground truth, or use confidence as a gate input.

Every AI proposal must pass GateEvaluation.

AI budgets are enforced from the first investigator implementation. Budget values are configuration and are persisted with benchmark/run metadata.

## Resolution gate

Every path to Resolution passes through GateEvaluation.

Checks include identity, bridge, currency, uniqueness, evidence completeness, conflicts, policy, state transition, and exact target-set equality.

AUTO_RESOLVED requires a passing gate.
Failed mandatory checks become HUMAN_REVIEW or UNRESOLVED.

A LedgerEntry may be the final resolved target of at most one Resolution across the system.

## Lifecycle

INGESTED -> RECONCILED -> CLASSIFIED -> INVESTIGATED -> GATED -> CLOSED

INVESTIGATED may be skipped by transitioning directly CLASSIFIED -> GATED when deterministic evidence is sufficient and no AI investigation is required. The skipped step is still represented in the audit trail as not required.

RESOLUTION_PROPOSED is represented by existence of ResolutionProposal, not a processing state.

Disposition:
- AUTO_RESOLVED
- HUMAN_REVIEW
- UNRESOLVED

Review outcome:
- APPROVED
- REJECTED
- PENDING

A rejected human review closes the current resolution attempt as rejected; it does not silently reopen or mutate source facts. Re-investigation, if supported later, creates a new proposal/gate path.

## Source/data integrity

Source entities contain no truth/decoy/noise/scenario flags.

Synthetic decoys and corrupted records must be indistinguishable from real source records except for naturally occurring data patterns. Scenario generation must not leak labels through ID ranges, timestamp ordering, formatting, or other artificial correlations.

## Development rules

Before implementation:
1. Read AGENTS.md and relevant docs.
2. Inspect existing code.
3. State affected boundaries and intended change.
4. Implement the smallest complete change.
5. Run relevant tests.
6. Run architecture/import-boundary checks.
7. Report changed files, tests, failures, and risks.

Do not reopen locked decisions in DECISIONS.md without explicit architectural justification.

Avoid unnecessary dependencies, speculative abstractions, microservices, graph DBs, Kafka, Kubernetes, Celery, Redis, or generic agent frameworks.

Agent roles:
- ChatGPT: architecture, decomposition, decisions, acceptance
- Claude: deep reasoning and adversarial review
- Agy: implementation, tests, iteration
- Human developer: final product validation
