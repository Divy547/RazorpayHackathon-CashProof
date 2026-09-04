"""Integration tests for the deterministic reconciliation pipeline (matcher -> evidence ->
classifier -> evaluate_gate() -> Resolution) against Phase 2 synthetic datasets.

These tests prove behavior is DISCOVERED from source facts by the production
pipeline, not hard-coded from scenario labels: ScenarioFamily/GroundTruth are
used only to group results for assertions, never passed into the pipeline.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

import pytest
from cashproof.application.batch import BatchReconciler, BatchReconciliationSummary
from cashproof.application.use_case import ReconcileSettlementUseCase
from cashproof.benchmark.generator import GeneratedDataset, generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import GroundTruth, ScenarioFamily
from cashproof.domain.source import Payment, SettlementItem
from cashproof.domain.types import Disposition

FIXED_NOW = datetime(2026, 8, 20, tzinfo=UTC)


def _build_batch_inputs(
    dataset: GeneratedDataset,
) -> tuple[dict[str, list[SettlementItem]], dict[str, list[Payment]]]:
    items_by_settlement: dict[str, list[SettlementItem]] = defaultdict(list)
    for item in dataset.settlement_items:
        items_by_settlement[item.settlement_id].append(item)

    payment_by_id = {p.id: p for p in dataset.payments}
    payments_by_settlement: dict[str, list[Payment]] = defaultdict(list)
    for item in dataset.settlement_items:
        payment = payment_by_id.get(item.payment_id)
        if payment is not None:
            payments_by_settlement[item.settlement_id].append(payment)
    return items_by_settlement, payments_by_settlement


def _run_batch(
    seed: int = 42, num_settlements: int = 100
) -> tuple[GeneratedDataset, BatchReconciliationSummary]:
    config = GeneratorConfig(seed=seed, num_settlements=num_settlements)
    dataset = generate_dataset(config)
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)
    reconciler = BatchReconciler()
    summary = reconciler.run(
        run_id="test-run",
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=FIXED_NOW,
    )
    return dataset, summary


def _grouped_by_family(
    dataset: GeneratedDataset, summary: BatchReconciliationSummary
) -> dict[ScenarioFamily, list]:  # type: ignore[type-arg]
    gt_by_case: dict[str, GroundTruth] = {gt.case_id: gt for gt in dataset.ground_truths}
    result_by_case = {r.case.case_id: r for r in summary.results}
    grouped: dict[ScenarioFamily, list] = defaultdict(list)  # type: ignore[type-arg]
    for case_id, gt in gt_by_case.items():
        grouped[gt.scenario_family].append(result_by_case[case_id])
    return grouped


def test_s1_clean_structured_match_auto_resolves() -> None:
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    s1_results = grouped[ScenarioFamily.S1_STRUCTURED_EXACT]
    assert s1_results

    auto_resolved = sum(
        1 for r in s1_results if r.resolution.disposition == Disposition.AUTO_RESOLVED
    )
    # The pipeline discovers auto-resolution from source facts; it is not
    # hard-coded per scenario. A small residual fraction may legitimately
    # downgrade to HUMAN_REVIEW when the full ledger pool contains a second
    # candidate signal (TARGET_SET_EQUALITY correctly enforcing exhaustive
    # candidate disclosure) - this is expected safe behavior, not a defect.
    assert auto_resolved / len(s1_results) >= 0.85

    for r in s1_results:
        assert r.resolution.disposition in (Disposition.AUTO_RESOLVED, Disposition.HUMAN_REVIEW)
        if r.resolution.disposition == Disposition.AUTO_RESOLVED:
            assert r.gate_evaluation.passed is True
            assert r.gate_evaluation.failing_check is None
            assert r.case.exception_type.value == "CLEAN_MATCH"


@pytest.mark.parametrize(
    "family",
    [
        ScenarioFamily.S2_STRUCTURED_AMBIGUOUS,
        ScenarioFamily.S3_FINANCIAL_MISMATCH,
        ScenarioFamily.S4_EXTERNAL_REF_TEXT,
        ScenarioFamily.S5_NARRATION_ALIAS_TEXT,
    ],
)
def test_s2_through_s5_never_auto_resolve(family: ScenarioFamily) -> None:
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    results = grouped[family]
    assert results

    for r in results:
        assert r.resolution.disposition != Disposition.AUTO_RESOLVED
        assert r.gate_evaluation.passed is False


def test_s2_ambiguous_fails_identity_check_with_multiple_candidates() -> None:
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    for r in grouped[ScenarioFamily.S2_STRUCTURED_AMBIGUOUS]:
        assert len(r.candidates) >= 2
        assert r.case.exception_type.value in ("AMBIGUOUS_MATCH", "CONFLICTING_EVIDENCE")


def test_s2_observed_ledger_state_reflects_structural_duplication_not_zero() -> None:
    """Regression: case.observed_ledger_total must report what the ledger itself
    structurally claims (both tied entries), not the classifier's empty proposed
    target set. This must NOT change the gate outcome or disposition - only the
    displayed observation.
    """
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    settlement_by_id = {s.settlement_id: s for s in dataset.settlements}

    for r in grouped[ScenarioFamily.S2_STRUCTURED_AMBIGUOUS]:
        settlement = settlement_by_id[r.case.case_id]
        # Both tied candidates share the settlement's own amount by construction.
        assert r.case.observed_ledger_total == 2 * settlement.net_deposited_minor
        assert r.case.delta == settlement.net_deposited_minor - r.case.observed_ledger_total
        assert r.case.delta < 0

        # Safety-relevant outcome is unaffected by the observation fix.
        assert r.gate_evaluation.failing_check == "IDENTITY"
        assert r.resolution.disposition == Disposition.HUMAN_REVIEW


def test_s3_amount_mismatch_fails_bridge_check() -> None:
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    for r in grouped[ScenarioFamily.S3_FINANCIAL_MISMATCH]:
        assert r.case.exception_type.value == "AMOUNT_MISMATCH"
        assert r.gate_evaluation.failing_check == "BRIDGE"
        # observed_ledger_total faithfully reflects the single structurally-linked
        # (wrong-amount) entry - unchanged in shape from before the observation fix.
        assert r.case.observed_ledger_total != r.case.expected_net
        assert r.case.delta != 0


def test_s4_s5_text_matches_fail_policy_check() -> None:
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    for family in (ScenarioFamily.S4_EXTERNAL_REF_TEXT, ScenarioFamily.S5_NARRATION_ALIAS_TEXT):
        for r in grouped[family]:
            assert r.case.exception_type.value == "NAME_ALIAS"
            assert r.gate_evaluation.failing_check == "POLICY"


def test_s6_missing_record_is_unresolved() -> None:
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    results = grouped[ScenarioFamily.S6_NON_PROVABLE_CONFLICT]
    assert results

    for r in results:
        assert r.resolution.disposition == Disposition.UNRESOLVED
        assert r.case.exception_type.value == "MISSING_RECORD"
        assert len(r.candidates) == 0
        assert r.gate_evaluation.failing_check == "IDENTITY"
        assert r.case.observed_ledger_total == 0


def test_s1_observed_ledger_total_equals_expected_net() -> None:
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    for r in grouped[ScenarioFamily.S1_STRUCTURED_EXACT]:
        assert r.case.observed_ledger_total == r.case.expected_net
        assert r.case.delta == 0


def test_s4_s5_structural_observation_is_zero_despite_text_candidate() -> None:
    """S4/S5 have a text-derived candidate (candidate_count > 0) but zero structural
    observation - distinguishing them from S6, where both are zero.
    """
    dataset, summary = _run_batch()
    grouped = _grouped_by_family(dataset, summary)
    for family in (ScenarioFamily.S4_EXTERNAL_REF_TEXT, ScenarioFamily.S5_NARRATION_ALIAS_TEXT):
        for r in grouped[family]:
            assert r.case.observed_ledger_total == 0
            assert len(r.candidates) > 0


def test_multi_item_settlement_produces_single_case_at_settlement_level() -> None:
    dataset, summary = _run_batch()
    items_by_settlement, _ = _build_batch_inputs(dataset)
    multi_item_ids = {sid for sid, items in items_by_settlement.items() if len(items) > 1}
    assert multi_item_ids, "fixture must include at least one multi-item settlement"

    case_ids = {r.case.case_id for r in summary.results}
    assert multi_item_ids.issubset(case_ids)
    assert len(summary.results) == len(dataset.settlements)


def test_deterministic_repeated_execution_produces_identical_results() -> None:
    _, summary1 = _run_batch(seed=777, num_settlements=60)
    _, summary2 = _run_batch(seed=777, num_settlements=60)

    dispositions1 = [(r.case.case_id, r.resolution.disposition) for r in summary1.results]
    dispositions2 = [(r.case.case_id, r.resolution.disposition) for r in summary2.results]
    assert dispositions1 == dispositions2

    targets1 = [(r.case.case_id, r.resolution.target_ledger_entry_ids) for r in summary1.results]
    targets2 = [(r.case.case_id, r.resolution.target_ledger_entry_ids) for r in summary2.results]
    assert targets1 == targets2


def test_duplicate_ledger_target_protection_across_batch() -> None:
    _, summary = _run_batch()
    auto_targets: list[str] = []
    for r in summary.results:
        if r.resolution.disposition == Disposition.AUTO_RESOLVED:
            auto_targets.extend(r.resolution.target_ledger_entry_ids)

    assert len(auto_targets) == len(set(auto_targets)), "a ledger entry was auto-resolved twice"


def test_duplicate_target_protection_blocks_second_claim_via_use_case() -> None:
    """Directly proves UNIQUENESS blocks a second case from claiming an already-resolved target."""
    dataset, batch_summary = _run_batch(seed=101, num_settlements=50)
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)

    auto_resolved = next(
        r for r in batch_summary.results if r.resolution.disposition == Disposition.AUTO_RESOLVED
    )
    settlement = next(
        s for s in dataset.settlements if s.settlement_id == auto_resolved.case.case_id
    )

    use_case = ReconcileSettlementUseCase()
    first = use_case.execute(
        run_id="dup-test",
        settlement=settlement,
        items=items_by_settlement[settlement.settlement_id],
        payments=payments_by_settlement[settlement.settlement_id],
        ledger_pool=dataset.ledger_entries,
        already_resolved_target_ids=frozenset(),
        now=FIXED_NOW,
    )
    assert first.resolution.disposition == Disposition.AUTO_RESOLVED

    already_claimed = first.resolution.target_ledger_entry_ids
    second = use_case.execute(
        run_id="dup-test",
        settlement=settlement,
        items=items_by_settlement[settlement.settlement_id],
        payments=payments_by_settlement[settlement.settlement_id],
        ledger_pool=dataset.ledger_entries,
        already_resolved_target_ids=already_claimed,
        now=FIXED_NOW,
    )
    assert second.resolution.disposition != Disposition.AUTO_RESOLVED
    assert second.gate_evaluation.failing_check == "UNIQUENESS"


def test_ground_truth_not_reachable_from_pipeline_result() -> None:
    """Production ReconciliationResult/ReconciliationCase objects carry no GroundTruth fields."""
    dataset, summary = _run_batch(num_settlements=50)
    assert summary.results
    for r in summary.results:
        assert not hasattr(r, "ground_truth")
        assert not hasattr(r.case, "ground_truth")
        assert not hasattr(r.case, "scenario_family")
        assert not hasattr(r.resolution, "ground_truth")


def test_classification_is_deterministic_and_independent_of_correlation_layer() -> None:
    """Re-running the use case in isolation (no dataset/demo correlation) yields the same
    classification as the batch run, proving scenario labels play no role in the decision.
    """
    dataset, summary = _run_batch(num_settlements=50)
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)
    use_case = ReconcileSettlementUseCase()

    for settlement in dataset.settlements[:5]:
        prior = next(r for r in summary.results if r.case.case_id == settlement.settlement_id)
        result = use_case.execute(
            run_id="isolated-run",
            settlement=settlement,
            items=items_by_settlement[settlement.settlement_id],
            payments=payments_by_settlement[settlement.settlement_id],
            ledger_pool=dataset.ledger_entries,
            already_resolved_target_ids=frozenset(),
            now=FIXED_NOW,
        )
        assert result.case.exception_type == prior.case.exception_type
        assert result.gate_evaluation.target_ledger_entry_ids == (
            prior.gate_evaluation.target_ledger_entry_ids
        )
