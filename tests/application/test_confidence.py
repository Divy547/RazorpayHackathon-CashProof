"""Tests for Operational Confidence Distribution and Belief-Authorization Separation."""

from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

from cashproof.application.confidence import OperationalConfidenceService
from cashproof.application.use_case import ReconciliationResult
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


def test_empty_results() -> None:
    service = OperationalConfidenceService()
    summary = service.analyze([], {})

    assert summary.hypotheses_evaluated == 0
    assert summary.high_confidence_count == 0
    assert summary.medium_confidence_count == 0
    assert summary.low_confidence_count == 0
    assert len(summary.buckets) == 10
    assert len(summary.gate_tiers) == 3
    assert len(summary.check_contexts) == 0


def test_operational_confidence_distribution_and_tiers() -> None:
    # 1. High confidence (1.0), Gate Passed (delta = 0)
    r1, s1 = _make_result_with_confidence("c1", score=1.0, delta=0)
    # 2. High confidence (1.0), Gate Failed on BRIDGE (delta = 500)
    r2, s2 = _make_result_with_confidence("c2", score=1.0, delta=500)
    # 3. Medium confidence (0.7), Gate Failed (delta = 100)
    r3, s3 = _make_result_with_confidence(
        "c3",
        score=0.7,
        delta=100,
        hypothesis_source=HypothesisSource.AI_INVESTIGATION,
    )
    # 4. Low confidence (0.3), Gate Failed on IDENTITY (omit identity)
    r4, s4 = _make_result_with_confidence(
        "c4",
        score=0.3,
        delta=0,
        omit_identity=True,
    )

    results = [r1, r2, r3, r4]
    settlements = {s.settlement_id: s for s in [s1, s2, s3, s4]}

    service = OperationalConfidenceService()
    summary = service.analyze(results, settlements)

    assert summary.hypotheses_evaluated == 4
    assert summary.high_confidence_count == 2
    assert summary.medium_confidence_count == 1
    assert summary.low_confidence_count == 1

    # Bucket check: 10 buckets
    assert len(summary.buckets) == 10
    bucket_counts_sum = sum(b.hypothesis_count for b in summary.buckets)
    assert bucket_counts_sum == 4

    # The [0.9, 1.0] bucket should have 2 hypotheses (1 pass, 1 fail)
    top_bucket = summary.buckets[-1]
    assert top_bucket.hypothesis_count == 2
    assert top_bucket.gate_pass_count == 1
    assert top_bucket.gate_fail_count == 1
    assert top_bucket.average_confidence == 1.0

    # Gate tiers check
    tier_map = {gt.tier: gt for gt in summary.gate_tiers}
    assert tier_map["HIGH"].total_count == 2
    assert tier_map["HIGH"].gate_pass_count == 1
    assert tier_map["HIGH"].gate_fail_count == 1
    high_blockers = dict(tier_map["HIGH"].failing_check_counts)
    assert high_blockers.get("BRIDGE") == 1

    assert tier_map["MEDIUM"].total_count == 1
    assert tier_map["MEDIUM"].gate_pass_count == 0
    assert tier_map["MEDIUM"].gate_fail_count == 1

    assert tier_map["LOW"].total_count == 1
    assert tier_map["LOW"].gate_pass_count == 0
    assert tier_map["LOW"].gate_fail_count == 1

    # Blocker check contexts
    check_map = {ctx.check_name: ctx for ctx in summary.check_contexts}
    assert "BRIDGE" in check_map
    assert check_map["BRIDGE"].case_count == 2
    assert check_map["BRIDGE"].average_confidence == 0.85
    assert check_map["BRIDGE"].min_confidence == 0.7
    assert check_map["BRIDGE"].max_confidence == 1.0


def test_confidence_module_zero_benchmark_dependencies() -> None:
    source_path = (
        Path(__file__).parent.parent.parent
        / "packages"
        / "application"
        / "src"
        / "cashproof"
        / "application"
        / "confidence.py"
    )
    assert source_path.exists(), f"Source file not found: {source_path}"

    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("cashproof.benchmark"), (
                    f"Forbidden import '{alias.name}' in application/confidence.py"
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not node.module.startswith("cashproof.benchmark"), (
                    f"Forbidden from-import '{node.module}' in application/confidence.py"
                )
