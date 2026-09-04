"""CashProof Benchmark layer: dataset generation, evaluation, and benchmarking."""

from cashproof.benchmark.confidence import (
    AutomationOpportunity,
    ConfidenceBucket,
    ConfidenceEvaluator,
    ConfidenceObservation,
    ConfidenceReport,
    GateConfidenceCell,
    ScenarioConfidenceMetric,
    SourceConfidenceMetric,
    ThresholdMetric,
)
from cashproof.benchmark.evaluator import (
    BenchmarkEvaluationError,
    BenchmarkEvaluator,
)
from cashproof.benchmark.generator import (
    CURRENT_GENERATOR_VERSION,
    GeneratedDataset,
    GeneratorConfig,
    ScenarioDistribution,
    SyntheticGenerationError,
    generate_dataset,
)
from cashproof.benchmark.models import (
    AIMetrics,
    BenchmarkRun,
    BenchmarkTiming,
    CaseEvaluation,
    GroundTruth,
    OverallMetrics,
    Resolvability,
    ScenarioFamily,
    ScenarioMetrics,
)
from cashproof.benchmark.runner import BenchmarkRunner
from cashproof.benchmark.service import InMemoryBenchmarkService

__version__ = "0.1.0"

__all__ = [
    "AIMetrics",
    "AutomationOpportunity",
    "BenchmarkEvaluationError",
    "BenchmarkEvaluator",
    "BenchmarkRun",
    "BenchmarkRunner",
    "BenchmarkTiming",
    "CURRENT_GENERATOR_VERSION",
    "CaseEvaluation",
    "ConfidenceBucket",
    "ConfidenceEvaluator",
    "ConfidenceObservation",
    "ConfidenceReport",
    "GateConfidenceCell",
    "GeneratedDataset",
    "GeneratorConfig",
    "GroundTruth",
    "InMemoryBenchmarkService",
    "OverallMetrics",
    "Resolvability",
    "ScenarioConfidenceMetric",
    "ScenarioDistribution",
    "ScenarioFamily",
    "ScenarioMetrics",
    "SourceConfidenceMetric",
    "SyntheticGenerationError",
    "ThresholdMetric",
    "generate_dataset",
]
