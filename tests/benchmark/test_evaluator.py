"""Tests for CashProof BenchmarkEvaluator.

Verifies:
- Exact target set equality evaluation.
- False auto-resolution detection on NOT_PROVABLE or mismatched targets.
- Zero false auto-resolution invariant.
- S1-S6 scenario taxonomy evaluation semantics.
- Metric and rate calculations.
- Timing metadata and records per minute throughput KPI.
- Scenario matrix aggregation invariants.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.evaluator import BenchmarkEvaluationError, BenchmarkEvaluator
from cashproof.benchmark.models import (
    GroundTruth,
    Resolvability,
    ScenarioFamily,
)
from cashproof.domain.decision import Resolution, evaluate_gate
from cashproof.domain.derived import Evidence, EvidencePointer, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem
from cashproof.domain.types import (
    Currency,
    Direction,
    Disposition,
    EvidenceStance,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
)

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)


def _make_result(
    case_id: str,
    disposition: Disposition,
    target_ids: tuple[str, ...],
) -> ReconciliationResult:
    settlement = Settlement(case_id, 10_000, Currency.INR, FIXED_NOW)
    items = [
        SettlementItem(f"item_{case_id}", case_id, f"pay_{case_id}", 10_000, 0, 0, 0, 0, 10_000)
    ]
    entry_amount = 10_000 if len(target_ids) <= 1 else (10_000 // len(target_ids))
    entries = [
        LedgerEntry(
            tid, entry_amount, Currency.INR, FIXED_NOW, Direction.CREDIT, payment_ref=case_id
        )
        for tid in target_ids
    ]
    candidates = [
        MatchCandidate(
            case_id,
            tid,
            1.0,
            ("payment_ref_exact_match", "amount_exact_match"),
            (),
            MatchProvenance.STRUCTURED_REFERENCE,
            "v1",
            "test_run",
        )
        for tid in target_ids
    ]
    evidence = [
        Evidence(
            pointer=EvidencePointer("LedgerEntry", tid, "id"),
            relevance=1.0,
            stance=EvidenceStance.SUPPORTS,
            decision_consumed=True,
        )
        for tid in target_ids
    ]
    case = ReconciliationCase(
        case_id=case_id,
        settlement_id=case_id,
        run_id="test_run",
        expected_net=10_000,
        observed_ledger_total=10_000,
        delta=0,
        exception_type=ExceptionType.CLEAN_MATCH
        if disposition == Disposition.AUTO_RESOLVED
        else ExceptionType.AMBIGUOUS_MATCH,
        processing_state=ProcessingState.CLASSIFIED,
    )

    should_pass_gate = disposition == Disposition.AUTO_RESOLVED
    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=items,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset(target_ids) if should_pass_gate else frozenset(),
        target_ledger_entries=entries if should_pass_gate else [],
        deterministic_candidates=candidates,
        evidence=evidence if should_pass_gate else [],
        already_resolved_target_ids=frozenset(),
    )

    if disposition == Disposition.AUTO_RESOLVED:
        resolution = Resolution.create_auto_resolved(gate)
    elif disposition == Disposition.UNRESOLVED:
        resolution = Resolution.create_unresolved(gate)
    else:
        resolution = Resolution.create_human_review_pending(gate)

    closed_case = replace(case, processing_state=ProcessingState.CLOSED)
    return ReconciliationResult(
        case=closed_case,
        candidates=tuple(candidates),
        evidence=tuple(evidence),
        gate_evaluation=gate,
        resolution=resolution,
        audit_events=(),
    )


def _make_gt(
    case_id: str,
    resolvability: Resolvability,
    target_ids: tuple[str, ...],
    scenario_family: ScenarioFamily,
    reason: str | None = None,
) -> GroundTruth:
    evidence = [EvidencePointer("LedgerEntry", tid, "id") for tid in target_ids]
    return GroundTruth(
        case_id=case_id,
        resolvability=resolvability,
        exact_target_ledger_entry_ids=target_ids,
        justifying_evidence=evidence,
        scenario_family=scenario_family,
        not_provable_reason=reason
        or ("test reason" if resolvability == Resolvability.NOT_PROVABLE else None),
    )


def test_evaluator_exact_target_match_auto_resolved() -> None:
    evaluator = BenchmarkEvaluator()
    results = [_make_result("c1", Disposition.AUTO_RESOLVED, ("le_1",))]
    gts = [_make_gt("c1", Resolvability.PROVABLE, ("le_1",), ScenarioFamily.S1_STRUCTURED_EXACT)]

    overall, matrix, evals, timing = evaluator.evaluate(results, gts, pipeline_duration_seconds=1.0)

    assert overall.total_cases == 1
    assert overall.auto_resolved == 1
    assert overall.correct_auto_resolutions == 1
    assert overall.false_auto_resolutions == 0
    assert overall.zero_false_auto_resolution is True
    assert overall.safety_gate_passed is True
    assert overall.exact_target_set_accuracy == 1.0
    assert evals[0].is_correct_auto_resolution is True
    assert evals[0].is_false_auto_resolution is False


def test_evaluator_target_set_mismatch_is_false_auto_resolution() -> None:
    evaluator = BenchmarkEvaluator()
    # Production picked le_1, but ground truth expected le_different
    results = [_make_result("c1", Disposition.AUTO_RESOLVED, ("le_1",))]
    gts = [
        _make_gt(
            "c1", Resolvability.PROVABLE, ("le_different",), ScenarioFamily.S1_STRUCTURED_EXACT
        )
    ]

    overall, matrix, evals, _ = evaluator.evaluate(results, gts, pipeline_duration_seconds=1.0)

    assert overall.total_cases == 1
    assert overall.auto_resolved == 1
    assert overall.correct_auto_resolutions == 0
    assert overall.false_auto_resolutions == 1
    assert overall.zero_false_auto_resolution is False
    assert overall.safety_gate_passed is False
    assert evals[0].is_false_auto_resolution is True


def test_evaluator_not_provable_auto_resolved_is_false_auto_resolution() -> None:
    evaluator = BenchmarkEvaluator()
    # Case was NOT_PROVABLE (S2 or S6), but production emitted AUTO_RESOLVED
    results = [_make_result("c2", Disposition.AUTO_RESOLVED, ("le_decoy",))]
    gts = [
        _make_gt(
            "c2",
            Resolvability.NOT_PROVABLE,
            (),
            ScenarioFamily.S2_STRUCTURED_AMBIGUOUS,
            "Ambiguous match",
        )
    ]

    overall, matrix, evals, _ = evaluator.evaluate(results, gts, pipeline_duration_seconds=1.0)

    assert overall.false_auto_resolutions == 1
    assert overall.zero_false_auto_resolution is False
    assert overall.safety_gate_passed is False
    assert evals[0].is_false_auto_resolution is True
    assert "False auto-resolution on NOT_PROVABLE" in (evals[0].notes or "")


def test_evaluator_rate_calculations() -> None:
    evaluator = BenchmarkEvaluator()
    results = [
        _make_result("c1", Disposition.AUTO_RESOLVED, ("le_1",)),
        _make_result("c2", Disposition.HUMAN_REVIEW, ()),
        _make_result("c3", Disposition.HUMAN_REVIEW, ()),
        _make_result("c4", Disposition.UNRESOLVED, ()),
    ]
    gts = [
        _make_gt("c1", Resolvability.PROVABLE, ("le_1",), ScenarioFamily.S1_STRUCTURED_EXACT),
        _make_gt("c2", Resolvability.PROVABLE, ("le_2",), ScenarioFamily.S3_FINANCIAL_MISMATCH),
        _make_gt("c3", Resolvability.NOT_PROVABLE, (), ScenarioFamily.S2_STRUCTURED_AMBIGUOUS),
        _make_gt("c4", Resolvability.NOT_PROVABLE, (), ScenarioFamily.S6_NON_PROVABLE_CONFLICT),
    ]

    overall, matrix, _, timing = evaluator.evaluate(results, gts, pipeline_duration_seconds=2.0)

    assert overall.total_cases == 4
    assert overall.auto_resolved == 1
    assert overall.human_review == 2
    assert overall.unresolved == 1
    assert pytest.approx(overall.auto_resolution_rate, 0.001) == 0.25
    assert pytest.approx(overall.human_review_rate, 0.001) == 0.50
    assert pytest.approx(overall.unresolved_rate, 0.001) == 0.25
    assert overall.safety_gate_passed is True
    assert pytest.approx(overall.records_per_minute, 0.001) == (1 / 2.0) * 60.0


def test_evaluator_scenario_matrix_aggregation_invariants() -> None:
    evaluator = BenchmarkEvaluator()
    results = [
        _make_result("s1", Disposition.AUTO_RESOLVED, ("le_1",)),
        _make_result("s2", Disposition.HUMAN_REVIEW, ()),
        _make_result("s3", Disposition.HUMAN_REVIEW, ()),
        _make_result("s4", Disposition.HUMAN_REVIEW, ()),
        _make_result("s5", Disposition.HUMAN_REVIEW, ()),
        _make_result("s6", Disposition.UNRESOLVED, ()),
    ]
    gts = [
        _make_gt("s1", Resolvability.PROVABLE, ("le_1",), ScenarioFamily.S1_STRUCTURED_EXACT),
        _make_gt("s2", Resolvability.NOT_PROVABLE, (), ScenarioFamily.S2_STRUCTURED_AMBIGUOUS),
        _make_gt("s3", Resolvability.PROVABLE, ("le_3",), ScenarioFamily.S3_FINANCIAL_MISMATCH),
        _make_gt("s4", Resolvability.PROVABLE, ("le_4",), ScenarioFamily.S4_EXTERNAL_REF_TEXT),
        _make_gt("s5", Resolvability.PROVABLE, ("le_5",), ScenarioFamily.S5_NARRATION_ALIAS_TEXT),
        _make_gt("s6", Resolvability.NOT_PROVABLE, (), ScenarioFamily.S6_NON_PROVABLE_CONFLICT),
    ]

    overall, matrix, evals, _ = evaluator.evaluate(results, gts, pipeline_duration_seconds=1.0)

    assert len(matrix) == 6
    assert sum(r.total for r in matrix) == overall.total_cases
    assert sum(r.auto_resolved for r in matrix) == overall.auto_resolved
    assert sum(r.human_review for r in matrix) == overall.human_review
    assert sum(r.unresolved for r in matrix) == overall.unresolved
    assert sum(r.false_auto_resolutions for r in matrix) == overall.false_auto_resolutions

    # In clean pipeline, all S1-S6 follow their prescribed outcomes
    for row in matrix:
        assert row.correct_outcomes == row.total
        assert row.false_auto_resolutions == 0


def test_evaluator_raises_on_unmatched_case_id() -> None:
    evaluator = BenchmarkEvaluator()
    results = [_make_result("c_orphan", Disposition.AUTO_RESOLVED, ("le_1",))]
    gts = [
        _make_gt("c_other", Resolvability.PROVABLE, ("le_1",), ScenarioFamily.S1_STRUCTURED_EXACT)
    ]

    with pytest.raises(BenchmarkEvaluationError, match="has no matching GroundTruth"):
        evaluator.evaluate(results, gts, pipeline_duration_seconds=1.0)
