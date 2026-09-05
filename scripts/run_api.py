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
from cashproof.ai.gemini_investigator import GeminiInvestigator
from cashproof.ai.investigator import AnthropicInvestigator
from cashproof.api.app import create_app
from cashproof.application.batch import BatchReconciler
from cashproof.application.ports import AIInvestigatorPort
from cashproof.application.store import InMemoryCaseStore
from cashproof.benchmark.generator import generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.service import InMemoryBenchmarkService
from cashproof.domain.ai import InvestigatorBudget
from cashproof.domain.source import Payment, SettlementItem
from cashproof.infrastructure.razorpay import RazorpayConnector

SEED = 42
NUM_SETTLEMENTS = 100

# Gemini free-tier model as of Sept 2026 with confirmed function-calling
# support, verified with a real authenticated call (not just
# client.models.list() - gemini-2.5-flash was LISTED as available but
# returned a real 404 "no longer available to new users" on an actual call;
# this is the model Google's own error message recommends as the
# replacement). Deliberately NOT the same model family Agy (the coding
# agent) uses. Override via CASHPROOF_GEMINI_MODEL if this identifier is
# ever retired too - re-verify with a real generate_content() call, not just
# a models.list() membership check, since that alone is not sufficient.
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"


def _investigator_budget(
    model_version: str, *, max_tool_calls: int = 6, max_tokens: int = 8_000
) -> InvestigatorBudget:
    """Build the budget for whichever provider is selected.

    Enforced actively by the AIInvestigatorPort implementation (see
    packages/ai/src/cashproof/ai/investigator.py and gemini_investigator.py),
    not merely recorded. max_tool_calls/max_tokens default to the Anthropic
    values; Gemini's real multi-turn conversations resend the full growing
    history every turn and were observed exhausting 8,000 cumulative tokens
    before reaching submit_proposal/abstain, so build_investigator() passes
    Gemini-specific overrides below.
    """
    return InvestigatorBudget(
        max_tool_calls=max_tool_calls,
        max_tokens=max_tokens,
        timeout_seconds=60.0,
        temperature=0.0,
        model_version=model_version,
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


def build_investigator() -> tuple[AIInvestigatorPort, InvestigatorBudget]:
    """Select the AIInvestigatorPort implementation via CASHPROOF_AI_PROVIDER.

    Both providers construct their real SDK client lazily and do not require
    their API key to be set to start the server - only to actually run an
    investigation (POST /api/cases/{id}/investigate), which fails closed with
    stop_reason=TOOL_FAILURE if the key is missing/invalid or the provider is
    unreachable. Default is "anthropic" - existing behavior is unchanged when
    CASHPROOF_AI_PROVIDER is unset.
    """
    provider = os.environ.get("CASHPROOF_AI_PROVIDER", "anthropic").strip().lower()

    if provider == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            print(
                "WARNING: GEMINI_API_KEY is not set. Read-only and review endpoints will "
                "work normally; POST /api/cases/{id}/investigate will fail closed with "
                "stop_reason=TOOL_FAILURE until a valid key is configured."
            )
        model_version = os.environ.get("CASHPROOF_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        return GeminiInvestigator(), _investigator_budget(
            model_version, max_tool_calls=8, max_tokens=16_000
        )

    if provider != "anthropic":
        print(
            f"WARNING: Unrecognized CASHPROOF_AI_PROVIDER={provider!r}; falling back to "
            "'anthropic'. Valid values are 'anthropic' and 'gemini'."
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "WARNING: ANTHROPIC_API_KEY is not set. Read-only and review endpoints will "
            "work normally; POST /api/cases/{id}/investigate will fail closed with "
            "stop_reason=TOOL_FAILURE until a valid key is configured."
        )
    return AnthropicInvestigator(), _investigator_budget("claude-sonnet-5")


def main() -> None:
    store = build_store()

    investigator, investigator_budget = build_investigator()

    # In-memory benchmark service for live Phase 4 evaluation
    benchmark_service = InMemoryBenchmarkService(
        investigator=investigator,
        investigator_budget=investigator_budget,
    )

    # RazorpayConnector gracefully reports UNCONFIGURED (never crashes) if
    # RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET are unset - the synthetic/demo path
    # above works unchanged either way.
    razorpay_connector = RazorpayConnector()
    if not razorpay_connector.status().configured:
        print(
            "WARNING: RAZORPAY_KEY_ID/RAZORPAY_KEY_SECRET are not set. "
            "POST /api/ingestion/razorpay will fail closed until both are configured; "
            "bank statement CSV ingestion and reconciliation are unaffected."
        )

    app = create_app(
        store,
        investigator,
        investigator_budget,
        benchmark_service=benchmark_service,
        razorpay_connector=razorpay_connector,
    )
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
