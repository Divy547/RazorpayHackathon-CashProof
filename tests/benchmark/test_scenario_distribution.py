"""Tests verifying deterministic scenario allocation and distribution coverage."""

from __future__ import annotations

from collections import Counter

from cashproof.benchmark.generator import generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig, ScenarioDistribution
from cashproof.benchmark.generator.prng import DeterministicRNG
from cashproof.benchmark.generator.scenarios import allocate_scenarios
from cashproof.benchmark.models import ScenarioFamily


def test_scenario_allocation_guarantees_all_families_represented() -> None:
    rng = DeterministicRNG(42)
    dist = ScenarioDistribution()

    # For 50 cases, all 6 families must be represented
    alloc50 = allocate_scenarios(50, dist, rng)
    counts50 = Counter(alloc50)
    for family in ScenarioFamily:
        assert counts50[family] >= 1

    # For 100 cases, all 6 families must be represented
    alloc100 = allocate_scenarios(100, dist, rng)
    counts100 = Counter(alloc100)
    for family in ScenarioFamily:
        assert counts100[family] >= 1


def test_scenario_allocation_51_cases() -> None:
    """Explicitly tests allocation edge case with odd number of settlements (51)."""
    rng = DeterministicRNG(42)
    dist = ScenarioDistribution()

    alloc51 = allocate_scenarios(51, dist, rng)
    counts51 = Counter(alloc51)
    assert sum(counts51.values()) == 51
    for family in ScenarioFamily:
        assert counts51[family] >= 1, f"Family {family} missing in 51-case allocation"


def test_scenario_allocation_1000_cases() -> None:
    """Explicitly tests allocation scale with large settlement count (1000)."""
    rng = DeterministicRNG(42)
    dist = ScenarioDistribution()

    alloc1000 = allocate_scenarios(1000, dist, rng)
    counts1000 = Counter(alloc1000)
    assert sum(counts1000.values()) == 1000
    for family in ScenarioFamily:
        assert counts1000[family] >= 1

    # Approximate check for 1000 cases against weights
    # S1 ~400, S2 ~150, S3 ~150, S4 ~100, S5 ~100, S6 ~100
    assert 380 <= counts1000[ScenarioFamily.S1_STRUCTURED_EXACT] <= 420
    assert 130 <= counts1000[ScenarioFamily.S2_STRUCTURED_AMBIGUOUS] <= 170
    assert 130 <= counts1000[ScenarioFamily.S3_FINANCIAL_MISMATCH] <= 170
    assert 80 <= counts1000[ScenarioFamily.S4_EXTERNAL_REF_TEXT] <= 120
    assert 80 <= counts1000[ScenarioFamily.S5_NARRATION_ALIAS_TEXT] <= 120
    assert 80 <= counts1000[ScenarioFamily.S6_NON_PROVABLE_CONFLICT] <= 120


def test_generated_dataset_scenario_coverage_100_cases() -> None:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)

    families = [gt.scenario_family for gt in dataset.ground_truths]
    counts = Counter(families)

    assert len(dataset.ground_truths) == 100
    # Every scenario family S1-S6 must have at least one case
    for family in ScenarioFamily:
        assert counts[family] >= 1, f"Family {family} had 0 cases in generated dataset"

    # Verify approximate adherence to weights (S1 ~40, S2 ~15, S3 ~15, S4 ~10, S5 ~10, S6 ~10)
    assert 35 <= counts[ScenarioFamily.S1_STRUCTURED_EXACT] <= 45
    assert 10 <= counts[ScenarioFamily.S2_STRUCTURED_AMBIGUOUS] <= 20
    assert 10 <= counts[ScenarioFamily.S3_FINANCIAL_MISMATCH] <= 20
    assert 5 <= counts[ScenarioFamily.S4_EXTERNAL_REF_TEXT] <= 15
    assert 5 <= counts[ScenarioFamily.S5_NARRATION_ALIAS_TEXT] <= 15
    assert 5 <= counts[ScenarioFamily.S6_NON_PROVABLE_CONFLICT] <= 15
