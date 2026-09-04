"""Tests for AIInvestigationUseCase: running a bounded AI investigation over a
HUMAN_REVIEW case.

Negative-path tests (S2/S3) run against the REAL Phase 2 dataset through the
REAL production pipeline with a FAKE AIInvestigatorPort (no network), proving
the unmodified deterministic gate independently refuses an AI proposal exactly
as it refuses a reviewer's, regardless of what the (fake, fully-controlled)
"model" claims. The positive-path test is hand-built, mirroring
tests/application/test_review.py's equivalent case.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

import pytest
from cashproof.application.batch import BatchReconciler
from cashproof.application.investigation import AIInvestigationUseCase
from cashproof.application.ports import InvestigationOutcome
from cashproof.application.review import ReviewNotApplicableError
from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.generator import GeneratedDataset, generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import ScenarioFamily
from cashproof.domain.ai import Investigation, InvestigatorBudget, ResolutionProposal
from cashproof.domain.decision import GateEvaluation, Resolution, evaluate_gate
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
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
    StopReason,
)

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)
BUDGET = InvestigatorBudget(
    max_tool_calls=5,
    max_tokens=4000,
    timeout_seconds=30.0,
    temperature=0.0,
    model_version="fake-model",
)


class FakeInvestigator:
    """Test double for AIInvestigatorPort - never touches the network."""

    def __init__(self, outcome: InvestigationOutcome) -> None:
        self._outcome = outcome
        self.calls: list[str] = []

    def investigate(
        self,
        *,
        case: ReconciliationCase,
        settlement: Settlement,
        items: Sequence[SettlementItem],
        candidates: Sequence[MatchCandidate],
        evidence: Sequence[Evidence],
        gate: GateEvaluation,
        ledger_entries_by_id: Mapping[str, LedgerEntry],
        budget: InvestigatorBudget,
        run_id: str,
    ) -> InvestigationOutcome:
        self.calls.append(case.case_id)
        return self._outcome


def _investigation(case_id: str, stop_reason: StopReason = StopReason.COMPLETED) -> Investigation:
    return Investigation(
        investigation_id="inv_test",
        case_id=case_id,
        run_id="run_test",
        budget=BUDGET,
        tool_calls=(),
        stop_reason=stop_reason,
        candidates_considered=(),
    )


def _proposal(
    case_id: str, target_ids: frozenset[str], confidence: float = 0.8
) -> ResolutionProposal:
    return ResolutionProposal(
        proposal_id="prop_test",
        investigation_id="inv_test",
        case_id=case_id,
        run_id="run_test",
        target_ledger_entry_ids=target_ids,
        rationale="test rationale",
        evidence=(),
        confidence=confidence,
    )


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


def _example(
    family: ScenarioFamily,
) -> tuple[GeneratedDataset, ReconciliationResult, Settlement, list[SettlementItem], list[Payment]]:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)
    summary = BatchReconciler().run(
        run_id="investigation-test",
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=FIXED_NOW,
    )
    results_by_case = {r.case.case_id: r for r in summary.results}
    gt_by_case = {gt.case_id: gt for gt in dataset.ground_truths}
    case_id = next(cid for cid, gt in gt_by_case.items() if gt.scenario_family == family)
    settlement = next(s for s in dataset.settlements if s.settlement_id == case_id)
    return (
        dataset,
        results_by_case[case_id],
        settlement,
        items_by_settlement[case_id],
        payments_by_settlement[case_id],
    )


def test_investigation_not_applicable_to_auto_resolved_case() -> None:
    config = GeneratorConfig(seed=42, num_settlements=100)
    dataset = generate_dataset(config)
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)
    summary = BatchReconciler().run(
        run_id="investigation-test",
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=FIXED_NOW,
    )
    gt_by_case = {gt.case_id: gt for gt in dataset.ground_truths}
    case_id = next(
        cid
        for cid, gt in gt_by_case.items()
        if gt.scenario_family == ScenarioFamily.S1_STRUCTURED_EXACT
    )
    result = next(r for r in summary.results if r.case.case_id == case_id)
    assert result.resolution.disposition == Disposition.AUTO_RESOLVED
    settlement = next(s for s in dataset.settlements if s.settlement_id == case_id)

    use_case = AIInvestigationUseCase(
        FakeInvestigator(InvestigationOutcome(_investigation(case_id), None))
    )
    with pytest.raises(ReviewNotApplicableError):
        use_case.run_investigation(
            result=result,
            settlement=settlement,
            items=items_by_settlement[case_id],
            payments=payments_by_settlement[case_id],
            ledger_pool=dataset.ledger_entries,
            budget=BUDGET,
            run_id="run_test",
            now=FIXED_NOW,
            already_resolved_target_ids=frozenset(),
        )


def test_investigation_rejects_out_of_pool_proposal() -> None:
    dataset, result, settlement, items, payments = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    outcome = InvestigationOutcome(
        _investigation(result.case.case_id),
        _proposal(result.case.case_id, frozenset({"le_not_a_real_candidate"})),
    )
    use_case = AIInvestigationUseCase(FakeInvestigator(outcome))

    run_result = use_case.run_investigation(
        result=result,
        settlement=settlement,
        items=items,
        payments=payments,
        ledger_pool=dataset.ledger_entries,
        budget=BUDGET,
        run_id="run_test",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert run_result.proposal is None
    assert run_result.preview_gate is None
    assert run_result.investigation.stop_reason == StopReason.MALFORMED_OUTPUT


def test_investigation_s2_proposal_fails_target_set_equality() -> None:
    dataset, result, settlement, items, payments = _example(ScenarioFamily.S2_STRUCTURED_AMBIGUOUS)
    assert len(result.candidates) >= 2
    chosen = frozenset({result.candidates[0].ledger_entry_id})
    outcome = InvestigationOutcome(
        _investigation(result.case.case_id), _proposal(result.case.case_id, chosen)
    )
    use_case = AIInvestigationUseCase(FakeInvestigator(outcome))

    run_result = use_case.run_investigation(
        result=result,
        settlement=settlement,
        items=items,
        payments=payments,
        ledger_pool=dataset.ledger_entries,
        budget=BUDGET,
        run_id="run_test",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert run_result.proposal is not None
    assert run_result.preview_gate is not None
    assert run_result.preview_gate.passed is False
    assert run_result.preview_gate.failing_check == "TARGET_SET_EQUALITY"
    # The AI must report this honestly rather than forcing a resolution.
    assert result.resolution.disposition == Disposition.HUMAN_REVIEW


def test_investigation_s3_proposal_fails_bridge() -> None:
    dataset, result, settlement, items, payments = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    chosen = frozenset({result.candidates[0].ledger_entry_id})
    outcome = InvestigationOutcome(
        _investigation(result.case.case_id), _proposal(result.case.case_id, chosen)
    )
    use_case = AIInvestigationUseCase(FakeInvestigator(outcome))

    run_result = use_case.run_investigation(
        result=result,
        settlement=settlement,
        items=items,
        payments=payments,
        ledger_pool=dataset.ledger_entries,
        budget=BUDGET,
        run_id="run_test",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert run_result.preview_gate is not None
    assert run_result.preview_gate.passed is False
    assert run_result.preview_gate.failing_check == "BRIDGE"


def test_investigation_result_never_mutates_original_resolution() -> None:
    """Whether the preview gate passes or fails, the case's actual disposition/
    resolution object is untouched - AI investigation never resolves a case.
    """
    dataset, result, settlement, items, payments = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    original_resolution = result.resolution
    chosen = frozenset({result.candidates[0].ledger_entry_id})
    outcome = InvestigationOutcome(
        _investigation(result.case.case_id), _proposal(result.case.case_id, chosen)
    )
    use_case = AIInvestigationUseCase(FakeInvestigator(outcome))

    use_case.run_investigation(
        result=result,
        settlement=settlement,
        items=items,
        payments=payments,
        ledger_pool=dataset.ledger_entries,
        budget=BUDGET,
        run_id="run_test",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert result.resolution is original_resolution
    assert result.resolution.disposition == Disposition.HUMAN_REVIEW


def test_investigation_non_completed_stop_reason_yields_no_proposal() -> None:
    dataset, result, settlement, items, payments = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    outcome = InvestigationOutcome(
        _investigation(result.case.case_id, stop_reason=StopReason.TIMEOUT), None
    )
    use_case = AIInvestigationUseCase(FakeInvestigator(outcome))

    run_result = use_case.run_investigation(
        result=result,
        settlement=settlement,
        items=items,
        payments=payments,
        ledger_pool=dataset.ledger_entries,
        budget=BUDGET,
        run_id="run_test",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert run_result.proposal is None
    assert run_result.preview_gate is None
    assert run_result.investigation.stop_reason == StopReason.TIMEOUT


def test_ai_audit_events_have_ai_actor() -> None:
    dataset, result, settlement, items, payments = _example(ScenarioFamily.S3_FINANCIAL_MISMATCH)
    chosen = frozenset({result.candidates[0].ledger_entry_id})
    outcome = InvestigationOutcome(
        _investigation(result.case.case_id), _proposal(result.case.case_id, chosen)
    )
    use_case = AIInvestigationUseCase(FakeInvestigator(outcome))

    run_result = use_case.run_investigation(
        result=result,
        settlement=settlement,
        items=items,
        payments=payments,
        ledger_pool=dataset.ledger_entries,
        budget=BUDGET,
        run_id="run_test",
        now=FIXED_NOW,
        already_resolved_target_ids=frozenset(),
    )

    assert run_result.audit_events
    for event in run_result.audit_events:
        assert event.actor == AuditActor.AI


def test_genuinely_passing_ai_proposal_yields_gate_passed_but_no_resolution() -> None:
    """Hand-built positive path: a genuinely clean structured candidate the gate
    independently verifies satisfies every check - but disposition/Resolution
    creation remain entirely outside this use case's authority.
    """
    now = FIXED_NOW
    settlement = Settlement("set_ai1", 10_000, Currency.INR, now)
    items = [SettlementItem("item_ai1", "set_ai1", "pay_ai1", 10_000, 0, 0, 0, 0, 10_000)]
    entry = LedgerEntry(
        "le_ai1", 10_000, Currency.INR, now, Direction.CREDIT, payment_ref="set_ai1"
    )
    candidate = MatchCandidate(
        "set_ai1",
        "le_ai1",
        1.0,
        ("payment_ref_exact_match", "amount_exact_match"),
        (),
        MatchProvenance.STRUCTURED_REFERENCE,
        "v1",
        "run_ai",
    )
    initial_case = ReconciliationCase(
        "set_ai1",
        "set_ai1",
        "run_ai",
        10_000,
        0,
        10_000,
        ExceptionType.AMBIGUOUS_MATCH,
        ProcessingState.CLASSIFIED,
    )
    initial_gate = evaluate_gate(
        case=initial_case,
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
        case=ReconciliationCase(
            "set_ai1",
            "set_ai1",
            "run_ai",
            10_000,
            0,
            10_000,
            ExceptionType.AMBIGUOUS_MATCH,
            ProcessingState.CLOSED,
        ),
        candidates=(candidate,),
        evidence=(),
        gate_evaluation=initial_gate,
        resolution=Resolution.create_human_review_pending(initial_gate),
        audit_events=(),
    )

    outcome = InvestigationOutcome(
        _investigation("set_ai1"), _proposal("set_ai1", frozenset({"le_ai1"}), confidence=0.95)
    )
    use_case = AIInvestigationUseCase(FakeInvestigator(outcome))

    run_result = use_case.run_investigation(
        result=original_result,
        settlement=settlement,
        items=items,
        payments=[],
        ledger_pool=[entry],
        budget=BUDGET,
        run_id="run_ai",
        now=now,
        already_resolved_target_ids=frozenset(),
    )

    assert run_result.preview_gate is not None
    assert run_result.preview_gate.passed is True
    assert run_result.proposal is not None
    # Confidence is present but plays no role in the gate outcome above - the
    # gate passed purely from independent, deterministic re-verification.
    assert run_result.proposal.confidence == 0.95
    assert run_result.proposal.evidence  # rebuilt deterministically, non-empty
    assert original_result.resolution.disposition == Disposition.HUMAN_REVIEW
