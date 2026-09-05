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
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3B5145]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
            <span>DATA INGESTION</span>
            <span className="text-[#CFC9BC]">/</span>
            <span className="text-[#4F514A]">SOURCE CONTROL</span>
          </div>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-[#171816]">
            DATA SOURCES
          </h1>
          <p className="mt-1 text-sm font-normal text-[#4F514A]">
            Connect financial sources, ingest evidence, and reconcile it through the same deterministic pipeline.
          </p>
        </div>

        {status && (
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#CFC9BC] bg-[#F8F6F0] px-3 py-1.5 text-[#3F413B]">
              <span>CONNECTORS</span>
              <strong className="font-semibold text-[#171816]">{status.connectors.length} ACTIVE</strong>
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#3B5145]/30 bg-[#3B5145]/10 px-3 py-1.5 font-medium text-[#3B5145]">
              FAIL-CLOSED PARSER
            </span>
          </div>
        )}
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-4 py-3.5 text-sm text-[#9A514C]">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#9A514C]" />
          <div className="font-mono text-xs">
            <strong className="block font-semibold uppercase tracking-wide">Data Source Error</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Loading state */}
      {!error && (!status || !runs) && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] py-24 text-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#CFC9BC] border-t-[#3B5145]" />
          <p className="mt-4 font-mono text-xs font-medium uppercase tracking-wider text-[#4F514A]">
            Loading data sources...
          </p>
        </div>
      )}

      {/* Ingestion Console */}
      {status && runs && <IngestionClient status={status} runs={runs} onRefresh={refresh} />}
    </div>
  );
}
