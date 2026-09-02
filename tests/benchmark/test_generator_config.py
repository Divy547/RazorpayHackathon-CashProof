"""Unit tests for synthetic dataset generator configuration models."""

from __future__ import annotations

import pytest
from cashproof.benchmark.generator.config import GeneratorConfig, ScenarioDistribution
from cashproof.domain.types import Currency


def test_generator_config_valid_defaults() -> None:
    config = GeneratorConfig(seed=42)
    assert config.seed == 42
    assert config.num_settlements == 100
    assert config.generator_version == "1.0.0"
    assert config.currency == Currency.INR
    assert config.min_items_per_settlement == 1
    assert config.max_items_per_settlement == 5
    assert config.refund_probability == 0.20
    assert config.noise_ratio == 0.30


def test_generator_config_num_settlements_minimum_enforced() -> None:
    with pytest.raises(ValueError, match="num_settlements must be >= 50"):
        GeneratorConfig(seed=42, num_settlements=49)

    # 50 is the valid lower bound
    config = GeneratorConfig(seed=42, num_settlements=50)
    assert config.num_settlements == 50


def test_generator_config_invalid_item_bounds() -> None:
    with pytest.raises(ValueError, match="Invalid items_per_settlement bounds"):
        GeneratorConfig(seed=42, min_items_per_settlement=0)

    with pytest.raises(ValueError, match="Invalid items_per_settlement bounds"):
        GeneratorConfig(seed=42, min_items_per_settlement=5, max_items_per_settlement=3)


def test_generator_config_invalid_refund_probability() -> None:
    with pytest.raises(ValueError, match="refund_probability must be between 0.0 and 1.0"):
        GeneratorConfig(seed=42, refund_probability=-0.1)

    with pytest.raises(ValueError, match="refund_probability must be between 0.0 and 1.0"):
        GeneratorConfig(seed=42, refund_probability=1.5)


def test_generator_config_invalid_noise_ratio() -> None:
    with pytest.raises(ValueError, match="noise_ratio must be non-negative"):
        GeneratorConfig(seed=42, noise_ratio=-0.5)


def test_generator_config_empty_version() -> None:
    with pytest.raises(ValueError, match="generator_version must not be empty"):
        GeneratorConfig(seed=42, generator_version="   ")


def test_scenario_distribution_sum_validation() -> None:
    with pytest.raises(ValueError, match="ScenarioDistribution weights must sum to 1.0"):
        ScenarioDistribution(s1_structured_exact=0.50, s2_structured_ambiguous=0.60)


def test_scenario_distribution_negative_weight() -> None:
    with pytest.raises(ValueError, match="ScenarioDistribution weights must be non-negative"):
        ScenarioDistribution(s1_structured_exact=-0.10, s2_structured_ambiguous=0.65)
