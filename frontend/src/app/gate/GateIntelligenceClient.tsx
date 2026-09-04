"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowRight,
  ExternalLink,
  Layers,
  Search,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/Badge";
import { KpiCard } from "@/components/KpiCard";
import {
  formatMinor,
  formatSignedMinor,
} from "@/lib/format";
import type {
  GateCheckBreakdown,
  GateIntelligenceResponse,
} from "@/lib/types";

const CHECK_DISPLAY_NAMES: Record<string, string> = {
  IDENTITY: "Identity",
  BRIDGE: "Bridge",
  CURRENCY: "Currency",
  UNIQUENESS: "Uniqueness",
  EVIDENCE_COMPLETENESS: "Evidence Completeness",
  CONFLICT: "Conflict",
  POLICY: "Policy",
  STATE_TRANSITION: "State Transition",
  TARGET_SET_EQUALITY: "Target Set Equality",
};

export function GateIntelligenceClient({
  initialData,
}: {
  initialData: GateIntelligenceResponse;
}) {
  const searchParams = useSearchParams();
  const initialCheckParam = searchParams.get("check");

  // Determine valid initial check from URL or top blocker
  const defaultCheck = useMemo(() => {
    if (
      initialCheckParam &&
      initialData.check_breakdowns.some((b) => b.check_name === initialCheckParam.toUpperCase())
    ) {
      return initialCheckParam.toUpperCase();
    }
    return (
      initialData.top_blocker ||
      initialData.check_breakdowns[0]?.check_name ||
      "IDENTITY"
    );
  }, [initialCheckParam, initialData]);

  const [selectedCheckName, setSelectedCheckName] = useState<string>(defaultCheck);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Selected check breakdown
  const selectedBreakdown: GateCheckBreakdown | undefined = useMemo(() => {
    return (
      initialData.check_breakdowns.find((b) => b.check_name === selectedCheckName) ||
      initialData.check_breakdowns[0]
    );
  }, [initialData.check_breakdowns, selectedCheckName]);

  // Filtered blockers
  const filteredBlockers = useMemo(() => {
    return initialData.automation_blockers.filter((b) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = b.check_name.toLowerCase().includes(q);
        const matchesDispName = (CHECK_DISPLAY_NAMES[b.check_name] || "").toLowerCase().includes(q);
        const matchesExp = b.explanation.summary.toLowerCase().includes(q);
        const matchesReq = b.explanation.eligibility_requirement.toLowerCase().includes(q);
        const matchesCluster = (b.top_cluster_name || "").toLowerCase().includes(q);
        const matchesCase = b.representative_case_ids.some((id) => id.toLowerCase().includes(q));
        if (
          !matchesName &&
          !matchesDispName &&
          !matchesExp &&
          !matchesReq &&
          !matchesCluster &&
          !matchesCase
        ) {
          return false;
        }
      }
      return true;
    });
  }, [initialData.automation_blockers, searchQuery]);

  const passRatePct = initialData.pass_rate <= 1 ? initialData.pass_rate * 100 : initialData.pass_rate;

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <KpiCard
          label="Gate Pass Rate"
          value={`${passRatePct.toFixed(1)}%`}
          tone={passRatePct > 50 ? "success" : "neutral"}
          hint={`${initialData.passed_cases} of ${initialData.total_cases} cases`}
        />
        <KpiCard
          label="Automation Blocked"
          value={initialData.failed_cases}
          tone={initialData.failed_cases > 0 ? "warning" : "success"}
          hint="cases stopped by gate firewall"
        />
        <KpiCard
          label="Top Blocker"
          value={
            initialData.top_blocker
              ? CHECK_DISPLAY_NAMES[initialData.top_blocker] ?? initialData.top_blocker
              : "None"
          }
          tone={initialData.top_blocker ? "danger" : "success"}
          hint="most frequent firewall check failure"
        />
        <KpiCard
          label="Blocked Net Volume"
          value={formatMinor(initialData.total_affected_settlement_net_minor, initialData.currency)}
          tone="neutral"
          hint="settlement value requiring human review"
        />
        <KpiCard
          label="Discrepancy Delta"
          value={formatSignedMinor(initialData.total_affected_delta_minor, initialData.currency)}
          tone={initialData.total_affected_delta_minor === 0 ? "success" : "warning"}
          hint="net variance across blocked cases"
        />
      </div>

      {/* Controller Firewall Banner */}
      <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-5">
        <div className="flex items-start gap-3.5">
          <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-amber-400">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <h2 className="text-sm font-semibold text-slate-100">
              Deterministic Controller Explainability &amp; Gate Firewall
            </h2>
            <p className="max-w-3xl text-xs leading-relaxed text-slate-400">
              The Resolution Gate is CashProof&apos;s non-negotiable financial firewall. Every case
              assigned an <code className="text-emerald-400">AUTO_RESOLVED</code> disposition must pass all
              9 mandatory checks. Gates are evaluated purely deterministically; neither candidate scores
              nor AI proposals can approve themselves or bypass gate requirements.
            </p>
            {initialData.top_blocker && (
              <div className="pt-2 text-xs text-slate-300">
                <span className="font-semibold text-amber-400">Primary Automation Blocker:</span>{" "}
                <span className="font-mono font-medium text-slate-100">
                  {initialData.top_blocker}
                </span>{" "}
                is the leading barrier preventing automated resolution, affecting{" "}
                <span className="font-mono text-slate-100">
                  {formatMinor(initialData.total_affected_settlement_net_minor, initialData.currency)}
                </span>{" "}
                in settlement net volume.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Ranked Automation Blockers Section */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Ranked Automation Blockers
            </h2>
            <p className="text-xs text-slate-400">
              Checks that cause gate rejection, ranked deterministically by failure frequency and settlement volume.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search check, cluster, or case..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64 rounded-md border border-slate-800 bg-[#0b0f16] py-1.5 pl-8 pr-3 text-xs text-slate-200 placeholder-slate-500 focus:border-slate-700 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {filteredBlockers.length === 0 ? (
          <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-8 text-center text-sm text-slate-500">
            No automation blockers match the search query.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-[#0d1219]">
            <table className="w-full min-w-[960px] border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-[#0b0f16] uppercase tracking-wider text-slate-500">
                  <th className="py-3 pl-4 pr-2 font-medium">Rank</th>
                  <th className="px-3 py-3 font-medium">Gate Check</th>
                  <th className="px-3 py-3 text-right font-medium">Failures</th>
                  <th className="px-3 py-3 text-right font-medium">% Blocked</th>
                  <th className="px-3 py-3 text-right font-medium">Blocked Net Volume</th>
                  <th className="px-3 py-3 text-right font-medium">Variance Delta</th>
                  <th className="px-3 py-3 font-medium">Top Exception Pattern</th>
                  <th className="py-3 pl-3 pr-4 text-center font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredBlockers.map((blocker) => {
                  const isSelected = selectedCheckName === blocker.check_name;
                  return (
                    <tr
                      key={blocker.check_name}
                      onClick={() => setSelectedCheckName(blocker.check_name)}
                      className={`cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-slate-800/50 hover:bg-slate-800/70"
                          : "hover:bg-slate-800/30"
                      }`}
                    >
                      <td className="py-3.5 pl-4 pr-2 font-mono font-semibold text-slate-400">
                        #{blocker.rank}
                      </td>
                      <td className="px-3 py-3.5">
                        <div className="font-semibold text-slate-200">
                          {CHECK_DISPLAY_NAMES[blocker.check_name] ?? blocker.check_name}
                        </div>
                        <div className="font-mono text-[10px] text-slate-500">
                          {blocker.check_name}
                        </div>
                      </td>
                      <td className="px-3 py-3.5 text-right font-mono text-slate-200">
                        {blocker.failure_count}
                      </td>
                      <td className="px-3 py-3.5 text-right">
                        <div className="font-mono text-slate-300">
                          {blocker.percentage_of_blocked_cases.toFixed(1)}%
                        </div>
                        <div className="mt-1 h-1.5 w-16 ml-auto overflow-hidden rounded-full bg-slate-800">
                          <div
                            className="h-full bg-red-500"
                            style={{ width: `${Math.min(100, blocker.percentage_of_blocked_cases)}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-3 py-3.5 text-right font-mono font-medium text-slate-200">
                        {formatMinor(blocker.affected_settlement_net_minor, blocker.currency)}
                      </td>
                      <td className="px-3 py-3.5 text-right font-mono text-slate-400">
                        {formatSignedMinor(blocker.affected_delta_minor, blocker.currency)}
                      </td>
                      <td className="px-3 py-3.5">
                        {blocker.top_cluster_name ? (
                          <div className="space-y-0.5">
                            <div className="font-medium text-slate-300">
                              {blocker.top_cluster_name}
                            </div>
                            {blocker.top_cluster_key && (
                              <div className="font-mono text-[10px] text-sky-400">
                                {blocker.top_cluster_key}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-500">None</span>
                        )}
                      </td>
                      <td className="py-3.5 pl-3 pr-4 text-center">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedCheckName(blocker.check_name);
                          }}
                          className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                            isSelected
                              ? "bg-sky-600 text-white"
                              : "border border-slate-700 bg-slate-800/80 text-slate-300 hover:bg-slate-700"
                          }`}
                        >
                          {isSelected ? "Active" : "Inspect"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 9-Check Navigator & Interactive Gate Inspector */}
      <div className="space-y-4">
        <div>
          <h2 className="text-base font-semibold text-slate-100">
            Gate Check Inspector
          </h2>
          <p className="text-xs text-slate-400">
            Select any of the 9 mandatory deterministic checks to view its technical invariant, pass/fail distribution, and eligibility requirements.
          </p>
        </div>

        {/* 9 Check Tabs */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-9">
          {initialData.check_breakdowns.map((b) => {
            const isSelected = b.check_name === selectedCheckName;
            const hasFailures = b.failure_count > 0;
            return (
              <button
                key={b.check_name}
                type="button"
                onClick={() => setSelectedCheckName(b.check_name)}
                className={`flex flex-col items-start rounded-lg border p-2.5 text-left transition-all ${
                  isSelected
                    ? "border-sky-500/60 bg-sky-500/10 text-white shadow-sm"
                    : "border-slate-800 bg-[#0d1219] text-slate-400 hover:border-slate-700 hover:text-slate-200"
                }`}
              >
                <div className="flex w-full items-center justify-between gap-1">
                  <span className="truncate text-xs font-semibold">
                    {CHECK_DISPLAY_NAMES[b.check_name] ?? b.check_name}
                  </span>
                  {hasFailures ? (
                    <span className="flex h-2 w-2 rounded-full bg-red-500" />
                  ) : (
                    <span className="flex h-2 w-2 rounded-full bg-emerald-500" />
                  )}
                </div>
                <div className="mt-1 flex items-baseline gap-1 text-[11px] font-mono">
                  {hasFailures ? (
                    <span className="font-semibold text-red-400">
                      {b.failure_count} failed
                    </span>
                  ) : (
                    <span className="text-emerald-400">100% pass</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Detailed Selected Check Inspector Panel */}
        {selectedBreakdown && (
          <div className="space-y-6 rounded-lg border border-slate-800 bg-[#0d1219] p-6">
            {/* Inspector Header */}
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 pb-5">
              <div>
                <div className="flex items-center gap-2.5">
                  <h3 className="text-lg font-bold text-slate-100">
                    {CHECK_DISPLAY_NAMES[selectedBreakdown.check_name] ?? selectedBreakdown.check_name}
                  </h3>
                  <span className="font-mono text-xs text-slate-500">
                    ({selectedBreakdown.check_name})
                  </span>
                  {selectedBreakdown.failure_count > 0 ? (
                    <Badge tone="danger">
                      {selectedBreakdown.failure_count} Blocked Cases
                    </Badge>
                  ) : (
                    <Badge tone="success">100% Passing Check</Badge>
                  )}
                </div>
                <p className="mt-1 max-w-2xl text-xs text-slate-400">
                  {selectedBreakdown.explanation.summary}
                </p>
              </div>

              <div className="flex items-center gap-4 text-right">
                <div>
                  <div className="text-[11px] uppercase tracking-wider text-slate-500">
                    Failure Rate
                  </div>
                  <div className="font-mono text-base font-semibold text-red-400">
                    {(selectedBreakdown.failure_rate <= 1 ? selectedBreakdown.failure_rate * 100 : selectedBreakdown.failure_rate).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-[11px] uppercase tracking-wider text-slate-500">
                    Evaluations
                  </div>
                  <div className="font-mono text-base font-semibold text-slate-200">
                    {selectedBreakdown.evaluation_count}
                  </div>
                </div>
              </div>
            </div>

            {/* Technical Invariant & Eligibility Requirement Cards */}
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-2 rounded-md border border-slate-800 bg-[#0b0f16] p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                  <ShieldCheck className="h-4 w-4 text-sky-400" />
                  <span>Technical Invariant Enforcement</span>
                </div>
                <p className="text-xs leading-relaxed text-slate-400">
                  {selectedBreakdown.explanation.description}
                </p>
              </div>

              <div className="space-y-2 rounded-md border border-amber-500/30 bg-amber-500/[0.04] p-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-300">
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                  <span>Deterministic Eligibility Requirement (&quot;What Must Change&quot;)</span>
                </div>
                <p className="text-xs leading-relaxed text-amber-200/90">
                  {selectedBreakdown.explanation.eligibility_requirement}
                </p>
              </div>
            </div>

            {/* Financial Impact & Dispositions */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-md border border-slate-800 bg-[#0b0f16] p-3.5">
                <div className="text-[11px] font-medium text-slate-500">
                  Affected Settlement Volume
                </div>
                <div className="mt-1 font-mono text-sm font-semibold text-slate-200">
                  {formatMinor(
                    selectedBreakdown.affected_settlement_net_minor,
                    selectedBreakdown.currency,
                  )}
                </div>
                <div className="mt-0.5 text-[10px] text-slate-500">
                  monetary value of blocked cases
                </div>
              </div>

              <div className="rounded-md border border-slate-800 bg-[#0b0f16] p-3.5">
                <div className="text-[11px] font-medium text-slate-500">
                  Reconciliation Discrepancy Delta
                </div>
                <div className="mt-1 font-mono text-sm font-semibold text-slate-200">
                  {formatSignedMinor(
                    selectedBreakdown.affected_delta_minor,
                    selectedBreakdown.currency,
                  )}
                </div>
                <div className="mt-0.5 text-[10px] text-slate-500">
                  observed vs expected variance
                </div>
              </div>

              <div className="rounded-md border border-slate-800 bg-[#0b0f16] p-3.5 sm:col-span-2">
                <div className="text-[11px] font-medium text-slate-500">
                  Resulting Dispositions
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(selectedBreakdown.disposition_counts).map(([disp, count]) => (
                    <div
                      key={disp}
                      className="flex items-center gap-1.5 rounded bg-slate-800/80 px-2.5 py-1 text-xs"
                    >
                      <Badge
                        tone={
                          disp === "AUTO_RESOLVED"
                            ? "success"
                            : disp === "HUMAN_REVIEW"
                              ? "warning"
                              : "danger"
                        }
                      >
                        {disp.replace("_", " ")}
                      </Badge>
                      <span className="font-mono font-semibold text-slate-200">
                        {count}
                      </span>
                    </div>
                  ))}
                  {Object.keys(selectedBreakdown.disposition_counts).length === 0 && (
                    <span className="text-xs text-slate-500">No cases affected</span>
                  )}
                </div>
              </div>
            </div>

            {/* Linked Clusters */}
            {selectedBreakdown.related_cluster_keys.length > 0 && (
              <div className="space-y-2 border-t border-slate-800 pt-4">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                  <Layers className="h-3.5 w-3.5 text-sky-400" />
                  <span>Linked Exception Intelligence Clusters (Phase 6)</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedBreakdown.related_cluster_keys.map((key) => (
                    <Link
                      key={key}
                      href={`/exceptions`}
                      className="inline-flex items-center gap-1.5 rounded border border-slate-700 bg-slate-800/80 px-2.5 py-1 text-xs text-slate-300 transition-colors hover:border-slate-600 hover:text-white"
                    >
                      <span>Cluster: <code className="text-sky-300">{key}</code></span>
                      <ExternalLink className="h-3 w-3 text-slate-500" />
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Representative Cases */}
            {selectedBreakdown.representative_case_ids.length > 0 && (
              <div className="space-y-2 border-t border-slate-800 pt-4">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                  <span>Representative Blocked Cases</span>
                  <span className="font-mono text-slate-500">
                    {selectedBreakdown.representative_case_ids.length} samples
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedBreakdown.representative_case_ids.map((id) => (
                    <Link
                      key={id}
                      href={`/cases/${id}`}
                      className="inline-flex items-center gap-1 rounded border border-slate-800 bg-[#0b0f16] px-2.5 py-1 font-mono text-xs text-slate-300 transition-colors hover:border-slate-700 hover:text-white"
                    >
                      <span>{id}</span>
                      <ArrowRight className="h-3 w-3 text-slate-500" />
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
