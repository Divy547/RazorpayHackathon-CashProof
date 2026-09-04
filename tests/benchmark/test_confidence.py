"""Tests for Evaluator-Only Confidence Calibration and Automation Quality."""

from __future__ import annotations

from datetime import UTC, datetime

from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.confidence import (
    ConfidenceEvaluator,
)
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import (
    GroundTruth,
    Resolvability,
    ScenarioFamily,
)
from cashproof.benchmark.runner import BenchmarkRunner
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

FIXED_TIME = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)


def _make_gt(
    case_id: str,
    target_ids: tuple[str, ...],
    scenario: ScenarioFamily = ScenarioFamily.S1_STRUCTURED_EXACT,
    resolvability: Resolvability = Resolvability.PROVABLE,
    not_provable_reason: str | None = None,
) -> GroundTruth:
    fallback = "Unresolvable conflict" if resolvability == Resolvability.NOT_PROVABLE else None
    reason = not_provable_reason or fallback
    return GroundTruth(
        case_id=case_id,
        resolvability=resolvability,
        exact_target_ledger_entry_ids=frozenset(target_ids),
        justifying_evidence=(),
        scenario_family=scenario,
        not_provable_reason=reason,
    )


def _make_result_with_confidence(
    case_id: str,
    score: float,
    expected_net: int = 10000,
    delta: int = 0,
    omit_identity: bool = False,
    hypothesis_source: HypothesisSource = HypothesisSource.DETERMINISTIC_RULES,
) -> tuple[ReconciliationResult, Settlement]:
    settlement = Settlement(case_id, expected_net, Currency.INR, FIXED_TIME)
    item = SettlementItem(
        f"item_{case_id}",
        case_id,
        f"pay_{case_id}",
        expected_net,
        0,
        0,
        0,
        0,
        expected_net,
    )
    observed_total = expected_net - delta
    case = ReconciliationCase(
        case_id=case_id,
        settlement_id=case_id,
        run_id="test_run",
        expected_net=expected_net,
        observed_ledger_total=observed_total,
        delta=delta,
        exception_type=ExceptionType.AMOUNT_MISMATCH if delta != 0 else ExceptionType.CLEAN_MATCH,
        processing_state=ProcessingState.INVESTIGATED,
    )

    candidates: list[MatchCandidate] = []
    entries: list[LedgerEntry] = []
    evidence_list: list[Evidence] = []

    if not omit_identity:
        entry_amount = observed_total
        entry = LedgerEntry(
            f"le_{case_id}",
            entry_amount if entry_amount >= 0 else 0,
            Currency.INR,
            FIXED_TIME,
            Direction.CREDIT,
        )
        entries.append(entry)
        cand = MatchCandidate(
            case_id,
            entry.id,
            score,
            ("ref_match",),
            ("rule_1",),
            MatchProvenance.STRUCTURED_REFERENCE,
            "v1",
            "test_run",
        )
        candidates.append(cand)
        evidence_list.append(
            Evidence(
                pointer=EvidencePointer("LedgerEntry", entry.id, "id"),
                relevance=score,
                stance=EvidenceStance.SUPPORTS,
                decision_consumed=True,
            )
        )

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=hypothesis_source,
        proposed_target_ids=frozenset(e.id for e in entries),
        target_ledger_entries=entries,
        deterministic_candidates=candidates,
        evidence=evidence_list,
        already_resolved_target_ids=frozenset(),
    )

    if gate.passed and hypothesis_source == HypothesisSource.DETERMINISTIC_RULES:
        resolution = Resolution.create_auto_resolved(gate)
    else:
        resolution = Resolution.create_human_review_pending(gate)

    result = ReconciliationResult(
        case=case,
        candidates=tuple(candidates),
        evidence=tuple(evidence_list),
        gate_evaluation=gate,
        resolution=resolution,
        audit_events=(),
    )
    return result, settlement


