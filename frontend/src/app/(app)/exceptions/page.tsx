"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { ApiError, fetchExceptionClusters } from "@/lib/api";
import type { ExceptionIntelligenceResponse } from "@/lib/types";
import { ExceptionIntelligenceClient } from "./ExceptionIntelligenceClient";

export default function ExceptionsPage() {
  const [data, setData] = useState<ExceptionIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadTrigger, setReloadTrigger] = useState(0);

  useEffect(() => {
    let cancelled = false;

    fetchExceptionClusters()
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? `Failed to load exception intelligence: ${err.message}`
            : "Could not reach the CashProof API. Start it with `uv run python scripts/run_api.py`.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [reloadTrigger]);

  const handleReload = () => {
    setLoading(true);
    setReloadTrigger((n) => n + 1);
  };

  return (
    <div className="space-y-6">
      {/* Operational Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3B5145]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
            <span>OPERATIONAL CLUSTERING</span>
            <span className="text-[#CFC9BC]">/</span>
            <span className="text-[#4F514A]">EXCEPTION INTELLIGENCE</span>
          </div>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-[#171816]">
            Exception Intelligence &amp; Clustering
          </h1>
          <p className="mt-1 text-sm font-normal text-[#4F514A]">
            Deterministic pattern analysis, recurring operational clusters, and financial impact across batch exceptions.
          </p>
        </div>

        <button
          type="button"
          onClick={handleReload}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3.5 py-2 font-mono text-xs font-semibold text-[#171816] transition-colors hover:bg-[#E5DFD1] disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-[#A85F59]/40 bg-[#A85F59]/10 px-4 py-3 text-xs text-[#9A514C]">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#A85F59]" />
          <span>{error}</span>
        </div>
      )}

      {!error && !data && (
        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs text-[#6B6D64]">
          Analyzing recurring exception patterns...
        </div>
      )}

      {data && <ExceptionIntelligenceClient initialData={data} onReload={handleReload} />}
    </div>
  );
}
