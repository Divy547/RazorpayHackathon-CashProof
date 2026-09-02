"""Scenario allocation and immutable transformation pipeline for S1-S6 benchmark scenarios."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta

from cashproof.benchmark.generator.config import ScenarioDistribution
from cashproof.benchmark.generator.prng import DeterministicRNG
from cashproof.benchmark.generator.world import BaselineSettlementCase
from cashproof.benchmark.models import GroundTruth, Resolvability, ScenarioFamily
from cashproof.domain.derived import EvidencePointer
from cashproof.domain.source import LedgerEntry, Payment, Refund, Settlement, SettlementItem
from cashproof.domain.types import Direction


@dataclass(frozen=True, slots=True)
class TransformedCase:
    """A settlement case after scenario transformation, with paired GroundTruth."""

    settlement: Settlement
    items: tuple[SettlementItem, ...]
    payments: tuple[Payment, ...]
    refunds: tuple[Refund, ...]
    ledger_entries: tuple[LedgerEntry, ...]
    ground_truth: GroundTruth


def allocate_scenarios(
    num_cases: int,
    distribution: ScenarioDistribution,
    rng: DeterministicRNG,
) -> list[ScenarioFamily]:
    """Deterministically allocate scenario families ensuring full S1-S6 coverage.

    When num_cases >= 6, guarantees at least one case per family (S1-S6),
    distributing the remaining cases using the largest remainder method based on configured weights.
    """
    all_families = (
        ScenarioFamily.S1_STRUCTURED_EXACT,
        ScenarioFamily.S2_STRUCTURED_AMBIGUOUS,
        ScenarioFamily.S3_FINANCIAL_MISMATCH,
        ScenarioFamily.S4_EXTERNAL_REF_TEXT,
        ScenarioFamily.S5_NARRATION_ALIAS_TEXT,
        ScenarioFamily.S6_NON_PROVABLE_CONFLICT,
    )

    if num_cases < len(all_families):
        # Fallback for small test runs
        return [all_families[i % len(all_families)] for i in range(num_cases)]

    weights = {
        ScenarioFamily.S1_STRUCTURED_EXACT: distribution.s1_structured_exact,
        ScenarioFamily.S2_STRUCTURED_AMBIGUOUS: distribution.s2_structured_ambiguous,
        ScenarioFamily.S3_FINANCIAL_MISMATCH: distribution.s3_financial_mismatch,
        ScenarioFamily.S4_EXTERNAL_REF_TEXT: distribution.s4_external_ref_text,
        ScenarioFamily.S5_NARRATION_ALIAS_TEXT: distribution.s5_narration_alias_text,
        ScenarioFamily.S6_NON_PROVABLE_CONFLICT: distribution.s6_non_provable_conflict,
    }

    # Step 1: Base allocation of 1 per family
    counts: dict[ScenarioFamily, int] = {family: 1 for family in all_families}
    remaining = num_cases - len(all_families)

    # Step 2: Largest remainder proportional distribution for remaining slots
    exact_shares = {family: remaining * weights[family] for family in all_families}
    integer_shares = {family: math.floor(share) for family, share in exact_shares.items()}
    remainders = {family: exact_shares[family] - integer_shares[family] for family in all_families}

    allocated_remaining = sum(integer_shares.values())
    leftover = remaining - allocated_remaining

    for family in all_families:
        counts[family] += integer_shares[family]

    # Assign remaining fractional slots by largest remainder
    sorted_by_remainder = sorted(
        all_families,
        key=lambda f: remainders[f],
        reverse=True,
    )
    for i in range(leftover):
        counts[sorted_by_remainder[i]] += 1

    allocation: list[ScenarioFamily] = []
    for family, count in counts.items():
        allocation.extend([family] * count)

    rng.shuffle(allocation)
    return allocation


def apply_scenario_transformations(
    baseline_cases: tuple[BaselineSettlementCase, ...],
    allocations: list[ScenarioFamily],
    rng: DeterministicRNG,
) -> tuple[TransformedCase, ...]:
    """Transform baseline cases into S1-S6 benchmark cases with paired GroundTruth."""
    transformed: list[TransformedCase] = []

    for baseline, family in zip(baseline_cases, allocations, strict=True):
        settlement = baseline.settlement
        settlement_id = settlement.settlement_id
        target = baseline.target_ledger_entry

        if family == ScenarioFamily.S1_STRUCTURED_EXACT:
            gt = GroundTruth(
                case_id=settlement_id,
                resolvability=Resolvability.PROVABLE,
                exact_target_ledger_entry_ids=[target.id],
                justifying_evidence=[
                    EvidencePointer(
                        entity_type="LedgerEntry",
                        entity_id=target.id,
                        field="payment_ref",
                    )
                ],
                scenario_family=ScenarioFamily.S1_STRUCTURED_EXACT,
                not_provable_reason=None,
            )
            transformed.append(
                TransformedCase(
                    settlement=settlement,
                    items=baseline.items,
                    payments=baseline.payments,
                    refunds=baseline.refunds,
                    ledger_entries=(target,),
                    ground_truth=gt,
                )
            )

        elif family == ScenarioFamily.S2_STRUCTURED_AMBIGUOUS:
            # Genuine structural ambiguity: target and decoy share identical
            # payment_ref, amount_minor, currency, and direction.
            # Both timestamps come from the exact same temporal distribution
            # within the locked structured candidate window (+-7 days).
            target_offset_hours = rng.integer(-160, 160)
            decoy_offset_hours = rng.integer(-160, 160)
            if target_offset_hours == decoy_offset_hours:
                decoy_offset_hours = (
                    (target_offset_hours + 12)
                    if target_offset_hours <= 0
                    else (target_offset_hours - 12)
                )

            s2_target = LedgerEntry(
                id=target.id,
                amount_minor=target.amount_minor,
                currency=target.currency,
                timestamp=settlement.settled_at
                + timedelta(hours=target_offset_hours, minutes=rng.integer(0, 59)),
                direction=target.direction,
                payment_ref=target.payment_ref,
                external_ref=target.external_ref,
                narration=target.narration,
                customer_name=target.customer_name,
            )

            decoy = LedgerEntry(
                id=rng.hex_id("le", 12),
                amount_minor=target.amount_minor,
                currency=target.currency,
                timestamp=settlement.settled_at
                + timedelta(hours=decoy_offset_hours, minutes=rng.integer(0, 59)),
                direction=Direction.CREDIT,
                payment_ref=target.payment_ref,  # Identical strong structured reference
                external_ref=None,
                narration=f"NEFT-RZPX-{settlement_id}-PAYOUT",
                customer_name=None,
            )
            gt = GroundTruth(
                case_id=settlement_id,
                resolvability=Resolvability.NOT_PROVABLE,
                exact_target_ledger_entry_ids=[],
                justifying_evidence=[],
                scenario_family=ScenarioFamily.S2_STRUCTURED_AMBIGUOUS,
                not_provable_reason=(
                    "Structured ambiguity: multiple ledger entries share identical "
                    "payment_ref, amount, currency, and direction within candidate window "
                    "(+-7 days) with no discriminating source signals"
                ),
            )
            transformed.append(
                TransformedCase(
                    settlement=settlement,
                    items=baseline.items,
                    payments=baseline.payments,
                    refunds=baseline.refunds,
                    ledger_entries=(s2_target, decoy),
                    ground_truth=gt,
                )
            )

        elif family == ScenarioFamily.S3_FINANCIAL_MISMATCH:
            # Observed ledger side variance: perturb target amount_minor
            # Source settlement and items remain 100% valid Phase 1 records
            delta_paise = rng.choice([50_00, 100_00, -50_00, -100_00])
            new_amount = target.amount_minor + delta_paise
            if new_amount <= 0:
                new_amount = target.amount_minor + 100_00

            perturbed_target = LedgerEntry(
                id=target.id,
                amount_minor=new_amount,
                currency=target.currency,
                timestamp=target.timestamp,
                direction=target.direction,
                payment_ref=target.payment_ref,
                external_ref=target.external_ref,
                narration=target.narration,
                customer_name=target.customer_name,
            )
            gt = GroundTruth(
                case_id=settlement_id,
                resolvability=Resolvability.PROVABLE,
                exact_target_ledger_entry_ids=[perturbed_target.id],
                justifying_evidence=[
                    EvidencePointer(
                        entity_type="LedgerEntry",
                        entity_id=perturbed_target.id,
                        field="payment_ref",
                    )
                ],
                scenario_family=ScenarioFamily.S3_FINANCIAL_MISMATCH,
                not_provable_reason=None,
            )
            transformed.append(
                TransformedCase(
                    settlement=settlement,
                    items=baseline.items,
                    payments=baseline.payments,
                    refunds=baseline.refunds,
                    ledger_entries=(perturbed_target,),
                    ground_truth=gt,
                )
            )

        elif family == ScenarioFamily.S4_EXTERNAL_REF_TEXT:
            # Unstructured external ref in text: strip payment_ref, embed world-derived ref
            # Timestamp sampled bidirectionally from locked unstructured candidate window (+-3 days)
            order_ref = baseline.payments[0].order_ref
            ext_ref = f"EXT-{order_ref}"
            offset_hours = rng.integer(-70, 70)
            unstructured_timestamp = settlement.settled_at + timedelta(
                hours=offset_hours, minutes=rng.integer(0, 59)
            )
            unstructured_target = LedgerEntry(
                id=target.id,
                amount_minor=target.amount_minor,
                currency=target.currency,
                timestamp=unstructured_timestamp,
                direction=target.direction,
                payment_ref=None,  # Structured reference stripped
                external_ref=None,
                narration=f"CMS/NETBANK/{ext_ref}/RZP-PAYOUT",
                customer_name=None,
            )
            gt = GroundTruth(
                case_id=settlement_id,
                resolvability=Resolvability.PROVABLE,
                exact_target_ledger_entry_ids=[unstructured_target.id],
                justifying_evidence=[
                    EvidencePointer(
                        entity_type="LedgerEntry",
                        entity_id=unstructured_target.id,
                        field="narration",
                    )
                ],
                scenario_family=ScenarioFamily.S4_EXTERNAL_REF_TEXT,
                not_provable_reason=None,
            )
            transformed.append(
                TransformedCase(
                    settlement=settlement,
                    items=baseline.items,
                    payments=baseline.payments,
                    refunds=baseline.refunds,
                    ledger_entries=(unstructured_target,),
                    ground_truth=gt,
                )
            )

        elif family == ScenarioFamily.S5_NARRATION_ALIAS_TEXT:
            # Narration alias text: strip references, embed customer name alias in narration
            # Timestamp sampled bidirectionally from locked unstructured candidate window (+-3 days)
            cust_name = baseline.payments[0].customer_name
            alias = "".join(c for c in cust_name.upper() if c.isalnum())
            offset_hours = rng.integer(-70, 70)
            alias_timestamp = settlement.settled_at + timedelta(
                hours=offset_hours, minutes=rng.integer(0, 59)
            )
            alias_target = LedgerEntry(
                id=target.id,
                amount_minor=target.amount_minor,
                currency=target.currency,
                timestamp=alias_timestamp,
                direction=target.direction,
                payment_ref=None,  # Structured reference stripped
                external_ref=None,
                narration=f"UPI-P2M-{alias}-PAYMENT",
                customer_name=None,
            )
            gt = GroundTruth(
                case_id=settlement_id,
                resolvability=Resolvability.PROVABLE,
                exact_target_ledger_entry_ids=[alias_target.id],
                justifying_evidence=[
                    EvidencePointer(
                        entity_type="LedgerEntry",
                        entity_id=alias_target.id,
                        field="narration",
                    )
                ],
                scenario_family=ScenarioFamily.S5_NARRATION_ALIAS_TEXT,
                not_provable_reason=None,
            )
            transformed.append(
                TransformedCase(
                    settlement=settlement,
                    items=baseline.items,
                    payments=baseline.payments,
                    refunds=baseline.refunds,
                    ledger_entries=(alias_target,),
                    ground_truth=gt,
                )
            )

        elif family == ScenarioFamily.S6_NON_PROVABLE_CONFLICT:
            # Non-provable / missing record: target entry is omitted from ledger pool
            gt = GroundTruth(
                case_id=settlement_id,
                resolvability=Resolvability.NOT_PROVABLE,
                exact_target_ledger_entry_ids=[],
                justifying_evidence=[],
                scenario_family=ScenarioFamily.S6_NON_PROVABLE_CONFLICT,
                not_provable_reason="Target ledger record missing from bank ledger pool",
            )
            transformed.append(
                TransformedCase(
                    settlement=settlement,
                    items=baseline.items,
                    payments=baseline.payments,
                    refunds=baseline.refunds,
                    ledger_entries=(),  # Omitted from ledger
                    ground_truth=gt,
                )
            )

    return tuple(transformed)
