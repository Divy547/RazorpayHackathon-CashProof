"""Configuration models for the CashProof synthetic dataset generator."""

from __future__ import annotations

from dataclasses import dataclass, field

from cashproof.domain.types import Currency


@dataclass(frozen=True, slots=True)
class ScenarioDistribution:
    """Target percentage weights for benchmark scenarios S1-S6."""

    s1_structured_exact: float = 0.40
    s2_structured_ambiguous: float = 0.15
    s3_financial_mismatch: float = 0.15
    s4_external_ref_text: float = 0.10
    s5_narration_alias_text: float = 0.10
    s6_non_provable_conflict: float = 0.10

    def __post_init__(self) -> None:
        weights = (
            self.s1_structured_exact,
            self.s2_structured_ambiguous,
            self.s3_financial_mismatch,
            self.s4_external_ref_text,
            self.s5_narration_alias_text,
            self.s6_non_provable_conflict,
        )
        for w in weights:
            if w < 0.0:
                raise ValueError(f"ScenarioDistribution weights must be non-negative, got {w}")
        total = sum(weights)
        if not (0.999 <= total <= 1.001):
            raise ValueError(f"ScenarioDistribution weights must sum to 1.0, got {total}")


@dataclass(frozen=True, slots=True)
class GeneratorConfig:
    """Top-level dataset generator configuration.

    Each generated Settlement corresponds to exactly one benchmark case.
    Benchmark scale requires at least 50 benchmark cases (enforced num_settlements >= 50).
    """

    seed: int
    num_settlements: int = 100
    generator_version: str = "1.0.0"
    min_items_per_settlement: int = 1
    max_items_per_settlement: int = 5
    refund_probability: float = 0.20
    noise_ratio: float = 0.30
    currency: Currency = Currency.INR
    scenario_distribution: ScenarioDistribution = field(default_factory=ScenarioDistribution)

    def __post_init__(self) -> None:
        if self.num_settlements < 50:
            raise ValueError("num_settlements must be >= 50 to satisfy benchmark scale requirement")
        if (
            self.min_items_per_settlement < 1
            or self.max_items_per_settlement < self.min_items_per_settlement
        ):
            raise ValueError("Invalid items_per_settlement bounds")
        if not (0.0 <= self.refund_probability <= 1.0):
            raise ValueError("refund_probability must be between 0.0 and 1.0")
        if self.noise_ratio < 0.0:
            raise ValueError("noise_ratio must be non-negative")
        if not self.generator_version.strip():
            raise ValueError("generator_version must not be empty")
