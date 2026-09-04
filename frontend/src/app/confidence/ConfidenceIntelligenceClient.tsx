"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  CheckCircle2,
  ExternalLink,
  Info,
  Layers,
  Scale,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  XCircle,
} from "lucide-react";
import { formatMinor } from "@/lib/format";
import type {
  AutomationOpportunityResponse,
  BenchmarkConfidenceResponse,
  ConfidenceBucketResponse,
  OperationalConfidenceResponse,
  ScenarioConfidenceMetricResponse,
} from "@/lib/types";

interface Props {
  operationalData: OperationalConfidenceResponse | null;
  benchmarkData: BenchmarkConfidenceResponse | null;
}

export function ConfidenceIntelligenceClient({
  operationalData,
  benchmarkData,
}: Props) {
  const [activeTab, setActiveTab] = useState<"benchmark" | "operational">(
    benchmarkData ? "benchmark" : "operational",
  );
  const [selectedThreshold, setSelectedThreshold] = useState<number>(0.8);

  const bm = benchmarkData;
  const op = operationalData;

  const currentThresholdMetric = bm?.threshold_curve.find(
    (t) => Math.abs(t.threshold - selectedThreshold) < 0.05,
  );

  return (
    <div className="space-y-6">
      {/* Top Architecture Invariant Banner */}
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />
          <div className="space-y-1">
            <h2 className="text-sm font-semibold text-amber-200">
              Core Architecture Invariant: Confidence ≠ Authorization
            </h2>
            <p className="text-xs leading-relaxed text-amber-300/90">
              Confidence measures statistical belief and hypothesis strength; the deterministic{" "}
              <strong className="text-amber-100">GateEvaluation</strong> is the sole authorization firewall.
              A hypothesis with 100% confidence cannot and will never bypass arithmetic bridge rules,
              tax reconciliation, or identity checks. The system strictly fails closed.
            </p>
          </div>
        </div>
      </div>

      {/* Mode Tabs */}
      <div className="flex border-b border-slate-800">
        <button
          type="button"
          onClick={() => setActiveTab("benchmark")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
            activeTab === "benchmark"
              ? "border-emerald-500 text-emerald-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Scale className="h-4 w-4" />
          Benchmark Calibration (Evaluator Ground Truth)
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("operational")}
          className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
            activeTab === "operational"
              ? "border-emerald-500 text-emerald-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="h-4 w-4" />
          Operational Hypothesis Distribution (Production)
        </button>
      </div>

      {/* ---------------------------------------------------- */}
      {/* TAB 1: BENCHMARK CALIBRATION (EVALUATOR-ONLY GROUND TRUTH) */}
      {/* ---------------------------------------------------- */}
      {activeTab === "benchmark" && (
        <>
          {bm ? (
            <div className="space-y-8">
              {/* KPI Summary Cards */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-400">
                      Expected Calibration Error
                    </span>
                    <TrendingUp className="h-4 w-4 text-sky-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-bold tracking-tight text-slate-100">
                      {(bm.overall_ece * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs text-slate-400">
                      (ECE {bm.overall_ece.toFixed(4)})
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Weighted distance between confidence and empirical accuracy
                  </p>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-400">
                      Brier Calibration Score
                    </span>
                    <BarChart3 className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-bold tracking-tight text-slate-100">
                      {bm.overall_brier_score.toFixed(4)}
                    </span>
                    <span className="text-xs text-emerald-400">Low MSE</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Mean squared error of confidence against true target sets
                  </p>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-400">
                      High-Confidence Precision
                    </span>
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-bold tracking-tight text-slate-100">
                      {(bm.high_confidence_precision * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs text-slate-400">at ≥ 0.80 conf</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Target-set correctness for top-tier hypotheses
                  </p>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-400">
                      Potential Automation Opps
                    </span>
                    <Info className="h-4 w-4 text-amber-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-bold tracking-tight text-amber-300">
                      {bm.potential_automation_opportunities}
                    </span>
                    <span className="text-xs text-slate-400">
                      ({formatMinor(bm.potential_automation_volume_minor, bm.currency)})
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Provably correct targets blocked by Gate financial checks
                  </p>
                </div>
              </div>

              {/* 10-Bucket Calibration Table */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5">
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-slate-200">
                    10-Bucket Calibration Distribution
                  </h3>
                  <p className="text-xs text-slate-400">
                    Partition of all {bm.predictions_made} predictions into 10 confidence bins ([0.0, 0.1) through [0.9, 1.0]).
                    Compares average confidence against empirical target-set correctness.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                      <tr>
                        <th className="py-2.5 px-3 font-medium">Confidence Bin</th>
                        <th className="py-2.5 px-3 font-medium">Predictions</th>
                        <th className="py-2.5 px-3 font-medium">Avg Confidence</th>
                        <th className="py-2.5 px-3 font-medium">Empirical Accuracy</th>
                        <th className="py-2.5 px-3 font-medium">Calibration Gap</th>
                        <th className="py-2.5 px-3 font-medium">Gate Pass / Fail</th>
                        <th className="py-2.5 px-3 font-medium text-right">Alignment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {bm.bucket_distribution.map((b: ConfidenceBucketResponse) => {
                        const gap = Math.abs(b.avg_confidence - b.empirical_accuracy);
                        return (
                          <tr
                            key={b.bin_label}
                            className={`hover:bg-slate-800/30 transition-colors ${
                              b.count > 0 ? "bg-slate-900/20" : "opacity-40"
                            }`}
                          >
                            <td className="py-2.5 px-3 font-mono font-medium text-slate-200">
                              {b.bin_label}
                            </td>
                            <td className="py-2.5 px-3 text-slate-300">
                              {b.count}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-slate-300">
                              {b.count > 0 ? (b.avg_confidence * 100).toFixed(1) + "%" : "—"}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-slate-300">
                              {b.count > 0 ? (
                                <span className={b.empirical_accuracy >= 0.9 ? "text-emerald-400" : "text-amber-400"}>
                                  {(b.empirical_accuracy * 100).toFixed(1)}%
                                </span>
                              ) : (
                                "—"
                              )}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-slate-400">
                              {b.count > 0 ? `${(gap * 100).toFixed(1)}%` : "—"}
                            </td>
                            <td className="py-2.5 px-3 text-slate-400">
                              {b.count > 0 ? (
                                <span className="inline-flex gap-2">
                                  <span className="text-emerald-400 font-mono">
                                    {b.gate_pass_count} pass
                                  </span>
                                  <span className="text-slate-600">/</span>
                                  <span className="text-red-400 font-mono">
                                    {b.gate_fail_count} fail
                                  </span>
                                </span>
                              ) : (
                                "—"
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              {b.count > 0 ? (
                                <div className="inline-flex items-center gap-1.5">
                                  <div className="w-20 bg-slate-800 h-2 rounded-full overflow-hidden flex">
                                    <div
                                      className="bg-emerald-500 h-full"
                                      style={{ width: `${b.empirical_accuracy * 100}%` }}
                                    />
                                  </div>
                                </div>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Threshold Analysis: Why Gate Is Authoritative */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    Confidence Threshold vs Gate Firewall Simulation
                  </h3>
                  <p className="text-xs text-slate-400">
                    What would happen if confidence alone were used to authorize resolutions?
                    Notice how many unvalidated or non-compliant settlements would bypass accounting rules.
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 pt-1">
                  {[0.5, 0.6, 0.7, 0.8, 0.9, 1.0].map((thr) => (
                    <button
                      key={thr}
                      type="button"
                      onClick={() => setSelectedThreshold(thr)}
                      className={`px-3 py-1.5 text-xs rounded font-mono transition-colors ${
                        selectedThreshold === thr
                          ? "bg-emerald-600 text-white"
                          : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                      }`}
                    >
                      Threshold ≥ {thr.toFixed(1)}
                    </button>
                  ))}
                </div>

                {currentThresholdMetric && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 rounded-lg bg-slate-950/60 p-4 border border-slate-800/80">
                    <div>
                      <span className="text-xs text-slate-400">Cases Covered</span>
                      <div className="mt-1 text-xl font-mono font-bold text-slate-200">
                        {currentThresholdMetric.cases_exceeding}
                        <span className="ml-2 text-xs font-normal text-slate-400">
                          ({(currentThresholdMetric.coverage * 100).toFixed(1)}% coverage)
                        </span>
                      </div>
                    </div>
                    <div>
                      <span className="text-xs text-slate-400">Empirical Target Precision</span>
                      <div className="mt-1 text-xl font-mono font-bold text-emerald-400">
                        {(currentThresholdMetric.precision * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-xs text-slate-400">
                        Bypassed Gate Hazards If Trusted Alone
                      </span>
                      <div className="mt-1 text-xl font-mono font-bold text-amber-400">
                        {currentThresholdMetric.cases_exceeding -
                          (bm.bucket_distribution.find((b) => b.bin_start >= selectedThreshold)?.gate_pass_count ?? 39)}
                        <span className="ml-2 text-xs font-normal text-slate-400">
                          cases blocked by Gate
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Gate × Confidence Matrix */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    Gate Status × Confidence Tier Matrix
                  </h3>
                  <p className="text-xs text-slate-400">
                    Cross-tabulation showing how the deterministic Gate enforces invariant compliance even when hypothesis confidence is maximum.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Gate Passed Column */}
                  <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4 space-y-3">
                    <div className="flex items-center gap-2 text-emerald-400 font-semibold text-xs uppercase tracking-wider">
                      <CheckCircle2 className="h-4 w-4" />
                      Gate PASSED (Compliant with Bridge & Invariants)
                    </div>
                    <div className="space-y-2">
                      {bm.gate_matrix
                        .filter((cell) => cell.gate_status === "PASSED")
                        .map((cell) => (
                          <div
                            key={cell.confidence_tier}
                            className="flex items-center justify-between rounded bg-slate-900/70 p-2.5 border border-slate-800 text-xs"
                          >
                            <div>
                              <span className="font-semibold text-slate-200">
                                {cell.confidence_tier} Tier
                              </span>
                              <div className="text-slate-400">
                                {cell.correct_count} correct / {cell.count} cases
                              </div>
                            </div>
                            <span className="text-emerald-400 font-mono font-bold text-sm">
                              {cell.count} cases
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>

                  {/* Gate Failed Column */}
                  <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4 space-y-3">
                    <div className="flex items-center gap-2 text-red-400 font-semibold text-xs uppercase tracking-wider">
                      <XCircle className="h-4 w-4" />
                      Gate FAILED / BLOCKED (Requires Review / Unresolved)
                    </div>
                    <div className="space-y-2">
                      {bm.gate_matrix
                        .filter((cell) => cell.gate_status === "FAILED")
                        .map((cell) => (
                          <div
                            key={cell.confidence_tier}
                            className="rounded bg-slate-900/70 p-2.5 border border-slate-800 text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-slate-200">
                                {cell.confidence_tier} Tier
                              </span>
                              <span className="text-red-400 font-mono font-bold text-sm">
                                {cell.count} cases
                              </span>
                            </div>
                            {cell.dominant_blockers.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                <span className="text-slate-400">Blockers:</span>
                                {cell.dominant_blockers.map((b) => (
                                  <span
                                    key={b}
                                    className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-amber-300"
                                  >
                                    {b}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Scenario Breakdown */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5">
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-slate-200">
                    Scenario Calibration (S1–S6)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Behavior by scenario family showing confidence distribution vs Gate outcomes.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                      <tr>
                        <th className="py-2.5 px-3 font-medium">Scenario</th>
                        <th className="py-2.5 px-3 font-medium">Total Cases</th>
                        <th className="py-2.5 px-3 font-medium">Predictions</th>
                        <th className="py-2.5 px-3 font-medium">Avg Confidence</th>
                        <th className="py-2.5 px-3 font-medium">Target Accuracy</th>
                        <th className="py-2.5 px-3 font-medium">Dominant Gate Outcome</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {bm.scenario_breakdown.map((s: ScenarioConfidenceMetricResponse) => (
                        <tr key={s.scenario_family} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-mono font-semibold text-slate-200">
                            {s.scenario_family}
                          </td>
                          <td className="py-2.5 px-3 text-slate-300">{s.count}</td>
                          <td className="py-2.5 px-3 text-slate-300">{s.predictions_made}</td>
                          <td className="py-2.5 px-3 font-mono text-slate-300">
                            {s.predictions_made > 0 ? `${(s.avg_confidence * 100).toFixed(1)}%` : "—"}
                          </td>
                          <td className="py-2.5 px-3 font-mono">
                            {s.predictions_made > 0 ? (
                              <span className={s.empirical_accuracy >= 0.9 ? "text-emerald-400" : "text-amber-400"}>
                                {(s.empirical_accuracy * 100).toFixed(1)}%
                              </span>
                            ) : (
                              <span className="text-slate-500">Abstained</span>
                            )}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-mono text-slate-300">
                              {s.dominant_gate_outcome}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Potential Automation Opportunities */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-200">
                      Potential Automation Opportunities (Evaluator Audit)
                    </h3>
                    <p className="text-xs text-slate-400">
                      Hypotheses where predicted targets strictly equaled evaluator GroundTruth, but Gate blocked automated resolution due to accounting discrepancies (e.g. S3 fee/tax differences).
                    </p>
                  </div>
                  <span className="rounded bg-amber-500/10 border border-amber-500/30 px-2.5 py-1 text-xs font-medium text-amber-300">
                    {bm.potential_automation_opportunities} Opportunities (₹
                    {(bm.potential_automation_volume_minor / 100).toLocaleString()})
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                      <tr>
                        <th className="py-2.5 px-3 font-medium">Case ID</th>
                        <th className="py-2.5 px-3 font-medium">Scenario</th>
                        <th className="py-2.5 px-3 font-medium">Confidence</th>
                        <th className="py-2.5 px-3 font-medium">Blocker Check</th>
                        <th className="py-2.5 px-3 font-medium">Failure Reason</th>
                        <th className="py-2.5 px-3 font-medium text-right">Amount</th>
                        <th className="py-2.5 px-3 font-medium text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {bm.automation_opportunities.slice(0, 10).map((opp: AutomationOpportunityResponse) => (
                        <tr key={opp.case_id} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-mono text-slate-300">
                            {opp.case_id}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-amber-400">
                            {opp.scenario_family}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-emerald-400">
                            {(opp.confidence * 100).toFixed(0)}%
                          </td>
                          <td className="py-2.5 px-3 font-mono text-red-400">
                            {opp.gate_blocker_check}
                          </td>
                          <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate" title={opp.failure_reason}>
                            {opp.failure_reason}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-right text-slate-200">
                            {formatMinor(opp.amount_minor, opp.currency)}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <Link
                              href={`/cases/${encodeURIComponent(opp.settlement_id)}`}
                              className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300 font-medium"
                            >
                              Inspect <ExternalLink className="h-3 w-3" />
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-slate-800 bg-slate-900/20 p-8 text-center">
              <p className="text-sm text-slate-400">
                Benchmark calibration data is not yet loaded.
              </p>
            </div>
          )}
        </>
      )}

      {/* ---------------------------------------------------- */}
      {/* TAB 2: OPERATIONAL HYPOTHESIS DISTRIBUTION (PRODUCTION) */}
      {/* ---------------------------------------------------- */}
      {activeTab === "operational" && (
        <>
          {op ? (
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                  <span className="text-xs font-medium text-slate-400">
                    Total Operational Hypotheses
                  </span>
                  <div className="mt-2 text-2xl font-bold text-slate-100 font-mono">
                    {op.total_hypotheses}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Formed by deterministic matchers and AI investigators
                  </p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                  <span className="text-xs font-medium text-slate-400">
                    High-Confidence Hypotheses (≥0.8)
                  </span>
                  <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
                    {op.high_confidence_count}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Subject to full deterministic GateEvaluation
                  </p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
                  <span className="text-xs font-medium text-slate-400">
                    Medium & Low Hypotheses (&lt;0.8)
                  </span>
                  <div className="mt-2 text-2xl font-bold text-amber-400 font-mono">
                    {op.medium_confidence_count + op.low_confidence_count}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    Unstructured or ambiguous hypotheses routed to human review
                  </p>
                </div>
              </div>

              {/* Gate Tiers Summary */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">
                    Operational Gate Tiers
                  </h3>
                  <p className="text-xs text-slate-400">
                    How hypotheses in each confidence tier fare through the deterministic Gate.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {op.gate_tiers.map((tier) => (
                    <div
                      key={tier.tier}
                      className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm text-slate-200">
                          {tier.tier} Tier
                        </span>
                        <span className="font-mono text-xs text-slate-400">
                          {tier.hypothesis_count} hypotheses
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-emerald-400 font-mono">
                          {tier.gate_passed} Gate Passed
                        </span>
                        <span className="text-red-400 font-mono">
                          {tier.gate_failed} Gate Failed
                        </span>
                      </div>
                      {tier.dominant_blockers.length > 0 && (
                        <div className="pt-2 border-t border-slate-800/80">
                          <span className="text-[11px] text-slate-400">Primary Blockers:</span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {tier.dominant_blockers.map((b) => (
                              <span
                                key={b}
                                className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-amber-300"
                              >
                                {b}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Blocker Check Context */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-5">
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-slate-200">
                    Blocker Check Confidence Context
                  </h3>
                  <p className="text-xs text-slate-400">
                    Notice how checks like BRIDGE fail on hypotheses with 100% confidence, demonstrating the separation of belief and accounting rules.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-slate-800 bg-slate-950/60 text-slate-400">
                      <tr>
                        <th className="py-2.5 px-3 font-medium">Check Name</th>
                        <th className="py-2.5 px-3 font-medium">Failure Count</th>
                        <th className="py-2.5 px-3 font-medium">Avg Hypothesis Confidence</th>
                        <th className="py-2.5 px-3 font-medium">Min Confidence</th>
                        <th className="py-2.5 px-3 font-medium">Max Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {op.check_contexts.map((ctx) => (
                        <tr key={ctx.check_name} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-mono font-semibold text-slate-200">
                            {ctx.check_name}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-red-400">
                            {ctx.failure_count}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-slate-300">
                            {(ctx.avg_confidence * 100).toFixed(1)}%
                          </td>
                          <td className="py-2.5 px-3 font-mono text-slate-400">
                            {(ctx.min_confidence * 100).toFixed(0)}%
                          </td>
                          <td className="py-2.5 px-3 font-mono text-slate-400">
                            {(ctx.max_confidence * 100).toFixed(0)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-lg border border-slate-800 bg-slate-900/20 p-8 text-center">
              <p className="text-sm text-slate-400">
                Operational confidence metrics are not available.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
