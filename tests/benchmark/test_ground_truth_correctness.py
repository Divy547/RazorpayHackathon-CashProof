"""Tests verifying GroundTruth join key, scenario correctness, and leakage prevention."""

from __future__ import annotations

from cashproof.benchmark.generator import generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.generator.prng import DeterministicRNG
from cashproof.benchmark.generator.scenarios import apply_scenario_transformations
from cashproof.benchmark.generator.world import build_baseline_world
from cashproof.benchmark.models import Resolvability, ScenarioFamily
from cashproof.domain.source import (
    SettlementItem,
    validate_settlement_items_aggregation,
)


def test_ground_truth_join_key_b1_and_zero_reconciliation_case() -> None:
    """Proves B1: GroundTruth.case_id matches Settlement.settlement_id, no cases emitted."""
    config = GeneratorConfig(seed=42, num_settlements=50)
    dataset = generate_dataset(config)

    settlement_ids = {s.settlement_id for s in dataset.settlements}
    assert len(settlement_ids) == 50

    # Every GroundTruth.case_id must be a settlement_id
    for gt in dataset.ground_truths:
        assert gt.case_id in settlement_ids

    # Zero ReconciliationCase objects emitted in Phase 2
    assert not hasattr(dataset, "reconciliation_cases")
    for key in ("cases", "reconciliation_cases", "candidates"):
        assert not hasattr(dataset, key)


def test_ground_truth_s1_structured_exact() -> None:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)

    s1_family = ScenarioFamily.S1_STRUCTURED_EXACT
    s1_gts = [gt for gt in dataset.ground_truths if gt.scenario_family == s1_family]
    assert len(s1_gts) > 0

    settlement_map = {s.settlement_id: s for s in dataset.settlements}
    ledger_map = {le.id: le for le in dataset.ledger_entries}

    for gt in s1_gts:
        assert gt.resolvability == Resolvability.PROVABLE
        assert len(gt.exact_target_ledger_entry_ids) == 1
        target_id = next(iter(gt.exact_target_ledger_entry_ids))
        assert target_id in ledger_map

        target = ledger_map[target_id]
        settlement = settlement_map[gt.case_id]
        assert target.amount_minor == settlement.net_deposited_minor
        assert target.payment_ref == settlement.settlement_id
        assert gt.not_provable_reason is None


def test_ground_truth_s2_genuine_structural_ambiguity_b2() -> None:
    """Proves B1/B2: S2 has multiple identical entries in +-7 days window and is NOT_PROVABLE."""
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)

    s2_family = ScenarioFamily.S2_STRUCTURED_AMBIGUOUS
    s2_gts = [gt for gt in dataset.ground_truths if gt.scenario_family == s2_family]
    assert len(s2_gts) > 0

    settlement_map = {s.settlement_id: s for s in dataset.settlements}

    for gt in s2_gts:
        assert gt.resolvability == Resolvability.NOT_PROVABLE
        assert gt.exact_target_ledger_entry_ids == frozenset()
        assert gt.justifying_evidence == ()
        assert gt.not_provable_reason is not None
        assert "Structured ambiguity" in gt.not_provable_reason

        settlement = settlement_map[gt.case_id]
        # Find matching ledger entries sharing the identical payment_ref and amount
        matching = [
            le
            for le in dataset.ledger_entries
            if le.payment_ref == settlement.settlement_id
            and le.amount_minor == settlement.net_deposited_minor
            and abs((le.timestamp - settlement.settled_at).total_seconds()) <= 7 * 86400
        ]
        assert len(matching) >= 2, f"Expected at least 2 identical entries for S2 case {gt.case_id}"


