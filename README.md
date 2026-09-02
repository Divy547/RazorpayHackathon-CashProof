# CashProof

Evidence-First Settlement Controller for the Razorpay Buildathon 2026 AI Finance Controller track.

Core thesis: Use deterministic software for certainty. Use AI for ambiguity. Use evidence to explain the decision.

Core loop:
Ingest -> Normalize -> Reconcile -> Investigate -> Validate -> Resolve / Review -> Audit -> Benchmark

## Canonical Context

Read `AGENTS.md` first, then:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DOMAIN.md](docs/DOMAIN.md)
- [docs/DECISIONS.md](docs/DECISIONS.md)
- [docs/AI_BOUNDARIES.md](docs/AI_BOUNDARIES.md)
- [docs/BENCHMARK.md](docs/BENCHMARK.md)
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## Repository Structure

```
cashproof/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .gitignore
├── docs/
├── apps/
│   ├── api/          # FastAPI HTTP adapter / composition root
│   └── cli/          # Primary CLI operational & benchmark runner
├── packages/
│   ├── domain/       # Pure domain model, zero external dependencies
│   ├── application/  # Use cases, lifecycle, orchestration, port definitions
│   ├── infrastructure/ # DB/storage and external adapters
│   ├── ai/           # Bounded AI investigator implementing application ports
│   └── benchmark/    # Synthetic generator, runner, and isolated evaluator
├── tests/
│   ├── architecture/ # AST import boundaries, forbidden dependencies, isolation
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── ai/
│   └── benchmark/
├── datasets/         # Benchmark dataset partitions and fixtures
└── frontend/         # Next.js presentation layer
```

## Quickstart

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
uv sync
```

### Run Tests

```bash
uv run pytest
```

### Run Linters & Type Checking

```bash
uv run ruff check .
uv run mypy packages apps tests
```