def test_confidence_evaluator_exact_target_equality() -> None:
    evaluator = ConfidenceEvaluator()

    # Case 1: Exact target match
    r1, s1 = _make_result_with_confidence("c1", score=1.0, delta=0)
    gt1 = _make_gt("c1", ("le_c1",), scenario=ScenarioFamily.S1_STRUCTURED_EXACT)

    # Case 2: Target mismatch (GT expects le_c2 AND le_c2_extra)
    r2, s2 = _make_result_with_confidence("c2", score=0.8, delta=0)
    gt2 = _make_gt("c2", ("le_c2", "le_c2_extra"), scenario=ScenarioFamily.S1_STRUCTURED_EXACT)

    # Case 3: Positive prediction on NOT_PROVABLE case
    r3, s3 = _make_result_with_confidence("c3", score=0.6, delta=0)
    gt3 = _make_gt(
        "c3",
        (),
        scenario=ScenarioFamily.S6_NON_PROVABLE_CONFLICT,
        resolvability=Resolvability.NOT_PROVABLE,
    )

    # Case 4: Proper abstention on NOT_PROVABLE case (no candidates, no proposed targets)
    r4, s4 = _make_result_with_confidence("c4", score=0.0, delta=0, omit_identity=True)
    gt4 = _make_gt(
        "c4",
        (),
        scenario=ScenarioFamily.S6_NON_PROVABLE_CONFLICT,
        resolvability=Resolvability.NOT_PROVABLE,
    )

    results = [r1, r2, r3, r4]
    gts = [gt1, gt2, gt3, gt4]
    settlements = {s.settlement_id: s for s in [s1, s2, s3, s4]}

    report = evaluator.evaluate(results, gts, settlements)

    assert report.total_observations == 4
    # r4 was abstained, so 3 predictions made
    assert len([o for o in report.observations if not o.abstained]) == 3

    # 10 buckets
    assert len(report.buckets) == 10
    total_bucket_count = sum(b.observation_count for b in report.buckets)
    assert total_bucket_count == 4


def test_perfect_calibration_case() -> None:
    evaluator = ConfidenceEvaluator()

    results: list[ReconciliationResult] = []
    gts: list[GroundTruth] = []
    settlements: dict[str, Settlement] = {}

    for i in range(5):
        cid = f"c_{i}"
        r, s = _make_result_with_confidence(cid, score=1.0, delta=0)
        gt = _make_gt(cid, (f"le_{cid}",))
        results.append(r)
        gts.append(gt)
        settlements[s.settlement_id] = s

    report = evaluator.evaluate(results, gts, settlements)
    assert report.overall_ece == 0.0
    assert report.overall_brier_score == 0.0


def test_confidence_threshold_coverage_monotonicity() -> None:
    evaluator = ConfidenceEvaluator()

    results: list[ReconciliationResult] = []
    gts: list[GroundTruth] = []
    settlements: dict[str, Settlement] = {}

    scores = [0.2, 0.4, 0.6, 0.8, 1.0]
    for i, s in enumerate(scores):
        cid = f"c_{i}"
        r, st = _make_result_with_confidence(cid, score=s, delta=0)
        gt = _make_gt(cid, (f"le_{cid}",))
        results.append(r)
        gts.append(gt)
        settlements[st.settlement_id] = st

    report = evaluator.evaluate(results, gts, settlements)

    prev_coverage = 1.1
    for tm in report.thresholds:
        assert tm.coverage <= prev_coverage + 1e-9
        prev_coverage = tm.coverage


def test_automation_opportunity_detection() -> None:
    evaluator = ConfidenceEvaluator()

    # S3 case: target is completely correct (exact match), confidence is 1.0,
    # but Gate correctly blocked it due to BRIDGE check (delta = 500)
    r, s = _make_result_with_confidence(
        "s3_case",
        score=1.0,
        expected_net=100000,
        delta=500,
    )
    gt = _make_gt("s3_case", ("le_s3_case",), scenario=ScenarioFamily.S3_FINANCIAL_MISMATCH)

    report = evaluator.evaluate([r], [gt], {s.settlement_id: s})

    assert report.automation_opportunity.opportunity_count == 1
    assert report.automation_opportunity.affected_settlement_net_minor == 100000
    assert report.automation_opportunity.sample_case_ids == ("s3_case",)


def test_benchmark_runner_full_integration_confidence() -> None:
    runner = BenchmarkRunner()
    config = GeneratorConfig(seed=42, num_settlements=100)
    run = runner.run(config=config, arm="deterministic", now=FIXED_TIME)

    assert run.confidence_report is not None
    cr = run.confidence_report
    assert cr.total_observations == 100
    assert cr.overall_ece > 0.0
    assert cr.overall_ece < 0.3
    assert cr.overall_brier_score > 0.0
    assert cr.overall_brier_score < 0.1
    assert cr.automation_opportunity.opportunity_count == 15
    assert cr.automation_opportunity.affected_settlement_net_minor == 17196914

    # Combined metrics verify runner persistence
    metrics_dict = run.metrics_dict
    assert "confidence_ece" in metrics_dict
    assert "confidence_brier_score" in metrics_dict
    assert metrics_dict["confidence_ece"] == cr.overall_ece
    assert metrics_dict["confidence_brier_score"] == cr.overall_brier_score
