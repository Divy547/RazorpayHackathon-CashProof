"""Tests verifying Phase 1 financial invariants on generated synthetic datasets."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from cashproof.benchmark.generator.builder import (
    SyntheticGenerationError,
    _validate_dataset_invariants,
    generate_dataset,
)
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import GroundTruth, Resolvability, ScenarioFamily
from cashproof.domain.money import calculate_gst_on_fee, calculate_settlement_item_net
from cashproof.domain.source import (
    Refund,
    Settlement,
    SettlementItem,
    validate_refund_netting_invariant,
    validate_settlement_items_aggregation,
)
from cashproof.domain.types import Currency, RefundStatus
from hypothesis import given, settings
from hypothesis import strategies as st


def test_generator_standard_invariants_pass() -> None:
    config = GeneratorConfig(seed=42, num_settlements=50)
    dataset = generate_dataset(config)

    assert len(dataset.settlements) == 50
    assert len(dataset.ground_truths) == 50
    assert len(dataset.payments) >= 50
    assert len(dataset.settlement_items) >= 50
    assert len(dataset.ledger_entries) >= 50

    # 1. SettlementItem bridge arithmetic and GST
    for item in dataset.settlement_items:
        expected_net = calculate_settlement_item_net(
            gross_minor=item.gross_minor,
            fee_minor=item.fee_minor,
            tax_on_fee_minor=item.tax_on_fee_minor,
            netted_refund_minor=item.netted_refund_minor,
            adjustment_minor=item.adjustment_minor,
        )
        assert item.computed_net_minor == expected_net
        assert item.tax_on_fee_minor == calculate_gst_on_fee(item.fee_minor)

    # 2. Settlement aggregation invariant
    items_by_settlement: dict[str, list[SettlementItem]] = {
        s.settlement_id: [] for s in dataset.settlements
    }
    for it in dataset.settlement_items:
        items_by_settlement[it.settlement_id].append(it)

    for settlement in dataset.settlements:
        items = items_by_settlement[settlement.settlement_id]
        validate_settlement_items_aggregation(settlement, items)

    # 3. Refund netting invariant
    validate_refund_netting_invariant(dataset.settlement_items, dataset.refunds)

    # 4. Non-negative magnitudes
    for le in dataset.ledger_entries:
        assert le.amount_minor >= 0
    for p in dataset.payments:
        assert p.gross_minor >= 0
    for r in dataset.refunds:
        assert r.amount_minor >= 0


@given(seed=st.integers(min_value=0, max_value=2**31 - 1))
@settings(max_examples=5, deadline=None)
def test_property_generator_invariants_hold_across_seeds(seed: int) -> None:
    """Hypothesis property test verifying invariant preservation across arbitrary seeds."""
    config = GeneratorConfig(seed=seed, num_settlements=50)
    dataset = generate_dataset(config)

    # Validate all items have correct bridge net and GST
    for item in dataset.settlement_items:
        assert item.computed_net_minor == calculate_settlement_item_net(
            item.gross_minor,
            item.fee_minor,
            item.tax_on_fee_minor,
            item.netted_refund_minor,
            item.adjustment_minor,
        )
        assert item.tax_on_fee_minor == calculate_gst_on_fee(item.fee_minor)

    # Validate settlement aggregation
    items_by_settlement: dict[str, list[SettlementItem]] = {
        s.settlement_id: [] for s in dataset.settlements
    }
    for it in dataset.settlement_items:
        items_by_settlement[it.settlement_id].append(it)

    for settlement in dataset.settlements:
        validate_settlement_items_aggregation(
            settlement, items_by_settlement[settlement.settlement_id]
        )

    # Validate refund netting invariant
    validate_refund_netting_invariant(dataset.settlement_items, dataset.refunds)


def test_validate_dataset_invariants_negative_gst_mismatch() -> None:
    """Negative-path: proves _validate_dataset_invariants catches tax/GST mismatch."""
    dt = datetime(2026, 8, 1, tzinfo=UTC)
    settlement = Settlement(
        settlement_id="set_test1",
        net_deposited_minor=9764,
        currency=Currency.INR,
        settled_at=dt,
    )
    # Fee is 200, expected GST is 36, but tax_on_fee_minor is corrupted to 30
    corrupted_item = SettlementItem(
        item_id="item_test1",
        settlement_id="set_test1",
        payment_id="pay_test1",
        gross_minor=10000,
        fee_minor=200,
        tax_on_fee_minor=30,  # Corrupted GST
        netted_refund_minor=0,
        adjustment_minor=0,
        computed_net_minor=9770,
    )
    gt = GroundTruth(
        case_id="set_test1",
        resolvability=Resolvability.PROVABLE,
        exact_target_ledger_entry_ids=["le_1"],
        justifying_evidence=[],
        scenario_family=ScenarioFamily.S1_STRUCTURED_EXACT,
    )

    with pytest.raises(SyntheticGenerationError, match="tax_on_fee_minor .* != expected GST"):
        _validate_dataset_invariants([settlement], [corrupted_item], [], [gt])


def test_validate_dataset_invariants_negative_settlement_sum_mismatch() -> None:
    """Negative-path: proves _validate_dataset_invariants catches settlement sum mismatch."""
    dt = datetime(2026, 8, 1, tzinfo=UTC)
    # Settlement net is 10000, but item computed net is 9764
    settlement = Settlement(
        settlement_id="set_test2",
        net_deposited_minor=10000,
        currency=Currency.INR,
        settled_at=dt,
    )
    item = SettlementItem(
        item_id="item_test2",
        settlement_id="set_test2",
        payment_id="pay_test2",
        gross_minor=10000,
        fee_minor=200,
        tax_on_fee_minor=36,
        netted_refund_minor=0,
        adjustment_minor=0,
        computed_net_minor=9764,
    )
    gt = GroundTruth(
        case_id="set_test2",
        resolvability=Resolvability.PROVABLE,
        exact_target_ledger_entry_ids=["le_1"],
        justifying_evidence=[],
        scenario_family=ScenarioFamily.S1_STRUCTURED_EXACT,
    )

    with pytest.raises(SyntheticGenerationError, match="failed aggregation validation"):
        _validate_dataset_invariants([settlement], [item], [], [gt])


def test_validate_dataset_invariants_negative_refund_netting_mismatch() -> None:
    """Negative-path: proves _validate_dataset_invariants catches refund netting mismatch."""
    dt = datetime(2026, 8, 1, tzinfo=UTC)
    settlement = Settlement(
        settlement_id="set_test3",
        net_deposited_minor=4764,
        currency=Currency.INR,
        settled_at=dt,
    )
    item = SettlementItem(
        item_id="item_test3",
        settlement_id="set_test3",
        payment_id="pay_test3",
        gross_minor=10000,
        fee_minor=200,
        tax_on_fee_minor=36,
        netted_refund_minor=5000,  # Claims 5000 refund
        adjustment_minor=0,
        computed_net_minor=4764,
    )
    # But refund record amount is 4000
    mismatched_refund = Refund(
        refund_id="rf_test3",
        payment_id="pay_test3",
        amount_minor=4000,
        currency=Currency.INR,
        created_at=dt,
        status=RefundStatus.PROCESSED,
        netted_into_settlement=True,
    )
    gt = GroundTruth(
        case_id="set_test3",
        resolvability=Resolvability.PROVABLE,
        exact_target_ledger_entry_ids=["le_1"],
        justifying_evidence=[],
        scenario_family=ScenarioFamily.S1_STRUCTURED_EXACT,
    )

    with pytest.raises(SyntheticGenerationError, match="Refund netting invariant failed"):
        _validate_dataset_invariants([settlement], [item], [mismatched_refund], [gt])


def test_validate_dataset_invariants_negative_unmatched_ground_truth_case_id() -> None:
    """Negative-path: proves _validate_dataset_invariants catches invalid GroundTruth case_id."""
    dt = datetime(2026, 8, 1, tzinfo=UTC)
    settlement = Settlement(
        settlement_id="set_test4",
        net_deposited_minor=9764,
        currency=Currency.INR,
        settled_at=dt,
    )
    item = SettlementItem(
        item_id="item_test4",
        settlement_id="set_test4",
        payment_id="pay_test4",
        gross_minor=10000,
        fee_minor=200,
        tax_on_fee_minor=36,
        netted_refund_minor=0,
        adjustment_minor=0,
        computed_net_minor=9764,
    )
    # GT points to non-existent settlement "set_ghost"
    ghost_gt = GroundTruth(
        case_id="set_ghost",
        resolvability=Resolvability.PROVABLE,
        exact_target_ledger_entry_ids=["le_1"],
        justifying_evidence=[],
        scenario_family=ScenarioFamily.S1_STRUCTURED_EXACT,
    )

    with pytest.raises(SyntheticGenerationError, match="does not match any Settlement"):
        _validate_dataset_invariants([settlement], [item], [], [ghost_gt])
