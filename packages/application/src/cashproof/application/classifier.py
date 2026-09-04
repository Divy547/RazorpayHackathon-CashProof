"""Deterministic exception classification using only production-visible facts.

Must never import benchmark ScenarioFamily/GroundTruth internals: classification
is derived exclusively from MatchCandidate facts already visible in production.
"""

from __future__ import annotations

from collections.abc import Sequence

from cashproof.domain.derived import MatchCandidate
from cashproof.domain.types import ExceptionType, MatchProvenance


def classify_exception(
    candidates: Sequence[MatchCandidate],
) -> tuple[ExceptionType, frozenset[str]]:
    """Classify a settlement's exception type from its ranked candidates.

    Returns the exception classification and the proposed target ledger entry id
    set. The proposed set is intentionally empty whenever no single hypothesis can
    be safely proposed (no candidates, or an unresolved tie at the top score).
    """
    if not candidates:
        return ExceptionType.MISSING_RECORD, frozenset()

    top_score = candidates[0].score
    top_candidates = [c for c in candidates if c.score == top_score]

    if len(top_candidates) > 1:
        provenances = {c.provenance for c in top_candidates}
        if len(provenances) > 1:
            # Distinct entries independently supported by different signal types:
            # a genuine conflict between evidence sources, not mere duplication.
            return ExceptionType.CONFLICTING_EVIDENCE, frozenset()
        return ExceptionType.AMBIGUOUS_MATCH, frozenset()

    top = top_candidates[0]
    proposed = frozenset({top.ledger_entry_id})

    if top.provenance != MatchProvenance.STRUCTURED_REFERENCE:
        return ExceptionType.NAME_ALIAS, proposed

    if "amount_exact_match" in top.matched_signals:
        return ExceptionType.CLEAN_MATCH, proposed

    return ExceptionType.AMOUNT_MISMATCH, proposed
