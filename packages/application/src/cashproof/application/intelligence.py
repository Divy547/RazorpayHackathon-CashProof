"""Deterministic Exception Intelligence and Recurring Exception Clustering.

Analyzes reconciliation exceptions across a batch to surface operational failure
patterns, recurrence rates, financial impact, and representative cases.

Core rules:
1. Deterministic first: clustering, counts, and monetary aggregation are purely deterministic.
2. GroundTruth isolation: this module operates exclusively on production-visible
   reconciliation facts (ReconciliationResult, Settlement). It never touches benchmark
   or evaluator GroundTruth.
3. Money semantics: integer minor units only. Distinguishes affected settlement net
   volume from net reconciliation accounting delta.
4. Non-mutating: this is an analytical and observational layer that never alters
   cases, gate evaluations, or resolutions.
"""

from __future__ import annotations

import enum
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

from cashproof.application.use_case import ReconciliationResult
from cashproof.domain.decision import GateEvaluation
from cashproof.domain.derived import MatchCandidate, ReconciliationCase
from cashproof.domain.source import Settlement
from cashproof.domain.types import (
    Currency,
    Disposition,
    ExceptionType,
    MatchProvenance,
)


class OperationalCategory(enum.StrEnum):
    """Operational root-cause category for reconciliation exception clusters.

    Derived exclusively from deterministic, production-visible signals.
    """

    REFERENCE_AMBIGUITY = "REFERENCE_AMBIGUITY"
    AMOUNT_INCONSISTENCY = "AMOUNT_INCONSISTENCY"
    UNSTRUCTURED_REFERENCE = "UNSTRUCTURED_REFERENCE"
    MISSING_RECORD = "MISSING_RECORD"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    POLICY_REVIEW = "POLICY_REVIEW"
    OTHER = "OTHER"


def bucket_candidate_count(count: int) -> str:
    """Bucket candidate cardinality to group structurally similar cases."""
    if count == 0:
        return "0"
    if count == 1:
        return "1"
    if count <= 5:
        return "2-5"
    return "6+"


def categorize_exception(
    case: ReconciliationCase,
    candidates: Sequence[MatchCandidate],
    gate: GateEvaluation,
) -> OperationalCategory:
    """Deterministically maps production signals into an operational root-cause category."""
    if case.exception_type == ExceptionType.MISSING_RECORD or not candidates:
        return OperationalCategory.MISSING_RECORD

    if case.exception_type == ExceptionType.CONFLICTING_EVIDENCE:
        return OperationalCategory.EVIDENCE_CONFLICT

    if case.exception_type == ExceptionType.AMBIGUOUS_MATCH or len(candidates) > 1:
        if (
            candidates
            and all(c.provenance == MatchProvenance.STRUCTURED_REFERENCE for c in candidates)
            and case.exception_type == ExceptionType.AMBIGUOUS_MATCH
        ):
            return OperationalCategory.REFERENCE_AMBIGUITY

    if (
        case.exception_type == ExceptionType.AMOUNT_MISMATCH
        or gate.failing_check == "BRIDGE"
        or (
            case.delta != 0
            and any(c.provenance == MatchProvenance.STRUCTURED_REFERENCE for c in candidates)
        )
    ):
        return OperationalCategory.AMOUNT_INCONSISTENCY

    if case.exception_type == ExceptionType.NAME_ALIAS:
        if candidates and any(
            c.provenance
            in (MatchProvenance.NARRATION_ALIAS_TEXT, MatchProvenance.EXTERNAL_REFERENCE_TEXT)
            for c in candidates
        ):
            return OperationalCategory.UNSTRUCTURED_REFERENCE
        return OperationalCategory.POLICY_REVIEW

    if gate.failing_check == "POLICY":
        return OperationalCategory.POLICY_REVIEW

    return OperationalCategory.OTHER


@dataclass(frozen=True, slots=True)
class ExceptionFingerprint:
    """Deterministic, immutable operational fingerprint of a reconciliation exception.

    Captures the structural signature of an operational failure pattern without
    any unique IDs, timestamps, GroundTruth, or evaluator-only metadata.
    """

    exception_type: ExceptionType
    failing_check: str | None
    operational_category: OperationalCategory
    candidate_count_bucket: str
    dominant_provenance: MatchProvenance | None
    currency: Currency
    has_delta: bool
    disposition: Disposition

    @property
    def fingerprint_key(self) -> str:
        """Deterministic, human-readable slug string uniquely identifying this fingerprint."""
        prov_str = self.dominant_provenance.value.lower() if self.dominant_provenance else "none"
        gate_str = self.failing_check.lower() if self.failing_check else "none"
        delta_str = "with_delta" if self.has_delta else "zero_delta"
        return (
            f"{self.operational_category.value.lower()}__"
            f"{self.exception_type.value.lower()}__"
            f"gate_{gate_str}__"
            f"cands_{self.candidate_count_bucket}__"
            f"{prov_str}__"
            f"{delta_str}__"
            f"{self.disposition.value.lower()}"
        )


