# CashProof Architecture

## Stack

- Next.js + TypeScript
- Tailwind + shadcn/ui
- Python + FastAPI
- Pydantic v2 at external boundaries
- PostgreSQL
- SQLAlchemy 2.0 + Alembic, isolated in infrastructure
- Anthropic SDK behind an application-defined AI port
- pytest + Hypothesis
- minimal Playwright
- uv
- Docker Compose for PostgreSQL

No Celery/Redis in the initial MVP.

## Dependency boundaries

`packages/domain`
- pure domain model
- invariants
- deterministic calculations
- no framework dependencies

`packages/application`
- use cases
- orchestration
- ports/interfaces
- lifecycle
- gate/resolution
- MUST NOT import infrastructure or concrete AI adapters

`packages/infrastructure`
- PostgreSQL/SQLAlchemy
- external connectors
- evidence storage
- configuration
- composition/wiring support
- concrete external adapters

`packages/ai`
- investigation contracts
- bounded investigator
- read-only tool definitions
- concrete Anthropic/model integration
- implements application-defined AI ports

The application defines ports; infrastructure and AI provide implementations. Composition roots (`apps/api`, `apps/cli`) wire concrete implementations into application use cases.

`packages/benchmark`
- synthetic data
- benchmark execution
- evaluator
- metrics
- reproducibility metadata
- may access GroundTruth only inside evaluator code paths

`apps/api`
- FastAPI adapter only

`apps/cli`
- primary benchmark/CI/operational adapter

`frontend`
- presentation

Domain must not import application, infrastructure, FastAPI, SQLAlchemy, Anthropic SDK, or frontend code.

## Execution

Prove the full domain/application pipeline in memory first.

AI investigation initially runs synchronously inside the batch process. Preserve an application boundary so it can later move behind a worker/job process.

Case identity:
- `case_id` is immutable identity for one case instance.
- each benchmark run creates its own case instance.
- `case_id` is NOT reused across runs.
- `settlement_id` is the stable cross-run join/comparison key.
- `run_id` identifies the execution.

Do not make case_id a composite of settlement_id and run_id.

Investigator budgets are enforced when the investigator is first implemented. Persist max_tool_calls, max_tokens, timeout and relevant decoding parameters with run/version metadata.

Deterministic dataset/rules/policies must be reproducible. Do not claim bit-for-bit LLM reproducibility.

`rule_version` must identify the deterministic engine code revision used by a benchmark run (for example, a release identifier or git SHA).

## Ground-truth isolation

GroundTruth is evaluator-only. Production application/AI ports do not expose it.

The benchmark evaluator reads GroundTruth through a benchmark-only evaluator interface. Production use cases receive only source/derived production data.

If shared PostgreSQL storage is used, evaluator access must be separated by repository/port boundaries and database permissions where practical. The AI runtime must not receive evaluator credentials or GroundTruth queries.

## UI

MVP:
dashboard, batch/run, results, exception center, investigation, evidence, audit, benchmark, health.

The Exception Center must render:
- evidence used
- relevant source records
- GateEvaluation outcome
- failing mandatory check when present
- proposed/final target set
- disposition and review state

The UI must show the governance machinery, not merely a match/disposition badge.

## Exception Intelligence & Clustering (Phase 6)

The Exception Intelligence engine (`packages/application/src/cashproof/application/intelligence.py`) provides deterministic post-reconciliation clustering of all batch exceptions:

1. **Deterministic Fingerprinting**:
   Each non-auto-resolved case produces an immutable `ExceptionFingerprint` composed of:
   - `operational_category`: High-level operational pattern (e.g. `REFERENCE_AMBIGUITY`, `AMOUNT_INCONSISTENCY`, `UNSTRUCTURED_REFERENCE`, `MISSING_RECORD`, `EVIDENCE_CONFLICT`, `POLICY_REVIEW`).
   - `failing_check`: Deterministic gate check that rejected automated resolution (e.g. `BRIDGE`, `TARGET_SET_EQUALITY`, `POLICY`, `IDENTITY`).
   - `candidate_count_bucket`: Structural density (`0`, `1`, `2_to_5`, `6_plus`).
   - `dominant_provenance`: Match signal origin (e.g. `STRUCTURED_REFERENCE`, `EXTERNAL_REFERENCE_TEXT`, `NARRATION_ALIAS_TEXT`).
   - `currency`: Monetary denomination (explicit integer minor units).
   - `has_delta`: Boolean indicator if `delta != 0`.
   - `disposition`: Target workflow state (`HUMAN_REVIEW`, `UNRESOLVED`).

