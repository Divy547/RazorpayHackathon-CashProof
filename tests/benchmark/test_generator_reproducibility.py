"""Tests verifying deterministic reproducibility and versioning discipline."""

from __future__ import annotations

import random

from cashproof.benchmark.generator import CURRENT_GENERATOR_VERSION, generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig


def test_generator_deterministic_reproducibility_same_seed() -> None:
    """Proves that identical seed and config produce identical logical datasets."""
    config1 = GeneratorConfig(seed=12345, num_settlements=50)
    config2 = GeneratorConfig(seed=12345, num_settlements=50)

    ds1 = generate_dataset(config1)
    ds2 = generate_dataset(config2)

    assert len(ds1.settlements) == len(ds2.settlements)
    assert len(ds1.payments) == len(ds2.payments)
    assert len(ds1.refunds) == len(ds2.refunds)
    assert len(ds1.settlement_items) == len(ds2.settlement_items)
    assert len(ds1.ledger_entries) == len(ds2.ledger_entries)
    assert len(ds1.ground_truths) == len(ds2.ground_truths)

    # Verify identical entity values and IDs
    assert [s.settlement_id for s in ds1.settlements] == [s.settlement_id for s in ds2.settlements]
    assert [p.id for p in ds1.payments] == [p.id for p in ds2.payments]
    assert [le.id for le in ds1.ledger_entries] == [le.id for le in ds2.ledger_entries]
    assert [gt.case_id for gt in ds1.ground_truths] == [gt.case_id for gt in ds2.ground_truths]

    # Verify full dataclass equality
    assert ds1.settlements == ds2.settlements
    assert ds1.payments == ds2.payments
    assert ds1.refunds == ds2.refunds
    assert ds1.settlement_items == ds2.settlement_items
    assert ds1.ledger_entries == ds2.ledger_entries
    assert ds1.ground_truths == ds2.ground_truths


def test_generator_distinct_seeds_produce_distinct_datasets() -> None:
    config1 = GeneratorConfig(seed=101, num_settlements=50)
    config2 = GeneratorConfig(seed=202, num_settlements=50)

    ds1 = generate_dataset(config1)
    ds2 = generate_dataset(config2)

    assert [s.settlement_id for s in ds1.settlements] != [s.settlement_id for s in ds2.settlements]
    assert [p.id for p in ds1.payments] != [p.id for p in ds2.payments]


def test_generator_version_metadata_persisted() -> None:
    """Generator Version Metadata Test: Verifies CURRENT_GENERATOR_VERSION is in metadata."""
    config = GeneratorConfig(seed=42, num_settlements=50)
    dataset = generate_dataset(config)

    meta_dict = dict(dataset.metadata)
    assert "generator_version" in meta_dict
    assert meta_dict["generator_version"] == CURRENT_GENERATOR_VERSION
    assert meta_dict["generator_version"] == "1.0.0"
    assert meta_dict["seed"] == "42"
    assert meta_dict["num_settlements"] == "50"


def test_rng_global_state_isolation() -> None:
    """Verifies that running generate_dataset does not mutate Python's global random state."""
    random.seed(987654321)
    # Record expected sequence of numbers from global random
    expected_draws = [random.random() for _ in range(5)]

    # Reset seed and re-draw first number
    random.seed(987654321)
    first_draw = random.random()
    assert first_draw == expected_draws[0]

    # Run full dataset generation
    _ = generate_dataset(GeneratorConfig(seed=42, num_settlements=50))

    # Next draw from global random must match expected_draws[1]
    second_draw = random.random()
    assert second_draw == expected_draws[1]


def test_same_seed_different_config_produces_different_dataset() -> None:
    """Proves that changing config parameters with the same seed alters the dataset."""
    config1 = GeneratorConfig(seed=42, num_settlements=50, refund_probability=0.10)
    config2 = GeneratorConfig(seed=42, num_settlements=50, refund_probability=0.80)

    ds1 = generate_dataset(config1)
    ds2 = generate_dataset(config2)

    assert ds1.refunds != ds2.refunds
    assert len(ds1.refunds) != len(ds2.refunds)
