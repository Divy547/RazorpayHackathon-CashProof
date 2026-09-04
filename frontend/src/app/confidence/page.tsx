"use client";

import { Suspense, useEffect, useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import {
  ApiError,
  fetchBenchmarkConfidence,
  fetchOperationalConfidence,
} from "@/lib/api";
import type {
  BenchmarkConfidenceResponse,
  OperationalConfidenceResponse,
} from "@/lib/types";
import { ConfidenceIntelligenceClient } from "./ConfidenceIntelligenceClient";

export default function ConfidencePage() {
  const [operationalData, setOperationalData] =
    useState<OperationalConfidenceResponse | null>(null);
  const [benchmarkData, setBenchmarkData] =
    useState<BenchmarkConfidenceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadTrigger, setReloadTrigger] = useState(0);

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([
      fetchOperationalConfidence(),
      fetchBenchmarkConfidence(),
    ])
      .then(([opResult, bmResult]) => {
        if (cancelled) return;

        if (opResult.status === "fulfilled") {
          setOperationalData(opResult.value);
        }

        if (bmResult.status === "fulfilled") {
          setBenchmarkData(bmResult.value);
        }

        if (opResult.status === "rejected" && bmResult.status === "rejected") {
          const reason = opResult.reason;
          setError(
            reason instanceof ApiError
              ? `Failed to load confidence data: ${reason.message}`
              : "Could not reach the CashProof API. Start it with `uv run python scripts/run_api.py`.",
          );
        } else {
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Unexpected error occurred.",
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
            Confidence Calibration & Automation Quality
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Statistical calibration (ECE, Brier score), hypothesis strength distributions, and firewall vs belief separation.
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

      {!error && !operationalData && !benchmarkData && (
        <p className="text-sm text-slate-500">
          Loading confidence calibration metrics...
        </p>
      )}

      {(operationalData || benchmarkData) && (
        <Suspense fallback={<p className="text-sm text-slate-500">Loading parameters...</p>}>
          <ConfidenceIntelligenceClient
            operationalData={operationalData}
            benchmarkData={benchmarkData}
          />
        </Suspense>
      )}
    </div>
  );
}
