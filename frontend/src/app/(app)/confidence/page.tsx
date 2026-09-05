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
      {/* Operational Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3B5145]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
            <span>MODEL EVALUATION</span>
            <span className="text-[#CFC9BC]">/</span>
            <span className="text-[#4F514A]">CALIBRATION</span>
          </div>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-[#171816]">
            Confidence Calibration &amp; Automation Quality
          </h1>
          <p className="mt-1 text-sm font-normal text-[#4F514A]">
            Statistical calibration (ECE, Brier score), hypothesis strength distributions, and firewall vs belief separation.
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

      {!error && !operationalData && !benchmarkData && (
        <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs text-[#6B6D64]">
          Loading confidence calibration metrics...
        </div>
      )}

      {(operationalData || benchmarkData) && (
        <Suspense fallback={
          <div className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-8 text-center font-mono text-xs text-[#6B6D64]">
            Loading parameters...
          </div>
        }>
          <ConfidenceIntelligenceClient
            operationalData={operationalData}
            benchmarkData={benchmarkData}
          />
        </Suspense>
      )}
    </div>
  );
}
