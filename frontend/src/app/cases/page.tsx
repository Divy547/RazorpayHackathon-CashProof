"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { ApiError, fetchCases } from "@/lib/api";
import type { CaseRow } from "@/lib/types";
import { CaseExplorerClient } from "./CaseExplorerClient";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchCases()
      .then((data) => {
        if (cancelled) return;
        setCases(data);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? `Failed to load cases: ${err.message}`
            : "Could not reach the CashProof API. Start it with `uv run python scripts/run_api.py`.",
        );
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-100">Case Explorer</h1>
        <p className="mt-1 text-sm text-slate-400">
          Every settlement processed by the deterministic reconciliation pipeline.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!error && !cases && <p className="text-sm text-slate-500">Loading cases...</p>}

      {cases && <CaseExplorerClient cases={cases} />}
    </div>
  );
}
