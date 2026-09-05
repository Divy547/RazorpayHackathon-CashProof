"use client";

import { useState } from "react";
import {
  Bot,
  CheckCircle2,
  Scale,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";

export function HowItWorks() {
  const [activeBranch, setActiveBranch] = useState<"clean" | "ambiguous">("clean");

  const lifecycleStages = [
    { num: "01", name: "Ingest", desc: "Raw settlement records & bank statements" },
    { num: "02", name: "Normalize", desc: "Paise integers, ISO dates, explicit currency" },
    { num: "03", name: "Reconcile", desc: "Structured ref matching in candidate windows" },
    { num: "04", name: "Investigate", desc: "AI triggered only for ambiguous exceptions" },
    { num: "05", name: "Validate", desc: "Mandatory 9-check deterministic gate firewall" },
    { num: "06", name: "Resolve", desc: "AUTO_RESOLVED or routed to Human Review" },
    { num: "07", name: "Audit", desc: "Immutable decision receipts & reviewer logs" },
    { num: "08", name: "Benchmark", desc: "Evaluator-only audit against ground truth" },
  ];

  return (
    <section id="how-it-works" className="py-20 bg-slate-50/60 border-b border-slate-200/70">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-wider text-slate-600">
            Reconciliation Engine
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
            How CashProof Works
          </h2>
          <p className="text-lg text-slate-600">
            A linear eight-stage lifecycle that isolates ambiguity from financial authority.
            AI only activates when deterministic matching encounters exceptions.
          </p>
        </div>

        {/* 8-Stage Progression Strip */}
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {lifecycleStages.map((stage) => (
            <div
              key={stage.num}
              className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm space-y-1.5"
            >
              <div className="font-mono text-xs font-bold text-red-600">{stage.num}</div>
              <div className="text-sm font-bold text-slate-900 leading-tight">{stage.name}</div>
              <div className="text-[11px] text-slate-500 leading-snug">{stage.desc}</div>
            </div>
          ))}
        </div>

        {/* Dual-Branch Interactive Architecture Diagram */}
        <div className="mt-14 rounded-2xl border border-slate-200 bg-white p-6 sm:p-10 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
            <div>
              <h3 className="text-xl font-bold text-slate-900">Branching Execution Flow</h3>
              <p className="text-xs text-slate-500 mt-1">
                Notice how AI is strictly isolated to the ambiguous branch, while the Gate guards both.
              </p>
            </div>

            {/* Branch Selector Toggle */}
            <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100/70 p-1">
              <button
                type="button"
                onClick={() => setActiveBranch("clean")}
                className={`rounded-md px-3.5 py-1.5 text-xs font-semibold transition-all ${
                  activeBranch === "clean"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Branch 1: Clean Exact Match (39%)
              </button>
              <button
                type="button"
                onClick={() => setActiveBranch("ambiguous")}
                className={`rounded-md px-3.5 py-1.5 text-xs font-semibold transition-all ${
                  activeBranch === "ambiguous"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                Branch 2: Ambiguous Exception (61%)
              </button>
            </div>
          </div>

          {/* Diagram Body */}
          <div className="mt-8">
            {activeBranch === "clean" ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                  {/* Step 1 */}
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 space-y-2">
                    <span className="font-mono text-xs font-semibold text-slate-500">STAGE 1</span>
                    <h4 className="text-base font-bold text-slate-900">Ingest & Normalize</h4>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Gateway settlement items paired with bank deposit records. Zero floating-point drift.
                    </p>
                  </div>

                  {/* Step 2 */}
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 space-y-2">
                    <span className="font-mono text-xs font-semibold text-slate-500">STAGE 2</span>
                    <h4 className="text-base font-bold text-slate-900">Deterministic Match</h4>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Single candidate identified via exact structured reference within &plusmn;7 day window.
                    </p>
                  </div>

                  {/* Step 3 */}
                  <div className="rounded-xl border-2 border-emerald-500/80 bg-emerald-50/40 p-5 space-y-2 shadow-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-emerald-800">STAGE 3: FIREWALL</span>
                      <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    </div>
                    <h4 className="text-base font-bold text-emerald-950">Deterministic Gate</h4>
                    <p className="text-xs text-emerald-800 leading-relaxed">
                      All 9 checks evaluated. Bridge, identity, uniqueness, and currency pass 100%.
                    </p>
                  </div>

                  {/* Step 4 */}
                  <div className="rounded-xl border border-emerald-300 bg-emerald-100/50 p-5 space-y-2">
                    <span className="font-mono text-xs font-bold text-emerald-800">OUTCOME</span>
                    <h4 className="text-base font-bold text-emerald-900">AUTO_RESOLVED</h4>
                    <p className="text-xs text-emerald-800 leading-relaxed">
                      Resolved without human intervention. Zero AI involvement. 100% target accuracy.
                    </p>
                  </div>
                </div>

                <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-4 flex items-center justify-between text-xs text-emerald-900">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                    <span>
                      <strong>Deterministic Guarantee:</strong> Clean matches require zero LLM tokens,
                      executing at over 1,380 records per minute with zero false resolutions.
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                  {/* Step 1 */}
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 space-y-2">
                    <span className="font-mono text-xs font-semibold text-slate-500">STAGE 1</span>
                    <h4 className="text-base font-bold text-slate-900">Exception Detected</h4>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Amount mismatch, duplicate references, or unstructured text narration discovered.
                    </p>
                  </div>

                  {/* Step 2 */}
                  <div className="rounded-xl border-2 border-sky-400 bg-sky-50/50 p-5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-sky-800">STAGE 2: BOUNDED AI</span>
                      <Bot className="h-4 w-4 text-sky-600" />
                    </div>
                    <h4 className="text-base font-bold text-sky-950">AI Investigation</h4>
                    <p className="text-xs text-sky-800 leading-relaxed">
                      Model retrieves allowed evidence, inspects candidate pool, explains variances, proposes target set.
                    </p>
                  </div>

                  {/* Step 3 */}
                  <div className="rounded-xl border-2 border-amber-400 bg-amber-50/50 p-5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-amber-800">STAGE 3: FIREWALL</span>
                      <Scale className="h-4 w-4 text-amber-600" />
                    </div>
                    <h4 className="text-base font-bold text-amber-950">Deterministic Gate</h4>
                    <p className="text-xs text-amber-800 leading-relaxed">
                      Gate re-verifies AI proposal against bridge & policy checks. Fails closed on any discrepancy.
                    </p>
                  </div>

                  {/* Step 4 */}
                  <div className="rounded-xl border border-amber-300 bg-amber-100/50 p-5 space-y-2">
                    <span className="font-mono text-xs font-bold text-amber-800">OUTCOME</span>
                    <h4 className="text-base font-bold text-amber-900">HUMAN_REVIEW</h4>
                    <p className="text-xs text-amber-800 leading-relaxed">
                      Presented to human controller with AI hypothesis, gate blocker reason, and one-click review.
                    </p>
                  </div>
                </div>

                <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 flex items-center justify-between text-xs text-amber-900">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0" />
                    <span>
                      <strong>Safety Invariant:</strong> AI never has write access to the ledger.
                      Its proposal is merely input to the Deterministic Gate, which strictly enforces financial compliance.
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