2. **Impact & Metrics Aggregation**:
   Clusters aggregate:
   - `case_count` and `percentage_of_exceptions` in the batch.
   - `affected_settlement_net_minor`: Monetary volume of settlements encountering this exception.
   - `affected_delta_minor`: Signed net accounting discrepancy that must be balanced.
   - Deterministic representative selection (`-abs(delta)`, `-expected_net`, `case_id`).
   - Actionable operational descriptions and remediation playbooks.

3. **GroundTruth & Safety Isolation**:
   The engine processes only production-visible `ReconciliationResult` and `Settlement` records. It contains zero imports or knowledge of evaluator `GroundTruth` or benchmark scenario definitions.

## Gate Intelligence & Controller Explainability (Phase 7)

The Gate Intelligence engine (`packages/application/src/cashproof/application/gate_intelligence.py`) makes the resolution gate observable, rankable, and operationally explainable without weakening, bypassing, or duplicating `evaluate_gate()`:

1. **Zero Second Gate & Read-Only Governance**:
   Gate Intelligence performs strictly read-only diagnostics over authoritative `GateEvaluation` instances produced by the pipeline. It never computes alternative gate decisions or re-evaluates financial rules.

2. **Canonical Evaluation Precedence Rule**:
   Cases may accumulate multiple gate evaluations across their lifecycle (e.g. initial reconciliation gate, AI hypothesis preview gate, and human review gate). To prevent preview evaluations from inflating failure counts, the service applies canonical resolution:
   - If a `Resolution` exists, its `governing_gate_evaluation` is authoritative.
   - Otherwise, the latest evaluation on the case is used.

3. **Deterministic Explainability Catalog**:
   The application maintains `DETERMINISTIC_GATE_EXPLANATIONS`, a static catalog covering all 9 mandatory checks (`IDENTITY`, `CURRENCY`, `BRIDGE`, `UNIQUENESS`, `EVIDENCE_COMPLETENESS`, `CONFLICT`, `POLICY`, `STATE_TRANSITION`, `TARGET_SET_EQUALITY`). Each entry details:
   - Plain-language summary of the financial rule.
   - Technical invariant enforcement description.
   - Deterministic eligibility requirement answering "What exactly must change for this case to become eligible for automated resolution?".

4. **Ranked Automation Blockers & Dual Monetary Metrics**:
   - Automation blockers are ranked deterministically by `(-failure_count, -affected_volume, check_name)`.
   - Dual monetary accounting distinguishes `affected_settlement_net_minor` (total settlement net volume blocked behind the firewall) from `affected_delta_minor` (signed accounting variance).

5. **Bidirectional Intelligence Integration**:
   Gate Intelligence connects failing checks to Phase 6 Exception Clusters, providing deep operational context from root exception pattern to gate firewall failure to case detail.

## Confidence Calibration & Automation Quality Intelligence (Phase 8)

The Confidence Calibration and Quality engine bridges hypothesis belief with deterministic financial safety:

1. **Fundamental Principle: Belief vs Authorization**:
   - Confidence represents matcher or AI hypothesis strength.
   - The deterministic `GateEvaluation` represents legal, arithmetic, and policy authorization.
   - Confidence is NEVER an input to `evaluate_gate()` and never authorizes automatic resolution. Even a hypothesis with 100% confidence fails closed when an invariant (such as BRIDGE fee balance) is violated.

2. **Strict Evaluator vs Production Boundary**:
   - **Evaluator Calibration (`cashproof.benchmark.confidence`)**:
     Evaluates hypotheses against evaluator-only `GroundTruth`. Computes statistical Expected Calibration Error (ECE), Brier Calibration Score, 10-bin calibration curves, empirical threshold precision vs coverage curves, and identifies potential automation opportunities.
   - **Operational Distribution (`cashproof.application.confidence`)**:
     Computes production-visible hypothesis distribution across standard 10 bins, HIGH/MEDIUM/LOW gate tiers, and blocker check confidence contexts. Contains zero imports from `cashproof.benchmark` and zero knowledge of `GroundTruth`.

3. **Exact Target-Set Equality for Empirical Accuracy**:
   - Evaluator accuracy strictly requires `predicted_targets == ground_truth.exact_target_ledger_entry_ids`. Partial matches, superset matches, and disjoint matches count as false predictions.
   - Non-provable cases (S6) where the model proposes a positive target are evaluated as false predictions.
   - Classifier abstentions (ambiguous ties in S2, missing targets in S6) are explicitly distinguished from active prediction errors and provider failures.

4. **Automation Opportunities Without Compromise**:
   - Identifies high-confidence hypotheses whose predicted targets strictly match evaluator GroundTruth, but were held in human review due to deterministic financial discrepancies (e.g. S3 fee/tax differences).
   - Accurately reports affected volume and blocker check attribution while strictly maintaining closed financial invariants.

## Ingestion: Razorpay Test-Mode + Bank Statement CSV (Phase 9)

