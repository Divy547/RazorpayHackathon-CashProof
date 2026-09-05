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
        const count = c.disposition_counts[selectedDisposition] ?? 0;
        if (count <= 0) return false;
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
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 sm:p-5 shadow-sm">
          <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
            Total Exceptions
          </div>
          <div className="mt-2 font-mono text-xl sm:text-2xl lg:text-3xl font-bold tabular-nums text-[#8C6843]">
            {initialData.total_exceptions}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            {Math.round((initialData.total_exceptions / Math.max(1, initialData.total_settlements)) * 100)}% of batch settlements
          </div>
        </div>

        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 sm:p-5 shadow-sm">
          <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
            Recurring Patterns
          </div>
          <div className="mt-2 font-mono text-xl sm:text-2xl lg:text-3xl font-bold tabular-nums text-[#171816]">
            {initialData.recurring_clusters}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            {initialData.total_clusters} distinct clusters identified
          </div>
        </div>

        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 sm:p-5 shadow-sm">
          <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
            Affected Settlement Net
          </div>
          <div className="mt-2 font-mono text-xl sm:text-2xl lg:text-3xl font-bold tabular-nums text-[#171816] truncate">
            {formatMinor(initialData.total_affected_settlement_net_minor, initialData.currency)}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            Gross monetary volume in exceptions
          </div>
        </div>

        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 sm:p-5 shadow-sm">
          <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
            Reconciliation Delta
          </div>
          <div
            className={`mt-2 font-mono text-xl sm:text-2xl lg:text-3xl font-bold tabular-nums truncate ${
              initialData.total_affected_delta_minor === 0
                ? "text-[#3B5145]"
                : initialData.total_affected_delta_minor > 0
                ? "text-[#8C6843]"
                : "text-[#9A514C]"
            }`}
          >
            {formatSignedMinor(initialData.total_affected_delta_minor, initialData.currency)}
          </div>
          <div className="mt-1.5 font-mono text-xs text-[#4F514A]">
            Net discrepancy to balance
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 font-mono text-xs font-semibold text-[#4F514A]">
            <Filter className="h-3.5 w-3.5 text-[#6B6D64]" />
            <span>Category:</span>
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3 py-1.5 font-mono text-xs font-medium text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
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

          <div className="flex items-center gap-1.5 font-mono text-xs font-semibold text-[#4F514A]">
            <span>Failing Gate:</span>
          </div>
          <select
            value={selectedGate}
            onChange={(e) => setSelectedGate(e.target.value)}
            className="rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3 py-1.5 font-mono text-xs font-medium text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
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

          <div className="flex items-center gap-1.5 font-mono text-xs font-semibold text-[#4F514A]">
            <span>Disposition:</span>
          </div>
          <select
            value={selectedDisposition}
            onChange={(e) => setSelectedDisposition(e.target.value)}
            className="rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3 py-1.5 font-mono text-xs font-medium text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
          >
            <option value="ALL">All Dispositions</option>
            <option value="HUMAN_REVIEW">Human Review</option>
            <option value="UNRESOLVED">Unresolved</option>
            <option value="AUTO_RESOLVED">Auto Resolved</option>
          </select>
        </div>

        <div className="relative min-w-[240px] flex-1 sm:flex-initial">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#6B6D64]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search pattern, key, or case ID..."
            className="w-full rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] py-1.5 pl-8 pr-3 font-mono text-xs font-medium text-[#171816] placeholder-[#6B6D64] transition-colors focus:border-[#171816] focus:outline-none"
          />
        </div>
      </div>

      {/* Main Clustering Grid: List on Left, Selected Detail on Right */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Cluster Cards (7 cols) */}
        <div className="space-y-4 lg:col-span-7">
          <div className="flex items-center justify-between font-mono text-xs font-semibold uppercase tracking-wider text-[#3F413B]">
            <span>Identified Exception Patterns ({filteredClusters.length})</span>
            <span className="text-[11px] font-normal text-[#6B6D64]">Sorted by Frequency &amp; Impact</span>
          </div>

          {filteredClusters.length === 0 && (
            <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs text-[#6B6D64]">
              No exception clusters match the selected filters.
            </div>
          )}

          {filteredClusters.map((cluster) => {
            const isSelected = cluster.cluster_key === selectedClusterKey;
            return (
              <div
                key={cluster.cluster_key}
                onClick={() => setSelectedClusterKey(cluster.cluster_key)}
                className={`cursor-pointer rounded-2xl p-5 transition-all shadow-sm ${
                  isSelected
                    ? "border-2 border-[#171816] bg-[#F8F6F0] ring-1 ring-[#171816]/10"
                    : "border border-[#CFC9BC] bg-[#F8F6F0] hover:border-[#8C8D82]"
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-[#171816]">
                        {cluster.cluster_name}
                      </span>
                      {cluster.is_recurring && (
                        <span className="inline-flex items-center gap-1 rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2 py-0.5 font-mono text-[10px] font-bold tracking-wide text-[#8C6843]">
                          RECURRING
                        </span>
                      )}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <Badge tone={operationalCategoryTone(cluster.operational_category)}>
                        {operationalCategoryLabel(cluster.operational_category)}
                      </Badge>
                      {cluster.dominant_failing_gate && (
                        <Link
                          href={`/gate?check=${cluster.dominant_failing_gate}`}
                          onClick={(e) => e.stopPropagation()}
                          className="inline-flex items-center gap-1 rounded-md border border-[#A85F59]/30 bg-[#A85F59]/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-[#9A514C] transition-colors hover:bg-[#A85F59]/20"
                          title="View Gate Intelligence diagnostics for this check"
                        >
                          <span>Gate: {cluster.dominant_failing_gate} &rarr;</span>
                        </Link>
                      )}
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <div className="font-mono text-base font-bold tabular-nums text-[#171816]">
                      {cluster.case_count} cases
                    </div>
                    <div className="font-mono text-[11px] font-medium text-[#6B6D64]">
                      {cluster.percentage_of_exceptions}% of exceptions
                    </div>
                  </div>
                </div>

                {/* Monetary Metrics Bar */}
                <div className="mt-4 grid grid-cols-2 gap-3 border-t border-[#D9D5CA]/70 pt-3 sm:grid-cols-3">
                  <div>
                    <div className="font-mono text-[11px] font-medium uppercase tracking-wider text-[#6B6D64]">
                      Affected Volume
                    </div>
                    <div className="font-mono text-xs font-bold text-[#171816]">
                      {formatMinor(cluster.affected_settlement_net_minor, cluster.currency)}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[11px] font-medium uppercase tracking-wider text-[#6B6D64]">
                      Net Delta
                    </div>
                    <div
                      className={`font-mono text-xs font-bold ${
                        cluster.affected_delta_minor === 0
                          ? "text-[#3B5145]"
                          : cluster.affected_delta_minor > 0
                          ? "text-[#8C6843]"
                          : "text-[#9A514C]"
                      }`}
                    >
                      {formatSignedMinor(cluster.affected_delta_minor, cluster.currency)}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[11px] font-medium uppercase tracking-wider text-[#6B6D64]">
                      Dispositions
                    </div>
                    <div className="font-mono text-xs font-medium text-[#4F514A]">
                      {Object.entries(cluster.disposition_counts)
                        .filter(([, cnt]) => cnt > 0)
                        .map(([disp, cnt]) => `${cnt} ${disp.toLowerCase()}`)
                        .join(", ") || "None"}
                    </div>
                  </div>
                </div>

                {/* Deterministic Representatives */}
                <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-[#D9D5CA]/70 pt-3">
                  <span className="font-mono text-[11px] font-medium text-[#6B6D64]">
                    Representative cases to inspect:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {cluster.representative_case_ids.map((cid) => (
                      <Link
                        key={cid}
                        href={`/cases/${cid}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2 py-0.5 font-mono text-[11px] font-medium text-[#171816] transition-colors hover:border-[#171816] hover:bg-[#E5DFD1]"
                      >
                        <span>{cid}</span>
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
            <div className="font-mono text-xs font-semibold uppercase tracking-wider text-[#3F413B]">
              Cluster Deep-Dive &amp; Remediation
            </div>

            {selectedSummary ? (
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm space-y-5">
                {/* Header: Title & Cluster Key */}
                <div>
                  <h2 className="text-base font-bold tracking-tight text-[#171816]">
                    {selectedSummary.cluster_name}
                  </h2>
                  <p className="mt-1 font-mono text-[11px] text-[#6B6D64] break-all leading-snug">
                    Cluster Key: {selectedSummary.cluster_key}
                  </p>
                </div>

                {/* Category and Recurrence Badges */}
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={operationalCategoryTone(selectedSummary.operational_category)}>
                    {operationalCategoryLabel(selectedSummary.operational_category)}
                  </Badge>
                  <span className="inline-flex items-center gap-1 rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2 py-0.5 font-mono text-xs font-medium text-[#4F514A]">
                    {selectedSummary.is_recurring
                      ? `Recurring (${selectedSummary.case_count} cases)`
                      : "Single Case"}
                  </span>
                  {selectedSummary.dominant_failing_gate && (
                    <Link
                      href={`/gate?check=${selectedSummary.dominant_failing_gate}`}
                      className="inline-flex items-center gap-1 rounded-md border border-[#A85F59]/30 bg-[#A85F59]/10 px-2 py-0.5 font-mono text-xs font-semibold text-[#9A514C] transition-colors hover:bg-[#A85F59]/20"
                      title="View Gate Intelligence diagnostics for this check"
                    >
                      <span>Gate: {selectedSummary.dominant_failing_gate}</span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  )}
                </div>

                {/* Operational Description & Remediation Playbook */}
                <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4.5 space-y-3.5">
                  <div>
                    <div className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#3F413B]">
                      Operational Pattern Analysis
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#171816]">
                      {clusterDetail?.description ?? "Loading pattern analysis..."}
                    </p>
                  </div>

                  <div className="border-t border-[#CFC9BC]/80 pt-3">
                    <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-wider text-[#3B5145]">
                      <Sparkles className="h-3.5 w-3.5 text-[#3B5145]" />
                      <span>Suggested Remediation Playbook</span>
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-[#171816]">
                      {clusterDetail?.suggested_remediation ??
                        "Inspect case candidates and verify ledger references."}
                    </p>
                  </div>
                </div>

                {/* Metrics Summary */}
                <div className="grid grid-cols-2 gap-3 rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4 text-xs">
                  <div>
                    <div className="font-mono text-[11px] font-medium uppercase tracking-wider text-[#6B6D64]">
                      Affected Volume:
                    </div>
                    <div className="mt-1 font-mono text-sm font-bold text-[#171816] truncate">
                      {formatMinor(
                        selectedSummary.affected_settlement_net_minor,
                        selectedSummary.currency,
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[11px] font-medium uppercase tracking-wider text-[#6B6D64]">
                      Reconciliation Delta:
                    </div>
                    <div
                      className={`mt-1 font-mono text-sm font-bold truncate ${
                        selectedSummary.affected_delta_minor === 0
                          ? "text-[#3B5145]"
                          : selectedSummary.affected_delta_minor > 0
                          ? "text-[#8C6843]"
                          : "text-[#9A514C]"
                      }`}
                    >
                      {formatSignedMinor(
                        selectedSummary.affected_delta_minor,
                        selectedSummary.currency,
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[11px] font-medium uppercase tracking-wider text-[#6B6D64]">
                      First Seen:
                    </div>
                    <div className="mt-1 font-mono text-xs font-medium text-[#171816]">
                      {formatDateTime(selectedSummary.first_seen)}
                    </div>
                  </div>
                  <div>
                    <div className="font-mono text-[11px] font-medium uppercase tracking-wider text-[#6B6D64]">
                      Last Seen:
                    </div>
                    <div className="mt-1 font-mono text-xs font-medium text-[#171816]">
                      {formatDateTime(selectedSummary.last_seen)}
                    </div>
                  </div>
                </div>

                {/* All Cases in Cluster */}
                <div>
                  <div className="flex items-center justify-between font-mono text-xs font-semibold uppercase tracking-wider text-[#3F413B]">
                    <span>All Affected Settlements ({clusterDetail?.case_ids.length ?? selectedSummary.case_count})</span>
                    <span className="text-[11px] font-normal text-[#6B6D64]">
                      Click to review
                    </span>
                  </div>

                  <div className="mt-2 max-h-60 overflow-y-auto rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-1.5 divide-y divide-[#CFC9BC]/70">
                    {(clusterDetail?.case_ids ?? selectedSummary.representative_case_ids).map(
                      (cid) => (
                        <Link
                          key={cid}
                          href={`/cases/${cid}`}
                          className="group flex items-center justify-between px-3 py-2 text-xs rounded-lg transition-colors hover:bg-[#F8F6F0]"
                        >
                          <span className="font-mono font-medium text-[#171816]">{cid}</span>
                          <div className="flex items-center gap-1 font-mono text-[11px] text-[#6B6D64] group-hover:text-[#3B5145] transition-colors">
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
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#171816] px-4 py-3 font-mono text-xs font-semibold text-[#F8F6F0] shadow-sm transition-colors hover:bg-[#2C2E2B]"
                  >
                    <span>Review Highest-Impact Case ({selectedSummary.representative_case_ids[0]})</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                )}
              </div>
            ) : (
              <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs text-[#6B6D64]">
                Select an exception cluster to view operational diagnosis and remediation.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
