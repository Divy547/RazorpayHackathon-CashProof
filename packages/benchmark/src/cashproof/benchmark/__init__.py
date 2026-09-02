"""CashProof Benchmark layer: dataset generation, evaluation, and benchmarking."""

from cashproof.benchmark.generator import (
    CURRENT_GENERATOR_VERSION,
    GeneratedDataset,
    GeneratorConfig,
    ScenarioDistribution,
    SyntheticGenerationError,
    generate_dataset,
)
from cashproof.benchmark.models import (
    BenchmarkRun,
    GroundTruth,
    Resolvability,
    ScenarioFamily,
)

__version__ = "0.1.0"

__all__ = [
    "CURRENT_GENERATOR_VERSION",
    "BenchmarkRun",
    "GeneratedDataset",
    "GeneratorConfig",
    "GroundTruth",
    "Resolvability",
    "ScenarioDistribution",
    "ScenarioFamily",
    "SyntheticGenerationError",
    "generate_dataset",
]
