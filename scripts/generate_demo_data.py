"""Demo-data composition root for the CashProof judge-facing dashboard.

Invokes the EXISTING Phase 3 production reconciliation pipeline
(cashproof.application) over an EXISTING Phase 2 synthetic dataset
(cashproof.benchmark.generator) and serializes the results to JSON for the
frontend.

Safety boundary: ScenarioFamily/GroundTruth are read ONLY in this script, at
the demo/evaluator composition boundary, purely to (a) label representative
examples for demo navigation and (b) compute the "false auto-resolution"
trust metric by comparing production Resolutions against evaluator truth.
They are never passed into cashproof.application code.

Run with: uv run python scripts/generate_demo_data.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cashproof.application.batch import BatchReconciler
from cashproof.application.use_case import ReconciliationResult
from cashproof.benchmark.generator import GeneratedDataset, generate_dataset
from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.models import GroundTruth, Resolvability
from cashproof.domain.decision import GateCheckOutcome
from cashproof.domain.derived import Evidence, MatchCandidate
from cashproof.domain.source import Payment, Settlement, SettlementItem
from cashproof.domain.types import Disposition

SEED = 42
NUM_SETTLEMENTS = 100
FIXED_NOW = datetime(2026, 9, 4, 12, 0, 0, tzinfo=UTC)
_FRONTEND_DATA_DIR = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data"
OUTPUT_PATH = _FRONTEND_DATA_DIR / "demo-data.json"


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


def _serialize_candidate(candidate: MatchCandidate) -> dict[str, Any]:
    return {
        "ledger_entry_id": candidate.ledger_entry_id,
        "score": candidate.score,
        "matched_signals": list(candidate.matched_signals),
        "rule_trace": list(candidate.rule_trace),
        "provenance": candidate.provenance.value,
    }


def _serialize_evidence(item: Evidence) -> dict[str, Any]:
    return {
        "entity_type": item.pointer.entity_type,
        "entity_id": item.pointer.entity_id,
        "field": item.pointer.field,
        "relevance": item.relevance,
        "stance": item.stance.value,
        "decision_consumed": item.decision_consumed,
    }


def _serialize_check(check: GateCheckOutcome) -> dict[str, Any]:
    return {
        "name": check.check_name,
        "passed": check.passed,
        "reason": check.reason,
        "is_mandatory": check.is_mandatory,
    }


def _bridge(items: list[SettlementItem], settlement: Settlement) -> dict[str, Any]:
    gross = sum(i.gross_minor for i in items)
    fee = sum(i.fee_minor for i in items)
    tax = sum(i.tax_on_fee_minor for i in items)
    refund = sum(i.netted_refund_minor for i in items)
    adjustment = sum(i.adjustment_minor for i in items)
    computed = sum(i.computed_net_minor for i in items)
    return {
        "gross_minor": gross,
        "fee_minor": fee,
        "tax_on_fee_minor": tax,
        "netted_refund_minor": refund,
        "adjustment_minor": adjustment,
        "computed_net_minor": computed,
        "expected_net_minor": settlement.net_deposited_minor,
    }


def _serialize_audit_events(result: ReconciliationResult) -> list[dict[str, Any]]:
    events = []
    for event in result.audit_events:
        events.append(
            {
                "event_id": event.event_id,
                "entity_type": event.entity_type,
                "event_type": event.event_type,
                "actor": event.actor.value,
                "timestamp": event.timestamp.isoformat(),
                "metadata": dict(event.metadata),
            }
        )
    return events


def main() -> None:
    config = GeneratorConfig(seed=SEED, num_settlements=NUM_SETTLEMENTS)
    dataset = generate_dataset(config)
    items_by_settlement, payments_by_settlement = _build_batch_inputs(dataset)

    reconciler = BatchReconciler()
    summary = reconciler.run(
        run_id="demo-run-001",
        settlements=dataset.settlements,
        items_by_settlement=items_by_settlement,
        payments_by_settlement=payments_by_settlement,
        ledger_pool=dataset.ledger_entries,
        now=FIXED_NOW,
    )

    # --- Demo/evaluator boundary only: label + trust-metric correlation ---
    gt_by_case: dict[str, GroundTruth] = {gt.case_id: gt for gt in dataset.ground_truths}
    settlement_by_id: dict[str, Settlement] = {s.settlement_id: s for s in dataset.settlements}

    cases: list[dict[str, Any]] = []
    case_detail: dict[str, Any] = {}
    scenario_examples: dict[str, str] = {}
    false_auto_resolutions = 0

    for result in summary.results:
        settlement = settlement_by_id[result.case.case_id]
        gt = gt_by_case.get(result.case.case_id)
        scenario_family = gt.scenario_family.value if gt else None

        if result.resolution.disposition == Disposition.AUTO_RESOLVED and gt is not None:
            is_correct = (
                gt.resolvability == Resolvability.PROVABLE
                and result.resolution.target_ledger_entry_ids == gt.exact_target_ledger_entry_ids
            )
            if not is_correct:
                false_auto_resolutions += 1

        if scenario_family is not None and scenario_family not in scenario_examples:
            scenario_examples[scenario_family] = result.case.case_id

        row = {
            "settlement_id": result.case.case_id,
            "expected_net_minor": result.case.expected_net,
            "observed_net_minor": result.case.observed_ledger_total,
            "delta_minor": result.case.delta,
            "exception_type": result.case.exception_type.value,
            "candidate_count": len(result.candidates),
            "disposition": result.resolution.disposition.value,
            "scenario_family": scenario_family,
        }
        cases.append(row)

        items = items_by_settlement.get(result.case.case_id, [])
        case_detail[result.case.case_id] = {
            **row,
            "currency": settlement.currency.value,
            "settled_at": settlement.settled_at.isoformat(),
            "bridge": _bridge(items, settlement),
            "candidates": [_serialize_candidate(c) for c in result.candidates],
            "evidence": [_serialize_evidence(e) for e in result.evidence],
            "gate": {
                "passed": result.gate_evaluation.passed,
                "failing_check": result.gate_evaluation.failing_check,
                "checks": [_serialize_check(c) for c in result.gate_evaluation.check_outcomes],
                # Gate-level observation: the net amount of the specific proposed
                # target set, as computed internally by evaluate_gate(). Distinct
                # from the case-level observed_net_minor above, which is the
                # authoritative structural ledger state independent of any
                # hypothesis. Empty proposed_target_ids means no target was
                # proposed at all (e.g. ambiguous/missing cases).
                "proposed_target_ids": sorted(result.gate_evaluation.target_ledger_entry_ids),
                "proposed_target_net_minor": (
                    result.gate_evaluation.bridge_snapshot.observed_net_minor
                ),
                "variance_minor": result.gate_evaluation.bridge_snapshot.delta_minor,
            },
            "resolution": {
                "disposition": result.resolution.disposition.value,
                "target_ledger_entry_ids": sorted(result.resolution.target_ledger_entry_ids),
            },
            "audit_events": _serialize_audit_events(result),
        }

    cases.sort(key=lambda c: c["settlement_id"])

    payload = {
        "meta": {
            "run_id": "demo-run-001",
            "generated_at": FIXED_NOW.isoformat(),
            "seed": SEED,
            "num_settlements": NUM_SETTLEMENTS,
            "generator_version": dict(dataset.metadata).get("generator_version"),
        },
        "overview": {
            "total_settlements": summary.total_settlements,
            "auto_resolved": summary.auto_resolved_count,
            "human_review": summary.human_review_count,
            "unresolved": summary.unresolved_count,
            "false_auto_resolutions": false_auto_resolutions,
        },
        "cases": cases,
        "case_detail": case_detail,
        "scenario_examples": scenario_examples,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"Wrote {OUTPUT_PATH} ({len(cases)} cases, {false_auto_resolutions} false auto-resolutions)"
    )


if __name__ == "__main__":
    main()
