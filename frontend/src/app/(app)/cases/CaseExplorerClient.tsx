"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/cn";
import {
  dispositionLabel,
  exceptionLabel,
  formatMinor,
  formatSignedMinor,
} from "@/lib/format";
import type { CaseRow, Disposition } from "@/lib/types";

type Filter = "ALL" | Disposition;

interface FilterOption {
  key: Filter;
  label: string;
  dotColor?: string;
}

const FILTERS: FilterOption[] = [
  { key: "ALL", label: "ALL" },
  { key: "AUTO_RESOLVED", label: "AUTO RESOLVED", dotColor: "bg-[#3B5145]" },
  { key: "HUMAN_REVIEW", label: "HUMAN REVIEW", dotColor: "bg-[#8C6843]" },
  { key: "UNRESOLVED", label: "UNRESOLVED", dotColor: "bg-[#9A514C]" },
];

export function CaseExplorerClient({ cases }: { cases: CaseRow[] }) {
  const [filter, setFilter] = useState<Filter>("ALL");

  const counts = useMemo(() => {
    return {
      ALL: cases.length,
      AUTO_RESOLVED: cases.filter((c) => c.disposition === "AUTO_RESOLVED").length,
      HUMAN_REVIEW: cases.filter((c) => c.disposition === "HUMAN_REVIEW").length,
      UNRESOLVED: cases.filter((c) => c.disposition === "UNRESOLVED").length,
    };
  }, [cases]);

  const filtered = useMemo(
    () => (filter === "ALL" ? cases : cases.filter((c) => c.disposition === filter)),
    [cases, filter],
  );

  return (
    <div className="space-y-4">
      {/* Filter / Scope Control Strip */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="inline-flex flex-wrap items-center gap-1.5 rounded-xl border border-[#CFC9BC] bg-[#EEEAE0]/70 p-1">
          {FILTERS.map((f) => {
            const count = counts[f.key];
            const active = filter === f.key;
            return (
              <button
                key={f.key}
                type="button"
                onClick={() => setFilter(f.key)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-[8px] px-3.5 py-1.5 font-mono text-xs font-semibold tracking-tight transition-all duration-150",
                  active
                    ? "border border-[#171816] bg-[#171816] text-[#F8F6F0] shadow-sm"
                    : "border border-[#CFC9BC] bg-[#F8F6F0] text-[#3F413B] hover:bg-[#EEEAE0] hover:text-[#171816]",
                )}
              >
                {f.dotColor && (
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      f.dotColor,
                      active && "ring-1 ring-[#F8F6F0]/50",
                    )}
                  />
                )}
                <span>{f.label}</span>
                <span
                  className={cn(
                    "tabular-nums text-[11px] font-semibold",
                    active ? "text-[#D9D5CA]" : "text-[#6B6D64]",
                  )}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        <div className="font-mono text-xs text-[#4F514A]">
          Showing <span className="font-semibold text-[#171816]">{filtered.length}</span> of{" "}
          <span className="font-semibold text-[#171816]">{cases.length}</span> cases
        </div>
      </div>

      {/* Case Table Surface Container */}
      <div className="w-full overflow-hidden rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] shadow-sm">
        {/* Mobile horizontal scroll hint */}
        <div className="border-b border-[#CFC9BC] bg-[#EEEAE0]/60 px-4 py-1.5 font-mono text-[11px] text-[#4F514A] sm:hidden">
          Swipe horizontally to view all columns →
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[920px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                <th scope="col" className="px-5 py-3.5 text-left text-[#3F413B]">
                  SETTLEMENT ID
                </th>
                <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                  EXPECTED NET
                </th>
                <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                  OBSERVED NET
                </th>
                <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                  DELTA
                </th>
                <th scope="col" className="px-5 py-3.5 text-left text-[#3F413B]">
                  EXCEPTION
                </th>
                <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                  CANDIDATES
                </th>
                <th scope="col" className="px-5 py-3.5 text-left text-[#3F413B]">
                  DISPOSITION
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#D9D5CA]">
              {filtered.map((row) => {
                const isZero = row.delta_minor === 0;
                const isNegative = row.delta_minor < 0;
                const deltaClass = isZero
                  ? "text-[#65745F]"
                  : isNegative
                  ? "text-[#9A514C]"
                  : "text-[#8C6843]";

                return (
                  <tr
                    key={row.settlement_id}
                    className="transition-colors duration-100 hover:bg-[#F2ECE1]"
                  >
                    {/* Settlement ID */}
                    <td className="px-5 py-3.5">
                      <Link
                        href={`/cases/${row.settlement_id}`}
                        className="group inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#171816] transition-colors hover:text-[#3B5145]"
                      >
                        <span className="underline decoration-[#CFC9BC] underline-offset-2 transition-colors group-hover:decoration-[#3B5145]">
                          {row.settlement_id}
                        </span>
                        <ArrowUpRight className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100 text-[#3B5145]" />
                      </Link>
                    </td>

                    {/* Expected Net */}
                    <td className="px-5 py-3.5 text-right font-mono text-xs font-medium tabular-nums text-[#4B4D46]">
                      {formatMinor(row.expected_net_minor)}
                    </td>

                    {/* Observed Net */}
                    <td className="px-5 py-3.5 text-right font-mono text-xs font-medium tabular-nums text-[#4B4D46]">
                      {formatMinor(row.observed_net_minor)}
                    </td>

                    {/* Delta */}
                    <td className={cn("px-5 py-3.5 text-right font-mono text-xs font-semibold tabular-nums", deltaClass)}>
                      {formatSignedMinor(row.delta_minor)}
                    </td>

                    {/* Exception */}
                    <td className="px-5 py-3.5 text-xs font-medium text-[#4F514A]">
                      {exceptionLabel(row.exception_type)}
                    </td>

                    {/* Candidates */}
                    <td className="px-5 py-3.5 text-right font-mono text-xs font-medium tabular-nums text-[#4B4D46]">
                      {row.candidate_count}
                    </td>

                    {/* Disposition */}
                    <td className="px-5 py-3.5">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border px-2.5 py-0.5 font-mono text-xs font-semibold tracking-tight",
                          row.disposition === "AUTO_RESOLVED" && "border-[#3B5145]/30 bg-[#3B5145]/10 text-[#3B5145]",
                          row.disposition === "HUMAN_REVIEW" && "border-[#8C6843]/30 bg-[#8C6843]/10 text-[#8C6843]",
                          row.disposition === "UNRESOLVED" && "border-[#9A514C]/30 bg-[#9A514C]/10 text-[#9A514C]",
                        )}
                      >
                        {dispositionLabel(row.disposition)}
                      </span>
                    </td>
                  </tr>
                );
              })}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-14 text-center">
                    <p className="font-mono text-xs uppercase tracking-wider text-[#6B6D64]">
                      No settlement cases match this filter.
                    </p>
                    <button
                      type="button"
                      onClick={() => setFilter("ALL")}
                      className="mt-3 inline-flex items-center rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3.5 py-1.5 font-mono text-xs font-medium text-[#171816] transition-colors hover:bg-[#E5DFD1]"
                    >
                      Reset Filter
                    </button>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Table Footer Summary Bar */}
        <div className="flex flex-col gap-2 border-t border-[#CFC9BC] bg-[#EEEAE0]/50 px-5 py-3 sm:flex-row sm:items-center sm:justify-between text-xs font-mono text-[#4F514A]">
          <div>
            Showing <strong className="font-semibold text-[#171816]">{filtered.length}</strong> of{" "}
            <span className="font-semibold text-[#171816]">{cases.length}</span> settlements
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
              <span>Auto:</span>
              <strong className="font-semibold text-[#171816]">{counts.AUTO_RESOLVED}</strong>
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#8C6843]" />
              <span>Review:</span>
              <strong className="font-semibold text-[#171816]">{counts.HUMAN_REVIEW}</strong>
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#9A514C]" />
              <span>Unresolved:</span>
              <strong className="font-semibold text-[#171816]">{counts.UNRESOLVED}</strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
