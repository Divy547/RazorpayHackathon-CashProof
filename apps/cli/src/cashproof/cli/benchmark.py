"""CashProof Benchmark CLI.

Evaluates the real production reconciliation pipeline against Phase 2 GroundTruth.
Run with: uv run python -m cashproof.cli.benchmark
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.runner import BenchmarkRunner


def run_cli() -> int:
    parser = argparse.ArgumentParser(description="CashProof Controller Benchmark Runner")
    parser.add_argument("--seed", type=int, default=42, help="PRNG seed for dataset generator")
    parser.add_argument(
        "--num-settlements",
        type=int,
        default=100,
        help="Number of settlements to generate (>= 50)",
    )
    parser.add_argument("--run-id", type=str, default=None, help="Optional run identifier")
    parser.add_argument(
        "--arm",
        type=str,
        default="deterministic",
        choices=["deterministic", "ai_investigator"],
        help="Reconciliation evaluation arm",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output benchmark results in JSON format",
    )

    args = parser.parse_args()

    if args.num_settlements < 50:
        print("ERROR: --num-settlements must be >= 50", file=sys.stderr)
        return 1

    config = GeneratorConfig(seed=args.seed, num_settlements=args.num_settlements)
    runner = BenchmarkRunner()

    if not args.json:
        print("=" * 70)
        print("CashProof Controller Benchmark")
        print(f"Seed: {args.seed} | Settlements: {args.num_settlements} | Arm: {args.arm}")
        print("=" * 70)

    run = runner.run(
        config=config,
        run_id=args.run_id,
        arm=args.arm,
        now=datetime.now(UTC),
    )

    overall = run.overall_metrics
    if overall is None:
        print("ERROR: Benchmark run did not produce overall metrics", file=sys.stderr)
        return 1

    if args.json:
        import json

        payload = run.summary_dict()
        payload["scenario_matrix"] = [
            {
                "scenario_family": row.scenario_family.value,
                "total": row.total,
                "auto_resolved": row.auto_resolved,
                "human_review": row.human_review,
                "unresolved": row.unresolved,
                "correct_outcomes": row.correct_outcomes,
                "false_auto_resolutions": row.false_auto_resolutions,
            }
            for row in run.scenario_matrix
        ]
        if run.confidence_report is not None:
            payload["confidence_report"] = {
                "overall_ece": run.confidence_report.overall_ece,
                "overall_brier_score": run.confidence_report.overall_brier_score,
                "predictions_made": run.confidence_report.predictions_made,
                "abstentions": run.confidence_report.abstentions,
                "high_confidence_precision": run.confidence_report.high_confidence_precision,
                "potential_automation_opportunities": (
                    run.confidence_report.potential_automation_opportunities
                ),
                "potential_automation_volume_minor": (
                    run.confidence_report.potential_automation_volume_minor
                ),
            }
        print(json.dumps(payload, indent=2))
        return 0 if overall.safety_gate_passed else 1

    # Safety Gate Banner
    print()
    if overall.safety_gate_passed:
        print("  [PASS] SAFETY GATE PASSED (0 False Auto-Resolutions)")
    else:
        err_msg = (
            f"  [FAIL] SAFETY GATE FAILED "
            f"({overall.false_auto_resolution_count} False Auto-Resolutions)"
        )
        print(err_msg)
    print()

    # Headline KPI & Timing
    duration = run.timing.pipeline_duration_seconds if run.timing else 0.0
    boundary = run.timing.timing_boundary if run.timing else "N/A"
    print("-" * 70)
    print("PRIMARY PERFORMANCE KPI")
    print("-" * 70)
    print(f"  Correctly Resolved Records / Minute: {overall.records_per_minute:.1f} rec/min")
    print(f"  Pipeline Wall-Clock Duration:       {duration:.4f} s")
    print(f"  Timing Boundary:                    {boundary}")
    print()

    # Disposition Metrics & Rates
    print("-" * 70)
    print("DISPOSITION METRICS & CORRECTNESS")
    print("-" * 70)
    print(f"  Total Cases:               {overall.total_cases}")
    auto_pct = overall.auto_resolution_rate * 100
    print(f"  AUTO_RESOLVED:             {overall.auto_resolved} ({auto_pct:.1f}%)")
    hr_pct = overall.human_review_rate * 100
    print(f"  HUMAN_REVIEW:              {overall.human_review} ({hr_pct:.1f}%)")
    unres_pct = overall.unresolved_rate * 100
    print(f"  UNRESOLVED:                {overall.unresolved} ({unres_pct:.1f}%)")
    print(f"  Correct Auto-Resolutions:  {overall.correct_auto_resolutions}")
    print(f"  False Auto-Resolutions:    {overall.false_auto_resolutions}")
    print(f"  Target Set Accuracy:       {overall.exact_target_set_accuracy * 100:.1f}%")
    print()

    # Confidence Calibration & Quality
    if run.confidence_report is not None:
        cr = run.confidence_report
        print("-" * 70)
        print("CONFIDENCE CALIBRATION & AUTOMATION QUALITY (EVALUATOR-ONLY)")
        print("-" * 70)
        ece_pct = cr.overall_ece * 100
        print(f"  Expected Calibration Error (ECE): {cr.overall_ece:.4f} ({ece_pct:.1f}%)")
        print(f"  Brier Score:                     {cr.overall_brier_score:.4f}")
        print(
            f"  Predictions Made:                {cr.predictions_made} "
            f"(Abstentions: {cr.abstentions})"
        )
        high_prec = cr.high_confidence_precision * 100
        print(f"  High-Confidence Precision (>=0.8): {high_prec:.1f}%")
        vol_inr = cr.potential_automation_volume_minor / 100
        print(
            f"  Potential Automation Opportunities: {cr.potential_automation_opportunities} cases "
            f"(₹{vol_inr:,.2f})"
        )
        print("  Gate × Confidence Invariant:      Confidence belief never bypasses Gate firewall")
        print()

    # Scenario Matrix (S1 - S6)
    print("-" * 70)
    header = (
        f"{'Scenario':<8} | {'Total':<6} | {'Auto':<6} | "
        f"{'Review':<6} | {'Unres':<6} | {'Correct':<8} | {'FalseAuto':<10}"
    )
    print(header)
    print("-" * 70)
    for row in run.scenario_matrix:
        print(
            f"{row.scenario_family.value:<8} | {row.total:<6} | {row.auto_resolved:<6} | "
            f"{row.human_review:<6} | {row.unresolved:<6} | {row.correct_outcomes:<8} | "
            f"{row.false_auto_resolutions:<10}"
        )
    print("-" * 70)

    # AI Metrics (if applicable)
    if args.arm == "ai_investigator":
        ai = run.ai_metrics
        print()
        print("-" * 70)
        print("AI INVESTIGATOR METRICS")
        print("-" * 70)
        print(f"  Investigations Started:    {ai.investigations_started}")
        print(f"  Investigations Completed:  {ai.investigations_completed}")
        print(f"  Investigations Failed:     {ai.investigations_failed}")
        print(f"  Investigations Abstained:  {ai.investigations_abstained}")
        print(f"  Proposals Generated:       {ai.proposals_generated}")
        print(f"  Proposals Gate Passed:     {ai.proposals_gate_passed}")
        print(f"  Proposals Gate Failed:     {ai.proposals_gate_failed}")
        print(f"  Total Tool Calls:          {ai.total_tool_calls}")
        print(f"  Timeouts:                  {ai.timeout_count}")
        print(f"  Budget Exhaustions:        {ai.budget_exhaustion_count}")
        print(f"  Malformed Outputs:         {ai.malformed_output_count}")
        print(f"  Tool Failures:             {ai.tool_failure_count}")
        print("-" * 70)

    return 0 if overall.safety_gate_passed else 1


if __name__ == "__main__":
    sys.exit(run_cli())
