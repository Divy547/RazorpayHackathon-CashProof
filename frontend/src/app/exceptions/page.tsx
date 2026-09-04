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
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-slate-100">
            Exception Intelligence & Clustering
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Deterministic pattern analysis, recurring operational clusters, and financial impact across batch exceptions.
          </p>
        </div>
        <button
          type="button"
          onClick={handleReload}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700 hover:text-white disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!error && !data && (
        <p className="text-sm text-slate-500">Analyzing recurring exception patterns...</p>
      )}

      {data && <ExceptionIntelligenceClient initialData={data} onReload={handleReload} />}
    </div>
  );
}
