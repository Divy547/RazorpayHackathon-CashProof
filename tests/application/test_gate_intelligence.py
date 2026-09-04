"""Tests for Gate Intelligence, Canonical Gate Evaluation, and Controller Explainability."""

from __future__ import annotations

import ast
from datetime import UTC, datetime

from cashproof.application.gate_intelligence import (
    DETERMINISTIC_GATE_EXPLANATIONS,
    MANDATORY_GATE_CHECKS,
    GateIntelligenceService,
    resolve_canonical_evaluation,
)
from cashproof.application.intelligence import (
    ExceptionCluster,
    ExceptionFingerprint,
    OperationalCategory,
)
from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.decision import (
    Resolution,
    evaluate_gate,
)
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


def _make_result_with_gate(
    case_id: str,
    expected_net: int,
    delta: int = 0,
    failing_check: str | None = None,
    disposition: Disposition = Disposition.HUMAN_REVIEW,
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

    if failing_check != "IDENTITY":
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
            1.0,
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
    elif disposition == Disposition.UNRESOLVED:
        resolution = Resolution.create_unresolved(gate)
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


def test_explanation_catalog_completeness() -> None:
    for check_name in MANDATORY_GATE_CHECKS:
        assert check_name in DETERMINISTIC_GATE_EXPLANATIONS
        exp = DETERMINISTIC_GATE_EXPLANATIONS[check_name]
        assert exp.check_name == check_name
        assert len(exp.summary) > 0
        assert len(exp.description) > 0
        assert len(exp.eligibility_requirement) > 0
        assert exp.is_automation_blocker is True


def test_resolve_canonical_evaluation_precedence() -> None:
    res, _ = _make_result_with_gate("case_canon", 10000)
    canonical = resolve_canonical_evaluation(res)
    assert canonical == res.resolution.governing_gate_evaluation
    assert canonical == res.gate_evaluation


def test_analyze_gate_empty_results() -> None:
    service = GateIntelligenceService()
    summary = service.analyze_gate([], {})
    assert summary.total_cases == 0
    assert summary.total_evaluations == 0
    assert summary.passed_cases == 0
    assert summary.failed_cases == 0
    assert summary.pass_rate == 0.0
    assert summary.fail_rate == 0.0
    assert summary.top_blocker is None
    assert summary.automation_blockers == ()
    assert summary.check_breakdowns == ()


def test_analyze_gate_all_pass() -> None:
    res, settlement = _make_result_with_gate("case_pass", 50000, delta=0)
    assert res.gate_evaluation.passed is True

    service = GateIntelligenceService()
    summary = service.analyze_gate([res], {settlement.settlement_id: settlement})

    assert summary.total_cases == 1
    assert summary.passed_cases == 1
    assert summary.failed_cases == 0
    assert summary.pass_rate == 100.0
    assert summary.fail_rate == 0.0
    assert summary.top_blocker is None
    assert summary.total_affected_settlement_net_minor == 0
    assert summary.total_affected_delta_minor == 0
    assert len(summary.automation_blockers) == 0


def test_analyze_gate_mixed_and_deterministic_ranking() -> None:
    # 2 cases failing IDENTITY (no proposed candidates)
    res_id_1, set_id_1 = _make_result_with_gate(
        "case_id_1", 100000, delta=100000, failing_check="IDENTITY"
    )
    res_id_2, set_id_2 = _make_result_with_gate(
        "case_id_2", 200000, delta=200000, failing_check="IDENTITY"
    )

    # 1 case failing BRIDGE (amount mismatch delta 500)
    res_br_1, set_br_1 = _make_result_with_gate("case_br_1", 150000, delta=500)

    # 1 clean match passing
    res_clean, set_clean = _make_result_with_gate("case_clean", 80000, delta=0)

    all_results = [res_id_1, res_id_2, res_br_1, res_clean]
    settlements = {s.settlement_id: s for s in [set_id_1, set_id_2, set_br_1, set_clean]}

    service = GateIntelligenceService()
    summary = service.analyze_gate(all_results, settlements)

    assert summary.total_cases == 4
    assert summary.passed_cases == 1
    assert summary.failed_cases == 3
    assert summary.pass_rate == 25.0
    assert summary.fail_rate == 75.0

    # Total affected volume = 100000 + 200000 + 150000 = 450000
    assert summary.total_affected_settlement_net_minor == 450000
    # Total affected delta = 100000 + 200000 + 500 = 300500
    assert summary.total_affected_delta_minor == 300500

    # Blockers ranking:
    # #1 IDENTITY: 2 cases (vol: 300000)
    # #2 BRIDGE: 1 case (vol: 150000)
    assert len(summary.automation_blockers) == 2
    assert summary.top_blocker == "IDENTITY"

    b1 = summary.automation_blockers[0]
    assert b1.rank == 1
    assert b1.check_name == "IDENTITY"
    assert b1.failure_count == 2
    assert b1.affected_cases == 2
    assert b1.affected_settlement_net_minor == 300000
    assert b1.affected_delta_minor == 300000

    b2 = summary.automation_blockers[1]
    assert b2.rank == 2
    assert b2.check_name == "BRIDGE"
    assert b2.failure_count == 1
    assert b2.affected_cases == 1
    assert b2.affected_settlement_net_minor == 150000
    assert b2.affected_delta_minor == 500


def test_gate_intelligence_cluster_integration() -> None:
    res, settlement = _make_result_with_gate("case_br", 100000, delta=100)

    cluster = ExceptionCluster(
        cluster_key="bridge_discrepancy_key",
        cluster_name="Bridge Discrepancy Pattern",
        fingerprint=ExceptionFingerprint(
            exception_type=ExceptionType.AMOUNT_MISMATCH,
            failing_check="BRIDGE",
            operational_category=OperationalCategory.AMOUNT_INCONSISTENCY,
            candidate_count_bucket="1",
            dominant_provenance=MatchProvenance.STRUCTURED_REFERENCE,
            currency=Currency.INR,
            has_delta=True,
            disposition=Disposition.HUMAN_REVIEW,
        ),
        operational_category=OperationalCategory.AMOUNT_INCONSISTENCY,
        case_count=1,
        percentage_of_exceptions=100.0,
        affected_settlement_net_minor=100000,
        affected_delta_minor=100,
        currency=Currency.INR,
        first_seen=FIXED_TIME,
        last_seen=FIXED_TIME,
        is_recurring=False,
        dominant_classification=ExceptionType.AMOUNT_MISMATCH,
        dominant_failing_gate="BRIDGE",
        disposition_counts=(("HUMAN_REVIEW", 1),),
        representative_case_ids=("case_br",),
        case_ids=("case_br",),
        description="Amount discrepancy description",
        suggested_remediation="Verify bridge amounts",
    )

    service = GateIntelligenceService()
    summary = service.analyze_gate(
        [res],
        {settlement.settlement_id: settlement},
        clusters=[cluster],
    )

    assert len(summary.automation_blockers) == 1
    blocker = summary.automation_blockers[0]
    assert blocker.check_name == "BRIDGE"
    assert blocker.top_cluster_name == "Bridge Discrepancy Pattern"
    assert blocker.top_cluster_key == "bridge_discrepancy_key"

    outcome = summary.case_outcomes[0]
    assert outcome.case_id == "case_br"
    assert outcome.cluster_key == "bridge_discrepancy_key"
    assert outcome.operational_category == "AMOUNT_INCONSISTENCY"


def test_ground_truth_isolation() -> None:
    """Ensure cashproof.application.gate_intelligence never imports from cashproof.benchmark."""
    import cashproof.application.gate_intelligence as gate_module

    with open(gate_module.__file__) as f:
        tree = ast.parse(f.read(), filename=gate_module.__file__)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("cashproof.benchmark")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not node.module.startswith("cashproof.benchmark")
