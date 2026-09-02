"""Synthetic financial world generator for the CashProof benchmark."""

from cashproof.benchmark.generator.builder import (
    GeneratedDataset,
    SyntheticGenerationError,
    generate_dataset,
)
from cashproof.benchmark.generator.config import (
    GeneratorConfig,
    ScenarioDistribution,
)

CURRENT_GENERATOR_VERSION: str = "1.0.0"

__all__ = [
    "CURRENT_GENERATOR_VERSION",
    "GeneratedDataset",
    "GeneratorConfig",
    "ScenarioDistribution",
    "SyntheticGenerationError",
    "generate_dataset",
]
