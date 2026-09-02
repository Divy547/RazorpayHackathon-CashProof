"""Top-level dataset assembly, post-generation validation, and packaging."""

from __future__ import annotations

from dataclasses import dataclass

from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.generator.noise import generate_background_noise
from cashproof.benchmark.generator.prng import DeterministicRNG
from cashproof.benchmark.generator.scenarios import (
    allocate_scenarios,
    apply_scenario_transformations,
)
from cashproof.benchmark.generator.world import build_baseline_world
from cashproof.benchmark.models import GroundTruth
from cashproof.domain.money import calculate_gst_on_fee
from cashproof.domain.source import (
    LedgerEntry,
    Payment,
    Refund,
    Settlement,
    SettlementItem,
    validate_refund_netting_invariant,
    validate_settlement_items_aggregation,
)


class SyntheticGenerationError(Exception):
    """Raised when generated synthetic data violates financial or structural invariants."""


@dataclass(frozen=True, slots=True)
class GeneratedDataset:
    """Complete generated synthetic world with decoupled source facts and evaluator truth."""

    payments: tuple[Payment, ...]
    refunds: tuple[Refund, ...]
    settlements: tuple[Settlement, ...]
    settlement_items: tuple[SettlementItem, ...]
    ledger_entries: tuple[LedgerEntry, ...]
    ground_truths: tuple[GroundTruth, ...]
    config: GeneratorConfig
    metadata: tuple[tuple[str, str], ...]


def generate_dataset(config: GeneratorConfig) -> GeneratedDataset:
    """Generate a reproducible, invariant-checked synthetic world and benchmark ground truth."""
    rng = DeterministicRNG(config.seed)

    # 1. Generate clean baseline world
    baseline_cases = build_baseline_world(config, rng)

    # 2. Deterministically allocate scenarios ensuring full S1-S6 coverage
    allocations = allocate_scenarios(len(baseline_cases), config.scenario_distribution, rng)

    # 3. Apply scenario transformations and construct paired GroundTruth
    transformed_cases = apply_scenario_transformations(baseline_cases, allocations, rng)

    # 4. Collect source entities
    all_payments: list[Payment] = []
    all_refunds: list[Refund] = []
    all_settlements: list[Settlement] = []
    all_items: list[SettlementItem] = []
    target_ledger_entries: list[LedgerEntry] = []
    all_ground_truths: list[GroundTruth] = []

    for case in transformed_cases:
        all_settlements.append(case.settlement)
        all_items.extend(case.items)
        all_payments.extend(case.payments)
        all_refunds.extend(case.refunds)
        target_ledger_entries.extend(case.ledger_entries)
        all_ground_truths.append(case.ground_truth)

    # 5. Generate background distractor ledger activity
    noise_entries = generate_background_noise(config, len(target_ledger_entries), rng)
    all_ledger_entries = list(target_ledger_entries) + list(noise_entries)

    # 6. Post-generation invariant validation pipeline
    _validate_dataset_invariants(all_settlements, all_items, all_refunds, all_ground_truths)

    # 7. Deterministic shuffling so list ordering conveys zero scenario information
    rng.shuffle(all_payments)
    rng.shuffle(all_refunds)
    rng.shuffle(all_settlements)
    rng.shuffle(all_items)
    rng.shuffle(all_ledger_entries)
    rng.shuffle(all_ground_truths)

    metadata: tuple[tuple[str, str], ...] = (
        ("generator_version", config.generator_version),
        ("seed", str(config.seed)),
        ("num_settlements", str(len(all_settlements))),
        ("num_payments", str(len(all_payments))),
        ("num_refunds", str(len(all_refunds))),
        ("num_items", str(len(all_items))),
        ("num_ledger_entries", str(len(all_ledger_entries))),
        ("num_ground_truths", str(len(all_ground_truths))),
    )

    return GeneratedDataset(
        payments=tuple(all_payments),
        refunds=tuple(all_refunds),
        settlements=tuple(all_settlements),
        settlement_items=tuple(all_items),
        ledger_entries=tuple(all_ledger_entries),
        ground_truths=tuple(all_ground_truths),
        config=config,
        metadata=metadata,
    )


def _validate_dataset_invariants(
    settlements: list[Settlement],
    items: list[SettlementItem],
    refunds: list[Refund],
    ground_truths: list[GroundTruth],
) -> None:
    """Verify that all Phase 1 source invariants hold across generated records."""
    items_by_settlement: dict[str, list[SettlementItem]] = {}
    for item in items:
        items_by_settlement.setdefault(item.settlement_id, []).append(item)
        # Check GST calculation
        expected_gst = calculate_gst_on_fee(item.fee_minor)
        if item.tax_on_fee_minor != expected_gst:
            raise SyntheticGenerationError(
                f"SettlementItem {item.item_id} tax_on_fee_minor ({item.tax_on_fee_minor}) "
                f"!= expected GST ({expected_gst})"
            )

    # Validate settlement aggregation for each settlement
    for settlement in settlements:
        settlement_items = items_by_settlement.get(settlement.settlement_id, [])
        try:
            validate_settlement_items_aggregation(settlement, settlement_items)
        except Exception as e:
            raise SyntheticGenerationError(
                f"Settlement {settlement.settlement_id} failed aggregation validation: {e}"
            ) from e

    # Validate refund netting invariant across all items and refunds
    try:
        validate_refund_netting_invariant(items, refunds)
    except Exception as e:
        raise SyntheticGenerationError(f"Refund netting invariant failed: {e}") from e

    # Validate GroundTruth join key correspondence (case_id == settlement_id)
    settlement_ids = {s.settlement_id for s in settlements}
    for gt in ground_truths:
        if gt.case_id not in settlement_ids:
            raise SyntheticGenerationError(
                f"GroundTruth case_id '{gt.case_id}' does not match any Settlement settlement_id."
            )
