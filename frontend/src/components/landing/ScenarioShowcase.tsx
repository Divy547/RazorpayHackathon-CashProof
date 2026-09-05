"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, FileText, ShieldAlert } from "lucide-react";

interface ScenarioItem {
  id: string;
  code: string;
  name: string;
  disposition: "AUTO_RESOLVED" | "HUMAN_REVIEW" | "UNRESOLVED";
  reason: string;
  sampleCaseId: string;
  expectedNet: string;
  grossAmount: string;
  feeAmount: string;
  candidateCount: number;
  matchScore: string;
  evidenceType: string;
  evidenceDetail: string;
  gateResult: "PASSED" | "FAILED";
  gateFailingCheck?: string;
  description: string;
}

export function ScenarioShowcase() {
  const [selectedScenario, setSelectedScenario] = useState<string>("S1");

  const scenarios: Record<string, ScenarioItem> = {
    S1: {
      id: "S1",
      code: "01",
      name: "Clean Structured Match",
      disposition: "AUTO_RESOLVED",
      reason: "Structured reference matches 1:1, candidate amount equals net, candidate within +/- 7 days.",
      sampleCaseId: "set_001ad56f0350",
      expectedNet: "₹976.40",
      grossAmount: "₹1,000.00",
      feeAmount: "₹23.60",
      candidateCount: 1,
      matchScore: "1.00",
      evidenceType: "Structured Reference",
      evidenceDetail: "Gateway ref 'ref_001ad56f0350' matches bank reference exactly within +/- 7 day candidate window.",
      gateResult: "PASSED",
      description:
        "When standard payment gateway references match exactly without monetary variance or duplicate candidates, CashProof resolves the settlement automatically with zero human intervention.",
    },
    S2: {
      id: "S2",
      code: "02",
      name: "Ambiguous Duplicate Reference",
      disposition: "HUMAN_REVIEW",
      reason: "Two distinct ledger entries share the exact same reference, amount, currency, and date window.",
      sampleCaseId: "set_02b31b1f2eb1",
      expectedNet: "₹4,833.54",
      grossAmount: "₹5,000.00",
      feeAmount: "₹166.46",
      candidateCount: 2,
      matchScore: "1.00 (Conflict)",
      evidenceType: "Duplicate Reference",
      evidenceDetail: "Two ledger entries (ent_7a4b and ent_9c1d) share identical reference and net amount. Matcher refuses to guess.",
      gateResult: "FAILED",
      gateFailingCheck: "IDENTITY",
      description:
        "The deterministic matcher refuses to pick a random candidate. Because multiple identical entries exist, the classifier halts automation and routes both candidates to a human controller.",
    },
    S3: {
      id: "S3",
      code: "03",
      name: "Amount Variance / Bridge Mismatch",
      disposition: "HUMAN_REVIEW",
      reason: "Structured reference matches, but candidate net deviates from expected settlement net.",
      sampleCaseId: "set_097af6febc0e",
      expectedNet: "₹3,240.00",
      grossAmount: "₹3,350.00",
      feeAmount: "₹110.00",
      candidateCount: 1,
      matchScore: "0.85 (Variance)",
      evidenceType: "Fee Discrepancy",
      evidenceDetail: "Gateway calculated net is ₹3,240.00, but bank deposit observed is ₹3,290.00 (variance: -₹50.00).",
      gateResult: "FAILED",
      gateFailingCheck: "BRIDGE",
      description:
        "Even when an AI investigator has high confidence that the entry belongs to this settlement, the deterministic Gate blocks auto-resolution because gross minus fees does not balance to the bank deposit.",
    },
    S4: {
      id: "S4",
      code: "04",
      name: "External Reference in Narration",
      disposition: "HUMAN_REVIEW",
      reason: "Reference found only inside unstructured bank narration string within +/- 3 days.",
      sampleCaseId: "set_25d97fae69e5",
      expectedNet: "₹1,845.20",
      grossAmount: "₹1,900.00",
      feeAmount: "₹54.80",
      candidateCount: 1,
      matchScore: "0.92 (Text)",
      evidenceType: "Bank Narration Text",
      evidenceDetail: "Extracted reference 'RZP98234' from remarks string: 'CMS/RZP98234/CORP_SETTLE_09/HDFC'.",
      gateResult: "FAILED",
      gateFailingCheck: "POLICY",
      description:
        "Unstructured text references cannot be blindly trusted for automated booking. Policy strictly mandates human confirmation whenever narration heuristics or regex extractions are used.",
    },
    S5: {
      id: "S5",
      code: "05",
      name: "Customer Alias Heuristic",
      disposition: "HUMAN_REVIEW",
      reason: "Customer alias or merchant name match found in unstructured bank remarks.",
      sampleCaseId: "set_37ad5781a700",
      expectedNet: "₹12,450.00",
      grossAmount: "₹12,800.00",
      feeAmount: "₹350.00",
      candidateCount: 1,
      matchScore: "0.88 (Alias)",
      evidenceType: "Merchant Alias",
      evidenceDetail: "AI Investigator associated 'ACME ENTERPRISES PVT' to merchant account 'ACME-CORP-IN'.",
      gateResult: "FAILED",
      gateFailingCheck: "POLICY",
      description:
        "Fuzzy name matching and natural language aliases are investigated by AI to assemble evidence, but the Gate ensures a human controller approves the final association.",
    },
    S6: {
      id: "S6",
      code: "06",
      name: "Missing Bank Record (Fail-Closed)",
      disposition: "UNRESOLVED",
      reason: "Zero matching entries exist in the candidate pool for this settlement.",
      sampleCaseId: "set_0f9c7aa1c567",
      expectedNet: "₹720.00",
      grossAmount: "₹750.00",
      feeAmount: "₹30.00",
      candidateCount: 0,
      matchScore: "0.00",
      evidenceType: "No Candidates",
      evidenceDetail: "Zero bank credits found within +/- 7 days matching either reference, amount, or narration.",
      gateResult: "FAILED",
      gateFailingCheck: "EMPTY_TARGET_SET",
      description:
        "CashProof fails closed. Instead of guessing or forcing a match, the settlement is classified as UNRESOLVED, preventing phantom balance reconciliations.",
    },
  };

  const active = scenarios[selectedScenario];

  return (
    <section id="scenarios" className="py-20 bg-[#F4F6F8] border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#FFFFFF] px-2.5 py-1 text-[11px] font-mono text-[#475467]">
            <span>ADVERSARIAL SUITE // 6 SCENARIOS</span>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-[#101828] sm:text-4xl">
            Controlled Exception Scenarios
          </h2>
          <p className="text-base sm:text-lg text-[#475467] leading-relaxed">
            Real settlement flows encounter ambiguous references, fee discrepancies, and missing
            bank entries. Here is how CashProof handles each scenario deterministically.
          </p>
        </div>

        {/* Operating Invariant Banner */}
        <div className="mt-8 rounded-xl border border-[#3157D5]/20 bg-[#FFFFFF] p-4 sm:p-5 flex items-start gap-3.5 shadow-2xs">
          <ShieldAlert className="h-5 w-5 text-[#3157D5] mt-0.5 shrink-0" />
          <div className="text-sm text-[#101828]">
            <strong className="font-semibold text-[#101828]">Core Operating Invariant:</strong>{" "}
            <span className="text-[#475467]">
              Uncertainty never becomes automation. It becomes an explicit exception backed by
              immutable evidence.
            </span>
          </div>
        </div>

        {/* Interactive Scenario Layout */}
        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: 6 Scenario Selectors */}
          <div className="lg:col-span-5 space-y-2">
            {Object.values(scenarios).map((s) => {
              const isSelected = s.id === selectedScenario;
              const badgeTone =
                s.disposition === "AUTO_RESOLVED"
                  ? "bg-[#12A67A]/15 text-[#12A67A] border-[#12A67A]/30"
                  : s.disposition === "HUMAN_REVIEW"
                  ? "bg-[#D98B20]/15 text-[#D98B20] border-[#D98B20]/30"
                  : "bg-[#D64545]/15 text-[#D64545] border-[#D64545]/30";

              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setSelectedScenario(s.id)}
                  className={`w-full text-left rounded-xl p-4 transition-all border flex items-center justify-between cursor-pointer ${
                    isSelected
                      ? "bg-[#FFFFFF] border-[#3157D5] shadow-xs ring-1 ring-[#3157D5]"
                      : "bg-[#FFFFFF] border-[#DDE2E7] hover:border-[#475467]/40 hover:bg-[#F4F6F8]/60"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-mono text-xs font-bold ${
                          isSelected ? "text-[#3157D5]" : "text-[#475467]"
                        }`}
                      >
                        {s.code}
                      </span>
                      <span className="text-sm font-semibold text-[#101828]">{s.name}</span>
                    </div>
                    <div className="text-xs text-[#475467] line-clamp-1">{s.reason}</div>
                  </div>

                  <span
                    className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded border shrink-0 ${badgeTone}`}
                  >
                    {s.disposition.replace("_", " ")}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Right Column: Case Artifact Inspector */}
          <div className="lg:col-span-7">
            <div className="rounded-2xl border border-[#DDE2E7] bg-[#FFFFFF] p-6 sm:p-7 shadow-xs space-y-6">
              {/* Artifact Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#DDE2E7] pb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#3157D5]">
                      SCENARIO {active.code}
                    </span>
                    <span className="text-xs text-[#475467]">&middot;</span>
                    <h3 className="text-lg font-semibold text-[#101828]">{active.name}</h3>
                  </div>
                  <span className="font-mono text-xs text-[#475467] mt-1 block">
                    Case Ref: <strong className="text-[#101828]">{active.sampleCaseId}</strong>
                  </span>
                </div>

                <div
                  className={`rounded-full px-3 py-1 text-xs font-mono font-bold border ${
                    active.disposition === "AUTO_RESOLVED"
                      ? "bg-[#12A67A]/15 text-[#12A67A] border-[#12A67A]/30"
                      : active.disposition === "HUMAN_REVIEW"
                      ? "bg-[#D98B20]/15 text-[#D98B20] border-[#D98B20]/30"
                      : "bg-[#D64545]/15 text-[#D64545] border-[#D64545]/30"
                  }`}
                >
                  {active.disposition}
                </div>
              </div>

              {/* Financial & Candidate Data Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="rounded-lg border border-[#DDE2E7] bg-[#F4F6F8]/60 p-3 space-y-0.5">
                  <span className="text-[10px] font-mono uppercase text-[#475467]">Expected Net</span>
                  <div className="font-mono text-sm font-bold text-[#101828] tabular-nums">
                    {active.expectedNet}
                  </div>
                </div>
                <div className="rounded-lg border border-[#DDE2E7] bg-[#F4F6F8]/60 p-3 space-y-0.5">
                  <span className="text-[10px] font-mono uppercase text-[#475467]">Gross / Fee</span>
                  <div className="font-mono text-xs font-medium text-[#101828] tabular-nums">
                    {active.grossAmount} / {active.feeAmount}
                  </div>
                </div>
                <div className="rounded-lg border border-[#DDE2E7] bg-[#F4F6F8]/60 p-3 space-y-0.5">
                  <span className="text-[10px] font-mono uppercase text-[#475467]">Candidates</span>
                  <div className="font-mono text-sm font-bold text-[#101828]">
                    {active.candidateCount} found
                  </div>
                </div>
                <div className="rounded-lg border border-[#DDE2E7] bg-[#F4F6F8]/60 p-3 space-y-0.5">
                  <span className="text-[10px] font-mono uppercase text-[#475467]">Match Score</span>
                  <div className="font-mono text-xs font-bold text-[#3157D5]">
                    {active.matchScore}
                  </div>
                </div>
              </div>

              {/* Behavior Description */}
              <div className="space-y-2">
                <h4 className="text-xs font-mono font-semibold uppercase tracking-wider text-[#475467]">
                  Reconciliation Controller Logic
                </h4>
                <p className="text-sm text-[#475467] leading-relaxed">{active.description}</p>
              </div>

              {/* Evidence & Gate Firewall Strip */}
              <div className="rounded-xl border border-[#DDE2E7] bg-[#F4F6F8] p-4 space-y-3">
                <div className="flex items-start gap-2.5">
                  <FileText className="h-4 w-4 text-[#3157D5] mt-0.5 shrink-0" />
                  <div className="text-xs space-y-0.5">
                    <span className="font-mono font-bold text-[#101828]">
                      EVIDENCE: {active.evidenceType}
                    </span>
                    <p className="text-[#475467] leading-relaxed">{active.evidenceDetail}</p>
                  </div>
                </div>

                <div className="pt-2 border-t border-[#DDE2E7] flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="font-mono text-[#475467]">Gate Invariant Check:</span>
                  {active.gateResult === "PASSED" ? (
                    <span className="inline-flex items-center gap-1 font-mono font-bold text-[#12A67A]">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      ALL 9 INVARIANTS PASSED
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 font-mono font-bold text-[#D64545]">
                      <ShieldAlert className="h-3.5 w-3.5" />
                      GATE: {active.gateFailingCheck} FAILED
                    </span>
                  )}
                </div>
              </div>

              {/* Action Links */}
              <div className="pt-2 flex items-center justify-between border-t border-[#DDE2E7]">
                <Link
                  href={`/cases/${active.sampleCaseId}`}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#3157D5] hover:text-[#3157D5]/80"
                >
                  <span>Inspect Case in Controller</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <Link
                  href="/scenarios"
                  className="text-xs font-medium text-[#475467] hover:text-[#101828]"
                >
                  View all 6 scenarios in benchmark &rarr;
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