@dataclass(frozen=True, slots=True)
class ExceptionCluster:
    """Aggregated operational cluster of reconciliation cases sharing an identical fingerprint.

    Financial metrics:
    - affected_settlement_net_minor: total net volume of settlements encountering this pattern.
    - affected_delta_minor: net aggregate accounting discrepancy (expected net minus observed
      ledger total).
    All amounts are strictly integer minor units.
    """

    cluster_key: str
    cluster_name: str
    fingerprint: ExceptionFingerprint
    operational_category: OperationalCategory
    case_count: int
    percentage_of_exceptions: float
    affected_settlement_net_minor: int
    affected_delta_minor: int
    currency: Currency
    first_seen: datetime
    last_seen: datetime
    is_recurring: bool
    dominant_classification: ExceptionType
    dominant_failing_gate: str | None
    disposition_counts: tuple[tuple[str, int], ...]
    representative_case_ids: tuple[str, ...]
    case_ids: tuple[str, ...]
    description: str
    suggested_remediation: str


@dataclass(frozen=True, slots=True)
class ExceptionIntelligenceSummary:
    """High-level batch metrics for reconciliation exception intelligence."""

    total_settlements: int
    total_exceptions: int
    total_clusters: int
    recurring_clusters: int
    total_affected_settlement_net_minor: int
    total_affected_delta_minor: int
    currency: Currency
    clusters: tuple[ExceptionCluster, ...]


def _resolve_cluster_metadata(
    category: OperationalCategory,
    failing_gate: str | None,
    exception_type: ExceptionType,
    provenance: MatchProvenance | None,
) -> tuple[str, str, str]:
    """Provides human-readable name, description, and remediation guidance."""
    if category == OperationalCategory.REFERENCE_AMBIGUITY:
        return (
            "Ambiguous Structured References (Multi-Candidate)",
            "Multiple distinct ledger entries share matching structured identifiers or amounts. "
            "The deterministic safety gate blocks automated resolution to prevent "
            "multi-allocation.",
            "Review candidate transaction timestamps and merchant reference metadata to select "
            "the single valid target entry.",
        )

    if category == OperationalCategory.AMOUNT_INCONSISTENCY:
        return (
            "Settlement Amount Bridge Discrepancy",
            "A reference-matched candidate exists, but the monetary bridge fails to balance "
            "due to fee, tax, refund netting, or adjustment discrepancies.",
            "Inspect the settlement fee, GST (18%), and netted refund lines against payment "
            "processor fee schedule.",
        )

    if category == OperationalCategory.UNSTRUCTURED_REFERENCE:
        if provenance == MatchProvenance.EXTERNAL_REFERENCE_TEXT:
            return (
                "Unstructured External Payment Reference Match",
                "Candidate matched via external payment reference in free-text fields. "
                "Automated resolution is blocked by the policy gate to require explicit "
                "verification.",
                "Inspect candidate external reference string and verify payment authorization "
                "before approving.",
            )
        if provenance == MatchProvenance.NARRATION_ALIAS_TEXT:
            return (
                "Unstructured Bank Narration Alias Match",
                "Candidate matched via fuzzy bank narration text or merchant account alias. "
                "The policy gate requires human inspection of unstructured text.",
                "Inspect candidate narration text against merchant alias mapping before "
                "explicitly approving resolution.",
            )
        return (
            "Unstructured Reference Match",
            "Candidate matched via unstructured free-text attributes. Policy gate requires "
            "manual verification.",
            "Inspect candidate reference and narration text before approving resolution.",
        )

    if category == OperationalCategory.MISSING_RECORD:
        return (
            "Unmatched Missing Settlement Record",
            "No candidate ledger entries were found within the +/- 7 day candidate window "
            "for this settlement.",
            "Verify whether bank ledger entries are pending ingestion or if processor "
            "settlement batch is delayed.",
        )

    if category == OperationalCategory.EVIDENCE_CONFLICT:
        return (
            "Conflicting Evidence Provenance",
            "Multiple candidates surfaced with conflicting evidence stances or incompatible "
            "source provenance.",
            "Examine conflicting source records to determine whether a duplicate payment or "
            "refund reversal occurred.",
        )

    if category == OperationalCategory.POLICY_REVIEW:
        return (
            "Policy Gate Exception Review",
            "Candidates satisfy monetary matching but violate automated settlement release "
            "policy rules.",
            "Perform manual compliance and authorization verification before approving the "
            "target set.",
        )

    name = f"{category.value.replace('_', ' ').title()} ({exception_type.value.replace('_', ' ')})"
    desc = (
        f"Operational exception of type {exception_type.value} "
        f"failing gate check {failing_gate or 'NONE'}."
    )
    remed = "Inspect case details and evidence trail to determine resolution."
    return name, desc, remed


