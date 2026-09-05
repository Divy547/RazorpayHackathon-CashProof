# CashProof — Evidence-First Settlement Control

**Live Demo:** https://razorpay-hackathon-cash-proof-yy6i.vercel.app/

**API:** https://razorpayhackathon-cashproof.onrender.com/

CashProof is a settlement reconciliation controller built on one premise:
**reconciliation is not record matching, it is a certainty problem.** Matching
a settlement to a ledger entry is trivial when the evidence is clean. The
actual engineering problem is knowing, for every settlement, whether the
evidence is strong enough to authorize an outcome automatically — and failing
closed, honestly and auditably, whenever it is not.

Financial automation that quietly guesses when evidence is ambiguous is not
automation, it is undisclosed risk. CashProof never does this: every
settlement is either resolved with a provably correct target set, or routed
to a human with the exact reason it could not be resolved automatically.

## Core Principle

> **AI investigates. Deterministic software authorizes.**

Deterministic code owns monetary truth end to end: matching, the settlement
bridge, and the final authorization gate. A bounded AI investigator may be
used to gather evidence and propose a hypothesis when a case is ambiguous —
but it can never author, approve, or bypass a resolution. Every proposal,
AI-originated or not, passes through the same unmodified deterministic gate
before it can affect any case's disposition.

## The Workflow

```
Ingest → Normalize → Reconcile → Investigate → Validate → Resolve/Review → Audit → Benchmark
```

- **Ingest** — pull settlement/payment/refund data from a source (Razorpay
  Test Mode API, or a bank statement CSV) and store it, unmodified.
- **Normalize** — convert source-specific shapes into CashProof's domain
  model (integer minor-unit money, explicit currency, UTC timestamps).
- **Reconcile** — deterministically match settlements to ledger entries and
  compute the expected-vs-observed settlement bridge.
- **Investigate** — for ambiguous cases, a bounded AI investigator may
  inspect evidence and propose a hypothesis (or abstain).
- **Validate** — every hypothesis, deterministic or AI-originated, is
  independently re-verified by the deterministic gate.
- **Resolve / Review** — a passing gate can produce `AUTO_RESOLVED`; anything
  else becomes `HUMAN_REVIEW` or `UNRESOLVED`, with a human able to approve
  or reject.
- **Audit** — every decision-relevant event is recorded as an immutable,
  append-only audit trail.
- **Benchmark** — the same production reconciliation path is evaluated
  against a synthetic dataset with known ground truth, entirely outside the
  production decision path.

## The Deterministic Financial Boundary

All monetary truth is owned by deterministic code, never by AI:

- **Integer minor-unit money.** No floats in the financial path; every
  amount is an integer count of minor units (paise) with an explicit
  currency.
- **Deterministic settlement arithmetic.** The settlement bridge
  (`gross − fee − tax_on_fee − netted_refund + adjustment = net`) is computed
  once, by code, and never re-derived or overridden by a model.
- **Candidate/evidence validation** happens before any hypothesis is
  considered — evidence is built deterministically from source records, never
  asserted by a model.
- A resolution hypothesis must pass **all nine mandatory gate checks**:
  **Identity, Bridge, Currency, Uniqueness, Evidence Completeness, Conflict,
  Policy, State Transition,** and **Target Set Equality.**
- **AI confidence never authorizes money.** Confidence is a descriptive
  signal for human reviewers; it is not an input to the gate and cannot
  relax any check.
- **AI cannot write source records or move money.** The AI investigator has
  read-only access to a single case's already-computed candidates and
  evidence. It cannot mutate a `Payment`, `Refund`, `Settlement`,
  `SettlementItem`, or `LedgerEntry`, and it has no path to any money-movement
  or ledger-posting capability — there isn't one in the system.

## AI Investigation