def test_regression_s2_timestamp_proximity_leakage_prevented() -> None:
    """Proves Blocker 1 fix: S2 true target is not systematically closer to settlement than decoy"""
    rng = DeterministicRNG(999)
    config = GeneratorConfig(seed=999, num_settlements=50)
    baseline_cases = build_baseline_world(config, rng)

    allocations = [ScenarioFamily.S2_STRUCTURED_AMBIGUOUS] * len(baseline_cases)
    transformed = apply_scenario_transformations(baseline_cases, allocations, rng)

    target_closer_count = 0
    decoy_closer_count = 0

    for case in transformed:
        target = case.ledger_entries[0]
        decoy = case.ledger_entries[1]

        target_dist = abs((target.timestamp - case.settlement.settled_at).total_seconds())
        decoy_dist = abs((decoy.timestamp - case.settlement.settled_at).total_seconds())

        if target_dist < decoy_dist:
            target_closer_count += 1
        elif decoy_dist < target_dist:
            decoy_closer_count += 1

    total = len(transformed)
    # If the bug was present, target was always +2h to +12h and decoy >=25h (100% closer).
    # With identical temporal distributions, target is closer roughly ~50% of the time.
    assert target_closer_count < total, "Target was closer in 100% of cases (leakage detected)"
    assert decoy_closer_count > 0, "Decoy was never closer to settlement (leakage detected)"
    ratio = target_closer_count / total
    assert 0.25 <= ratio <= 0.75, f"Expected balanced proximity ~0.50, got {ratio:.2f}"


def test_ground_truth_s3_financial_mismatch_b2() -> None:
    """Proves B2: S3 is PROVABLE with valid Phase 1 source records and observed ledger variance."""
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)

    s3_family = ScenarioFamily.S3_FINANCIAL_MISMATCH
    s3_gts = [gt for gt in dataset.ground_truths if gt.scenario_family == s3_family]
    assert len(s3_gts) > 0

    settlement_map = {s.settlement_id: s for s in dataset.settlements}
    ledger_map = {le.id: le for le in dataset.ledger_entries}
    items_by_settlement: dict[str, list[SettlementItem]] = {
        s.settlement_id: [] for s in dataset.settlements
    }
    for it in dataset.settlement_items:
        items_by_settlement[it.settlement_id].append(it)

    for gt in s3_gts:
        assert gt.resolvability == Resolvability.PROVABLE
        assert len(gt.exact_target_ledger_entry_ids) == 1
        target_id = next(iter(gt.exact_target_ledger_entry_ids))
        assert target_id in ledger_map

        target = ledger_map[target_id]
        settlement = settlement_map[gt.case_id]
        # Reference links match
        assert target.payment_ref == settlement.settlement_id
        # Observed ledger amount diverges from settlement net
        assert target.amount_minor != settlement.net_deposited_minor
        assert gt.not_provable_reason is None

        # Source settlement and items remain 100% valid Phase 1 records
        items = items_by_settlement[settlement.settlement_id]
        validate_settlement_items_aggregation(settlement, items)


def test_ground_truth_s4_external_reference_text() -> None:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)

    s4_family = ScenarioFamily.S4_EXTERNAL_REF_TEXT
    s4_gts = [gt for gt in dataset.ground_truths if gt.scenario_family == s4_family]
    assert len(s4_gts) > 0

    settlement_map = {s.settlement_id: s for s in dataset.settlements}
    ledger_map = {le.id: le for le in dataset.ledger_entries}

    for gt in s4_gts:
        assert gt.resolvability == Resolvability.PROVABLE
        target_id = next(iter(gt.exact_target_ledger_entry_ids))
        target = ledger_map[target_id]
        settlement = settlement_map[gt.case_id]

        # payment_ref stripped, external_ref explicitly None
        assert target.payment_ref is None
        assert target.external_ref is None
        # narration contains deterministic external reference
        assert "CMS/NETBANK/EXT-ORD-" in (target.narration or "")
        # within +-3 days candidate window
        assert abs((target.timestamp - settlement.settled_at).total_seconds()) <= 3 * 86400


