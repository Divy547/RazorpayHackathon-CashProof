"""Tests for Exception Intelligence and Recurring Exception Clustering."""

from __future__ import annotations

import ast
from datetime import UTC, datetime

import pytest
from cashproof.application.intelligence import (
    ExceptionFingerprint,
    ExceptionIntelligenceService,
    OperationalCategory,
)
from cashproof.application.use_case import ReconciliationResult
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

FIXED_TIME = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)


def _make_case_and_settlement(
    case_id: str,
    exception_type: ExceptionType,
    expected_net: int,
    delta: int = 0,
    provenance: MatchProvenance = MatchProvenance.STRUCTURED_REFERENCE,
    candidate_count: int = 1,
    custom_entry_amount: int | None = None,
) -> tuple[ReconciliationResult, Settlement]:
    now = FIXED_TIME
    settlement = Settlement(case_id, expected_net, Currency.INR, now)
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
        exception_type=exception_type,
        processing_state=ProcessingState.INVESTIGATED,
    )

    candidates: list[MatchCandidate] = []
    entries: list[LedgerEntry] = []
    evidence_list: list[Evidence] = []
    for i in range(candidate_count):
        cand_entry_id = f"le_{case_id}_{i}"
        entry_amount = custom_entry_amount if custom_entry_amount is not None else expected_net
        entry = LedgerEntry(
            cand_entry_id,
            entry_amount,
            Currency.INR,
            now,
            Direction.CREDIT,
        )
        entries.append(entry)
        candidate = MatchCandidate(
            case_id,
            cand_entry_id,
            1.0,
            ("ref_match",),
            ("rule_1",),
            provenance,
            "v1",
            "test_run",
        )
        candidates.append(candidate)
        evidence_list.append(
            Evidence(
                pointer=EvidencePointer("LedgerEntry", cand_entry_id, "id"),
                relevance=1.0,
                stance=EvidenceStance.SUPPORTS,
                decision_consumed=True,
            )
        )

    gate = evaluate_gate(
        case=case,
        settlement=settlement,
        items=item,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset(e.id for e in entries),
        target_ledger_entries=entries,
        deterministic_candidates=candidates,
        evidence=evidence_list,
        already_resolved_target_ids=frozenset(),
    )

    if gate.passed:
        resolution = Resolution.create_auto_resolved(gate)
    elif len(candidates) > 0 and not gate.passed:
        resolution = Resolution.create_human_review_pending(gate)
    else:
        resolution = Resolution.create_unresolved(gate)

    result = ReconciliationResult(
        case=case,
        candidates=tuple(candidates),
        evidence=tuple(evidence_list),
        gate_evaluation=gate,
        resolution=resolution,
        audit_events=(),
    )
    return result, settlement


def test_operational_category_enum() -> None:
    assert OperationalCategory.REFERENCE_AMBIGUITY.value == "REFERENCE_AMBIGUITY"
    assert OperationalCategory.AMOUNT_INCONSISTENCY.value == "AMOUNT_INCONSISTENCY"
    assert OperationalCategory.UNSTRUCTURED_REFERENCE.value == "UNSTRUCTURED_REFERENCE"
    assert OperationalCategory.MISSING_RECORD.value == "MISSING_RECORD"
    assert OperationalCategory.EVIDENCE_CONFLICT.value == "EVIDENCE_CONFLICT"
    assert OperationalCategory.POLICY_REVIEW.value == "POLICY_REVIEW"
    assert OperationalCategory.OTHER.value == "OTHER"


def test_exception_fingerprint_immutability_and_hash() -> None:
    fp1 = ExceptionFingerprint(
        exception_type=ExceptionType.AMBIGUOUS_MATCH,
        failing_check="TARGET_SET_EQUALITY",
        operational_category=OperationalCategory.REFERENCE_AMBIGUITY,
        candidate_count_bucket="2_to_5",
        dominant_provenance=MatchProvenance.STRUCTURED_REFERENCE,
        currency=Currency.INR,
        has_delta=False,
        disposition=Disposition.HUMAN_REVIEW,
    )
    fp2 = ExceptionFingerprint(
        exception_type=ExceptionType.AMBIGUOUS_MATCH,
        failing_check="TARGET_SET_EQUALITY",
        operational_category=OperationalCategory.REFERENCE_AMBIGUITY,
        candidate_count_bucket="2_to_5",
        dominant_provenance=MatchProvenance.STRUCTURED_REFERENCE,
        currency=Currency.INR,
        has_delta=False,
        disposition=Disposition.HUMAN_REVIEW,
    )

    assert fp1 == fp2
    assert hash(fp1) == hash(fp2)
    s = {fp1}
    assert fp2 in s

    with pytest.raises(AttributeError):
        fp1.candidate_count_bucket = "0"  # type: ignore[misc]

    assert "reference_ambiguity" in fp1.fingerprint_key
    assert "target_set_equality" in fp1.fingerprint_key


