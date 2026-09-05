"use client";

import { Suspense, useEffect, useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { ApiError, fetchGateIntelligence } from "@/lib/api";
import type { GateIntelligenceResponse } from "@/lib/types";
import { GateIntelligenceClient } from "./GateIntelligenceClient";

export default function GateIntelligencePage() {
  const [data, setData] = useState<GateIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadTrigger, setReloadTrigger] = useState(0);

  useEffect(() => {
    let cancelled = false;

    fetchGateIntelligence()
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? `Failed to load gate intelligence: ${err.message}`
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
            <span>GATE CONTROL</span>
            <span className="text-[#CFC9BC]">/</span>
            <span className="text-[#4F514A]">DETERMINISTIC AUTHORIZATION</span>
          </div>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-[#171816]">
            Gate Intelligence &amp; Controller Explainability
          </h1>
          <p className="mt-1 text-sm font-normal text-[#4F514A]">
            Authoritative firewall diagnostics, automation blocker ranking, and deterministic eligibility explainability.
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

      {/* Error State */}
      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-4 py-3.5 text-sm text-[#9A514C]">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#9A514C]" />
          <div className="font-mono text-xs">
            <strong className="block font-semibold uppercase tracking-wide">Gate Intelligence Error</strong>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Loading State */}
      {!error && !data && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] py-24 text-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#CFC9BC] border-t-[#3B5145]" />
          <p className="mt-4 font-mono text-xs font-medium uppercase tracking-wider text-[#4F514A]">
            Analyzing deterministic gate evaluations...
          </p>
        </div>
      )}

      {data && (
        <Suspense
          fallback={
            <div className="py-12 text-center font-mono text-xs text-[#6B6D64]">
              Loading parameters...
            </div>
          }
        >
          <GateIntelligenceClient initialData={data} />
        </Suspense>
      )}
    </div>
  );
}
