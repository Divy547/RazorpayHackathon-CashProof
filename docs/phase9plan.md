# Phase 9 Implementation Plan — Razorpay Test-Mode + Bank Statement Integration

## Inspection Summary

### Current architecture (Phase 8 state)
- **`packages/infrastructure/`** — minimal: `__init__.py` only; `pyproject.toml` depends on `cashproof-domain` + `cashproof-application` only. **This is exactly where the new adapters belong.**
- **`packages/application/ports.py`** — only `AIInvestigatorPort` exists. New ingestion ports go here.
- **`packages/application/store.py`** — `InMemoryCaseStore` holds settlements/items/payments/ledger in-memory. Needs a source identity registry for idempotency.
- **`scripts/run_api.py`** — composition root; wires benchmark generator → BatchReconciler → InMemoryCaseStore → FastAPI. New ingestion wiring happens here.
- **Architecture tests** — `test_import_boundaries.py` + `test_forbidden_dependencies.py` enforce strict layer isolation. Infrastructure may import `cashproof.domain` and `cashproof.application` but NOT `cashproof.ai` or `cashproof.benchmark`.

### Razorpay API contract (confirmed from docs)
- Base: `https://api.razorpay.com/v1/`
- Auth: HTTP Basic (key_id:key_secret)
- Payments: `GET /payments` (list, paginated via `count`/`skip`), `GET /payments/{id}`
- Refunds: `GET /refunds`, `GET /payments/{id}/refunds`
- Settlements: `GET /settlements`, `GET /settlements/{id}`
- Settlement recon (items): `GET /settlements/recon/combined?year=yyyy&month=mm`
- All amounts in **paise** (integer minor units) — identical to our domain convention
- All timestamps: Unix epoch seconds (must normalize to UTC datetime)
- Currency: ISO 3-letter string (e.g. "INR")

### LedgerEntry contract
```python
LedgerEntry(
    id,
    amount_minor,
    currency,
    timestamp,
    direction,
    payment_ref=None,
    external_ref=None,
    narration=None,
    customer_name=None,
)
```

### Key constraints from architecture tests
- `cashproof.infrastructure` may NOT import `cashproof.ai`, `cashproof.benchmark`, `apps`
- `cashproof.application.ports` may NOT import `cashproof.infrastructure` (application defines ports; infra implements them)
- Domain has zero external dependencies; cannot add any
- Infrastructure `pyproject.toml` currently has `cashproof-domain` + `cashproof-application` — we'll add `httpx` (already in dev deps) as runtime dep for the Razorpay client

---

## Architecture Decision (before implementation)

### Decision 35 — Razorpay Adapter Boundary
The Razorpay connector lives entirely in `packages/infrastructure/src/cashproof/infrastructure/razorpay/`. It uses `httpx` for HTTP. Razorpay-specific field names (snake_case mirrors of API JSON) are contained within a private `_dto` module inside that sub-package. The public normalizer converts DTOs → domain objects. Domain code has zero knowledge of Razorpay field names.

### Decision 36 — Bank Statement Adapter Boundary
CSV bank statement parsing lives in `packages/infrastructure/src/cashproof/infrastructure/bank/`. Parsing is fail-closed: malformed rows accumulate structured errors; a batch with any critical error (missing required column, invalid amount) raises `IngestionValidationError` rather than silently producing partial records.

### Decision 37 — Ingestion Port (application-defined)
`packages/application/ports.py` gains two new ports:
- `SourceConnectorPort` — read-only connector that returns raw normalized domain records
- `IngestionResultStore` — records run metadata (application-level dataclass, not domain entity)

Application defines the contract; infrastructure provides the implementation.

### Decision 38 — Idempotency via External ID Registry
Source records carry stable external IDs (Razorpay `pay_xxx`, `rfnd_xxx`, `setl_xxx`; bank CSV `transaction_id`). The `InMemoryCaseStore` gains an `ingested_source_ids: set[str]` registry. Re-ingesting the same external ID is silently ignored (idempotent). Conflicting data (same ID, different amount) raises `DuplicateSourceConflictError`. This design defers to persistence without rewriting the application layer — a future SQLAlchemy-backed store implements the same `IngestionResultStore` port.

### Decision 39 — Ingestion Service (application layer)
`packages/application/src/cashproof/application/ingestion.py` — orchestrates:
1. Connector fetches raw records
2. Normalizer validates and produces domain objects
3. Idempotency check against registry
4. Accepted records stored in `InMemoryCaseStore` source pools
5. **Does NOT run reconciliation** — caller triggers reconciliation separately via existing `BatchReconciler`
No reconciliation algorithm lives in the ingestion service.

### Decision 40 — IngestionRun Result Model
`IngestionRun` is an application-level dataclass (NOT a domain entity — no financial invariants). Fields: `run_id`, `source`, `status`, `fetched_count`, `accepted_count`, `rejected_count`, `duplicate_count`, `validation_errors`, `failure_reason`, `started_at`, `completed_at`. Stored in `InMemoryCaseStore.ingestion_runs`.

---

## Files to Create / Modify