When a case is ambiguous, a bounded AI investigator (Anthropic or Gemini,
selected by configuration — see [Running the API](#running-the-api)) may be
invoked:

- It has exactly **six read-only tools** scoped to that one case: case
  context, bridge breakdown, deterministic candidates, one ledger entry at a
  time (restricted to that case's own candidate pool), existing evidence, and
  the original gate result.
- It can end the investigation only two ways: **submit a proposal** (target
  ledger entry IDs + rationale + confidence) or **abstain**. Any other model
  output is treated as a malformed result, not a decision.
- **Proposal evidence is never trusted from the model.** Whatever evidence
  the model claims is discarded; the application layer rebuilds evidence
  deterministically from the proposal's target records before anything is
  evaluated.
- **Every proposal returns through the same deterministic gate** used for
  the fully-automated path — a second, independent re-verification, not a
  rubber stamp.
- **AI has no resolution authority.** A passing gate produces a
  recommendation for a human reviewer; only `HumanReviewUseCase` can turn a
  proposal into an approved `Resolution`, and it re-runs the gate itself.
- Tool-call count, token usage, and wall-clock timeout are enforced in code
  against a configured budget — never left to the model's own judgment.
  Provider failures, timeouts, and malformed output all fail closed
  (`TOOL_FAILURE` / `TIMEOUT` / `MALFORMED_OUTPUT`), never a fabricated
  proposal.

See [docs/AI_BOUNDARIES.md](docs/AI_BOUNDARIES.md) for the complete
allowed/forbidden list.

## Benchmark Results

Measured against the production reconciliation pipeline (not a separate
benchmark-only code path), synthetic dataset, seed `42`, 100 settlements:

| Metric | Value |
|---|---|
| Total settlements | 100 |
| AUTO_RESOLVED | 39 |
| HUMAN_REVIEW | 51 |
| UNRESOLVED | 10 |
| False auto-resolutions | **0** |
| Exact target-set accuracy | **100%** (39/39 auto-resolved cases) |
| Expected Calibration Error (ECE) | 0.1240 |
| Brier score | 0.0332 |
| Precision at confidence ≥ 0.80 | 100% |
| High-confidence cases (≥ 0.80) | 69 total — 39 gate-passed, 30 gate-blocked |
| Exception cases | 61, across 5 recurring patterns |

**This is not a "100% match rate."** 61 of 100 settlements were correctly
*not* auto-resolved — they were routed to human review or left unresolved
because the evidence did not meet the bar for automatic authorization.
Exceptions are not failures of the system; failing to flag them would be.
Exact target-set accuracy is measured only over the 39 cases the system
chose to auto-resolve: on every one of them, the resolved target set exactly
matched ground truth, with zero false auto-resolutions anywhere in the
batch. The 30 gate-blocked cases among the 69 high-confidence ones are the
concrete evidence that confidence and gate authorization are independent —
a model or heuristic can be highly confident and still be correctly refused.

Reproduce with `uv run python -m cashproof.cli.benchmark --seed 42
--num-settlements 100` (see [Benchmark / Demo](#benchmark--demo)).

### Benchmark Isolation

`GroundTruth` (the scenario label, provability, and exact expected target
set for each synthetic case) is **evaluator-only**. It is never constructed
in, imported by, or reachable from any production code path — the matcher,
classifier, evidence builder, gate, and AI investigator have no access to it
and no way to detect its existence. This is enforced by architecture tests
(`tests/architecture/test_ground_truth_isolation.py`,
`test_scenario_isolation.py`, `test_benchmark_isolation.py`), not by
convention alone. The benchmark evaluates the same `BatchReconciler` and use
cases production uses — there is no separate benchmark-only reconciliation
implementation.

### Exception Classes Demonstrated

The synthetic dataset exercises five real-world exception patterns, each
individually reproducible and, together, accounting for the 61 exception
cases above:

- **Structured reference ambiguity** — two ledger entries share the same
  structured reference, amount, currency, and direction; the deterministic
  matcher refuses to guess between them.
- **Settlement amount mismatch / bridge discrepancy** — the reference
  correctly identifies one ledger entry, but the settlement bridge does not
  balance against it.
- **Unstructured external payment reference** — no structured reference
  exists; the order reference is found only as text embedded in a bank
  narration.
- **Narration alias** — no structured reference exists; a customer-name
  alias is found embedded in a bank narration.
- **Missing settlement record** — no ledger entry corresponds to the
  settlement at all; the system fails closed rather than guessing.

## Documentation

| Document | Covers |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, module boundaries, ports/adapters, per-phase design decisions |
| [docs/DOMAIN.md](docs/DOMAIN.md) | Domain model: entities, invariants, the settlement bridge, money handling |
| [docs/AI_BOUNDARIES.md](docs/AI_BOUNDARIES.md) | Exactly what the AI investigator may and may not do |
| [docs/BENCHMARK.md](docs/BENCHMARK.md) | Benchmark methodology, scenario taxonomy, metrics, isolation guarantees |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Numbered log of locked architectural decisions |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Development workflow and phase order |

[AGENTS.md](AGENTS.md) is the authoritative, machine-readable summary of the
non-negotiable architecture, financial rules, and AI boundaries — read it
before making any change to domain, application, or AI code.

## Repository Structure

```
ledger/
├── AGENTS.md            # Non-negotiable architecture/financial/AI rules
├── README.md            # This file
├── pyproject.toml       # Workspace root (uv), shared tool config
├── uv.lock
├── docs/                # Architecture, domain, AI boundaries, benchmark, decisions
├── apps/
│   ├── api/              # FastAPI HTTP adapter / composition root
│   └── cli/              # Ingestion, benchmark, and demo CLI entry points
├── packages/
│   ├── domain/           # Pure domain model — zero external dependencies
│   ├── application/      # Use cases, ports, orchestration
│   ├── infrastructure/   # Razorpay + bank-statement adapters, in-memory store
│   ├── ai/                # AnthropicInvestigator / GeminiInvestigator (AIInvestigatorPort)
│   └── benchmark/        # Synthetic generator, evaluator, isolated GroundTruth
├── scripts/
│   ├── run_api.py         # API composition root (loads the demo dataset, starts uvicorn)
│   └── generate_demo_data.py  # Static JSON snapshot for the frontend demo pages
├── tests/                # architecture / domain / application / infrastructure / ai / benchmark / api
├── datasets/             # Benchmark dataset partitions and fixtures
└── frontend/             # Next.js presentation layer
```

## Setup

**Prerequisites:** Python 3.12+, [uv](https://github.com/astral-sh/uv),
Node.js (for the frontend).

```bash
uv sync
```

## Running the Tests

```bash
uv run pytest
```

## Lint & Type Checking

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy packages apps tests
```

## Running the API

```bash
uv run python scripts/run_api.py
```

This generates the seed-42, 100-settlement synthetic dataset, reconciles it
through the real production pipeline, and serves it at
`http://127.0.0.1:8000`.

The AI provider is selected via environment variable (default `anthropic`,
existing behavior is unchanged if unset):

```bash
# Anthropic (default)
ANTHROPIC_API_KEY=sk-... uv run python scripts/run_api.py

# Gemini
CASHPROOF_AI_PROVIDER=gemini GEMINI_API_KEY=... uv run python scripts/run_api.py
# optional: CASHPROOF_GEMINI_MODEL to override the default model
```

Without a valid key, the API still boots normally — only
`POST /api/cases/{id}/investigate` fails closed with `stop_reason:
TOOL_FAILURE`. Read-only and human-review endpoints are unaffected either
way.

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

Serves at `http://localhost:3000` and expects the API at
`http://localhost:8000` by default (override with
`NEXT_PUBLIC_API_BASE_URL`).

```bash
npm run build   # production build (also runs the TypeScript compiler)
npm run start   # serve the production build
npm run lint    # ESLint
```

## Benchmark / Demo

```bash
# Deterministic-only arm
uv run python -m cashproof.cli.benchmark --seed 42 --num-settlements 100

# With AI investigation on ambiguous cases
uv run python -m cashproof.cli.benchmark --seed 42 --num-settlements 100 --arm ai_investigator

# Machine-readable output
uv run python -m cashproof.cli.benchmark --seed 42 --num-settlements 100 --json

# End-to-end reconciliation demo (readable console walkthrough)
uv run python -m cashproof.cli.demo
```

## Data Ingestion

```bash
# Connector configuration status (never prints credentials)
uv run python -m cashproof.cli.ingestion status

# Ingest the bundled sample bank statement CSV, then reconcile
uv run python -m cashproof.cli.ingestion ingest-bank --reconcile
# or a specific file:
uv run python -m cashproof.cli.ingestion ingest-bank --file path/to/statement.csv --reconcile

# Razorpay Test Mode ingestion for a given month
RAZORPAY_KEY_ID=... RAZORPAY_KEY_SECRET=... \
  uv run python -m cashproof.cli.ingestion ingest-razorpay --year 2026 --month 8 --reconcile
```

Bank CSV ingestion is fail-closed: any malformed row (missing column,
invalid amount/timestamp/currency/direction, or a conflicting duplicate)
rejects the entire file rather than accepting a partially-valid batch.
Razorpay ingestion requires `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET`; without
them, ingestion fails closed and reports `UNCONFIGURED` rather than
crashing. Ingestion never runs reconciliation on its own — it only stores
normalized source records; `--reconcile` (or `POST /api/reconcile`) is a
separate, explicit step over the same unmodified `BatchReconciler`.

### Razorpay Integration — Test Mode Only

The Razorpay connector authenticates against the **Razorpay Test Mode API**
using HTTP Basic auth over `httpx`, and is strictly read-only (settlements,
payments, refunds). It is a demonstration integration against sandbox data —
**CashProof does not connect to, or process transactions through, a live
Razorpay production account**, and nothing in this repository does.

## What CashProof Does Not Do

- **Does not move money.** There is no code path anywhere in this system
  that initiates a payment, transfer, or settlement.
- **Does not issue refunds.**
- **Does not autonomously post arbitrary accounting journals.** Resolutions
  reference existing ledger entries; nothing is invented or written to an
  external ledger.
- **Does not let AI confidence authorize anything.** Confidence never
  appears in the deterministic gate's inputs and cannot relax, skip, or
  override any of its nine checks.
