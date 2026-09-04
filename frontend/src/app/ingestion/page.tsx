"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { ApiError, fetchIngestionRuns, fetchIngestionStatus } from "@/lib/api";
import type { IngestionRun, IngestionStatusResponse } from "@/lib/types";
import { IngestionClient } from "./IngestionClient";

export default function IngestionPage() {
  const [status, setStatus] = useState<IngestionStatusResponse | null>(null);
  const [runs, setRuns] = useState<IngestionRun[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    Promise.all([fetchIngestionStatus(), fetchIngestionRuns()])
      .then(([statusResponse, runsResponse]) => {
        setStatus(statusResponse);
        setRuns(runsResponse);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(
          err instanceof ApiError
            ? `Failed to load data sources: ${err.message}`
            : "Could not reach the CashProof API. Start it with `uv run python scripts/run_api.py`.",
        );
      });
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-100">Data Sources</h1>
        <p className="mt-1 text-sm text-slate-400">
          Ingest read-only Razorpay test-mode data or a bank statement CSV, then reconcile it
          through the same deterministic pipeline as the synthetic benchmark dataset.
        </p>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!error && (!status || !runs) && (
        <p className="text-sm text-slate-500">Loading data sources...</p>
      )}

      {status && runs && <IngestionClient status={status} runs={runs} onRefresh={refresh} />}
    </div>
  );
}
