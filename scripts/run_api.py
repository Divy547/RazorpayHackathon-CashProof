"""Composition root for the CashProof review API MVP.

Generates a Phase 2 synthetic dataset, runs it once through the production
Phase 3 reconciliation pipeline, and serves the result over the FastAPI
adapter with a mutable in-memory store (no database). This is the ONLY place
Phase 2 (benchmark) and the API layer are wired together - apps/api itself
never imports cashproof.benchmark, matching the same production/evaluator
boundary the CLI demo (apps/cli/src/cashproof/cli/demo.py) already follows.

Run with: uv run python scripts/run_api.py
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import UTC, datetime

import uvicorn
from cashproof.ai.investigator import AnthropicInvestigator
from cashproof.api.app import create_app
from cashproof.application.batch import BatchReconciler
from cashproof.application.store import InMemoryCaseStore
from cashproof.benchmark.generator import generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.service import InMemoryBenchmarkService
from cashproof.domain.ai import InvestigatorBudget
from cashproof.domain.source import Payment, SettlementItem

SEED = 42
NUM_SETTLEMENTS = 100

# Investigator budget: enforced actively by AnthropicInvestigator (see
# packages/ai/src/cashproof/ai/investigator.py), not merely recorded. These
# are configuration and are persisted verbatim on every Investigation.budget.
INVESTIGATOR_BUDGET = InvestigatorBudget(
    max_tool_calls=6,
    max_tokens=8_000,
    timeout_seconds=60.0,
    temperature=0.0,
    model_version="claude-sonnet-5",
)


def build_store() -> InMemoryCaseStore:
    config = GeneratorConfig(seed=SEED, num_settlements=NUM_SETTLEMENTS)
    dataset = generate_dataset(config)

    items_by_settlement: dict[str, list[SettlementItem]] = defaultdict(list)
    for item in dataset.settlement_items:
        items_by_settlement[item.settlement_id].append(item)

    payment_by_id = {p.id: p for p in dataset.payments}
    payments_by_settlement: dict[str, list[Payment]] = defaultdict(list)
    for item in dataset.settlement_items:
        payment = payment_by_id.get(item.payment_id)
        if payment is not None:
            payments_by_settlement[item.settlement_id].append(payment)

    run_id = "review-mvp-001"
    summary = BatchReconciler().run(
        run_id=run_id,
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=datetime.now(UTC),
    )

    store = InMemoryCaseStore(
        run_id=run_id,
        settlements={s.settlement_id: s for s in dataset.settlements},
        items_by_settlement=dict(items_by_settlement),
        payments_by_settlement=dict(payments_by_settlement),
        ledger_pool=list(dataset.ledger_entries),
    )
    for result in summary.results:
        store.put(result)

    print(
        f"Loaded {len(store.results)} cases (seed={SEED}, run_id={run_id}) into the "
        "in-memory review store."
    )
    return store


def main() -> None:
    store = build_store()

    # AnthropicInvestigator constructs the real SDK client lazily and does not
    # require ANTHROPIC_API_KEY to be set to start the server - only to
    # actually run an investigation (POST /api/cases/{id}/investigate), which
    # fails closed with stop_reason=TOOL_FAILURE if the key is missing/invalid
    # or the provider is unreachable.
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "WARNING: ANTHROPIC_API_KEY is not set. Read-only and review endpoints will "
            "work normally; POST /api/cases/{id}/investigate will fail closed with "
            "stop_reason=TOOL_FAILURE until a valid key is configured."
        )
    investigator = AnthropicInvestigator()

    # In-memory benchmark service for live Phase 4 evaluation
    benchmark_service = InMemoryBenchmarkService(
        investigator=investigator,
        investigator_budget=INVESTIGATOR_BUDGET,
    )

    app = create_app(store, investigator, INVESTIGATOR_BUDGET, benchmark_service=benchmark_service)
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