class ExceptionIntelligenceService:
    """Service for deterministic exception fingerprinting, clustering, and impact aggregation."""

    def create_fingerprint(
        self,
        result: ReconciliationResult,
        settlement: Settlement | None = None,
    ) -> ExceptionFingerprint:
        """Derives a deterministic ExceptionFingerprint for a single reconciliation result."""
        case = result.case
        gate = result.gate_evaluation
        candidates = result.candidates

        category = categorize_exception(case, candidates, gate)
        cand_bucket = bucket_candidate_count(len(candidates))

        dominant_prov = candidates[0].provenance if candidates else None
        currency = settlement.currency if settlement else Currency.INR
        has_delta = case.delta != 0

        return ExceptionFingerprint(
            exception_type=case.exception_type,
            failing_check=gate.failing_check,
            operational_category=category,
            candidate_count_bucket=cand_bucket,
            dominant_provenance=dominant_prov,
            currency=currency,
            has_delta=has_delta,
            disposition=result.resolution.disposition,
        )

    def cluster_exceptions(
        self,
        results: Sequence[ReconciliationResult],
        settlements: Mapping[str, Settlement],
    ) -> ExceptionIntelligenceSummary:
        """Clusters all exception cases in the batch into deterministic ExceptionClusters."""
        exceptions = [
            r
            for r in results
            if r.resolution.disposition != Disposition.AUTO_RESOLVED
            and r.case.exception_type != ExceptionType.CLEAN_MATCH
        ]

        total_settlements = len(results)
        total_exceptions = len(exceptions)
        default_currency = Currency.INR

        if not exceptions:
            return ExceptionIntelligenceSummary(
                total_settlements=total_settlements,
                total_exceptions=0,
                total_clusters=0,
                recurring_clusters=0,
                total_affected_settlement_net_minor=0,
                total_affected_delta_minor=0,
                currency=default_currency,
                clusters=(),
            )

        groups: dict[ExceptionFingerprint, list[ReconciliationResult]] = defaultdict(list)
        for r in exceptions:
            settlement = settlements.get(r.case.case_id)
            fp = self.create_fingerprint(r, settlement)
            groups[fp].append(r)

        clusters: list[ExceptionCluster] = []
        total_settlement_net = 0
        total_delta = 0

        for fp, group in groups.items():
            case_count = len(group)
            pct = round((case_count / total_exceptions) * 100.0, 1)

            settlement_net = sum(r.case.expected_net for r in group)
            delta_net = sum(r.case.delta for r in group)

            total_settlement_net += settlement_net
            total_delta += delta_net

            settled_ats = [
                settlements[r.case.case_id].settled_at
                for r in group
                if r.case.case_id in settlements
            ]
            first_seen = min(settled_ats) if settled_ats else datetime.min
            last_seen = max(settled_ats) if settled_ats else datetime.max

            disp_counter = Counter(r.resolution.disposition.value for r in group)
            disposition_counts = tuple(sorted(disp_counter.items()))

            sorted_for_reps = sorted(
                group,
                key=lambda r: (-abs(r.case.delta), -r.case.expected_net, r.case.case_id),
            )
            representative_ids = tuple(r.case.case_id for r in sorted_for_reps[:3])
            all_case_ids = tuple(sorted(r.case.case_id for r in group))

            name, desc, remed = _resolve_cluster_metadata(
                fp.operational_category,
                fp.failing_check,
                fp.exception_type,
                fp.dominant_provenance,
            )

            clusters.append(
                ExceptionCluster(
                    cluster_key=fp.fingerprint_key,
                    cluster_name=name,
                    fingerprint=fp,
                    operational_category=fp.operational_category,
                    case_count=case_count,
                    percentage_of_exceptions=pct,
                    affected_settlement_net_minor=settlement_net,
                    affected_delta_minor=delta_net,
                    currency=fp.currency,
                    first_seen=first_seen,
                    last_seen=last_seen,
                    is_recurring=case_count > 1,
                    dominant_classification=fp.exception_type,
                    dominant_failing_gate=fp.failing_check,
                    disposition_counts=disposition_counts,
                    representative_case_ids=representative_ids,
                    case_ids=all_case_ids,
                    description=desc,
                    suggested_remediation=remed,
                )
            )

        ordered_clusters = tuple(
            sorted(
                clusters,
                key=lambda c: (-c.case_count, -abs(c.affected_settlement_net_minor), c.cluster_key),
            )
        )

        recurring_count = sum(1 for c in ordered_clusters if c.is_recurring)

        return ExceptionIntelligenceSummary(
            total_settlements=total_settlements,
            total_exceptions=total_exceptions,
            total_clusters=len(ordered_clusters),
            recurring_clusters=recurring_count,
            total_affected_settlement_net_minor=total_settlement_net,
            total_affected_delta_minor=total_delta,
            currency=ordered_clusters[0].currency if ordered_clusters else default_currency,
            clusters=ordered_clusters,
        )
