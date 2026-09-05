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
import { cn } from "@/lib/cn";
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
      {/* 5 Operational KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {/* 1. Gate Pass Rate */}
        <div className="rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 shadow-sm">
          <div className="flex items-center justify-between text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
            <span>Gate Pass Rate</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
          </div>
          <div className="mt-2 font-mono text-3xl font-bold tabular-nums text-[#3B5145]">
            {passRatePct.toFixed(1)}%
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            {initialData.passed_cases} of {initialData.total_cases} cases passed
          </div>
        </div>

        {/* 2. Automation Blocked */}
        <div className="rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 shadow-sm">
          <div className="flex items-center justify-between text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
            <span>Automation Blocked</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#9A514C]" />
          </div>
          <div className="mt-2 font-mono text-3xl font-bold tabular-nums text-[#171816]">
            {initialData.failed_cases}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            cases stopped by firewall
          </div>
        </div>

        {/* 3. Top Blocker */}
        <div className="rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 shadow-sm">
          <div className="flex items-center justify-between text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
            <span>Top Blocker</span>
            <span className="h-1.5 w-1.5 rounded-full bg-[#9A514C]" />
          </div>
          <div className="mt-2 font-mono text-2xl font-bold tracking-tight text-[#9A514C] truncate">
            {initialData.top_blocker
              ? CHECK_DISPLAY_NAMES[initialData.top_blocker] ?? initialData.top_blocker
              : "None"}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            leading failure check
          </div>
        </div>

        {/* 4. Blocked Net Volume */}
        <div className="rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 shadow-sm">
          <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
            Blocked Net Volume
          </div>
          <div className="mt-2 font-mono text-2xl font-bold tabular-nums text-[#171816] truncate">
            {formatMinor(initialData.total_affected_settlement_net_minor, initialData.currency)}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            requires reviewer sign-off
          </div>
        </div>

        {/* 5. Discrepancy Delta */}
        <div className="rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 shadow-sm col-span-2 lg:col-span-1">
          <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
            Discrepancy Delta
          </div>
          <div className="mt-2 font-mono text-2xl font-bold tabular-nums text-[#8C6843] truncate">
            {formatSignedMinor(initialData.total_affected_delta_minor, initialData.currency)}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            net variance across blocked
          </div>
        </div>
      </div>

      {/* Controller Firewall Banner */}
      <section className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="rounded-xl border border-[#8C6843]/30 bg-[#8C6843]/10 p-2.5 text-[#8C6843]">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div className="space-y-1.5">
            <h2 className="text-sm font-bold tracking-tight text-[#171816]">
              Deterministic Controller Explainability &amp; Gate Firewall
            </h2>
            <p className="max-w-3xl text-xs leading-relaxed text-[#4F514A]">
              The Resolution Gate is CashProof&apos;s non-negotiable financial firewall. Every case
              assigned an <code className="font-mono text-xs font-semibold text-[#3B5145] bg-[#3B5145]/15 border border-[#3B5145]/30 px-1.5 py-0.5 rounded">AUTO_RESOLVED</code> disposition must pass all
              9 mandatory checks. Gates are evaluated purely deterministically; neither candidate scores
              nor AI proposals can approve themselves or bypass gate requirements.
            </p>
            {initialData.top_blocker && (
              <div className="pt-2 font-mono text-xs text-[#4F514A]">
                <span className="font-semibold text-[#8C6843]">Primary Automation Blocker:</span>{" "}
                <span className="font-bold text-[#171816]">
                  {initialData.top_blocker}
                </span>{" "}
                is the leading barrier preventing automated resolution, affecting{" "}
                <span className="font-bold text-[#171816]">
                  {formatMinor(initialData.total_affected_settlement_net_minor, initialData.currency)}
                </span>{" "}
                in settlement net volume.
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Ranked Automation Blockers Section */}
      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-bold tracking-tight text-[#171816]">
              Ranked Automation Blockers
            </h2>
            <p className="text-xs text-[#4F514A]">
              Checks that cause gate rejection, ranked deterministically by failure frequency and settlement volume.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#6B6D64]" />
              <input
                type="text"
                placeholder="Search check, cluster, or case..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64 rounded-lg border border-[#CFC9BC] bg-[#F8F6F0] py-1.5 pl-8 pr-3 font-mono text-xs font-medium text-[#171816] placeholder-[#6B6D64] transition-colors focus:border-[#171816] focus:outline-none"
              />
            </div>
          </div>
        </div>

        {filteredBlockers.length === 0 ? (
          <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs uppercase tracking-wider text-[#6B6D64]">
            No automation blockers match the search query.
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[960px] border-collapse text-left text-xs">
                <thead>
                  <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                    <th className="py-3.5 pl-5 pr-2">Rank</th>
                    <th className="px-4 py-3.5">Gate Check</th>
                    <th className="px-4 py-3.5 text-right">Failures</th>
                    <th className="px-4 py-3.5 text-right">% Blocked</th>
                    <th className="px-4 py-3.5 text-right">Blocked Net Volume</th>
                    <th className="px-4 py-3.5 text-right">Variance Delta</th>
                    <th className="px-4 py-3.5">Top Exception Pattern</th>
                    <th className="py-3.5 pl-4 pr-5 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D9D5CA]">
                  {filteredBlockers.map((blocker) => {
                    const isSelected = selectedCheckName === blocker.check_name;
                    return (
                      <tr
                        key={blocker.check_name}
                        onClick={() => setSelectedCheckName(blocker.check_name)}
                        className={cn(
                          "cursor-pointer transition-colors duration-100",
                          isSelected
                            ? "bg-[#EEEAE0]/70 hover:bg-[#EEEAE0]"
                            : "hover:bg-[#F2ECE1]",
                        )}
                      >
                        <td className="py-3.5 pl-5 pr-2 font-mono font-semibold text-[#6B6D64]">
                          #{blocker.rank}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="font-semibold text-[#171816]">
                            {CHECK_DISPLAY_NAMES[blocker.check_name] ?? blocker.check_name}
                          </div>
                          <div className="font-mono text-[10px] text-[#6B6D64]">
                            {blocker.check_name}
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-right font-mono font-semibold tabular-nums text-[#171816]">
                          {blocker.failure_count}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <div className="font-mono text-[#4F514A]">
                            {blocker.percentage_of_blocked_cases.toFixed(1)}%
                          </div>
                          <div className="mt-1 h-1.5 w-16 ml-auto overflow-hidden rounded-full bg-[#EEEAE0] border border-[#CFC9BC]/60">
                            <div
                              className="h-full bg-[#9A514C]"
                              style={{ width: `${Math.min(100, blocker.percentage_of_blocked_cases)}%` }}
                            />
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-right font-mono font-medium tabular-nums text-[#171816]">
                          {formatMinor(blocker.affected_settlement_net_minor, blocker.currency)}
                        </td>
                        <td className="px-4 py-3.5 text-right font-mono tabular-nums text-[#8C6843]">
                          {formatSignedMinor(blocker.affected_delta_minor, blocker.currency)}
                        </td>
                        <td className="px-4 py-3.5">
                          {blocker.top_cluster_name ? (
                            <div className="space-y-0.5">
                              <div className="font-medium text-[#171816]">
                                {blocker.top_cluster_name}
                              </div>
                              {blocker.top_cluster_key && (
                                <div className="font-mono text-[10px] text-[#6B6D64]">
                                  {blocker.top_cluster_key}
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="text-[#6B6D64]">None</span>
                          )}
                        </td>
                        <td className="py-3.5 pl-4 pr-5 text-center">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedCheckName(blocker.check_name);
                            }}
                            className={cn(
                              "rounded-[6px] px-2.5 py-1 font-mono text-xs font-semibold transition-colors",
                              isSelected
                                ? "bg-[#171816] text-[#F8F6F0] shadow-sm"
                                : "border border-[#CFC9BC] bg-[#EEEAE0] text-[#3F413B] hover:bg-[#E5DFD1]",
                            )}
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
          </div>
        )}
      </div>

      {/* 9-Check Navigator & Interactive Gate Inspector */}
      <div className="space-y-4">
        <div>
          <h2 className="text-base font-bold tracking-tight text-[#171816]">
            Gate Check Inspector
          </h2>
          <p className="text-xs text-[#4F514A]">
            Select any of the 9 mandatory deterministic checks to view its technical invariant, pass/fail distribution, and eligibility requirements.
          </p>
        </div>

        {/* 9 Check Tabs Control Matrix */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-9">
          {initialData.check_breakdowns.map((b) => {
            const isSelected = b.check_name === selectedCheckName;
            const hasFailures = b.failure_count > 0;
            return (
              <button
                key={b.check_name}
                type="button"
                onClick={() => setSelectedCheckName(b.check_name)}
                className={cn(
                  "flex flex-col items-start rounded-xl p-3 text-left transition-all duration-150",
                  isSelected
                    ? "border-2 border-[#171816] bg-[#EEEAE0] shadow-sm"
                    : "border border-[#CFC9BC] bg-[#F8F6F0] hover:bg-[#EEEAE0]/70",
                )}
              >
                <div className="flex w-full items-center justify-between gap-1">
                  <span className="truncate text-xs font-semibold text-[#171816]">
                    {CHECK_DISPLAY_NAMES[b.check_name] ?? b.check_name}
                  </span>
                  {hasFailures ? (
                    <span className="flex h-2 w-2 shrink-0 rounded-full bg-[#9A514C]" />
                  ) : (
                    <span className="flex h-2 w-2 shrink-0 rounded-full bg-[#3B5145]" />
                  )}
                </div>
                <div className="mt-1 flex items-baseline gap-1 font-mono text-[11px]">
                  {hasFailures ? (
                    <span className="font-semibold text-[#9A514C]">
                      {b.failure_count} failed
                    </span>
                  ) : (
                    <span className="font-medium text-[#3B5145]">100% pass</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Detailed Selected Check Inspector Panel */}
        {selectedBreakdown && (
          <section className="space-y-6 rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm">
            {/* Inspector Header */}
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#CFC9BC] pb-5">
              <div>
                <div className="flex flex-wrap items-center gap-2.5">
                  <h3 className="text-lg font-bold text-[#171816]">
                    {CHECK_DISPLAY_NAMES[selectedBreakdown.check_name] ?? selectedBreakdown.check_name}
                  </h3>
                  <span className="font-mono text-xs text-[#6B6D64]">
                    ({selectedBreakdown.check_name})
                  </span>
                  {selectedBreakdown.failure_count > 0 ? (
                    <span className="inline-flex items-center gap-1.5 rounded-md border border-[#9A514C]/30 bg-[#9A514C]/10 px-2.5 py-0.5 font-mono text-xs font-semibold text-[#9A514C]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#9A514C]" />
                      {selectedBreakdown.failure_count} Blocked Cases
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 rounded-md border border-[#3B5145]/30 bg-[#3B5145]/10 px-2.5 py-0.5 font-mono text-xs font-semibold text-[#3B5145]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
                      100% Passing Check
                    </span>
                  )}
                </div>
                <p className="mt-1.5 max-w-2xl text-xs text-[#4F514A] leading-relaxed">
                  {selectedBreakdown.explanation.summary}
                </p>
              </div>

              <div className="flex items-center gap-6 text-right font-mono">
                <div>
                  <div className="text-[11px] uppercase tracking-wider text-[#6B6D64]">
                    Failure Rate
                  </div>
                  <div className={cn(
                    "text-base font-bold tabular-nums",
                    selectedBreakdown.failure_count > 0 ? "text-[#9A514C]" : "text-[#3B5145]",
                  )}>
                    {(selectedBreakdown.failure_rate <= 1 ? selectedBreakdown.failure_rate * 100 : selectedBreakdown.failure_rate).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-[11px] uppercase tracking-wider text-[#6B6D64]">
                    Evaluations
                  </div>
                  <div className="text-base font-bold tabular-nums text-[#171816]">
                    {selectedBreakdown.evaluation_count}
                  </div>
                </div>
              </div>
            </div>

            {/* Technical Invariant & Eligibility Requirement Cards */}
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-2 rounded-xl border border-[#CFC9BC] bg-[#EEEAE0]/50 p-4">
                <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
                  <ShieldCheck className="h-4 w-4 text-[#3B5145]" />
                  <span>Technical Invariant Enforcement</span>
                </div>
                <p className="text-xs leading-relaxed text-[#4F514A]">
                  {selectedBreakdown.explanation.description}
                </p>
              </div>

              <div className="space-y-2 rounded-xl border border-[#8C6843]/30 bg-[#8C6843]/10 p-4">
                <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wider text-[#8C6843]">
                  <ShieldAlert className="h-4 w-4 text-[#8C6843]" />
                  <span>Deterministic Eligibility Requirement (&quot;What Must Change&quot;)</span>
                </div>
                <p className="text-xs leading-relaxed font-medium text-[#171816]">
                  {selectedBreakdown.explanation.eligibility_requirement}
                </p>
              </div>
            </div>

            {/* Financial Impact & Dispositions */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0]/40 p-3.5">
                <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
                  Affected Settlement Volume
                </div>
                <div className="mt-1 font-mono text-sm font-bold tabular-nums text-[#171816]">
                  {formatMinor(
                    selectedBreakdown.affected_settlement_net_minor,
                    selectedBreakdown.currency,
                  )}
                </div>
                <div className="mt-0.5 text-[10px] font-mono text-[#6B6D64]">
                  monetary value of blocked cases
                </div>
              </div>

              <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0]/40 p-3.5">
                <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
                  Reconciliation Discrepancy Delta
                </div>
                <div className={cn(
                  "mt-1 font-mono text-sm font-bold tabular-nums",
                  selectedBreakdown.affected_delta_minor === 0 ? "text-[#3B5145]" : "text-[#9A514C]",
                )}>
                  {formatSignedMinor(
                    selectedBreakdown.affected_delta_minor,
                    selectedBreakdown.currency,
                  )}
                </div>
                <div className="mt-0.5 text-[10px] font-mono text-[#6B6D64]">
                  observed vs expected variance
                </div>
              </div>

              <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0]/40 p-3.5 sm:col-span-2">
                <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#6B6D64]">
                  Resulting Dispositions
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(selectedBreakdown.disposition_counts).map(([disp, count]) => (
                    <div
                      key={disp}
                      className="flex items-center gap-2 rounded-md border border-[#CFC9BC] bg-[#F8F6F0] px-2.5 py-1 text-xs"
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
                      <span className="font-mono font-bold text-[#171816]">
                        {count}
                      </span>
                    </div>
                  ))}
                  {Object.keys(selectedBreakdown.disposition_counts).length === 0 && (
                    <span className="text-xs font-mono text-[#6B6D64]">No cases affected</span>
                  )}
                </div>
              </div>
            </div>

            {/* Linked Clusters */}
            {selectedBreakdown.related_cluster_keys.length > 0 && (
              <div className="space-y-2 border-t border-[#CFC9BC] pt-4">
                <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
                  <Layers className="h-3.5 w-3.5 text-[#3B5145]" />
                  <span>Linked Exception Intelligence Clusters</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedBreakdown.related_cluster_keys.map((key) => (
                    <Link
                      key={key}
                      href={`/exceptions`}
                      className="inline-flex max-w-full items-center gap-1.5 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3 py-1.5 font-mono text-xs font-semibold text-[#171816] transition-colors hover:border-[#171816] hover:bg-[#E5DFD1]"
                    >
                      <span className="min-w-0 break-all">
                        Cluster: <code className="text-[#3B5145]">{key}</code>
                      </span>
                      <ExternalLink className="h-3 w-3 shrink-0 text-[#6B6D64]" />
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Representative Cases */}
            {selectedBreakdown.representative_case_ids.length > 0 && (
              <div className="space-y-2 border-t border-[#CFC9BC] pt-4">
                <div className="flex items-center justify-between font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
                  <span>Representative Blocked Cases</span>
                  <span className="text-[#6B6D64]">
                    {selectedBreakdown.representative_case_ids.length} samples
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedBreakdown.representative_case_ids.map((id) => (
                    <Link
                      key={id}
                      href={`/cases/${id}`}
                      className="inline-flex max-w-full items-center gap-1.5 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3 py-1.5 font-mono text-xs font-semibold text-[#171816] transition-colors hover:border-[#3B5145] hover:bg-[#E5DFD1]"
                    >
                      <span className="truncate">{id}</span>
                      <ArrowRight className="h-3 w-3 shrink-0 text-[#6B6D64]" />
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}