Ingestion and reconciliation are separate responsibilities. The ingestion
layer (`cashproof.application.ingestion.IngestionService`) fetches/parses
external source data, normalizes it into the existing Phase 1 domain objects
(Payment, Refund, Settlement, SettlementItem, LedgerEntry), performs
idempotency/conflict checks, and stores accepted records. It never generates
MatchCandidates, classifies exceptions, runs `BatchReconciler`, evaluates the
gate, invokes AI, or reads GroundTruth. Real/test-ingested data enters the
exact same, unmodified `BatchReconciler` path as synthetic benchmark data via
`POST /api/reconcile` - there is only ever one reconciliation implementation.

1. **Connector port (application-defined)**:
   `cashproof.application.ports.SourceConnectorPort` is a read-only contract
   (`status()` / `fetch(year, month)`) implemented by
   `cashproof.infrastructure.razorpay.RazorpayConnector`. `ConnectorStatus`
   never carries credential values, only `configured: bool` and a secret-free
   `detail` string - an unconfigured or unreachable connector fails closed
   (`IngestionRun.status = FAILED`) rather than crashing the API process.

2. **Razorpay adapter (`packages/infrastructure/.../razorpay/`)**:
   `client.py` is a thin, read-only httpx wrapper (HTTP Basic auth,
   count/skip pagination, timeout -> `RazorpayClientError`) over
   `GET /payments`, `/payments/{id}`, `/payments/{id}/refunds`, `/refunds`,
   `/settlements`, `/settlements/{id}`, and
   `/settlements/recon/combined?year=&month=`. `_dto.py` mirrors Razorpay's
   own JSON field names (private to this sub-package). `normalizer.py`
   converts paise -> existing integer minor units, Unix epoch seconds -> UTC
   `datetime`, and ISO currency codes -> the existing `Currency` enum, raising
   `IngestionValidationError` (fail closed) on anything that cannot be safely
   mapped onto an existing domain invariant. Razorpay field names never appear
   outside this sub-package.

3. **Bank statement CSV adapter (`packages/infrastructure/.../bank/`)**:
   `csv_parser.py` produces only `LedgerEntry` objects. Fail-closed: a single
   malformed row (missing column, invalid amount/timestamp/currency/direction,
   or an in-file duplicate with conflicting data) rejects the entire file via
   `IngestionValidationError` rather than ingesting a partially valid, unsafe
   subset. `sample_statement.csv` is a small, deterministic, credential-free
   fixture for local demo/testing.

4. **Idempotency (`InMemoryCaseStore`, extended)**: every accepted source
   record's stable external id (Razorpay `pay_xxx`/`rfnd_xxx`/`setl_xxx`,
   bank CSV `transaction_id`) is registered against a fingerprint of its
   critical fields. Re-ingesting the same id with an identical fingerprint is
   silently idempotent (`duplicate_count`); a different fingerprint under the
   same id raises `DuplicateSourceConflictError` - source facts are never
   silently overwritten. Classification happens in a first pass with no store
   mutation, so a conflict anywhere in a batch leaves nothing from that batch
   written (atomic accept-or-refuse).

5. **`IngestionRun`**: an application-level dataclass (not a domain entity -
   no financial invariants) recording `run_id`, `source`, `status`,
   `fetched_count`, `accepted_count`, `rejected_count`, `duplicate_count`,
   `validation_errors`, `failure_reason`, `started_at`/`completed_at`.
   Persisted via `InMemoryCaseStore.ingestion_runs` (implements the
   application-defined `IngestionResultStore` port).

6. **API** (`apps/api`, composition root): `GET /api/ingestion/status`,
   `POST /api/ingestion/razorpay`, `POST /api/ingestion/bank-statement`,
   `GET /api/ingestion/runs[/{run_id}]`, and `POST /api/reconcile` (invokes
   the existing, unmodified `BatchReconciler` over every currently stored
   source record; a case a reviewer has already finalized APPROVED/REJECTED
   is left untouched rather than being reset to a fresh pending gate outcome).
   `apps/api/app.py` depends only on `SourceConnectorPort`, never on
   `RazorpayConnector` directly - the concrete connector is wired in
   `scripts/run_api.py`, exactly like `AIInvestigatorPort`/`AnthropicInvestigator`.

7. **CLI** (`apps/cli/src/cashproof/cli/ingestion.py`): `status`,
   `ingest-bank [--file] [--reconcile]`, `ingest-razorpay --year --month
   [--reconcile]` - a standalone demonstration tool with no persistent store
   across invocations, delegating every decision to `IngestionService` and
   the existing `BatchReconciler`.

8. **Frontend**: `/ingestion` ("Data Sources") shows connector
   configured/unconfigured state (never secrets), a Razorpay trigger, a bank
   CSV upload, accepted/rejected/duplicate results with validation errors, a
   "Reconcile Now" action, and ingestion history.



