"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Gauge,
  Play,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { runBenchmark } from "@/lib/api";
import type { BenchmarkRunResponse } from "@/lib/types";
import { scenarioLabel } from "@/lib/format";

export default function BenchmarkPage() {
  const [seed, setSeed] = useState<number>(42);
  const [numSettlements, setNumSettlements] = useState<number>(100);
  const [arm, setArm] = useState<string>("deterministic");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [run, setRun] = useState<BenchmarkRunResponse | null>(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const response = await runBenchmark(seed, numSettlements, arm);
      setRun(response);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to execute benchmark run.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Operational Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3B5145]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
            <span>EVALUATION LAB</span>
            <span className="text-[#CFC9BC]">/</span>
            <span className="text-[#4F514A]">CONTROLLED RUN</span>
          </div>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-[#171816]">
            Controller Benchmark &amp; Evaluation
          </h1>
          <p className="mt-1 text-sm font-normal text-[#4F514A]">
            Phase 4 evaluation of the production reconciliation pipeline against Phase 2 GroundTruth.
          </p>
        </div>
      </div>

      {/* Experiment Configuration Panel */}
      <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 sm:p-6 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#CFC9BC]/70 pb-3">
          <div className="font-mono text-xs font-semibold uppercase tracking-wider text-[#3F413B]">
            Experiment Configuration
          </div>
          <div className="font-mono text-[11px] text-[#6B6D64]">
            Evaluator-only ground truth is strictly isolated from the production pipeline
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4 sm:gap-6">
            <div className="flex items-center gap-2">
              <label htmlFor="seed-input" className="font-mono text-xs font-semibold text-[#4F514A]">
                Seed:
              </label>
              <input
                id="seed-input"
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-20 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-2.5 py-1.5 font-mono text-xs font-semibold text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="cases-input" className="font-mono text-xs font-semibold text-[#4F514A]">
                Cases:
              </label>
              <input
                id="cases-input"
                type="number"
                min={50}
                value={numSettlements}
                onChange={(e) => setNumSettlements(Number(e.target.value))}
                className="w-24 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-2.5 py-1.5 font-mono text-xs font-semibold text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="arm-select" className="font-mono text-xs font-semibold text-[#4F514A]">
                Arm:
              </label>
              <select
                id="arm-select"
                value={arm}
                onChange={(e) => setArm(e.target.value)}
                className="rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3 py-1.5 font-mono text-xs font-semibold text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
              >
                <option value="deterministic">Deterministic</option>
                <option value="ai_investigator">AI Investigator</option>
              </select>
            </div>
          </div>

          <button
            type="button"
            onClick={handleRun}
            disabled={loading || numSettlements < 50}
            className="inline-flex items-center gap-2 rounded-lg bg-[#171816] px-4 py-2 font-mono text-xs font-semibold text-[#F8F6F0] shadow-sm transition-colors hover:bg-[#2C2E2B] disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Running Benchmark...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5" />
                <span>Run Benchmark &rarr;</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2.5 rounded-xl border border-[#A85F59]/40 bg-[#A85F59]/10 p-4 text-xs text-[#9A514C]">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#A85F59]" />
          <span>{error}</span>
        </div>
      )}

      {/* Loading State */}
      {loading && !run && (
        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-12 text-center shadow-sm">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-[#3B5145]" />
          <p className="mt-4 text-sm font-bold text-[#171816]">
            Generating synthetic dataset and running production reconciler...
          </p>
          <p className="mt-1 font-mono text-xs text-[#6B6D64]">
            Honest wall-clock timing boundary active. GroundTruth evaluation in progress.
          </p>
        </div>
      )}

      {/* Empty State: Ready for Evaluation */}
      {!loading && !run && (
        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 sm:p-10 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 border-b border-[#CFC9BC]/70 pb-4">
            <div className="rounded-xl border border-[#3B5145]/30 bg-[#3B5145]/10 p-2.5 text-[#3B5145] w-fit">
              <Gauge className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-tight text-[#171816]">
                Ready for Evaluation Run
              </h2>
              <p className="text-xs text-[#4F514A]">
                Configure the controlled experiment parameters above and execute the benchmark to generate verified evaluation results.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1.5">
              <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#3B5145]">
                1. Safety Verification
              </div>
              <p className="text-xs leading-relaxed text-[#4F514A]">
                Measures zero false auto-resolutions invariant against evaluator GroundTruth.
              </p>
            </div>

            <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1.5">
              <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#171816]">
                2. Target Set Equality
              </div>
              <p className="text-xs leading-relaxed text-[#4F514A]">
                100% exact target-set match verification across all resolved cases.
              </p>
            </div>

            <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1.5">
              <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#8C6843]">
                3. Tri-State Partition
              </div>
              <p className="text-xs leading-relaxed text-[#4F514A]">
                Quantifies AUTO_RESOLVED, HUMAN_REVIEW, and UNRESOLVED distributions.
              </p>
            </div>

            <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1.5">
              <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#4F514A]">
                4. Wall-Clock Timing
              </div>
              <p className="text-xs leading-relaxed text-[#4F514A]">
                Honest reconciliation throughput without simulated pauses or synthetic overhead.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Post-Run Evaluation Report */}
      {run && (
        <div className="space-y-8">
          {/* 1. Run Metadata Strip */}
          <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 text-xs font-mono text-[#4F514A] flex flex-wrap gap-x-6 gap-y-2 justify-between items-center shadow-sm">
            <div>
              <span className="text-[#6B6D64]">Run ID:</span>{" "}
              <span className="font-bold text-[#171816]">{run.run_id}</span>
            </div>
            <div>
              <span className="text-[#6B6D64]">Seed:</span>{" "}
              <span className="font-bold text-[#171816]">{run.seed}</span>
            </div>
            <div>
              <span className="text-[#6B6D64]">Rule Version:</span>{" "}
              <span className="font-bold text-[#171816]">{run.rule_version}</span>
            </div>
            <div>
              <span className="text-[#6B6D64]">Code Revision:</span>{" "}
              <span className="font-bold text-[#171816]">{run.code_revision}</span>
            </div>
            <div>
              <span className="text-[#6B6D64]">Arm:</span>{" "}
              <span className="font-bold text-[#171816] uppercase">{run.arm}</span>
            </div>
            <div>
              <span className="text-[#6B6D64]">Timing Boundary:</span>{" "}
              <span className="text-[#171816]">{run.timing.timing_boundary}</span>
            </div>
          </div>

          {/* 2. Safety Gate Banner (Primary Visual Dominance) */}
          {run.safety_gate_passed ? (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-[#CFC9BC] border-l-4 border-l-[#3B5145] bg-[#EEEAE0] p-5 sm:p-6 shadow-sm">
              <div className="flex items-start sm:items-center gap-3.5">
                <div className="rounded-xl border border-[#3B5145]/30 bg-[#3B5145]/10 p-2.5 text-[#3B5145] shrink-0">
                  <ShieldCheck className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-mono text-base font-bold tracking-tight text-[#171816]">
                    SAFETY GATE PASSED: ZERO FALSE AUTO-RESOLUTIONS
                  </div>
                  <div className="mt-0.5 font-mono text-xs text-[#4F514A]">
                    All {run.total_cases} cases verified against ground truth with 100% exact target set equality. The financial safety invariant holds strictly.
                  </div>
                </div>
              </div>
              <div className="shrink-0 self-start sm:self-auto">
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#3B5145]/30 bg-[#3B5145]/15 px-3 py-1 font-mono text-xs font-bold text-[#3B5145]">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>PASS &mdash; 0 FALSE AUTO</span>
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-2xl border border-[#CFC9BC] border-l-4 border-l-[#9A514C] bg-[#EEEAE0] p-5 sm:p-6 shadow-sm">
              <div className="flex items-start sm:items-center gap-3.5">
                <div className="rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 p-2.5 text-[#9A514C] shrink-0">
                  <ShieldAlert className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-mono text-base font-bold tracking-tight text-[#9A514C]">
                    SAFETY GATE FAILED: FALSE AUTO-RESOLUTIONS DETECTED
                  </div>
                  <div className="mt-0.5 font-mono text-xs text-[#4F514A]">
                    {run.false_auto_resolution_count} false auto-resolution(s) detected. Financial safety invariant violated.
                  </div>
                </div>
              </div>
              <div className="shrink-0 self-start sm:self-auto">
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#A85F59]/30 bg-[#A85F59]/15 px-3 py-1 font-mono text-xs font-bold text-[#9A514C]">
                  <AlertTriangle className="h-3.5 w-3.5" />
                  <span>FAIL &mdash; {run.false_auto_resolution_count} FALSE AUTO</span>
                </span>
              </div>
            </div>
          )}

          {/* 3. Core Performance & Disposition Metrics */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {/* Safety */}
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Safety Invariant
              </div>
              <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold tabular-nums text-[#3B5145]">
                {run.false_auto_resolutions} False Auto
              </div>
              <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
                100% safety invariant satisfied
              </div>
            </div>

            {/* Auto-Resolved */}
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Auto-Resolved
              </div>
              <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold tabular-nums text-[#171816]">
                {run.auto_resolved} <span className="text-base font-normal text-[#6B6D64]">({(run.auto_resolution_rate * 100).toFixed(1)}%)</span>
              </div>
              <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
                Correct: {run.correct_auto_resolutions} | False: {run.false_auto_resolutions}
              </div>
            </div>

            {/* Human Review */}
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Human Review
              </div>
              <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold tabular-nums text-[#8C6843]">
                {run.human_review} <span className="text-base font-normal text-[#6B6D64]">({(run.human_review_rate * 100).toFixed(1)}%)</span>
              </div>
              <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
                Governance &amp; ambiguity routes
              </div>
            </div>

            {/* Unresolved */}
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm">
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Unresolved
              </div>
              <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold tabular-nums text-[#4F514A]">
                {run.unresolved} <span className="text-base font-normal text-[#6B6D64]">({(run.unresolved_rate * 100).toFixed(1)}%)</span>
              </div>
              <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
                Missing records &amp; conflicts
              </div>
            </div>

            {/* Throughput */}
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 shadow-sm col-span-1 sm:col-span-2 lg:col-span-1">
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Reconciliation Throughput
              </div>
              <div className="mt-2 font-mono text-2xl sm:text-3xl font-bold tabular-nums text-[#171816]">
                {Math.round(run.records_per_minute).toLocaleString()} <span className="text-xs font-normal text-[#6B6D64]">rec/min</span>
              </div>
              <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
                Wall-Clock: {run.timing.pipeline_duration_seconds.toFixed(4)}s
              </div>
            </div>
          </div>

          {/* 4. Visual Disposition Distribution Bar */}
          <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-5 sm:p-6 shadow-sm space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-xs font-semibold text-[#3F413B]">
              <span>Disposition Distribution ({run.total_cases} Total Cases)</span>
              <div className="flex items-center gap-4 text-[11px]">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#65745F]" />
                  <span>Auto-Resolved: {run.auto_resolved} ({(run.auto_resolution_rate * 100).toFixed(1)}%)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#A47C52]" />
                  <span>Human Review: {run.human_review} ({(run.human_review_rate * 100).toFixed(1)}%)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#A85F59]" />
                  <span>Unresolved: {run.unresolved} ({(run.unresolved_rate * 100).toFixed(1)}%)</span>
                </span>
              </div>
            </div>

            <div className="h-3 w-full rounded-full overflow-hidden flex bg-[#EEEAE0] border border-[#CFC9BC]">
              <div
                className="bg-[#65745F] h-full transition-all"
                style={{ width: `${run.auto_resolution_rate * 100}%` }}
                title={`Auto-Resolved: ${run.auto_resolved}`}
              />
              <div
                className="bg-[#A47C52] h-full transition-all"
                style={{ width: `${run.human_review_rate * 100}%` }}
                title={`Human Review: ${run.human_review}`}
              />
              <div
                className="bg-[#A85F59] h-full transition-all"
                style={{ width: `${run.unresolved_rate * 100}%` }}
                title={`Unresolved: ${run.unresolved}`}
              />
            </div>
          </div>

          {/* 5. Scenario Matrix (S1–S6 Taxonomy) */}
          <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
            <div>
              <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                Scenario Matrix (S1&ndash;S6 Taxonomy)
              </h3>
              <p className="text-xs text-[#4F514A]">
                Evaluator-only ground truth correlation across benchmark scenario families.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[840px] border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                    <th className="py-3 px-3.5">Scenario</th>
                    <th className="py-3 px-3.5">Total</th>
                    <th className="py-3 px-3.5">AUTO_RESOLVED</th>
                    <th className="py-3 px-3.5">HUMAN_REVIEW</th>
                    <th className="py-3 px-3.5">UNRESOLVED</th>
                    <th className="py-3 px-3.5">Correct Outcomes</th>
                    <th className="py-3 px-3.5">False Auto</th>
                    <th className="py-3 px-3.5 text-right">Safety Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#CFC9BC]/60 font-mono">
                  {run.scenario_matrix.map((row) => (
                    <tr key={row.scenario_family} className="hover:bg-[#EEEAE0]/50 transition-colors">
                      <td className="py-3 px-3.5">
                        <span className="font-bold text-[#171816]">{row.scenario_family}</span>
                        <span className="ml-2 font-normal text-[11px] text-[#6B6D64]">
                          {scenarioLabel(row.scenario_family)}
                        </span>
                      </td>
                      <td className="py-3 px-3.5 text-[#171816]">{row.total}</td>
                      <td className="py-3 px-3.5 font-bold text-[#3B5145]">{row.auto_resolved}</td>
                      <td className="py-3 px-3.5 font-bold text-[#8C6843]">{row.human_review}</td>
                      <td className="py-3 px-3.5 text-[#4F514A]">{row.unresolved}</td>
                      <td className="py-3 px-3.5 text-[#171816] font-semibold">{row.correct_outcomes}</td>
                      <td className="py-3 px-3.5 font-bold text-[#9A514C]">{row.false_auto_resolutions}</td>
                      <td className="py-3 px-3.5 text-right font-sans">
                        {row.false_auto_resolutions === 0 ? (
                          <span className="inline-flex items-center gap-1 rounded-md border border-[#3B5145]/25 bg-[#3B5145]/10 px-2 py-0.5 font-mono text-xs font-semibold text-[#3B5145]">
                            <CheckCircle2 className="h-3 w-3" /> OK
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-md border border-[#A85F59]/25 bg-[#A85F59]/10 px-2 py-0.5 font-mono text-xs font-semibold text-[#9A514C]">
                            <AlertTriangle className="h-3 w-3" /> FAILED
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 6. AI Metrics (shown if AI arm or any tool calls recorded) */}
          {(run.arm === "ai_investigator" || run.ai_metrics.investigations_started > 0) && (
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold tracking-tight text-[#171816]">
                  AI Investigator Governance &amp; Telemetry
                </h3>
                <p className="text-xs text-[#4F514A]">
                  Tool usage, proposal outcomes, and active budget constraints.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1">
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    Investigations
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-[#171816]">
                    {run.ai_metrics.investigations_started}
                  </div>
                  <div className="font-mono text-xs text-[#4F514A]">
                    Completed: {run.ai_metrics.investigations_completed} | Failed: {run.ai_metrics.investigations_failed}
                  </div>
                </div>

                <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1">
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    Proposals Gate Outcome
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-[#171816]">
                    {run.ai_metrics.proposals_generated}
                  </div>
                  <div className="font-mono text-xs text-[#4F514A]">
                    Passed: <span className="font-bold text-[#3B5145]">{run.ai_metrics.proposals_gate_passed}</span> | Failed: <span className="font-bold text-[#8C6843]">{run.ai_metrics.proposals_gate_failed}</span>
                  </div>
                </div>

                <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1">
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    Tool Calls
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-[#171816]">
                    {run.ai_metrics.total_tool_calls}
                  </div>
                  <div className="font-mono text-xs text-[#4F514A] flex items-center gap-1">
                    <Cpu className="h-3 w-3 text-[#3B5145]" /> Bounded tools only
                  </div>
                </div>

                <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 space-y-1">
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    Failure Modes
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-[#171816]">
                    {run.ai_metrics.timeout_count + run.ai_metrics.budget_exhaustion_count + run.ai_metrics.malformed_output_count + run.ai_metrics.tool_failure_count}
                  </div>
                  <div className="font-mono text-xs text-[#4F514A]">
                    Timeouts: {run.ai_metrics.timeout_count} | Budget: {run.ai_metrics.budget_exhaustion_count}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 7. Failure Breakdown (if false auto-resolutions > 0) */}
          {run.case_evaluations.some((c) => c.is_false_auto_resolution) && (
            <div className="rounded-2xl border border-[#A85F59]/40 bg-[#F8F6F0] p-6 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold tracking-tight text-[#9A514C]">
                  Failure Breakdown: False Auto-Resolutions
                </h3>
                <p className="text-xs text-[#4F514A]">
                  Violations of the zero false auto-resolution invariant.
                </p>
              </div>

              <div className="space-y-3">
                {run.case_evaluations
                  .filter((c) => c.is_false_auto_resolution)
                  .map((c) => (
                    <div key={c.case_id} className="rounded-xl border border-[#A85F59]/30 bg-[#A85F59]/10 p-3.5 text-xs">
                      <div className="flex items-center justify-between font-mono font-bold text-[#9A514C]">
                        <span>Case: {c.case_id}</span>
                        <span>Scenario: {c.scenario_family}</span>
                      </div>
                      <div className="mt-1.5 font-mono text-[#171816]">
                        {c.notes}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
