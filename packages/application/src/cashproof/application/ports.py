"""Application-defined ports.

The application layer depends on these interfaces only; concrete
implementations live in packages/ai (or, for other ports, infrastructure).
Signatures are expressed entirely in Phase 1 domain types - no concrete AI
SDK type may appear here, and no infrastructure type may appear here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from cashproof.domain.ai import Investigation, InvestigatorBudget, ResolutionProposal
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import Evidence, MatchCandidate, ReconciliationCase
from cashproof.domain.source import LedgerEntry, Settlement, SettlementItem


@dataclass(frozen=True, slots=True)
class InvestigationOutcome:
    """Raw output of one AI investigation session.

    proposal is None whenever the investigation did not cleanly complete with
    a submitted proposal (budget exhausted, timeout, provider failure,
    malformed output, or an explicit abstain).
    """

    investigation: Investigation
    proposal: ResolutionProposal | None


class AIInvestigatorPort(Protocol):
    """Port implemented by a concrete AI adapter (e.g. cashproof.ai.AnthropicInvestigator).

    Receives only data already scoped to one case by the caller - never a
    store, never cross-case/cross-settlement data, never GroundTruth or
    ScenarioFamily. Implementations must never mutate any argument.
    """

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
    ) -> InvestigationOutcome: ...
