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
import { Badge } from "@/components/Badge";
import { KpiCard } from "@/components/KpiCard";
import { Panel } from "@/components/Panel";

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
    <div className="mx-auto max-w-7xl px-6 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2.5">
            <Gauge className="h-6 w-6 text-sky-400" />
            Controller Benchmark & Evaluation
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Phase 4 evaluation of the production reconciliation pipeline against Phase 2 GroundTruth.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-3 bg-[#0d1219] p-3 rounded-lg border border-slate-800">
          <div className="flex items-center gap-2">
            <label htmlFor="seed-input" className="text-xs font-medium text-slate-400">
              Seed:
            </label>
            <input
              id="seed-input"
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-20 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="cases-input" className="text-xs font-medium text-slate-400">
              Cases:
            </label>
            <input
              id="cases-input"
              type="number"
              min={50}
              value={numSettlements}
              onChange={(e) => setNumSettlements(Number(e.target.value))}
              className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="arm-select" className="text-xs font-medium text-slate-400">
              Arm:
            </label>
            <select
              id="arm-select"
              value={arm}
              onChange={(e) => setArm(e.target.value)}
              className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
            >
              <option value="deterministic">Deterministic</option>
              <option value="ai_investigator">AI Investigator</option>
            </select>
          </div>

          <button
            onClick={handleRun}
            disabled={loading || numSettlements < 50}
            className="flex items-center gap-1.5 rounded bg-sky-600 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run Benchmark
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-950/30 p-4 text-sm text-red-300 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && !run && (
        <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-12 text-center">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-sky-400" />
          <p className="mt-4 text-base font-medium text-slate-200">
            Generating synthetic dataset and running production reconciler...
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Honest wall-clock timing boundary active. GroundTruth evaluation in progress.
          </p>
        </div>
      )}

      {run && (
        <div className="space-y-8">
          {/* Safety Gate Banner */}
          {run.safety_gate_passed ? (
            <div className="flex items-center justify-between rounded-lg border border-emerald-500/40 bg-emerald-950/20 p-5">
              <div className="flex items-center gap-3">
                <ShieldCheck className="h-7 w-7 text-emerald-400" />
                <div>
                  <div className="text-base font-semibold text-emerald-300">
                    SAFETY GATE PASSED: ZERO FALSE AUTO-RESOLUTIONS
                  </div>
                  <div className="text-xs text-emerald-400/80">
                    All {run.total_cases} cases verified against ground truth with 100% exact target set equality.
                  </div>
                </div>
              </div>
              <Badge tone="success">PASS</Badge>
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-lg border border-red-500/40 bg-red-950/20 p-5">
              <div className="flex items-center gap-3">
                <ShieldAlert className="h-7 w-7 text-red-400" />
                <div>
                  <div className="text-base font-semibold text-red-300">
                    SAFETY GATE FAILED: FALSE AUTO-RESOLUTIONS DETECTED
                  </div>
                  <div className="text-xs text-red-400/80">
                    {run.false_auto_resolution_count} false auto-resolution(s) detected. Financial safety invariant violated.
                  </div>
                </div>
              </div>
              <Badge tone="danger">FAIL</Badge>
            </div>
          )}

          {/* Headline KPIs */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Primary Throughput KPI"
              value={`${Math.round(run.records_per_minute).toLocaleString()} rec/min`}
              tone="info"
              emphasize
              hint={`Pipeline Wall-Clock: ${run.timing.pipeline_duration_seconds.toFixed(4)}s`}
            />
            <KpiCard
              label="Auto-Resolved"
              value={`${run.auto_resolved} (${(run.auto_resolution_rate * 100).toFixed(1)}%)`}
              tone="success"
              hint={`Correct: ${run.correct_auto_resolutions} | False: ${run.false_auto_resolutions}`}
            />
            <KpiCard
              label="Human Review"
              value={`${run.human_review} (${(run.human_review_rate * 100).toFixed(1)}%)`}
              tone="warning"
              hint="Governance and ambiguity safety routes"
            />
            <KpiCard
              label="Unresolved"
              value={`${run.unresolved} (${(run.unresolved_rate * 100).toFixed(1)}%)`}
              tone="neutral"
              hint="Missing records and conflicts"
            />
          </div>

          {/* Timing & Metadata Details */}
          <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-4 text-xs text-slate-400 flex flex-wrap gap-6 justify-between items-center">
            <div>
              <span className="text-slate-500">Run ID:</span> <span className="text-slate-300 font-mono">{run.run_id}</span>
            </div>
            <div>
              <span className="text-slate-500">Seed:</span> <span className="text-slate-300 font-mono">{run.seed}</span>
            </div>
            <div>
              <span className="text-slate-500">Rule Version:</span> <span className="text-slate-300 font-mono">{run.rule_version}</span>
            </div>
            <div>
              <span className="text-slate-500">Revision:</span> <span className="text-slate-300 font-mono">{run.code_revision}</span>
            </div>
            <div className="w-full sm:w-auto text-slate-500">
              Timing Boundary: <span className="text-slate-300">{run.timing.timing_boundary}</span>
            </div>
          </div>

          {/* Scenario Matrix */}
          <Panel title="Scenario Matrix (S1–S6 Taxonomy)" subtitle="Evaluator-only ground truth correlation across benchmark scenario families.">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="pb-3 font-medium">Scenario</th>
                    <th className="pb-3 font-medium">Total</th>
                    <th className="pb-3 font-medium">AUTO_RESOLVED</th>
                    <th className="pb-3 font-medium">HUMAN_REVIEW</th>
                    <th className="pb-3 font-medium">UNRESOLVED</th>
                    <th className="pb-3 font-medium">Correct Outcomes</th>
                    <th className="pb-3 font-medium">False Auto</th>
                    <th className="pb-3 font-medium">Safety Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {run.scenario_matrix.map((row) => (
                    <tr key={row.scenario_family} className="hover:bg-slate-900/30">
                      <td className="py-2.5 font-bold text-slate-200">
                        {row.scenario_family}
                      </td>
                      <td className="py-2.5 text-slate-300">{row.total}</td>
                      <td className="py-2.5 text-emerald-400">{row.auto_resolved}</td>
                      <td className="py-2.5 text-amber-400">{row.human_review}</td>
                      <td className="py-2.5 text-slate-400">{row.unresolved}</td>
                      <td className="py-2.5 text-slate-200">{row.correct_outcomes}</td>
                      <td className="py-2.5 text-red-400 font-semibold">{row.false_auto_resolutions}</td>
                      <td className="py-2.5">
                        {row.false_auto_resolutions === 0 ? (
                          <span className="text-emerald-400 flex items-center gap-1 font-sans">
                            <CheckCircle2 className="h-3.5 w-3.5" /> OK
                          </span>
                        ) : (
                          <span className="text-red-400 flex items-center gap-1 font-sans">
                            <AlertTriangle className="h-3.5 w-3.5" /> FAILED
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>

          {/* AI Metrics (shown if AI arm or any tool calls recorded) */}
          {(run.arm === "ai_investigator" || run.ai_metrics.investigations_started > 0) && (
            <Panel
              title="AI Investigator Governance & Telemetry"
              subtitle="Tool usage, proposal outcomes, and active budget constraints."
            >
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div className="rounded border border-slate-800 bg-slate-900/50 p-3">
                  <div className="text-xs text-slate-500 uppercase">Investigations</div>
                  <div className="mt-1 text-xl font-bold text-slate-100">
                    {run.ai_metrics.investigations_started}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Completed: {run.ai_metrics.investigations_completed} | Failed: {run.ai_metrics.investigations_failed}
                  </div>
                </div>

                <div className="rounded border border-slate-800 bg-slate-900/50 p-3">
                  <div className="text-xs text-slate-500 uppercase">Proposals Gate Outcome</div>
                  <div className="mt-1 text-xl font-bold text-slate-100">
                    {run.ai_metrics.proposals_generated}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Passed: <span className="text-emerald-400">{run.ai_metrics.proposals_gate_passed}</span> | Failed: <span className="text-amber-400">{run.ai_metrics.proposals_gate_failed}</span>
                  </div>
                </div>

                <div className="rounded border border-slate-800 bg-slate-900/50 p-3">
                  <div className="text-xs text-slate-500 uppercase">Tool Calls</div>
                  <div className="mt-1 text-xl font-bold text-slate-100">
                    {run.ai_metrics.total_tool_calls}
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                    <Cpu className="h-3 w-3 text-sky-400" /> Bounded tools only
                  </div>
                </div>

                <div className="rounded border border-slate-800 bg-slate-900/50 p-3">
                  <div className="text-xs text-slate-500 uppercase">Failure Modes</div>
                  <div className="mt-1 text-xl font-bold text-slate-100">
                    {run.ai_metrics.timeout_count + run.ai_metrics.budget_exhaustion_count + run.ai_metrics.malformed_output_count + run.ai_metrics.tool_failure_count}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Timeouts: {run.ai_metrics.timeout_count} | Budget: {run.ai_metrics.budget_exhaustion_count}
                  </div>
                </div>
              </div>
            </Panel>
          )}

          {/* Failure Breakdown */}
          {run.case_evaluations.some((c) => c.is_false_auto_resolution) && (
            <Panel title="Failure Breakdown: False Auto-Resolutions" subtitle="Violations of the zero false auto-resolution invariant.">
              <div className="space-y-3">
                {run.case_evaluations
                  .filter((c) => c.is_false_auto_resolution)
                  .map((c) => (
                    <div key={c.case_id} className="rounded border border-red-500/30 bg-red-950/20 p-3 text-xs">
                      <div className="flex items-center justify-between font-mono font-bold text-red-300">
                        <span>Case: {c.case_id}</span>
                        <span>Scenario: {c.scenario_family}</span>
                      </div>
                      <div className="mt-1 text-slate-300">
                        {c.notes}
                      </div>
                    </div>
                  ))}
              </div>
            </Panel>
          )}
        </div>
      )}
    </div>
  );
}
