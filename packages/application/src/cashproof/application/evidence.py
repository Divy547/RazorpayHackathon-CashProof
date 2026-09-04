"""Field-level Evidence construction for reconciliation hypotheses."""

from __future__ import annotations

from collections.abc import Sequence

from cashproof.domain.derived import Evidence, EvidencePointer, MatchCandidate
from cashproof.domain.source import LedgerEntry, Settlement
from cashproof.domain.types import EvidenceStance, MatchProvenance

ALLOWED_ENTITY_TYPES = frozenset({"LedgerEntry", "Payment", "Settlement", "SettlementItem"})

_PROVENANCE_FIELD: dict[MatchProvenance, tuple[str, float]] = {
    MatchProvenance.STRUCTURED_REFERENCE: ("payment_ref", 1.0),
    MatchProvenance.EXTERNAL_REFERENCE_TEXT: ("narration", 0.7),
    MatchProvenance.NARRATION_ALIAS_TEXT: ("narration", 0.6),
}


def _pointer(entity_type: str, entity_id: str, field: str) -> EvidencePointer:
    if entity_type not in ALLOWED_ENTITY_TYPES:
        raise ValueError(f"Unsupported evidence entity_type: {entity_type}")
    return EvidencePointer(entity_type=entity_type, entity_id=entity_id, field=field)


class EvidenceBuilder:
    """Builds field-level Evidence for actual observable production signals only.

    Never fabricates evidence to force a gate check to pass; every emitted item
    reflects a genuine comparison against source facts.
    """

    def build(
        self,
        settlement: Settlement,
        target_entries: Sequence[LedgerEntry],
        candidates: Sequence[MatchCandidate],
    ) -> tuple[Evidence, ...]:
        candidate_by_entry = {c.ledger_entry_id: c for c in candidates}
        evidence: list[Evidence] = []

        for entry in target_entries:
            candidate = candidate_by_entry.get(entry.id)
            if candidate is not None:
                field, relevance = _PROVENANCE_FIELD[candidate.provenance]
                evidence.append(
                    Evidence(
                        pointer=_pointer("LedgerEntry", entry.id, field),
                        relevance=relevance,
                        stance=EvidenceStance.SUPPORTS,
                        decision_consumed=True,
                    )
                )

            currency_ok = entry.currency == settlement.currency
            evidence.append(
                Evidence(
                    pointer=_pointer("LedgerEntry", entry.id, "currency"),
                    relevance=1.0,
                    stance=EvidenceStance.SUPPORTS if currency_ok else EvidenceStance.CONTRADICTS,
                    decision_consumed=True,
                )
            )

            amount_ok = entry.amount_minor == settlement.net_deposited_minor
            evidence.append(
                Evidence(
                    pointer=_pointer("LedgerEntry", entry.id, "amount_minor"),
                    relevance=1.0,
                    stance=EvidenceStance.SUPPORTS if amount_ok else EvidenceStance.CONTRADICTS,
                    decision_consumed=True,
                )
            )

        return tuple(evidence)
