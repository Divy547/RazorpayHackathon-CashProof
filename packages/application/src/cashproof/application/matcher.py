"""Deterministic candidate matching over production source records.

Produces MatchCandidate hypotheses only. A candidate's score exists solely for
ranking/reporting and must never be used to authorize a resolution; only
evaluate_gate() may authorize a resolution.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta

from cashproof.domain.derived import MatchCandidate
from cashproof.domain.source import LedgerEntry, Payment, Settlement
from cashproof.domain.types import MatchProvenance

STRUCTURED_CANDIDATE_WINDOW = timedelta(days=7)
UNSTRUCTURED_CANDIDATE_WINDOW = timedelta(days=3)

_PROVENANCE_BASE_SCORE: dict[MatchProvenance, float] = {
    MatchProvenance.STRUCTURED_REFERENCE: 0.8,
    MatchProvenance.EXTERNAL_REFERENCE_TEXT: 0.5,
    MatchProvenance.NARRATION_ALIAS_TEXT: 0.5,
}
_AMOUNT_MATCH_BONUS = 0.2


def _alnum_upper(text: str) -> str:
    return "".join(c for c in text.upper() if c.isalnum())


def _score(provenance: MatchProvenance, amount_match: bool) -> float:
    base = _PROVENANCE_BASE_SCORE[provenance]
    bonus = _AMOUNT_MATCH_BONUS if amount_match else 0.0
    return round(base + bonus, 4)


class CandidateMatcher:
    """Deterministic, seedless matcher producing ranked MatchCandidate hypotheses.

    Only inspects observable production facts: structured payment_ref linkage,
    narration text (external references / customer-name aliases), and amount.
    Never reads benchmark scenario labels and never uses randomness.
    """

    def __init__(self, engine_version: str = "cashproof-matcher-1.0.0") -> None:
        self._engine_version = engine_version

    def find_candidates(
        self,
        case_id: str,
        run_id: str,
        settlement: Settlement,
        payments: Sequence[Payment],
        ledger_entries: Sequence[LedgerEntry],
    ) -> tuple[MatchCandidate, ...]:
        """Scan the full ledger pool for candidates matching the given settlement."""
        ext_refs = {f"EXT-{p.order_ref}" for p in payments if p.order_ref}
        name_aliases = {_alnum_upper(p.customer_name) for p in payments if p.customer_name}
        name_aliases.discard("")

        candidates: list[MatchCandidate] = []
        for entry in ledger_entries:
            provenance, signals, rule_trace = self._classify_entry(
                entry, settlement, ext_refs, name_aliases
            )
            if provenance is None:
                continue

            amount_match = entry.amount_minor == settlement.net_deposited_minor
            if amount_match:
                signals.append("amount_exact_match")

            candidates.append(
                MatchCandidate(
                    case_id=case_id,
                    ledger_entry_id=entry.id,
                    score=_score(provenance, amount_match),
                    matched_signals=tuple(signals),
                    rule_trace=tuple(rule_trace),
                    provenance=provenance,
                    engine_version=self._engine_version,
                    run_id=run_id,
                )
            )

        candidates.sort(key=lambda c: (-c.score, c.ledger_entry_id))
        return tuple(candidates)

    def _classify_entry(
        self,
        entry: LedgerEntry,
        settlement: Settlement,
        ext_refs: set[str],
        name_aliases: set[str],
    ) -> tuple[MatchProvenance | None, list[str], list[str]]:
        offset = abs(entry.timestamp - settlement.settled_at)
        signals: list[str] = []
        rule_trace: list[str] = []

        if entry.payment_ref == settlement.settlement_id and offset <= STRUCTURED_CANDIDATE_WINDOW:
            signals.append("payment_ref_exact_match")
            rule_trace.append("structured_reference_window_7d")
            return MatchProvenance.STRUCTURED_REFERENCE, signals, rule_trace

        if not entry.narration or offset > UNSTRUCTURED_CANDIDATE_WINDOW:
            return None, signals, rule_trace

        # Unstructured text signals additionally require amount agreement: narration
        # pattern matching alone is too weak a discriminator to surface as a candidate.
        if entry.amount_minor != settlement.net_deposited_minor:
            return None, signals, rule_trace

        matched_ext = next((r for r in ext_refs if r in entry.narration), None)
        if matched_ext is not None:
            signals.append(f"external_reference_text:{matched_ext}")
            rule_trace.append("external_reference_text_window_3d")
            return MatchProvenance.EXTERNAL_REFERENCE_TEXT, signals, rule_trace

        matched_alias = next((a for a in name_aliases if a in entry.narration), None)
        if matched_alias is not None:
            signals.append(f"narration_alias_text:{matched_alias}")
            rule_trace.append("narration_alias_text_window_3d")
            return MatchProvenance.NARRATION_ALIAS_TEXT, signals, rule_trace

        return None, signals, rule_trace
