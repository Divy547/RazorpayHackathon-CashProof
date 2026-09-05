"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  ExternalLink,
  Layers,
  Scale,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { formatMinor, scenarioLabel } from "@/lib/format";
import type {
  BenchmarkConfidenceResponse,
  CheckConfidenceContext,
  ConfidenceBucket,
  FamilyConfidenceMetric,
  GateConfidenceCell,
  GateTierSummary,
  OperationalConfidenceResponse,
  ThresholdMetric,
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

  const currentThresholdMetric = bm?.thresholds?.find(
    (t: ThresholdMetric) => Math.abs(t.threshold - selectedThreshold) < 0.05,
  );

  return (
    <div className="space-y-8">
      {/* Top Architecture Invariant Banner */}
      <div className="rounded-2xl border border-[#CFC9BC] border-l-4 border-l-[#8C6843] bg-[#EEEAE0] p-5 sm:p-6 shadow-sm space-y-4">
        <div className="flex items-start gap-3.5">
          <div className="rounded-xl border border-[#8C6843]/30 bg-[#8C6843]/10 p-2.5 text-[#8C6843] shrink-0">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div className="space-y-1.5">
            <h2 className="text-sm font-bold tracking-tight text-[#171816]">
              Core Architecture Invariant: <span className="font-mono uppercase tracking-wider text-[#8C6843]">Confidence ≠ Authorization</span>
            </h2>
            <p className="text-xs leading-relaxed text-[#4F514A]">
              Confidence measures statistical belief and hypothesis strength; the deterministic{" "}
              <code className="rounded border border-[#3B5145]/30 bg-[#3B5145]/10 px-1.5 py-0.5 font-mono text-xs font-semibold text-[#3B5145]">
                GateEvaluation
              </code>{" "}
              is the sole financial authorization firewall. A hypothesis with 100% confidence cannot and will never bypass arithmetic bridge rules,
              tax reconciliation, or identity checks. The system strictly fails closed.
            </p>
          </div>
        </div>

        {/* Conceptual Relationship Pipeline */}
        <div className="rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] px-4 py-3">
          <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64] mb-2">
            Deterministic Separation Principle
          </div>
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <span className="rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2.5 py-1 font-semibold text-[#171816]">
              HIGH CONFIDENCE <span className="text-[10px] font-normal text-[#6B6D64]">(Statistical Belief)</span>
            </span>
            <span className="text-[#6B6D64]">&rarr;</span>
            <span className="rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2.5 py-1 font-semibold text-[#171816]">
              STRONG HYPOTHESIS
            </span>
            <span className="text-[#6B6D64]">&rarr;</span>
            <span className="rounded-md border border-[#3B5145]/30 bg-[#3B5145]/10 px-2.5 py-1 font-bold text-[#3B5145]">
              DETERMINISTIC GATE <span className="text-[10px] font-normal text-[#3B5145]">(Financial Firewall)</span>
            </span>
            <span className="text-[#6B6D64]">&rarr;</span>
            <span className="rounded-md border border-[#171816] bg-[#171816] px-2.5 py-1 font-bold text-[#F8F6F0]">
              AUTHORIZATION DECISION
            </span>
          </div>
        </div>
      </div>

      {/* Mode Tabs */}
      <div className="flex border-b border-[#CFC9BC] gap-2 sm:gap-4 overflow-x-auto">
        <button
          type="button"
          onClick={() => setActiveTab("benchmark")}
          className={`flex items-center gap-2 border-b-2 px-3 sm:px-4 py-3 font-mono text-xs font-semibold whitespace-nowrap shrink-0 transition-colors ${
            activeTab === "benchmark"
              ? "border-[#171816] text-[#171816]"
              : "border-transparent text-[#6B6D64] hover:text-[#171816]"
          }`}
        >
          <Scale className="h-4 w-4 text-[#4F514A]" />
          <span>Benchmark Calibration (Evaluator Ground Truth)</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("operational")}
          className={`flex items-center gap-2 border-b-2 px-3 sm:px-4 py-3 font-mono text-xs font-semibold whitespace-nowrap shrink-0 transition-colors ${
            activeTab === "operational"
              ? "border-[#171816] text-[#171816]"
              : "border-transparent text-[#6B6D64] hover:text-[#171816]"
          }`}
        >
          <Layers className="h-4 w-4 text-[#4F514A]" />
          <span>Operational Hypothesis Distribution (Production)</span>
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
                <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                      Expected Calibration Error
                    </span>
                    <TrendingUp className="h-4 w-4 text-[#4F514A]" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="font-mono text-2xl sm:text-3xl font-bold tracking-tight text-[#171816]">
                      {(bm.overall_ece * 100).toFixed(1)}%
                    </span>
                    <span className="font-mono text-xs text-[#6B6D64]">
                      (ECE {bm.overall_ece.toFixed(4)})
                    </span>
                  </div>
                  <p className="mt-1.5 font-mono text-xs text-[#4F514A]">
                    Weighted distance between confidence and empirical accuracy
                  </p>
                </div>

                <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                      Brier Calibration Score
                    </span>
                    <BarChart3 className="h-4 w-4 text-[#4F514A]" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="font-mono text-2xl sm:text-3xl font-bold tracking-tight text-[#171816]">
                      {bm.overall_brier_score.toFixed(4)}
                    </span>
                    <span className="rounded bg-[#3B5145]/10 border border-[#3B5145]/25 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[#3B5145]">
                      Low MSE
                    </span>
                  </div>
                  <p className="mt-1.5 font-mono text-xs text-[#4F514A]">
                    Mean squared error of confidence against true target sets
                  </p>
                </div>

                <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                      High-Confidence Precision
                    </span>
                    <ShieldCheck className="h-4 w-4 text-[#3B5145]" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="font-mono text-2xl sm:text-3xl font-bold tracking-tight text-[#3B5145]">
                      {(bm.high_confidence_precision * 100).toFixed(1)}%
                    </span>
                    <span className="font-mono text-xs text-[#6B6D64]">
                      at &ge; 0.80 conf
                    </span>
                  </div>
                  <p className="mt-1.5 font-mono text-xs text-[#4F514A]">
                    Target-set correctness for top-tier hypotheses
                  </p>
                </div>

                <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                      Potential Automation Opps
                    </span>
                    <span className="rounded-md border border-[#A47C52]/30 bg-[#A47C52]/10 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-[#8C6843]">
                      AUDIT
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="font-mono text-2xl sm:text-3xl font-bold tracking-tight text-[#8C6843]">
                      {bm.potential_automation_opportunities}
                    </span>
                    <span className="font-mono text-xs text-[#6B6D64]">
                      ({formatMinor(bm.potential_automation_volume_minor, bm.currency)})
                    </span>
                  </div>
                  <p className="mt-1.5 font-mono text-xs text-[#4F514A]">
                    Provably correct targets blocked by Gate financial checks
                  </p>
                </div>
              </div>

              {/* 10-Bucket Calibration Table */}
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
                <div>
                  <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                    10-Bucket Calibration Distribution
                  </h3>
                  <p className="text-xs text-[#4F514A]">
                    Partition of all {bm.predictions_made} predictions into 10 confidence bins ([0.0, 0.1) through [0.9, 1.0]).
                    Compares average confidence against empirical target-set correctness.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[760px] border-collapse text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                        <th className="py-3 px-3.5">Confidence Bin</th>
                        <th className="py-3 px-3.5">Predictions</th>
                        <th className="py-3 px-3.5">Avg Confidence</th>
                        <th className="py-3 px-3.5">Empirical Accuracy</th>
                        <th className="py-3 px-3.5">Calibration Gap</th>
                        <th className="py-3 px-3.5">Gate Pass / Fail</th>
                        <th className="py-3 px-3.5 text-right">Alignment</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#CFC9BC]/60 font-mono">
                      {bm.buckets.map((b: ConfidenceBucket) => {
                        const gap = Math.abs(b.average_confidence - b.empirical_accuracy);
                        const hasObs = b.observation_count > 0;
                        return (
                          <tr
                            key={b.bin_label}
                            className={`transition-colors ${
                              hasObs ? "hover:bg-[#EEEAE0]/50" : "opacity-45 text-[#8C8D82]"
                            }`}
                          >
                            <td className="py-2.5 px-3.5 font-bold text-[#171816]">
                              {b.bin_label}
                            </td>
                            <td className="py-2.5 px-3.5 text-[#171816]">
                              {b.observation_count}
                            </td>
                            <td className="py-2.5 px-3.5 text-[#171816]">
                              {hasObs ? `${(b.average_confidence * 100).toFixed(1)}%` : "—"}
                            </td>
                            <td className="py-2.5 px-3.5 font-semibold">
                              {hasObs ? (
                                <span className={b.empirical_accuracy >= 0.9 ? "text-[#3B5145]" : "text-[#8C6843]"}>
                                  {(b.empirical_accuracy * 100).toFixed(1)}%
                                </span>
                              ) : (
                                "—"
                              )}
                            </td>
                            <td className="py-2.5 px-3.5 text-[#4F514A]">
                              {hasObs ? `${(gap * 100).toFixed(1)}%` : "—"}
                            </td>
                            <td className="py-2.5 px-3.5">
                              {hasObs ? (
                                <span className="inline-flex items-center gap-1.5">
                                  <span className="text-[#3B5145] font-semibold">
                                    {b.gate_pass_count} pass
                                  </span>
                                  <span className="text-[#CFC9BC]">/</span>
                                  <span className="text-[#9A514C] font-semibold">
                                    {b.gate_fail_count} fail
                                  </span>
                                </span>
                              ) : (
                                "—"
                              )}
                            </td>
                            <td className="py-2.5 px-3.5 text-right">
                              {hasObs ? (
                                <div className="inline-flex items-center justify-end gap-1.5">
                                  <div className="w-24 bg-[#EEEAE0] border border-[#CFC9BC] h-2 rounded-full overflow-hidden flex">
                                    <div
                                      className="bg-[#3B5145] h-full"
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
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
                <div>
                  <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                    Confidence Threshold vs Gate Firewall Simulation
                  </h3>
                  <p className="text-xs text-[#4F514A]">
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
                      className={`px-3.5 py-1.5 font-mono text-xs font-semibold rounded-lg transition-colors shadow-sm ${
                        selectedThreshold === thr
                          ? "bg-[#171816] text-[#F8F6F0] border border-[#171816]"
                          : "bg-[#EEEAE0] text-[#4F514A] border border-[#CFC9BC] hover:bg-[#E5DFD1] hover:text-[#171816]"
                      }`}
                    >
                      Threshold &ge; {thr.toFixed(1)}
                    </button>
                  ))}
                </div>

                {currentThresholdMetric && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-5">
                    <div>
                      <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                        Cases Covered
                      </div>
                      <div className="mt-1.5 font-mono text-2xl font-bold text-[#171816]">
                        {currentThresholdMetric.predictions_meeting_threshold}
                        <span className="ml-2 font-mono text-xs font-normal text-[#6B6D64]">
                          ({(currentThresholdMetric.coverage * 100).toFixed(1)}% coverage)
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                        Empirical Target Precision
                      </div>
                      <div className="mt-1.5 font-mono text-2xl font-bold text-[#3B5145]">
                        {(currentThresholdMetric.precision * 100).toFixed(1)}%
                      </div>
                      <div className="mt-0.5 font-mono text-xs text-[#4F514A]">
                        correct target sets identified
                      </div>
                    </div>
                    <div>
                      <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#9A514C]">
                        Bypassed Gate Hazards If Trusted Alone
                      </div>
                      <div className="mt-1.5 font-mono text-2xl font-bold text-[#9A514C]">
                        {currentThresholdMetric.false_auto_count_if_trusted_alone}
                      </div>
                      <div className="mt-0.5 font-mono text-xs text-[#4F514A]">
                        false auto-resolutions if Gate bypassed
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Gate × Confidence Matrix */}
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
                <div>
                  <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                    Gate Status &times; Confidence Tier Matrix
                  </h3>
                  <p className="text-xs text-[#4F514A]">
                    Cross-tabulation showing how the deterministic Gate enforces invariant compliance even when hypothesis confidence is maximum.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {bm.gate_matrix.map((cell: GateConfidenceCell) => (
                    <div
                      key={cell.tier}
                      className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4.5 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-bold text-sm text-[#171816]">
                            {cell.tier} Tier
                          </span>
                          <span className="ml-2 font-mono text-xs text-[#6B6D64]">
                            ({cell.confidence_range})
                          </span>
                        </div>
                        <span className="font-mono text-xs font-semibold text-[#171816]">
                          {cell.total_count} cases
                        </span>
                      </div>
                      <div className="flex items-center justify-between font-mono text-xs">
                        <span className="text-[#3B5145] font-bold">
                          {cell.gate_pass_count} Gate Passed
                        </span>
                        <span className="text-[#9A514C] font-bold">
                          {cell.gate_fail_count} Gate Blocked
                        </span>
                      </div>
                      {cell.dominant_failing_checks.length > 0 && (
                        <div className="pt-2.5 border-t border-[#CFC9BC]/80">
                          <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                            Dominant Blockers:
                          </span>
                          <div className="mt-1.5 flex flex-wrap gap-1.5">
                            {cell.dominant_failing_checks.map(([chk, count]) => (
                              <span
                                key={chk}
                                className="rounded-md border border-[#A47C52]/30 bg-[#A47C52]/10 px-2 py-0.5 font-mono text-[10px] font-bold text-[#8C6843]"
                              >
                                {chk} ({count})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Scenario Breakdown */}
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
                <div>
                  <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                    Scenario Calibration (S1–S6)
                  </h3>
                  <p className="text-xs text-[#4F514A]">
                    Behavior by scenario family showing confidence distribution vs Gate outcomes. Notice that high target precision does not imply gate authorization.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[760px] border-collapse text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                        <th className="py-3 px-3.5">Scenario</th>
                        <th className="py-3 px-3.5">Total Cases</th>
                        <th className="py-3 px-3.5">Avg Confidence</th>
                        <th className="py-3 px-3.5">Target Precision</th>
                        <th className="py-3 px-3.5">Gate Pass Rate</th>
                        <th className="py-3 px-3.5">Abstention Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#CFC9BC]/60 font-mono">
                      {bm.scenario_metrics.map((s: FamilyConfidenceMetric) => (
                        <tr key={s.scenario_family} className="hover:bg-[#EEEAE0]/50 transition-colors">
                          <td className="py-2.5 px-3.5">
                            <span className="font-bold text-[#171816]">{s.scenario_family}</span>
                            <span className="ml-2 text-[11px] font-normal text-[#6B6D64]">
                              {scenarioLabel(s.scenario_family)}
                            </span>
                          </td>
                          <td className="py-2.5 px-3.5 text-[#171816]">{s.observation_count}</td>
                          <td className="py-2.5 px-3.5 text-[#171816]">
                            {s.observation_count > 0 ? `${(s.average_confidence * 100).toFixed(1)}%` : "—"}
                          </td>
                          <td className="py-2.5 px-3.5 font-semibold">
                            {s.observation_count > 0 && s.coverage > 0 ? (
                              <span className={s.precision >= 0.9 ? "text-[#3B5145]" : "text-[#8C6843]"}>
                                {(s.precision * 100).toFixed(1)}%
                              </span>
                            ) : (
                              <span className="text-[#8C8D82]">—</span>
                            )}
                          </td>
                          <td className="py-2.5 px-3.5 font-semibold">
                            {s.observation_count > 0 ? (
                              <span className={s.gate_pass_rate > 0 ? "text-[#3B5145]" : "text-[#9A514C]"}>
                                {(s.gate_pass_rate * 100).toFixed(1)}%
                              </span>
                            ) : (
                              "—"
                            )}
                          </td>
                          <td className="py-2.5 px-3.5 text-[#4F514A]">
                            {s.observation_count > 0 ? `${(s.abstention_rate * 100).toFixed(1)}%` : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Potential Automation Opportunities */}
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                      Potential Automation Opportunities (Evaluator Audit)
                    </h3>
                    <p className="text-xs text-[#4F514A]">
                      Hypotheses where predicted targets strictly equaled evaluator GroundTruth, but Gate blocked automated resolution due to accounting discrepancies (e.g. S3 fee/tax differences).
                    </p>
                  </div>
                  <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#A47C52]/30 bg-[#A47C52]/10 px-3 py-1 font-mono text-xs font-semibold text-[#8C6843]">
                    {bm.automation_opportunity.opportunity_count} Opportunities (
                    {formatMinor(bm.automation_opportunity.affected_settlement_net_minor, bm.automation_opportunity.currency)})
                  </span>
                </div>

                {bm.automation_opportunity.opportunity_count > 0 ? (
                  <div className="space-y-4 pt-1">
                    {bm.automation_opportunity.failing_gate_checks.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="font-mono text-xs font-semibold text-[#3F413B]">
                          Failing Gate Checks
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {bm.automation_opportunity.failing_gate_checks.map(([chk, count]) => (
                            <span
                              key={chk}
                              className="rounded-md border border-[#A85F59]/30 bg-[#A85F59]/10 px-2.5 py-1 font-mono text-xs font-semibold text-[#9A514C]"
                            >
                              {chk}: <span className="font-bold">{count}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {bm.automation_opportunity.current_dispositions.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="font-mono text-xs font-semibold text-[#3F413B]">
                          Current Dispositions
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {bm.automation_opportunity.current_dispositions.map(([disp, count]) => (
                            <span
                              key={disp}
                              className="rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2.5 py-1 font-mono text-xs font-semibold text-[#171816]"
                            >
                              {disp}: <span className="font-bold">{count}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {bm.automation_opportunity.sample_case_ids.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="font-mono text-xs font-semibold text-[#3F413B]">
                          Sample Cases Requiring Review
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {bm.automation_opportunity.sample_case_ids.map((cid) => (
                            <Link
                              key={cid}
                              href={`/cases/${encodeURIComponent(cid)}`}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-2.5 py-1 font-mono text-xs font-semibold text-[#171816] transition-colors hover:border-[#171816] hover:bg-[#E5DFD1]"
                            >
                              <span>{cid}</span>
                              <ExternalLink className="h-3 w-3 opacity-60" />
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="font-mono text-xs text-[#6B6D64]">
                    No automation opportunities found at threshold &ge; {bm.automation_opportunity.threshold}.
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs text-[#6B6D64]">
              Benchmark calibration data is not yet loaded.
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
            <div className="space-y-8">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    Total Operational Hypotheses
                  </div>
                  <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold text-[#171816]">
                    {op.hypotheses_evaluated}
                  </div>
                  <p className="mt-1.5 font-mono text-xs text-[#4F514A]">
                    Across {op.total_cases} reconciliation cases
                  </p>
                </div>
                <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    High-Confidence Hypotheses (&ge;0.8)
                  </div>
                  <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold text-[#3B5145]">
                    {op.high_confidence_count}
                  </div>
                  <p className="mt-1.5 font-mono text-xs text-[#8C6843]">
                    {op.high_confidence_gate_blocked_count} blocked by Gate financial checks
                  </p>
                </div>
                <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    Medium &amp; Low Hypotheses (&lt;0.8)
                  </div>
                  <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold text-[#8C6843]">
                    {op.medium_confidence_count + op.low_confidence_count}
                  </div>
                  <p className="mt-1.5 font-mono text-xs text-[#4F514A]">
                    Unstructured or ambiguous hypotheses routed to human review
                  </p>
                </div>
              </div>

              {/* Gate Tiers Summary */}
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
                <div>
                  <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                    Operational Gate Tiers
                  </h3>
                  <p className="text-xs text-[#4F514A]">
                    How hypotheses in each confidence tier fare through the deterministic Gate.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {op.gate_tiers.map((tier: GateTierSummary) => (
                    <div
                      key={tier.tier}
                      className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4.5 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-bold text-sm text-[#171816]">
                            {tier.tier} Tier
                          </span>
                          <span className="ml-2 font-mono text-xs text-[#6B6D64]">
                            ({tier.confidence_range})
                          </span>
                        </div>
                        <span className="font-mono text-xs font-semibold text-[#171816]">
                          {tier.total_count} hypotheses
                        </span>
                      </div>
                      <div className="flex items-center justify-between font-mono text-xs">
                        <span className="text-[#3B5145] font-bold">
                          {tier.gate_pass_count} Gate Passed ({tier.pass_rate_pct.toFixed(1)}%)
                        </span>
                        <span className="text-[#9A514C] font-bold">
                          {tier.gate_fail_count} Gate Blocked
                        </span>
                      </div>
                      {tier.failing_check_counts.length > 0 && (
                        <div className="pt-2.5 border-t border-[#CFC9BC]/80">
                          <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                            Primary Blockers:
                          </span>
                          <div className="mt-1.5 flex flex-wrap gap-1.5">
                            {tier.failing_check_counts.map(([b, count]) => (
                              <span
                                key={b}
                                className="rounded-md border border-[#A47C52]/30 bg-[#A47C52]/10 px-2 py-0.5 font-mono text-[10px] font-bold text-[#8C6843]"
                              >
                                {b} ({count})
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
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
                <div>
                  <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                    Blocker Check Confidence Context
                  </h3>
                  <p className="text-xs text-[#4F514A]">
                    Notice how checks like BRIDGE fail on hypotheses with 100% confidence, demonstrating the separation of belief and accounting rules.
                  </p>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[760px] border-collapse text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                        <th className="py-3 px-3.5">Check Name</th>
                        <th className="py-3 px-3.5">Failure Count</th>
                        <th className="py-3 px-3.5">Avg Hypothesis Confidence</th>
                        <th className="py-3 px-3.5">Min Confidence</th>
                        <th className="py-3 px-3.5">Max Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#CFC9BC]/60 font-mono">
                      {op.check_contexts.map((ctx: CheckConfidenceContext) => (
                        <tr key={ctx.check_name} className="hover:bg-[#EEEAE0]/50 transition-colors">
                          <td className="py-2.5 px-3.5 font-bold text-[#171816]">
                            {ctx.check_name}
                          </td>
                          <td className="py-2.5 px-3.5 font-bold text-[#9A514C]">
                            {ctx.case_count}
                          </td>
                          <td className="py-2.5 px-3.5 text-[#171816]">
                            {(ctx.average_confidence * 100).toFixed(1)}%
                          </td>
                          <td className="py-2.5 px-3.5 text-[#4F514A]">
                            {(ctx.min_confidence * 100).toFixed(0)}%
                          </td>
                          <td className="py-2.5 px-3.5 text-[#4F514A]">
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
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs text-[#6B6D64]">
              Operational confidence metrics are not available.
            </div>
          )}
        </>
      )}
    </div>
  );
}
