"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, Gauge, ShieldAlert, Sparkles } from "lucide-react";

export function ConfidenceRiskControl() {
  return (
    <section id="confidence" className="py-20 bg-[#FFFFFF] border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#F4F6F8] px-2.5 py-1 text-[11px] font-mono text-[#475467]">
              <span>CONFIDENCE & RISK CALIBRATION</span>
            </div>
            <h2 className="text-3xl font-semibold tracking-tight text-[#101828] sm:text-4xl">
              Confidence is belief. The gate is authority.
            </h2>
            <p className="text-base sm:text-lg text-[#475467] leading-relaxed">
              In financial systems, AI confidence cannot authorize a transaction. Even when an LLM
              is 100% confident, the proposal is blocked if monetary bridge invariants fail.
            </p>
          </div>

          <div className="shrink-0">
            <Link
              href="/confidence"
              className="inline-flex items-center gap-2 rounded-lg border border-[#DDE2E7] bg-[#FFFFFF] px-4 py-2.5 text-xs font-semibold text-[#101828] shadow-2xs transition-all hover:bg-[#F4F6F8] hover:border-[#475467]/30"
            >
              <Gauge className="h-4 w-4 text-[#3157D5]" />
              <span>Explore Confidence Intelligence</span>
              <ArrowRight className="h-3.5 w-3.5 text-[#475467]" />
            </Link>
          </div>
        </div>

        {/* 3 Benchmark Calibration Metrics */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="rounded-xl border border-[#DDE2E7] bg-[#F4F6F8]/60 p-6 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-[#475467]">
                Calibration Error (ECE)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#12A67A]/15 text-[#12A67A] font-semibold border border-[#12A67A]/30">
                Well-Calibrated
              </span>
            </div>
            <div className="font-mono text-3xl font-bold text-[#101828] tabular-nums">
              12.4%
            </div>
            <p className="text-xs text-[#475467] leading-relaxed">
              Expected Calibration Error measures reliability between predicted confidence and
              empirical accuracy across 10-bin evaluation.
            </p>
          </div>

          <div className="rounded-xl border border-[#DDE2E7] bg-[#F4F6F8]/60 p-6 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-[#475467]">
                Brier Score
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#12A67A]/15 text-[#12A67A] font-semibold border border-[#12A67A]/30">
                Strict Metric
              </span>
            </div>
            <div className="font-mono text-3xl font-bold text-[#101828] tabular-nums">
              0.0332
            </div>
            <p className="text-xs text-[#475467] leading-relaxed">
              Strictly proper scoring rule for binary outcomes. Near-zero score demonstrates high
              investigator decisiveness without probability drift.
            </p>
          </div>

          <div className="rounded-xl border border-[#DDE2E7] bg-[#F4F6F8]/60 p-6 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-[#475467]">
                High-Conf Precision
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#3157D5]/15 text-[#3157D5] font-semibold border border-[#3157D5]/30">
                Gate Guarded
              </span>
            </div>
            <div className="font-mono text-3xl font-bold text-[#101828] tabular-nums">
              100.0%
            </div>
            <p className="text-xs text-[#475467] leading-relaxed">
              When investigator confidence exceeds 0.90, the deterministic gate ensures zero false
              resolutions ever reach the ledger.
            </p>
          </div>
        </div>

        {/* 2x2 Risk Control Matrix */}
        <div className="mt-12 rounded-2xl border border-[#DDE2E7] bg-[#FFFFFF] shadow-2xs overflow-hidden">
          <div className="bg-[#F4F6F8] px-6 py-4 border-b border-[#DDE2E7] flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-[#3157D5]" />
              <h3 className="text-sm font-semibold text-[#101828]">
                Deterministic Risk Matrix: AI Confidence vs. Gate Evaluation
              </h3>
            </div>
            <span className="text-xs font-mono text-[#475467]">
              Decision Firewall Guarantee
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#DDE2E7]">
            {/* Cell 1: High Conf + Gate Pass */}
            <div className="p-6 sm:p-7 space-y-3 bg-[#FFFFFF]">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#12A67A]">
                  HIGH CONFIDENCE (&ge; 0.90) + GATE PASSED
                </span>
                <span className="font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-[#12A67A]/15 text-[#12A67A] border border-[#12A67A]/30">
                  AUTO RESOLVED
                </span>
              </div>
              <p className="text-xs text-[#475467] leading-relaxed">
                Both investigator confidence and all 9 deterministic invariants align. The settlement
                is finalized automatically with zero human touch. Complete cryptographic audit receipt
                is generated.
              </p>
              <div className="pt-2 flex items-center gap-1.5 text-xs font-mono text-[#12A67A]">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Safe automation path &middot; 39% benchmark rate</span>
              </div>
            </div>

            {/* Cell 2: High Conf + Gate Fail */}
            <div className="p-6 sm:p-7 space-y-3 bg-[#FFFBEB]/30">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#D98B20]">
                  HIGH CONFIDENCE (1.00) + GATE FAILED
                </span>
                <span className="font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-[#D98B20]/15 text-[#D98B20] border border-[#D98B20]/30">
                  HUMAN REVIEW
                </span>
              </div>
              <p className="text-xs text-[#475467] leading-relaxed">
                <strong>Crucial Invariant:</strong> The model asserts 100% certainty, but gross - fees
                &ne; net or candidate reference has duplicates. The Gate halts automation immediately
                and routes the case to a human controller.
              </p>
              <div className="pt-2 flex items-center gap-1.5 text-xs font-mono text-[#D98B20]">
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>Zero model halluncination risk &middot; System fails safe</span>
              </div>
            </div>

            {/* Cell 3: Low Conf + Gate Pass */}
            <div className="p-6 sm:p-7 space-y-3 bg-[#F4F6F8]/40 border-t border-[#DDE2E7]">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#475467]">
                  LOW CONFIDENCE (&lt; 0.90) + GATE PASSED
                </span>
                <span className="font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-[#F4F6F8] text-[#475467] border border-[#DDE2E7]">
                  HUMAN REVIEW
                </span>
              </div>
              <p className="text-xs text-[#475467] leading-relaxed">
                Arithmetic balance passes, but AI investigator expresses uncertainty or relies on
                unstructured narration heuristics. Routed to human reviewer for explicit confirmation.
              </p>
              <div className="pt-2 flex items-center gap-1.5 text-xs font-mono text-[#475467]">
                <Sparkles className="h-3.5 w-3.5 text-[#3157D5]" />
                <span>Investigator abstains &middot; Policy sign-off mandated</span>
              </div>
            </div>

            {/* Cell 4: Low Conf + Gate Fail */}
            <div className="p-6 sm:p-7 space-y-3 bg-[#FEF2F2]/30 border-t border-[#DDE2E7]">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-[#D64545]">
                  LOW CONFIDENCE + GATE FAILED
                </span>
                <span className="font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-[#D64545]/15 text-[#D64545] border border-[#D64545]/30">
                  UNRESOLVED
                </span>
              </div>
              <p className="text-xs text-[#475467] leading-relaxed">
                No matching records found, fee discrepancy unresolved, or candidate pool empty.
                Case terminates closed as UNRESOLVED. No phantom balance entries are created.
              </p>
              <div className="pt-2 flex items-center gap-1.5 text-xs font-mono text-[#D64545]">
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>Fail-closed termination &middot; 10% benchmark rate</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