### NEW — Infrastructure
1. `packages/infrastructure/src/cashproof/infrastructure/razorpay/__init__.py`
2. `packages/infrastructure/src/cashproof/infrastructure/razorpay/_dto.py` — Razorpay response DTOs (TypedDicts, no domain imports needed here)
3. `packages/infrastructure/src/cashproof/infrastructure/razorpay/client.py` — httpx-based read-only client with pagination, timeout, auth
4. `packages/infrastructure/src/cashproof/infrastructure/razorpay/normalizer.py` — DTO → Payment/Refund/Settlement/SettlementItem/LedgerEntry
5. `packages/infrastructure/src/cashproof/infrastructure/razorpay/connector.py` — implements `SourceConnectorPort`; UNCONFIGURED state if no env vars
6. `packages/infrastructure/src/cashproof/infrastructure/bank/__init__.py`
7. `packages/infrastructure/src/cashproof/infrastructure/bank/csv_parser.py` — CSV → LedgerEntry; fail-closed; structured errors
8. `packages/infrastructure/src/cashproof/infrastructure/bank/sample_statement.csv` — deterministic demo data (no credentials needed)

### MODIFY — Application ports
9. `packages/application/src/cashproof/application/ports.py` — add `SourceConnectorPort`, `IngestionResultStore`

### NEW — Application ingestion service
10. `packages/application/src/cashproof/application/ingestion.py` — `IngestionRun`, `IngestionService`, `IngestionValidationError`, `DuplicateSourceConflictError`

### MODIFY — Application store
11. `packages/application/src/cashproof/application/store.py` — add `ingestion_runs`, `ingested_source_ids`, `add_source_records()`

### MODIFY — Infrastructure pyproject.toml
12. `packages/infrastructure/pyproject.toml` — add `httpx>=0.27.0`

### MODIFY — API schemas
13. `apps/api/src/cashproof/api/schemas.py` — add `ConnectorStatusResponse`, `IngestionRunOut`, `IngestionTriggerRequest`, `BankStatementIngestionResponse`

### MODIFY — API serializers
14. `apps/api/src/cashproof/api/serializers.py` — add ingestion serializers

### MODIFY — API app
15. `apps/api/src/cashproof/api/app.py` — add ingestion endpoints; `create_app()` gains optional `razorpay_connector` + `ingestion_service` params

### MODIFY — scripts/run_api.py
16. `scripts/run_api.py` — wire Razorpay connector + ingestion service + bank parser; handle UNCONFIGURED gracefully

### MODIFY — CLI
17. `apps/cli/src/cashproof/cli/ingestion.py` — NEW: CLI commands for connector status, bank ingest, reconcile ingested
18. `apps/cli/src/cashproof/cli/__init__.py` — expose ingestion CLI

### MODIFY — Frontend
19. `frontend/src/app/ingestion/page.tsx` — Data Sources page (server component shell)
20. `frontend/src/app/ingestion/IngestionClient.tsx` — client component: connector status, bank upload, ingestion history
21. `frontend/src/components/Nav.tsx` — add "Data Sources" link

### NEW — Tests
22. `tests/infrastructure/__init__.py`
23. `tests/infrastructure/test_razorpay_normalizer.py` — normalization, amounts, timestamps, currencies, relationships
24. `tests/infrastructure/test_razorpay_connector.py` — unconfigured, pagination mock, failure handling
25. `tests/infrastructure/test_bank_csv_parser.py` — valid CSV, malformed rows, missing columns, duplicates, empty refs
26. `tests/application/test_ingestion.py` — idempotency, duplicate conflict, integration with store, no second reconciliation
27. `tests/api/test_ingestion_api.py` — connector status endpoint, bank ingest endpoint, security (no secrets in responses)

### MODIFY — Docs
28. `docs/ARCHITECTURE.md` — Phase 9 section
29. `docs/DECISIONS.md` — Decisions 35–40

---

## API Endpoints (following existing conventions)

```
GET  /api/ingestion/status              # Connector/configuration status (no secrets)
POST /api/ingestion/razorpay            # Trigger read-only Razorpay ingestion
POST /api/ingestion/bank-statement      # Upload bank CSV → ingest
GET  /api/ingestion/runs                # List ingestion runs
GET  /api/ingestion/runs/{run_id}       # Get specific run result
POST /api/reconcile                     # Trigger reconciliation over currently stored source records
```

---

## Execution Order

1. Application ports + ingestion service + store extension (no external deps)
2. Infrastructure: pyproject.toml → Razorpay client + normalizer + connector
3. Infrastructure: Bank CSV parser + sample statement
4. API schemas + serializers + endpoints
5. Frontend: ingestion page + nav link
6. CLI: ingestion commands
7. Tests
8. scripts/run_api.py wiring
9. Docs
10. Full validation suite

---

## Boundary Verification Checklist
- [ ] `cashproof.domain` has zero new external imports
- [ ] `cashproof.application` has zero infra/AI/benchmark imports
- [ ] Razorpay field names (`pay_xxx`, `entity`, `amount`) do NOT appear in application or domain
- [ ] No reconciliation algorithm in ingestion service
- [ ] No AI logic in ingestion
- [ ] No benchmark GroundTruth in infrastructure or application
- [ ] Ingestion errors fail closed
- [ ] Duplicate source records raise conflict rather than silently overwrite
- [ ] No secrets in API responses (connector status shows configured/unconfigured, never key values)
- [ ] Benchmark uses its existing synthetic generator path unchanged
- [ ] Real/test data enters same BatchReconciler path as synthetic data
