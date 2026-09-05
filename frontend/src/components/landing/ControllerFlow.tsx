"use client";

import { useState } from "react";
import { CheckCircle2, ChevronRight } from "lucide-react";

interface FlowNode {
  id: string;
  num: string;
  name: string;
  type: "deterministic" | "ai" | "gate" | "terminal";
  input: string;
  logic: string;
  output: string;
  invariants: string;
}

export function ControllerFlow() {
  const [activeStep, setActiveStep] = useState<number>(2); // Default to Reconcile

  const nodes: FlowNode[] = [
    {
      id: "ingest",
      num: "01",
      name: "INGEST",
      type: "deterministic",
      input: "Gateway settlements, fees, taxes & raw bank statement feeds.",
      logic: "Stateless ingestion connectors stream records into repository storage without mutations.",
      output: "Raw immutable source facts stored in append-only format.",
      invariants: "Source facts are immutable. No decoy or synthetic labels leaked.",
    },
    {
      id: "normalize",
      num: "02",
      name: "NORMALIZE",
      type: "deterministic",
      input: "Raw currency amounts, ISO timestamps, and gateway IDs.",
      logic: "Cast floats to integer minor units (paise). Standardize ISO 8601 timestamps and currencies.",
      output: "SettlementItems and BankLedgerEntries with integer minor amounts.",
      invariants: "Zero float arithmetic. Currency is explicit on every single record.",
    },
    {
      id: "reconcile",
      num: "03",
      name: "RECONCILE",
      type: "deterministic",
      input: "Canonical settlement items and bank ledger pool.",
      logic: "Candidate generation window (+/- 7 days for structured references, +/- 3 days for text).",
      output: "MatchCandidates scored with provenance (Structured Ref, Text, Alias).",
      invariants: "Candidate windows only filter potential matches; they are never proof.",
    },
    {
      id: "investigate",
      num: "04",
      name: "INVESTIGATE",
      type: "ai",
      input: "Ambiguous cases (S2-S5): amount variance, duplicate refs, or narration text.",
      logic: "AI Investigator calls read-only tools within 5-tool / 4,000-token budget to synthesize evidence.",
      output: "ResolutionProposal specifying target entry IDs, explanation, and confidence.",
      invariants: "AI has zero ledger write-access. Budgets enforced. Abstains on uncertainty.",
    },
    {
      id: "validate",
      num: "05",
      name: "VALIDATE",
      type: "gate",
      input: "Proposed resolution (from deterministic matcher or AI investigator).",
      logic: "Deterministic GateEvaluation checks 9 invariant rules: identity, bridge, currency, etc.",
      output: "GateEvaluationResult: PASSED or FAILED with exact failing check name.",
      invariants: "Sole authorization firewall. AI confidence is never a gate input.",
    },
    {
      id: "resolve",
      num: "06",
      name: "RESOLVE / REVIEW",
      type: "terminal",
      input: "ReconciliationCase and GateEvaluationResult.",
      logic: "If gate passed: AUTO_RESOLVED. If gate failed or ambiguous: routed to HUMAN_REVIEW.",
      output: "Final immutable Resolution record with auditor signature.",
      invariants: "A ledger entry may be resolved to at most one settlement system-wide.",
    },
    {
      id: "audit",
      num: "07",
      name: "AUDIT",
      type: "terminal",
      input: "Final resolved settlement and full execution trace.",
      logic: "Persist decision receipt linking settlement ID to candidate matches, gate checks, and reviewer.",
      output: "Cryptographic decision receipt for financial controllers and auditors.",
      invariants: "Material decisions remain permanently traceable. Audit receipts are immutable.",
    },
  ];

  const current = nodes[activeStep];

  return (
    <section id="flow" className="py-20 bg-[#F4F6F8] border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#FFFFFF] px-2.5 py-1 text-[11px] font-mono text-[#475467]">
            SYSTEM PIPELINE
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-[#101828] sm:text-4xl">
            The Controller Operating Loop
          </h2>
          <p className="text-base sm:text-lg text-[#475467] leading-relaxed">
            Seven discrete stages ensure that every transaction moves from raw ingestion to immutable audit
            without a single unvalidated AI decision touching the financial ledger.
          </p>
        </div>

        {/* Technical Process Visualization */}
        <div className="mt-12 space-y-8">
          {/* Node Rail */}
          <div className="rounded-lg border border-[#DDE2E7] bg-[#FFFFFF] p-2 shadow-2xs overflow-x-auto">
            <div className="flex items-center min-w-max gap-1">
              {nodes.map((node, idx) => {
                const isActive = idx === activeStep;
                return (
                  <button
                    key={node.id}
                    type="button"
                    onClick={() => setActiveStep(idx)}
                    className={`flex items-center gap-2 rounded px-3 py-2.5 text-xs font-mono transition-all text-left ${
                      isActive
                        ? "bg-[#3157D5] text-white shadow-xs font-bold"
                        : "text-[#475467] hover:bg-[#F4F6F8] hover:text-[#101828]"
                    }`}
                  >
                    <span className={isActive ? "text-white/80" : "text-[#475467]"}>
                      {node.num}
                    </span>
                    <span>{node.name}</span>
                    {idx < nodes.length - 1 && (
                      <ChevronRight
                        className={`h-3 w-3 ml-1 ${isActive ? "text-white/60" : "text-[#DDE2E7]"}`}
                      />
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Detailed Node Inspector Panel */}
          <div className="rounded-lg border border-[#DDE2E7] bg-[#FFFFFF] p-6 sm:p-8 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#DDE2E7] pb-5">
              <div className="flex items-center gap-3">
                <span className="font-mono text-sm font-bold text-[#3157D5] bg-[#3157D5]/10 px-2.5 py-1 rounded">
                  STAGE {current.num}
                </span>
                <h3 className="text-xl font-bold text-[#101828]">{current.name}</h3>
                <span
                  className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold border ${
                    current.type === "ai"
                      ? "bg-[#D98B20]/10 text-[#D98B20] border-[#D98B20]/30"
                      : current.type === "gate"
                      ? "bg-[#12A67A]/10 text-[#12A67A] border-[#12A67A]/30"
                      : "bg-[#F4F6F8] text-[#475467] border-[#DDE2E7]"
                  }`}
                >
                  {current.type === "ai"
                    ? "BOUNDED AI INVESTIGATION"
                    : current.type === "gate"
                    ? "FIREWALL VALIDATION"
                    : "DETERMINISTIC COMPUTE"}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={activeStep === 0}
                  onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
                  className="rounded border border-[#DDE2E7] px-2.5 py-1 text-xs font-mono text-[#475467] hover:bg-[#F4F6F8] disabled:opacity-30"
                >
                  &larr; PREV
                </button>
                <button
                  type="button"
                  disabled={activeStep === nodes.length - 1}
                  onClick={() => setActiveStep((prev) => Math.min(nodes.length - 1, prev + 1))}
                  className="rounded border border-[#DDE2E7] px-2.5 py-1 text-xs font-mono text-[#475467] hover:bg-[#F4F6F8] disabled:opacity-30"
                >
                  NEXT &rarr;
                </button>
              </div>
            </div>

            {/* Technical Detail Grid */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
              <div className="space-y-1.5 rounded border border-[#DDE2E7] bg-[#F4F6F8]/50 p-4">
                <span className="text-[10px] uppercase font-bold text-[#475467] tracking-wider">
                  Input Stream
                </span>
                <p className="text-xs font-sans text-[#101828] leading-relaxed pt-1">
                  {current.input}
                </p>
              </div>

              <div className="space-y-1.5 rounded border border-[#DDE2E7] bg-[#F4F6F8]/50 p-4">
                <span className="text-[10px] uppercase font-bold text-[#475467] tracking-wider">
                  Transformation Logic
                </span>
                <p className="text-xs font-sans text-[#101828] leading-relaxed pt-1">
                  {current.logic}
                </p>
              </div>

              <div className="space-y-1.5 rounded border border-[#DDE2E7] bg-[#F4F6F8]/50 p-4">
                <span className="text-[10px] uppercase font-bold text-[#475467] tracking-wider">
                  Emitted Output
                </span>
                <p className="text-xs font-sans text-[#101828] leading-relaxed pt-1">
                  {current.output}
                </p>
              </div>
            </div>

            {/* Enforced Invariant Bar */}
            <div className="mt-4 rounded border border-[#3157D5]/20 bg-[#3157D5]/5 p-3.5 flex items-center justify-between text-xs text-[#3157D5]">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-[#3157D5]" />
                <span className="font-mono text-[11px]">
                  <strong>ENFORCED INVARIANT:</strong> {current.invariants}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