def test_ground_truth_s5_narration_alias_text() -> None:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)

    s5_family = ScenarioFamily.S5_NARRATION_ALIAS_TEXT
    s5_gts = [gt for gt in dataset.ground_truths if gt.scenario_family == s5_family]
    assert len(s5_gts) > 0

    settlement_map = {s.settlement_id: s for s in dataset.settlements}
    ledger_map = {le.id: le for le in dataset.ledger_entries}

    for gt in s5_gts:
        assert gt.resolvability == Resolvability.PROVABLE
        target_id = next(iter(gt.exact_target_ledger_entry_ids))
        target = ledger_map[target_id]
        settlement = settlement_map[gt.case_id]

        assert target.payment_ref is None
        assert target.external_ref is None
        assert "UPI-P2M-" in (target.narration or "")
        assert abs((target.timestamp - settlement.settled_at).total_seconds()) <= 3 * 86400


def test_regression_s4_s5_timestamp_leakage_and_separability_prevented() -> None:
    """Proves Blocker 2 fix: S4/S5 timestamps are bidirectional and overlap S1/S3 range."""
    rng = DeterministicRNG(888)
    config = GeneratorConfig(seed=888, num_settlements=50)
    baseline_cases = build_baseline_world(config, rng)

    s4_allocations = [ScenarioFamily.S4_EXTERNAL_REF_TEXT] * len(baseline_cases)
    s4_cases = apply_scenario_transformations(baseline_cases, s4_allocations, rng)

    s5_allocations = [ScenarioFamily.S5_NARRATION_ALIAS_TEXT] * len(baseline_cases)
    s5_cases = apply_scenario_transformations(baseline_cases, s5_allocations, rng)

    # 1. Verify bidirectionality: both negative (< settled_at) and positive offsets exist
    s4_negative_offsets = [
        (c.ledger_entries[0].timestamp - c.settlement.settled_at).total_seconds()
        for c in s4_cases
        if c.ledger_entries[0].timestamp < c.settlement.settled_at
    ]
    s4_positive_offsets = [
        (c.ledger_entries[0].timestamp - c.settlement.settled_at).total_seconds()
        for c in s4_cases
        if c.ledger_entries[0].timestamp > c.settlement.settled_at
    ]
    assert len(s4_negative_offsets) > 0, "S4 timestamps must be bidirectional (missing negative)"
    assert len(s4_positive_offsets) > 0, "S4 timestamps must have positive offsets"

    s5_negative_offsets = [
        (c.ledger_entries[0].timestamp - c.settlement.settled_at).total_seconds()
        for c in s5_cases
        if c.ledger_entries[0].timestamp < c.settlement.settled_at
    ]
    assert len(s5_negative_offsets) > 0, "S5 timestamps must be bidirectional (missing negative)"

    # 2. Verify overlap with S1/S3 range (+2h to +12h = 7200s to 43200s)
    # In the original bug, S4/S5 were always +25h to +36h (> 90000s),
    # making them trivially separable by a threshold of e.g. 18 hours.
    s4_overlapping_s1_range = [
        offset for offset in s4_positive_offsets if 2 * 3600 <= offset <= 12 * 3600
    ]
    assert len(s4_overlapping_s1_range) > 0, (
        "S4 timestamps must overlap S1/S3 range (+2h to +12h) to prevent threshold separation"
    )


def test_ground_truth_s6_non_provable_conflict() -> None:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)

    s6_family = ScenarioFamily.S6_NON_PROVABLE_CONFLICT
    s6_gts = [gt for gt in dataset.ground_truths if gt.scenario_family == s6_family]
    assert len(s6_gts) > 0

    for gt in s6_gts:
        assert gt.resolvability == Resolvability.NOT_PROVABLE
        assert gt.exact_target_ledger_entry_ids == frozenset()
        assert gt.not_provable_reason is not None
        assert "missing from bank ledger pool" in gt.not_provable_reason
