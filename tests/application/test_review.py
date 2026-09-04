"""Tests for HumanReviewUseCase: applying a reviewer decision to a HUMAN_REVIEW case.

Negative-path tests (S2/S3/S4/S5) run against the REAL Phase 2 dataset through the
REAL production pipeline, proving the deterministic gate - unmodified - independently
refuses every unsafe reviewer selection. The one positive-path test is hand-built
(no real case in the generated dataset ever reaches HUMAN_REVIEW with a cleanly
approvable candidate - see the design report), proving the mechanism itself works
when a selection genuinely satisfies every check.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from cashproof.application.batch import BatchReconciler
from cashproof.application.review import (
    HumanReviewUseCase,
    InvalidCandidateSelectionError,
    ReviewNotApplicableError,
)
from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.generator import GeneratedDataset, generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import ScenarioFamily
from cashproof.domain.decision import Resolution, evaluate_gate
from cashproof.domain.derived import MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Payment, Settlement, SettlementItem
from cashproof.domain.types import (
    AuditActor,
    Currency,
    Direction,
    Disposition,
    ExceptionType,
    HypothesisSource,
    MatchProvenance,
    ProcessingState,
    ReviewOutcome,
)

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)


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


def _run_real_batch() -> tuple[GeneratedDataset, dict[str, ReconciliationResult]]:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)
    summary = BatchReconciler().run(
        run_id="review-test",
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=FIXED_NOW,
    )
    results_by_case = {r.case.case_id: r for r in summary.results}
    return dataset, results_by_case


def _example(family: ScenarioFamily) -> tuple[GeneratedDataset, ReconciliationResult, str]:
    dataset, results_by_case = _run_real_batch()
    gt_by_case = {gt.case_id: gt for gt in dataset.ground_truths}
    case_id = next(cid for cid, gt in gt_by_case.items() if gt.scenario_family == family)
    return dataset, results_by_case[case_id], case_id


def _settlement_context(
    dataset: GeneratedDataset, case_id: str
) -> tuple[Settlement, list[SettlementItem]]:
    settlement = next(s for s in dataset.settlements if s.settlement_id == case_id)
    items_by_settlement, _ = _build_batch_inputs(dataset)
    return settlement, items_by_settlement[case_id]


def test_s2_single_candidate_approved_by_human_review() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    settlement, items = _settlement_context(dataset, case_id)
    assert len(result.candidates) >= 2

    chosen = frozenset({result.candidates[0].ledger_entry_id})
    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="approve",
        selected_target_ids=chosen,
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.gate_evaluation.passed is True
    assert updated.gate_evaluation.failing_check is None
    assert updated.resolution.disposition == Disposition.HUMAN_REVIEW
    assert updated.resolution.review_outcome == ReviewOutcome.APPROVED
    assert updated.resolution.reviewer == "rev_alice"
    assert updated.resolution.target_ledger_entry_ids == chosen


def test_s2_both_candidates_rejected_by_bridge() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    settlement, items = _settlement_context(dataset, case_id)

    both = frozenset(c.ledger_entry_id for c in result.candidates)
    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="approve",
        selected_target_ids=both,
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.gate_evaluation.passed is False
    assert updated.gate_evaluation.failing_check == "BRIDGE"
    assert updated.resolution.review_outcome == ReviewOutcome.PENDING


def test_s3_approval_rejected_by_bridge() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    settlement, items = _settlement_context(dataset, case_id)
    assert len(result.candidates) == 1

    chosen = frozenset({result.candidates[0].ledger_entry_id})
    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="approve",
        selected_target_ids=chosen,
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.gate_evaluation.failing_check == "BRIDGE"
    assert updated.resolution.disposition == Disposition.HUMAN_REVIEW
    assert updated.resolution.review_outcome == ReviewOutcome.PENDING


def test_s4_approval_passes_policy_for_human_review() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S4_EXTERNAL_REF_TEXT)
    settlement, items = _settlement_context(dataset, case_id)
    assert len(result.candidates) == 1

    chosen = frozenset({result.candidates[0].ledger_entry_id})
    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="approve",
        selected_target_ids=chosen,
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.gate_evaluation.passed is True
    assert updated.gate_evaluation.failing_check is None
    assert updated.resolution.disposition == Disposition.HUMAN_REVIEW
    assert updated.resolution.review_outcome == ReviewOutcome.APPROVED
    assert updated.resolution.reviewer == "rev_alice"


def test_s5_approval_passes_policy_for_human_review() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S5_NARRATION_ALIAS_TEXT)
    settlement, items = _settlement_context(dataset, case_id)
    assert len(result.candidates) == 1

    chosen = frozenset({result.candidates[0].ledger_entry_id})
    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="approve",
        selected_target_ids=chosen,
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.gate_evaluation.passed is True
    assert updated.gate_evaluation.failing_check is None
    assert updated.resolution.disposition == Disposition.HUMAN_REVIEW
    assert updated.resolution.review_outcome == ReviewOutcome.APPROVED
    assert updated.resolution.reviewer == "rev_alice"


def test_s4_s5_still_cannot_auto_resolve_via_batch_reconciler() -> None:
    dataset, results_by_case = _run_real_batch()
    gt_by_case = {gt.case_id: gt for gt in dataset.ground_truths}
    for cid, gt in gt_by_case.items():
        if gt.scenario_family in (
            ScenarioFamily.S4_EXTERNAL_REF_TEXT,
            ScenarioFamily.S5_NARRATION_ALIAS_TEXT,
        ):
            r = results_by_case[cid]
            assert r.resolution.disposition == Disposition.HUMAN_REVIEW
            assert r.resolution.review_outcome == ReviewOutcome.PENDING
            assert r.gate_evaluation.passed is False
            assert r.gate_evaluation.failing_check == "POLICY"


def test_invalid_candidate_selection_rejected() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    settlement, items = _settlement_context(dataset, case_id)

    with pytest.raises(InvalidCandidateSelectionError):
        HumanReviewUseCase().submit_review(
            result=result,
            settlement=settlement,
            items=items,
            ledger_pool=dataset.ledger_entries,
            decision="approve",
            selected_target_ids=frozenset({"le_not_a_real_candidate"}),
            reviewer="rev_alice",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )


def test_empty_selection_rejected_on_approve() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    settlement, items = _settlement_context(dataset, case_id)

    with pytest.raises(InvalidCandidateSelectionError):
        HumanReviewUseCase().submit_review(
            result=result,
            settlement=settlement,
            items=items,
            ledger_pool=dataset.ledger_entries,
            decision="approve",
            selected_target_ids=frozenset(),
            reviewer="rev_alice",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )


def test_reject_becomes_unresolved_and_never_auto_resolved() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    settlement, items = _settlement_context(dataset, case_id)

    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="reject",
        selected_target_ids=frozenset(),
        reviewer="rev_bob",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.resolution.disposition == Disposition.UNRESOLVED
    assert updated.resolution.review_outcome == ReviewOutcome.REJECTED


def test_leaving_pending_is_a_no_op_on_resolution() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S4_EXTERNAL_REF_TEXT)
    settlement, items = _settlement_context(dataset, case_id)

    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="pending",
        selected_target_ids=frozenset(),
        reviewer="rev_carol",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.resolution.disposition == Disposition.HUMAN_REVIEW
    assert updated.resolution.review_outcome == ReviewOutcome.PENDING
    assert updated.resolution is result.resolution  # untouched


def test_reviewer_audit_events_emitted_with_reviewer_actor() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    settlement, items = _settlement_context(dataset, case_id)

    updated = HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="reject",
        selected_target_ids=frozenset(),
        reviewer="rev_dana",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    new_events = [e for e in updated.audit_events if e not in result.audit_events]
    assert new_events
    for event in new_events:
        assert event.actor == AuditActor.REVIEWER
        assert dict(event.metadata).get("reviewer") == "rev_dana"


def test_review_not_applicable_to_auto_resolved_case() -> None:
    dataset, results_by_case = _run_real_batch()
    gt_by_case = {gt.case_id: gt for gt in dataset.ground_truths}
    case_id = next(
        cid
        for cid, gt in gt_by_case.items()
        if gt.scenario_family == ScenarioFamily.S1_STRUCTURED_EXACT
    )
    result = results_by_case[case_id]
    assert result.resolution.disposition == Disposition.AUTO_RESOLVED
    settlement, items = _settlement_context(dataset, case_id)

    with pytest.raises(ReviewNotApplicableError):
        HumanReviewUseCase().submit_review(
            result=result,
            settlement=settlement,
            items=items,
            ledger_pool=dataset.ledger_entries,
            decision="reject",
            selected_target_ids=frozenset(),
            reviewer="rev_alice",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )


def test_original_gate_evaluation_and_resolution_untouched() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    settlement, items = _settlement_context(dataset, case_id)
    original_gate = result.gate_evaluation
    original_resolution = result.resolution

    HumanReviewUseCase().submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="reject",
        selected_target_ids=frozenset(),
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert result.gate_evaluation is original_gate
    assert result.resolution is original_resolution
    assert original_resolution.disposition == Disposition.HUMAN_REVIEW
    assert original_resolution.review_outcome == ReviewOutcome.PENDING


def test_immutability_already_approved_case_rejects_subsequent_reviews() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S4_EXTERNAL_REF_TEXT)
    settlement, items = _settlement_context(dataset, case_id)
    chosen = frozenset({result.candidates[0].ledger_entry_id})

    use_case = HumanReviewUseCase()
    approved = use_case.submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="approve",
        selected_target_ids=chosen,
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )
    assert approved.resolution.review_outcome == ReviewOutcome.APPROVED

    # Subsequent approve attempt fails with ReviewNotApplicableError
    with pytest.raises(ReviewNotApplicableError, match="APPROVED"):
        use_case.submit_review(
            result=approved,
            settlement=settlement,
            items=items,
            ledger_pool=dataset.ledger_entries,
            decision="approve",
            selected_target_ids=chosen,
            reviewer="rev_bob",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )

    # Subsequent reject attempt fails with ReviewNotApplicableError
    with pytest.raises(ReviewNotApplicableError, match="APPROVED"):
        use_case.submit_review(
            result=approved,
            settlement=settlement,
            items=items,
            ledger_pool=dataset.ledger_entries,
            decision="reject",
            selected_target_ids=frozenset(),
            reviewer="rev_bob",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )

    # Original approved resolution is completely untouched
    assert approved.resolution.review_outcome == ReviewOutcome.APPROVED
    assert approved.resolution.reviewer == "rev_alice"


def test_immutability_already_rejected_case_rejects_subsequent_reviews() -> None:
    dataset, result, case_id = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    settlement, items = _settlement_context(dataset, case_id)

    use_case = HumanReviewUseCase()
    rejected = use_case.submit_review(
        result=result,
        settlement=settlement,
        items=items,
        ledger_pool=dataset.ledger_entries,
        decision="reject",
        selected_target_ids=frozenset(),
        reviewer="rev_alice",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )
    assert rejected.resolution.disposition == Disposition.UNRESOLVED
    assert rejected.resolution.review_outcome == ReviewOutcome.REJECTED

    # Subsequent approve attempt fails with ReviewNotApplicableError
    with pytest.raises(ReviewNotApplicableError, match="REJECTED"):
        use_case.submit_review(
            result=rejected,
            settlement=settlement,
            items=items,
            ledger_pool=dataset.ledger_entries,
            decision="approve",
            selected_target_ids=frozenset({result.candidates[0].ledger_entry_id}),
            reviewer="rev_bob",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )

    # Subsequent reject attempt fails with ReviewNotApplicableError
    with pytest.raises(ReviewNotApplicableError, match="REJECTED"):
        use_case.submit_review(
            result=rejected,
            settlement=settlement,
            items=items,
            ledger_pool=dataset.ledger_entries,
            decision="reject",
            selected_target_ids=frozenset(),
            reviewer="rev_bob",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )

    # Original rejected resolution is completely untouched
    assert rejected.resolution.disposition == Disposition.UNRESOLVED
    assert rejected.resolution.review_outcome == ReviewOutcome.REJECTED
    assert rejected.resolution.reviewer == "rev_alice"


def test_uniqueness_blocks_approval_of_already_claimed_target() -> None:
    """A genuinely clean candidate must still be blocked if another case already
    claimed the same ledger entry - already_resolved_target_ids is honored.
    """
    now = FIXED_NOW
    settlement = Settlement("set_u1", 10_000, Currency.INR, now)
    items = [SettlementItem("item_u1", "set_u1", "pay_u1", 10_000, 0, 0, 0, 0, 10_000)]
    entry = LedgerEntry("le_u1", 10_000, Currency.INR, now, Direction.CREDIT, payment_ref="set_u1")
    candidate = MatchCandidate(
        "set_u1",
        "le_u1",
        1.0,
        ("payment_ref_exact_match",),
        (),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "run_u",
    )
    original_case = ReconciliationCase(
        "set_u1",
        "set_u1",
        "run_u",
        10_000,
        0,
        10_000,
        ExceptionType.AMBIGUOUS_MATCH,
        ProcessingState.CLOSED,
    )
    original_gate = evaluate_gate(
        case=ReconciliationCase(
            "set_u1",
            "set_u1",
            "run_u",
            10_000,
            0,
            10_000,
            ExceptionType.AMBIGUOUS_MATCH,
            ProcessingState.CLASSIFIED,
        ),
        settlement=settlement,
        items=items,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset(),
        target_ledger_entries=[],
        deterministic_candidates=[candidate],
        evidence=[],
        already_resolved_target_ids=frozenset(),
    )

    original_result = ReconciliationResult(
        case=original_case,
        candidates=(candidate,),
        evidence=(),
        gate_evaluation=original_gate,
        resolution=Resolution.create_human_review_pending(original_gate),
        audit_events=(),
    )

    updated = HumanReviewUseCase().submit_review(
        result=original_result,
        settlement=settlement,
        items=items,
        ledger_pool=[entry],
        decision="approve",
        selected_target_ids=frozenset({"le_u1"}),
        reviewer="rev_alice",
        now=now,
        already_resolved_target_ids=frozenset({"le_u1"}),
    )

    assert updated.gate_evaluation.failing_check == "UNIQUENESS"
    assert updated.resolution.review_outcome == ReviewOutcome.PENDING


def test_genuinely_passing_candidate_set_can_be_approved() -> None:
    """Hand-built positive path: a single, genuinely clean structured candidate
    that the gate independently verifies satisfies every check when approved.
    """
    now = FIXED_NOW
    settlement = Settlement("set_p1", 10_000, Currency.INR, now)
    items = [SettlementItem("item_p1", "set_p1", "pay_p1", 10_000, 0, 0, 0, 0, 10_000)]
    entry = LedgerEntry("le_p1", 10_000, Currency.INR, now, Direction.CREDIT, payment_ref="set_p1")
    candidate = MatchCandidate(
        "set_p1",
        "le_p1",
        1.0,
        ("payment_ref_exact_match", "amount_exact_match"),
        (),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "run_p",
    )
    # Original attempt failed IDENTITY (proposed nothing), simulating a case that
    # was conservatively routed to human review despite one clean candidate existing.
    initial_case_for_gate = ReconciliationCase(
        "set_p1",
        "set_p1",
        "run_p",
        10_000,
        0,
        10_000,
        ExceptionType.AMBIGUOUS_MATCH,
        ProcessingState.CLASSIFIED,
    )
    initial_gate = evaluate_gate(
        case=initial_case_for_gate,
        settlement=settlement,
        items=items,
        hypothesis_source=HypothesisSource.DETERMINISTIC_RULES,
        proposed_target_ids=frozenset(),
        target_ledger_entries=[],
        deterministic_candidates=[candidate],
        evidence=[],
        already_resolved_target_ids=frozenset(),
    )
    assert initial_gate.passed is False and initial_gate.failing_check == "IDENTITY"

    original_result = ReconciliationResult(
        case=replace(initial_case_for_gate, processing_state=ProcessingState.CLOSED),
        candidates=(candidate,),
        evidence=(),
        gate_evaluation=initial_gate,
        resolution=Resolution.create_human_review_pending(initial_gate),
        audit_events=(),
    )

    updated = HumanReviewUseCase().submit_review(
        result=original_result,
        settlement=settlement,
        items=items,
        ledger_pool=[entry],
        decision="approve",
        selected_target_ids=frozenset({"le_p1"}),
        reviewer="rev_alice",
        now=now,
        already_resolved_target_ids=frozenset(),
    )

    assert updated.gate_evaluation.passed is True
    assert updated.gate_evaluation.failing_check is None
    assert updated.resolution.disposition == Disposition.HUMAN_REVIEW
    assert updated.resolution.review_outcome == ReviewOutcome.APPROVED
    assert updated.resolution.reviewer == "rev_alice"
