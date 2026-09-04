"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ChevronRight,
  ExternalLink,
  Filter,
  Search,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/Badge";
import { KpiCard } from "@/components/KpiCard";
import { Panel } from "@/components/Panel";
import {
  formatDateTime,
  formatMinor,
  formatSignedMinor,
  operationalCategoryLabel,
  operationalCategoryTone,
} from "@/lib/format";
import type {
  ExceptionClusterDetail,
  ExceptionIntelligenceResponse,
  OperationalCategory,
} from "@/lib/types";
import { fetchExceptionClusterDetail } from "@/lib/api";

const CATEGORIES: OperationalCategory[] = [
  "REFERENCE_AMBIGUITY",
  "AMOUNT_INCONSISTENCY",
  "UNSTRUCTURED_REFERENCE",
  "MISSING_RECORD",
  "EVIDENCE_CONFLICT",
  "POLICY_REVIEW",
  "OTHER",
];

const GATES = [
  "TARGET_SET_EQUALITY",
  "BRIDGE",
  "POLICY",
  "IDENTITY",
  "UNIQUENESS",
  "EVIDENCE_COMPLETENESS",
  "CONFLICT",
  "STATE_TRANSITION",
];

export function ExceptionIntelligenceClient({
  initialData,
}: {
  initialData: ExceptionIntelligenceResponse;
  onReload: () => void;
}) {
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedGate, setSelectedGate] = useState<string>("ALL");
  const [selectedDisposition, setSelectedDisposition] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const [selectedClusterKey, setSelectedClusterKey] = useState<string | null>(
    initialData.clusters.length > 0 ? initialData.clusters[0].cluster_key : null,
  );
  const [clusterDetail, setClusterDetail] = useState<ExceptionClusterDetail | null>(null);

  // Filter clusters in client
  const filteredClusters = useMemo(() => {
    return initialData.clusters.filter((c) => {
      if (selectedCategory !== "ALL" && c.operational_category !== selectedCategory) {
        return false;
      }
      if (selectedGate !== "ALL" && c.dominant_failing_gate !== selectedGate) {
        return false;
      }
      if (selectedDisposition !== "ALL") {
        const hasDisp = c.disposition_counts.some(
          ([disp, count]) => disp === selectedDisposition && count > 0,
        );
        if (!hasDisp) return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = c.cluster_name.toLowerCase().includes(q);
        const matchesKey = c.cluster_key.toLowerCase().includes(q);
        const matchesCat = c.operational_category.toLowerCase().includes(q);
        const matchesRep = c.representative_case_ids.some((id) => id.toLowerCase().includes(q));
        if (!matchesName && !matchesKey && !matchesCat && !matchesRep) return false;
      }
      return true;
    });
  }, [initialData.clusters, selectedCategory, selectedGate, selectedDisposition, searchQuery]);

  // Load cluster detail asynchronously in an effect
  useEffect(() => {
    if (!selectedClusterKey) return;
    let cancelled = false;

    fetchExceptionClusterDetail(selectedClusterKey)
      .then((detail) => {
        if (!cancelled) setClusterDetail(detail);
      })
      .catch((err: unknown) => {
        console.error("Failed to load cluster detail", err);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedClusterKey]);

  const selectedSummary = useMemo(() => {
    return initialData.clusters.find((c) => c.cluster_key === selectedClusterKey) ?? null;
  }, [initialData.clusters, selectedClusterKey]);

  return (
    <div className="space-y-8">
      {/* KPI Overview */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          label="Total Exceptions"
          value={initialData.total_exceptions}
          hint={`${Math.round(
            (initialData.total_exceptions / Math.max(1, initialData.total_settlements)) * 100,
          )}% of batch settlements`}
          tone="warning"
        />
        <KpiCard
          label="Recurring Patterns"
          value={initialData.recurring_clusters}
          hint={`${initialData.total_clusters} distinct clusters`}
          tone="info"
        />
        <KpiCard
          label="Affected Settlement Net"
          value={formatMinor(initialData.total_affected_settlement_net_minor, initialData.currency)}
          hint="Gross monetary volume in exceptions"
        />
        <KpiCard
          label="Reconciliation Delta"
          value={formatSignedMinor(initialData.total_affected_delta_minor, initialData.currency)}
          hint="Net discrepancy to balance"
          tone={initialData.total_affected_delta_minor === 0 ? "success" : "danger"}
          emphasize={initialData.total_affected_delta_minor !== 0}
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800 bg-[#0d1219] p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
            <Filter className="h-3.5 w-3.5 text-slate-500" />
            Category:
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
          >
            <option value="ALL">All Categories ({initialData.clusters.length})</option>
            {CATEGORIES.map((cat) => {
              const count = initialData.clusters.filter((c) => c.operational_category === cat).length;
              if (count === 0) return null;
              return (
                <option key={cat} value={cat}>
                  {operationalCategoryLabel(cat)} ({count})
                </option>
              );
            })}
          </select>

          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
            Failing Gate:
          </div>
          <select
            value={selectedGate}
            onChange={(e) => setSelectedGate(e.target.value)}
            className="rounded border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
          >
            <option value="ALL">All Gates</option>
            {GATES.map((gate) => {
              const count = initialData.clusters.filter((c) => c.dominant_failing_gate === gate).length;
              if (count === 0) return null;
              return (
                <option key={gate} value={gate}>
                  {gate} ({count})
                </option>
              );
            })}
          </select>

          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
            Disposition:
          </div>
          <select
            value={selectedDisposition}
            onChange={(e) => setSelectedDisposition(e.target.value)}
            className="rounded border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none"
          >
            <option value="ALL">All Dispositions</option>
            <option value="HUMAN_REVIEW">Human Review</option>
            <option value="UNRESOLVED">Unresolved</option>
            <option value="AUTO_RESOLVED">Auto Resolved</option>
          </select>
        </div>

        <div className="relative min-w-[220px]">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search pattern, key, or case ID..."
            className="w-full rounded border border-slate-700 bg-slate-900 py-1 pl-8 pr-3 text-xs text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Main Clustering Grid: List on Left, Selected Detail on Right */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Cluster Cards (7 cols) */}
        <div className="space-y-4 lg:col-span-7">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
            <span>Identified Exception Patterns ({filteredClusters.length})</span>
            <span>Sorted by Frequency & Impact</span>
          </div>

          {filteredClusters.length === 0 && (
            <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-8 text-center text-sm text-slate-500">
              No exception clusters match the selected filters.
            </div>
          )}

          {filteredClusters.map((cluster) => {
            const isSelected = cluster.cluster_key === selectedClusterKey;
            return (
              <div
                key={cluster.cluster_key}
                onClick={() => setSelectedClusterKey(cluster.cluster_key)}
                className={`cursor-pointer rounded-lg border p-5 transition-all ${
                  isSelected
                    ? "border-emerald-500/50 bg-emerald-500/[0.04] shadow-lg shadow-emerald-950/20 ring-1 ring-emerald-500/30"
                    : "border-slate-800 bg-[#0d1219] hover:border-slate-700 hover:bg-slate-900/60"
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-100">
                        {cluster.cluster_name}
                      </span>
                      {cluster.is_recurring && (
                        <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-amber-400 border border-amber-500/20">
                          RECURRING
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                      <Badge tone={operationalCategoryTone(cluster.operational_category)}>
                        {operationalCategoryLabel(cluster.operational_category)}
                      </Badge>
                      {cluster.dominant_failing_gate && (
                        <Link
                          href={`/gate?check=${cluster.dominant_failing_gate}`}
                          onClick={(e) => e.stopPropagation()}
                          className="font-mono text-[11px] text-red-400 bg-red-950/40 border border-red-800/40 px-1.5 py-0.5 rounded hover:bg-red-900/50 hover:text-red-300 transition-colors"
                          title="View Gate Intelligence diagnostics for this check"
                        >
                          Gate: {cluster.dominant_failing_gate} &rarr;
                        </Link>
                      )}
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="font-mono text-base font-semibold text-slate-100">
                      {cluster.case_count} cases
                    </div>
                    <div className="text-[11px] text-slate-400">
                      {cluster.percentage_of_exceptions}% of exceptions
                    </div>
                  </div>
                </div>

                {/* Monetary Metrics Bar */}
                <div className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-800/80 pt-3 sm:grid-cols-3">
                  <div>
                    <div className="text-[11px] text-slate-500">Affected Volume</div>
                    <div className="font-mono text-xs font-medium text-slate-200">
                      {formatMinor(cluster.affected_settlement_net_minor, cluster.currency)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-500">Net Delta</div>
                    <div
                      className={`font-mono text-xs font-medium ${
                        cluster.affected_delta_minor === 0 ? "text-emerald-400" : "text-amber-400"
                      }`}
                    >
                      {formatSignedMinor(cluster.affected_delta_minor, cluster.currency)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] text-slate-500">Dispositions</div>
                    <div className="text-xs text-slate-300">
                      {cluster.disposition_counts
                        .map(([disp, cnt]) => `${cnt} ${disp.toLowerCase()}`)
                        .join(", ")}
                    </div>
                  </div>
                </div>

                {/* Deterministic Representatives */}
                <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-800/60 pt-3">
                  <span className="text-[11px] font-medium text-slate-500">
                    Representative cases to inspect:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {cluster.representative_case_ids.map((cid) => (
                      <Link
                        key={cid}
                        href={`/cases/${cid}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 rounded border border-slate-700 bg-slate-800/80 px-2 py-0.5 font-mono text-[11px] text-slate-300 transition-colors hover:border-emerald-500 hover:text-emerald-300"
                      >
                        {cid}
                        <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Selected Cluster Deep-Dive (5 cols) */}
        <div className="lg:col-span-5">
          <div className="sticky top-20 space-y-4">
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Cluster Deep-Dive & Remediation
            </div>

            {selectedSummary ? (
              <Panel
                title={selectedSummary.cluster_name}
                subtitle={`Cluster Key: ${selectedSummary.cluster_key}`}
              >
                <div className="space-y-5">
                  {/* Category and Recurrence */}
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={operationalCategoryTone(selectedSummary.operational_category)}>
                      {operationalCategoryLabel(selectedSummary.operational_category)}
                    </Badge>
                    <Badge tone={selectedSummary.is_recurring ? "warning" : "neutral"}>
                      {selectedSummary.is_recurring
                        ? `Recurring (${selectedSummary.case_count} cases)`
                        : "Single Case"}
                    </Badge>
                    {selectedSummary.dominant_failing_gate && (
                      <Link
                        href={`/gate?check=${selectedSummary.dominant_failing_gate}`}
                        className="inline-flex items-center gap-1 font-mono text-xs text-red-300 bg-red-950/50 border border-red-800/50 px-2 py-0.5 rounded hover:bg-red-900/60 hover:text-red-200 transition-colors"
                        title="View Gate Intelligence diagnostics for this check"
                      >
                        <span>Gate: {selectedSummary.dominant_failing_gate}</span>
                        <ExternalLink className="h-3 w-3 text-red-400" />
                      </Link>
                    )}
                  </div>

                  {/* Operational Description & Playbook */}
                  <div className="rounded-md border border-slate-800 bg-[#0b0f16] p-4">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      Operational Pattern Analysis
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-slate-300">
                      {clusterDetail?.description ?? "Loading pattern analysis..."}
                    </p>

                    <div className="mt-4 border-t border-slate-800/80 pt-3">
                      <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
                        <Sparkles className="h-3.5 w-3.5" />
                        Suggested Remediation Playbook
                      </div>
                      <p className="mt-1 text-xs leading-relaxed text-slate-300">
                        {clusterDetail?.suggested_remediation ??
                          "Inspect case candidates and verify ledger references."}
                      </p>
                    </div>
                  </div>

                  {/* Metrics Summary */}
                  <div className="grid grid-cols-2 gap-3 rounded-md border border-slate-800 bg-[#0b0f16] p-3 text-xs">
                    <div>
                      <span className="text-slate-500">Affected Volume:</span>
                      <div className="font-mono font-medium text-slate-200">
                        {formatMinor(
                          selectedSummary.affected_settlement_net_minor,
                          selectedSummary.currency,
                        )}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500">Reconciliation Delta:</span>
                      <div
                        className={`font-mono font-medium ${
                          selectedSummary.affected_delta_minor === 0
                            ? "text-emerald-400"
                            : "text-amber-400"
                        }`}
                      >
                        {formatSignedMinor(
                          selectedSummary.affected_delta_minor,
                          selectedSummary.currency,
                        )}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500">First Seen:</span>
                      <div className="text-slate-300">
                        {formatDateTime(selectedSummary.first_seen)}
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-500">Last Seen:</span>
                      <div className="text-slate-300">
                        {formatDateTime(selectedSummary.last_seen)}
                      </div>
                    </div>
                  </div>

                  {/* All Cases in Cluster */}
                  <div>
                    <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
                      <span>All Affected Settlements ({clusterDetail?.case_ids.length ?? selectedSummary.case_count})</span>
                      <span className="text-[11px] font-normal text-slate-500">
                        Click to review
                      </span>
                    </div>

                    <div className="mt-2 max-h-60 overflow-y-auto rounded-md border border-slate-800 bg-[#0b0f16] p-2 divide-y divide-slate-800/60">
                      {(clusterDetail?.case_ids ?? selectedSummary.representative_case_ids).map(
                        (cid) => (
                          <Link
                            key={cid}
                            href={`/cases/${cid}`}
                            className="group flex items-center justify-between px-2.5 py-1.5 text-xs text-slate-300 transition-colors hover:bg-slate-800/70 hover:text-white"
                          >
                            <span className="font-mono">{cid}</span>
                            <div className="flex items-center gap-1 text-[11px] text-slate-500 group-hover:text-emerald-400">
                              <span>Inspect</span>
                              <ChevronRight className="h-3 w-3" />
                            </div>
                          </Link>
                        ),
                      )}
                    </div>
                  </div>

                  {/* Primary Action Button */}
                  {selectedSummary.representative_case_ids.length > 0 && (
                    <Link
                      href={`/cases/${selectedSummary.representative_case_ids[0]}`}
                      className="flex w-full items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-emerald-500"
                    >
                      <span>Review Highest-Impact Case ({selectedSummary.representative_case_ids[0]})</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  )}
                </div>
              </Panel>
            ) : (
              <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-8 text-center text-xs text-slate-500">
                Select an exception cluster to view operational diagnosis and remediation.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
