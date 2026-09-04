"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/Badge";
import { dispositionLabel, dispositionTone, exceptionLabel, formatSignedMinor } from "@/lib/format";
import type { CaseRow, Disposition } from "@/lib/types";

type Filter = "ALL" | Disposition;

const FILTERS: { key: Filter; label: string }[] = [
  { key: "ALL", label: "All" },
  { key: "AUTO_RESOLVED", label: "Auto Resolved" },
  { key: "HUMAN_REVIEW", label: "Human Review" },
  { key: "UNRESOLVED", label: "Unresolved" },
];

export function CaseExplorerClient({ cases }: { cases: CaseRow[] }) {
  const [filter, setFilter] = useState<Filter>("ALL");

  const filtered = useMemo(
    () => (filter === "ALL" ? cases : cases.filter((c) => c.disposition === filter)),
    [cases, filter],
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {FILTERS.map((f) => {
          const count = f.key === "ALL" ? cases.length : cases.filter((c) => c.disposition === f.key).length;
          const active = filter === f.key;
          return (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                active
                  ? "border-slate-600 bg-slate-800 text-slate-100"
                  : "border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
              }`}
            >
              {f.label}
              <span className="ml-1.5 text-slate-500">{count}</span>
            </button>
          );
        })}
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full min-w-[900px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-[#0b0f16] text-left text-xs font-medium uppercase tracking-wide text-slate-500">
              <th className="px-4 py-3">Settlement ID</th>
              <th className="px-4 py-3 text-right">Expected Net</th>
              <th className="px-4 py-3 text-right">Observed Net</th>
              <th className="px-4 py-3 text-right">Delta</th>
              <th className="px-4 py-3">Exception</th>
              <th className="px-4 py-3 text-right">Candidates</th>
              <th className="px-4 py-3">Disposition</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {filtered.map((row) => (
              <tr key={row.settlement_id} className="transition-colors hover:bg-slate-900/60">
                <td className="px-4 py-2.5">
                  <Link
                    href={`/cases/${row.settlement_id}`}
                    className="font-mono text-xs text-slate-300 hover:text-emerald-400"
                  >
                    {row.settlement_id}
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-xs tabular-nums text-slate-300">
                  {formatSignedMinor(row.expected_net_minor).replace("+", "")}
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-xs tabular-nums text-slate-300">
                  {formatSignedMinor(row.observed_net_minor).replace("+", "")}
                </td>
                <td
                  className={`px-4 py-2.5 text-right font-mono text-xs tabular-nums ${
                    row.delta_minor === 0 ? "text-slate-500" : "text-amber-400"
                  }`}
                >
                  {formatSignedMinor(row.delta_minor)}
                </td>
                <td className="px-4 py-2.5 text-xs text-slate-400">
                  {exceptionLabel(row.exception_type)}
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-xs tabular-nums text-slate-400">
                  {row.candidate_count}
                </td>
                <td className="px-4 py-2.5">
                  <Badge tone={dispositionTone(row.disposition)}>
                    {dispositionLabel(row.disposition)}
                  </Badge>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-sm text-slate-500">
                  No cases match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
