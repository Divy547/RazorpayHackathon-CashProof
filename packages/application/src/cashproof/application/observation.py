"""Authoritative, hypothesis-independent observed ledger state.

Answers exactly one question: "what does the ledger itself structurally,
unambiguously claim belongs to this settlement?" This is a source-asserted
fact (LedgerEntry.payment_ref is populated by the bank/ledger side), not an
inference. It must never depend on candidate matching, scoring,
classification, resolution disposition, or any evaluator-only concept.

This is deliberately a *different* concept from GateEvaluation.bridge_snapshot
.observed_net_minor, which evaluate_gate() computes from the specific
hypothesis proposed to it (target_ledger_entries) and answers "does *this*
proposed hypothesis balance." Both are legitimate, but they answer different
questions and must not be conflated.
"""

from __future__ import annotations

from collections.abc import Sequence

from cashproof.domain.exceptions import CurrencyMismatchError
from cashproof.domain.money import aggregate_ledger_total
from cashproof.domain.source import LedgerEntry, Settlement


class ObservationCurrencyConflictError(Exception):
    """Raised when structurally linked ledger entries disagree with the settlement's
    currency.

    The observation layer refuses to guess in this situation: it will neither
    silently drop the mismatched entries (that would understate what the
    ledger actually claims) nor partially aggregate across currencies (that
    would produce a meaningless mixed-currency number). It fails closed by
    raising loudly, the same way Phase 2's SyntheticGenerationError fails
    closed on an invariant violation rather than continuing with corrupted
    state - this is an application-layer concern, not a Phase 1 domain type.
    """


def compute_observed_ledger_state(
    settlement: Settlement,
    ledger_pool: Sequence[LedgerEntry],
) -> int:
    """Aggregate every LedgerEntry the ledger itself structurally links to this settlement.

    A LedgerEntry is structurally linked when its payment_ref equals the
    settlement's own settlement_id (the bank's own settlement-level payout
    reference). No ranking, deduplication, or interpretation is applied: if
    the ledger structurally labels more than one entry as belonging to this
    settlement, the observation reports the sum of all of them, exposing the
    duplication rather than hiding it behind a hypothesis-driven selection.

    Raises ObservationCurrencyConflictError (fail closed) if any structurally
    linked entry is denominated in a currency other than the settlement's own
    - it is never silently dropped or partially summed.
    """
    linked_entries = tuple(
        entry for entry in ledger_pool if entry.payment_ref == settlement.settlement_id
    )
    try:
        return aggregate_ledger_total(linked_entries, settlement.currency)
    except CurrencyMismatchError as exc:
        conflicting_ids = sorted(
            entry.id for entry in linked_entries if entry.currency != settlement.currency
        )
        raise ObservationCurrencyConflictError(
            f"Settlement {settlement.settlement_id} has structurally linked ledger "
            f"entries denominated outside its currency ({settlement.currency}): "
            f"{conflicting_ids}. Refusing to silently drop or partially aggregate "
            "mismatched-currency entries."
        ) from exc