def test_clustering_empty_results() -> None:
    service = ExceptionIntelligenceService()
    summary = service.cluster_exceptions([], {})
    assert summary.clusters == ()
    assert summary.total_exceptions == 0
    assert summary.total_clusters == 0
    assert summary.recurring_clusters == 0
    assert summary.total_affected_settlement_net_minor == 0
    assert summary.total_affected_delta_minor == 0


def test_clustering_clean_matches_excluded() -> None:
    service = ExceptionIntelligenceService()
    clean_res, settlement = _make_case_and_settlement(
        case_id="case_clean",
        exception_type=ExceptionType.CLEAN_MATCH,
        expected_net=50000,
        candidate_count=1,
    )
    assert clean_res.gate_evaluation.passed is True

    summary = service.cluster_exceptions([clean_res], {settlement.settlement_id: settlement})
    assert summary.clusters == ()
    assert summary.total_exceptions == 0


def test_cluster_grouping_and_financial_aggregation() -> None:
    service = ExceptionIntelligenceService()

    # 2 candidates with same amount will fail BRIDGE check (2 * 100000 != 100000)
    res1, set1 = _make_case_and_settlement(
        case_id="case_001",
        exception_type=ExceptionType.AMBIGUOUS_MATCH,
        expected_net=100000,
        candidate_count=2,
    )
    res2, set2 = _make_case_and_settlement(
        case_id="case_002",
        exception_type=ExceptionType.AMBIGUOUS_MATCH,
        expected_net=250000,
        candidate_count=2,
    )

    summary = service.cluster_exceptions(
        [res1, res2], {set1.settlement_id: set1, set2.settlement_id: set2}
    )
    assert len(summary.clusters) == 1

    c = summary.clusters[0]
    assert c.operational_category == OperationalCategory.REFERENCE_AMBIGUITY
    assert c.case_count == 2
    assert c.is_recurring is True
    # Monetary volume: 100000 + 250000 = 350000
    assert c.affected_settlement_net_minor == 350000
    assert c.affected_delta_minor == 0
    assert c.currency == Currency.INR
    assert c.disposition_counts == (("HUMAN_REVIEW", 2),)
    assert set(c.case_ids) == {"case_001", "case_002"}
    # Representatives: abs(delta) desc, expected_net desc, case_id asc
    # -> case_002 (250000), then case_001 (100000)
    assert c.representative_case_ids == ("case_002", "case_001")


def test_cluster_sorting_and_representative_selection() -> None:
    service = ExceptionIntelligenceService()

    # Create 4 cases in cluster A (amount inconsistency)
    cluster_a_pairs = [
        _make_case_and_settlement(
            case_id=f"case_a_{i}",
            exception_type=ExceptionType.AMOUNT_MISMATCH,
            expected_net=10000 * i,
            delta=500 + i,
            candidate_count=1,
            custom_entry_amount=10000 * i - (500 + i),
        )
        for i in range(1, 5)
    ]

    # Create 2 cases in cluster B (missing record, 0 candidates)
    cluster_b_pairs = [
        _make_case_and_settlement(
            case_id=f"case_b_{i}",
            exception_type=ExceptionType.MISSING_RECORD,
            expected_net=50000 * i,
            delta=50000 * i,
            candidate_count=0,
        )
        for i in range(1, 3)
    ]

    all_results = [p[0] for p in cluster_a_pairs + cluster_b_pairs]
    all_settlements = {p[1].settlement_id: p[1] for p in cluster_a_pairs + cluster_b_pairs}

    summary = service.cluster_exceptions(all_results, all_settlements)

    # Sorted by case_count desc -> Cluster A (4 cases) first, Cluster B (2 cases) second
    assert len(summary.clusters) == 2
    assert summary.clusters[0].case_count == 4
    assert summary.clusters[0].operational_category == OperationalCategory.AMOUNT_INCONSISTENCY
    assert summary.clusters[1].case_count == 2
    assert summary.clusters[1].operational_category == OperationalCategory.MISSING_RECORD

    # Representative cases capped at 3
    assert len(summary.clusters[0].representative_case_ids) == 3
    # Case a_4 had highest delta (504), then a_3 (503), then a_2 (502)
    assert summary.clusters[0].representative_case_ids == ("case_a_4", "case_a_3", "case_a_2")


def test_ground_truth_isolation() -> None:
    """Ensure cashproof.application.intelligence never imports from cashproof.benchmark."""
    import cashproof.application.intelligence as intel_module

    with open(intel_module.__file__) as f:
        tree = ast.parse(f.read(), filename=intel_module.__file__)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("cashproof.benchmark")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not node.module.startswith("cashproof.benchmark")
