"""Tests for compute_observed_ledger_state(): the authoritative, hypothesis-independent
observed ledger state.

Proves the observation is derived purely from Settlement + the full ledger pool via
structural payment_ref linkage, using ONLY hand-built fixtures (never the Phase 2
generator, never MatchCandidate/classifier output) - so these tests cannot pass by
accident through any candidate-ranking side effect.
"""

from __future__ import annotations

import inspect
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cashproof.application.observation import (
    ObservationCurrencyConflictError,
    compute_observed_ledger_state,
)
from cashproof.domain.source import LedgerEntry, Settlement
from cashproof.domain.types import Currency, Direction

DT = datetime(2026, 8, 1, tzinfo=UTC)


def _settlement(settlement_id: str = "set_1", net_deposited_minor: int = 100_000) -> Settlement:
    return Settlement(
        settlement_id=settlement_id,
        net_deposited_minor=net_deposited_minor,
        currency=Currency.INR,
        settled_at=DT,
    )


def _entry(
    entry_id: str,
    amount_minor: int,
    payment_ref: str | None,
    narration: str | None = None,
    direction: Direction = Direction.CREDIT,
    currency: Currency = Currency.INR,
) -> LedgerEntry:
    return LedgerEntry(
        id=entry_id,
        amount_minor=amount_minor,
        currency=currency,
        timestamp=DT,
        direction=direction,
        payment_ref=payment_ref,
        external_ref=None,
        narration=narration,
        customer_name=None,
    )


def test_s1_single_structural_match_observed_equals_amount() -> None:
    """S1: one legitimate structurally-linked ledger record -> observed = its amount."""
    settlement = _settlement(net_deposited_minor=100_000)
    target = _entry("le_1", 100_000, payment_ref="set_1")
    noise = _entry("le_noise", 50_000, payment_ref=None, narration="SALARY-BATCH")

    observed = compute_observed_ledger_state(settlement, [noise, target])

    assert observed == 100_000


def test_s2_duplicate_structural_matches_sum_both() -> None:
    """S2: two structurally-linked ledger records (genuine ledger-side duplication) ->
    observed = sum of both, NOT zero, NOT a single-candidate pick.
    """
    settlement = _settlement(net_deposited_minor=100_000)
    target = _entry("le_1", 100_000, payment_ref="set_1")
    decoy = _entry("le_2", 100_000, payment_ref="set_1")

    observed = compute_observed_ledger_state(settlement, [target, decoy])

    assert observed == 200_000
    # Independent of ordering: the observation is a set-derived sum, not a ranking pick.
    assert observed == compute_observed_ledger_state(settlement, [decoy, target])


def test_s3_structural_match_with_wrong_amount_reports_wrong_amount() -> None:
    """S3: one structurally-linked record with the wrong amount -> observed = that
    (wrong) amount, faithfully reflecting the true discrepancy.
    """
    settlement = _settlement(net_deposited_minor=100_000)
    mismatched = _entry("le_1", 95_000, payment_ref="set_1")

    observed = compute_observed_ledger_state(settlement, [mismatched])

    assert observed == 95_000


def test_s4_text_only_reference_yields_zero_structural_observation() -> None:
    """S4: an entry only linkable via narration text (payment_ref stripped) contributes
    nothing to the structural observation - text-derived attribution is an inference,
    not a source-asserted fact.
    """
    settlement = _settlement(net_deposited_minor=100_000)
    text_linked = _entry(
        "le_1", 100_000, payment_ref=None, narration="CMS/NETBANK/EXT-ORD-202608-ABCDEF/RZP-PAYOUT"
    )

    observed = compute_observed_ledger_state(settlement, [text_linked])

    assert observed == 0


def test_s5_alias_only_reference_yields_zero_structural_observation() -> None:
    """S5: an entry only linkable via a customer-name alias in narration (payment_ref
    stripped) contributes nothing to the structural observation, same reasoning as S4.
    """
    settlement = _settlement(net_deposited_minor=100_000)
    alias_linked = _entry("le_1", 100_000, payment_ref=None, narration="UPI-P2M-DIYASHARMA-PAYMENT")

    observed = compute_observed_ledger_state(settlement, [alias_linked])

    assert observed == 0


def test_s6_no_corresponding_record_is_zero() -> None:
    """S6: no ledger record corresponds to this settlement at all -> observed = 0."""
    settlement = _settlement(net_deposited_minor=100_000)
    unrelated = _entry("le_other", 100_000, payment_ref="set_2")
    noise = _entry("le_noise", 5_000, payment_ref=None, narration="GST-PAYMENT-GOV")

    observed = compute_observed_ledger_state(settlement, [unrelated, noise])

    assert observed == 0


def test_direction_signing_is_preserved_via_aggregate_ledger_total() -> None:
    """A structurally-linked DEBIT (e.g. a reversal referencing this settlement) nets
    against linked CREDITs, exactly as aggregate_ledger_total already defines.
    """
    settlement = _settlement(net_deposited_minor=100_000)
    credit = _entry("le_1", 100_000, payment_ref="set_1", direction=Direction.CREDIT)
    reversal = _entry("le_2", 20_000, payment_ref="set_1", direction=Direction.DEBIT)

    observed = compute_observed_ledger_state(settlement, [credit, reversal])

    assert observed == 80_000


def test_currency_mismatch_among_structurally_linked_entries_fails_closed() -> None:
    """A structurally linked entry denominated in a foreign currency must never be
    silently dropped or partially summed - the observation must raise loudly,
    naming the settlement and the conflicting entry, rather than guess.
    """
    settlement = _settlement(net_deposited_minor=100_000)
    inr_entry = _entry("le_1", 100_000, payment_ref="set_1", currency=Currency.INR)
    usd_entry = _entry("le_2", 100_000, payment_ref="set_1", currency=Currency.USD)

    with pytest.raises(ObservationCurrencyConflictError, match="set_1.*le_2"):
        compute_observed_ledger_state(settlement, [inr_entry, usd_entry])


def test_observation_signature_takes_no_candidate_or_hypothesis_input() -> None:
    """Structural proof of independence: the function cannot even accept
    MatchCandidate/classifier/proposed-target/disposition input - there is no
    parameter through which one could be threaded in.
    """
    params = set(inspect.signature(compute_observed_ledger_state).parameters)
    assert params == {"settlement", "ledger_pool"}


def test_observation_module_does_not_import_classifier_or_matcher() -> None:
    """observation.py must never depend on candidate ranking, scoring, or
    classification - enforced directly against the source file, not just by
    the function signature.
    """
    module_path = (
        Path(__file__).resolve().parent.parent.parent
        / "packages"
        / "application"
        / "src"
        / "cashproof"
        / "application"
        / "observation.py"
    )
    content = module_path.read_text(encoding="utf-8")
    assert "classifier" not in content
    assert "matcher" not in content
    assert "MatchCandidate" not in content
    assert "ScenarioFamily" not in content
    assert "GroundTruth" not in content
