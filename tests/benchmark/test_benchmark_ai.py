"""Tests for AI Investigator metrics collection during benchmark runs.

Uses fake providers (no network/SDK access) to test all stop reasons:
- completed
- abstain
- timeout
- budget exhaustion
- malformed output
- provider failure
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from cashproof.application.ports import AIInvestigatorPort, InvestigationOutcome
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.runner import BenchmarkRunner
from cashproof.domain.ai import (
    Investigation,
    InvestigatorBudget,
    ResolutionProposal,
    ToolCallRecord,
)
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem
from cashproof.domain.types import StopReason

FIXED_NOW = datetime(2026, 9, 4, tzinfo=UTC)
BUDGET = InvestigatorBudget(
    max_tool_calls=5,
    max_tokens=4000,
    timeout_seconds=30.0,
    temperature=0.0,
    model_version="fake-model",
)


class ScriptedAIInvestigator(AIInvestigatorPort):
    """Deterministic fake investigator returning configured outcomes."""

    def __init__(
        self,
        outcomes_by_case: Mapping[str, InvestigationOutcome] | None = None,
        default_outcome: InvestigationOutcome | None = None,
    ) -> None:
        self.outcomes_by_case = dict(outcomes_by_case or {})
        self.default_outcome = default_outcome
        self.investigated_cases: list[str] = []

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
        self.investigated_cases.append(case.case_id)
        if case.case_id in self.outcomes_by_case:
            return self.outcomes_by_case[case.case_id]
        if self.default_outcome is not None:
            return self.default_outcome

        # Default fallback: completed without proposal
        return InvestigationOutcome(
            investigation=Investigation(
                investigation_id="inv_default",
                case_id=case.case_id,
                run_id=run_id,
                budget=budget,
                tool_calls=(),
                stop_reason=StopReason.COMPLETED,
                candidates_considered=(),
            ),
            proposal=None,
        )


def _make_investigation(
    case_id: str, stop_reason: StopReason, tool_call_count: int = 1
) -> Investigation:
    tc = [
        ToolCallRecord("get_candidates", (("case_id", case_id),), "found candidates", 10)
        for _ in range(tool_call_count)
    ]
    return Investigation(
        investigation_id=f"inv_{case_id}",
        case_id=case_id,
        run_id="ai_test_run",
        budget=BUDGET,
        tool_calls=tuple(tc),
        stop_reason=stop_reason,
        candidates_considered=(),
    )


def test_ai_benchmark_metrics_completed_and_abstain() -> None:
    config = GeneratorConfig(seed=42, num_settlements=50)

    # First run without investigator to discover case_ids for HUMAN_REVIEW
    base_run = BenchmarkRunner().run(config=config, run_id="discovery_run", now=FIXED_NOW)
    hr_cases = [
        c.case_id for c in base_run.case_evaluations if c.disposition.value == "HUMAN_REVIEW"
    ]
    assert len(hr_cases) >= 2

    c_completed = hr_cases[0]
    c_abstained = hr_cases[1]

    # For c_completed: provide a completed investigation with a proposal
    prop = ResolutionProposal(
        proposal_id="prop_c1",
        investigation_id="inv_c1",
        case_id=c_completed,
        run_id="ai_test_run",
        target_ledger_entry_ids=frozenset(),  # AIInvestigationUseCase checks pool
        rationale="looks good",
        evidence=(),
        confidence=0.85,
    )
    outcome_completed = InvestigationOutcome(
        investigation=_make_investigation(c_completed, StopReason.COMPLETED, tool_call_count=2),
        proposal=prop,
    )
    outcome_abstained = InvestigationOutcome(
        investigation=_make_investigation(c_abstained, StopReason.COMPLETED, tool_call_count=1),
        proposal=None,
    )

    investigator = ScriptedAIInvestigator(
        outcomes_by_case={c_completed: outcome_completed, c_abstained: outcome_abstained},
        default_outcome=outcome_abstained,
    )

    run = BenchmarkRunner().run(
        config=config,
        run_id="ai_test_run",
        investigator=investigator,
        ai_budget=BUDGET,
        now=FIXED_NOW,
    )

    ai = run.ai_metrics
    assert ai.investigations_started >= 2
    assert ai.investigations_abstained >= 1
    assert ai.total_tool_calls >= 3


def test_ai_benchmark_metrics_failure_modes() -> None:
    """Test timeout, budget exhaustion, malformed output, and provider tool failure."""
    config = GeneratorConfig(seed=42, num_settlements=50)
    base_run = BenchmarkRunner().run(config=config, run_id="discovery_run", now=FIXED_NOW)
    hr_cases = [
        c.case_id for c in base_run.case_evaluations if c.disposition.value == "HUMAN_REVIEW"
    ]
    assert len(hr_cases) >= 4

    outcomes = {
        hr_cases[0]: InvestigationOutcome(
            _make_investigation(hr_cases[0], StopReason.TIMEOUT), None
        ),
        hr_cases[1]: InvestigationOutcome(
            _make_investigation(hr_cases[1], StopReason.BUDGET_EXHAUSTED), None
        ),
        hr_cases[2]: InvestigationOutcome(
            _make_investigation(hr_cases[2], StopReason.MALFORMED_OUTPUT), None
        ),
        hr_cases[3]: InvestigationOutcome(
            _make_investigation(hr_cases[3], StopReason.TOOL_FAILURE), None
        ),
    }

    investigator = ScriptedAIInvestigator(
        outcomes_by_case=outcomes,
        default_outcome=InvestigationOutcome(
            _make_investigation("default", StopReason.COMPLETED), None
        ),
    )

    run = BenchmarkRunner().run(
        config=config,
        run_id="ai_failure_run",
        investigator=investigator,
        ai_budget=BUDGET,
        now=FIXED_NOW,
    )

    ai = run.ai_metrics
    assert ai.timeout_count == 1
    assert ai.budget_exhaustion_count == 1
    assert ai.malformed_output_count == 1
    assert ai.tool_failure_count == 1
    assert ai.investigations_failed >= 4
