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
