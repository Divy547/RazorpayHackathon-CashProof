"""Tests ensuring generated source records contain zero scenario labels or leakage tells."""

from __future__ import annotations

import re

from cashproof.benchmark.generator import generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig

FORBIDDEN_ATTRIBUTES: tuple[str, ...] = (
    "is_decoy",
    "is_noise",
    "scenario_label",
    "scenario_family",
    "scenario_type",
    "ground_truth_id",
    "is_truth",
    "is_corrupted",
)


def test_source_entities_have_zero_forbidden_attributes() -> None:
    config = GeneratorConfig(seed=42, num_settlements=50)
    dataset = generate_dataset(config)

    all_source_records = (
        list(dataset.payments)
        + list(dataset.refunds)
        + list(dataset.settlements)
        + list(dataset.settlement_items)
        + list(dataset.ledger_entries)
    )

    for record in all_source_records:
        record_attrs = dir(record)
        for forbidden in FORBIDDEN_ATTRIBUTES:
            assert forbidden not in record_attrs, (
                f"Source entity {type(record).__name__} contains forbidden attribute '{forbidden}'"
            )


def test_id_format_invariance_across_all_records() -> None:
    config = GeneratorConfig(seed=42, num_settlements=50)
    dataset = generate_dataset(config)

    pay_pattern = re.compile(r"^pay_[0-9a-f]{12}$")
    rf_pattern = re.compile(r"^rf_[0-9a-f]{12}$")
    set_pattern = re.compile(r"^set_[0-9a-f]{12}$")
    item_pattern = re.compile(r"^item_[0-9a-f]{12}$")
    le_pattern = re.compile(r"^le_[0-9a-f]{12}$")

    for p in dataset.payments:
        assert pay_pattern.match(p.id), f"Payment ID {p.id} violates uniform format"

    for r in dataset.refunds:
        assert rf_pattern.match(r.refund_id), f"Refund ID {r.refund_id} fails format"

    for s in dataset.settlements:
        assert set_pattern.match(s.settlement_id), f"Settlement ID {s.settlement_id} fails format"

    for it in dataset.settlement_items:
        assert item_pattern.match(it.item_id), f"SettlementItem ID {it.item_id} fails format"

    for le in dataset.ledger_entries:
        assert le_pattern.match(le.id), f"LedgerEntry ID {le.id} violates uniform format"


def test_temporal_dispersion_across_scenarios() -> None:
    """Verifies timestamps across scenarios are not segregated by date."""
    config = GeneratorConfig(seed=42, num_settlements=50)
    dataset = generate_dataset(config)

    # Check that settlements and ledger entries span across multiple days
    settlement_days = {s.settled_at.day for s in dataset.settlements}
    assert len(settlement_days) >= 5, "Settlements should be distributed across multiple days"

    ledger_days = {le.timestamp.day for le in dataset.ledger_entries}
    assert len(ledger_days) >= 5, "Ledger entries should be distributed across multiple days"
