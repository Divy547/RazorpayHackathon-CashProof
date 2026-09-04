"""Hypothesis Property-Based Tests for Confidence Calibration Invariants."""

from __future__ import annotations

from datetime import UTC, datetime

from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.confidence import (
    ConfidenceEvaluator,
)
from cashproof.benchmark.models import (
    GroundTruth,
    Resolvability,
    ScenarioFamily,
)
from cashproof.domain.decision import (
    Resolution,
    evaluate_gate,
)
from cashproof.domain.derived import (
    Evidence,
    EvidencePointer,
    MatchCandidate,
    ReconciliationCase,
)
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem
from cashproof.domain.types import (
    Currency,
    Direction,
    EvidenceStance,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
)
from hypothesis import given, settings
from hypothesis import strategies as st

FIXED_TIME = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)


@st.composite
def synthetic_confidence_batch(
    draw: st.DrawFn,
) -> tuple[list[ReconciliationResult], list[GroundTruth], dict[str, Settlement]]:
    n_cases = draw(st.integers(min_value=1, max_value=20))
    scores = draw(
        st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=n_cases,
            max_size=n_cases,
        )
    )
    deltas = draw(st.lists(st.sampled_from([0, 100, 500]), min_size=n_cases, max_size=n_cases))
    correct_flags = draw(st.lists(st.booleans(), min_size=n_cases, max_size=n_cases))

    results = []
    gts = []
    settlements = {}

    for i in range(n_cases):
        cid = f"case_{i}"
        score = scores[i]
        delta = deltas[i]
        is_correct = correct_flags[i]

        expected_net = 10000
        observed_total = expected_net - delta

        settlement = Settlement(cid, expected_net, Currency.INR, FIXED_TIME)
        settlements[cid] = settlement

        item = SettlementItem(
            f"item_{cid}", cid, f"pay_{cid}", expected_net, 0, 0, 0, 0, expected_net
        )
        exc_type = ExceptionType.CLEAN_MATCH if delta == 0 else ExceptionType.AMOUNT_MISMATCH
        case = ReconciliationCase(
            case_id=cid,
            settlement_id=cid,
            run_id="run_test",
            expected_net=expected_net,
            observed_ledger_total=observed_total,
            delta=delta,
            exception_type=exc_type,
            processing_state=ProcessingState.INVESTIGATED,
        )

        entry = LedgerEntry(
            f"entry_{cid}", observed_total, Currency.INR, FIXED_TIME, Direction.CREDIT
        )
        cand = MatchCandidate(
            cid,
            entry.id,
            score,
            ("ref",),
            ("r1",),
            MatchProvenance.STRUCTURED_REFERENCE,
            "v1",
            "run_test",
        )
        evidence = Evidence(
            pointer=EvidencePointer("LedgerEntry", entry.id, "id"),
            relevance=score,
            stance=EvidenceStance.SUPPORTS,
            decision_consumed=True,
        )

        gate = evaluate_gate(
            case=case,
            settlement=settlement,
            items=item,
            hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
            proposed_target_ids=frozenset([entry.id]),
            target_ledger_entries=[entry],
            deterministic_candidates=[cand],
            evidence=[evidence],
            already_resolved_target_ids=frozenset(),
        )

        if gate.passed:
            res = Resolution.create_auto_resolved(gate)
        else:
            res = Resolution.create_human_review_pending(gate)

        rec_result = ReconciliationResult(
            case=case,
            candidates=(cand,),
            evidence=(evidence,),
            gate_evaluation=gate,
            resolution=res,
            audit_events=(),
        )
        results.append(rec_result)

        target_ids = (entry.id,) if is_correct else (f"diff_entry_{cid}",)
        gt = GroundTruth(
            case_id=cid,
            resolvability=Resolvability.PROVABLE,
            exact_target_ledger_entry_ids=frozenset(target_ids),
            justifying_evidence=(),
            scenario_family=ScenarioFamily.S1_STRUCTURED_EXACT,
            not_provable_reason=None,
        )
        gts.append(gt)

    return results, gts, settlements


@settings(max_examples=50, deadline=None)
@given(synthetic_confidence_batch())
def test_calibration_metrics_bounded(
    batch_data: tuple[list[ReconciliationResult], list[GroundTruth], dict[str, Settlement]],
) -> None:
    results, gts, settlements = batch_data
    evaluator = ConfidenceEvaluator()
    report = evaluator.evaluate(results, gts, settlements)

    # Invariant 1: ECE bounded in [0.0, 1.0]
    assert 0.0 <= report.overall_ece <= 1.0 + 1e-9

    # Invariant 2: Brier score bounded in [0.0, 1.0]
    assert 0.0 <= report.overall_brier_score <= 1.0 + 1e-9

    # Invariant 3: Buckets sum to total observations
    bucket_sum = sum(b.observation_count for b in report.buckets)
    assert bucket_sum == report.total_observations

    # Invariant 4: Threshold coverage monotonicity
    prev_coverage = 1.0 + 1e-9
    for tm in report.thresholds:
        assert tm.coverage <= prev_coverage
        assert 0.0 <= tm.precision <= 1.0
        prev_coverage = tm.coverage
