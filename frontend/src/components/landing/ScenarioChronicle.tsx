"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { FileText } from "lucide-react";
import { motion, useMotionValueEvent, useScroll } from "motion/react";
import { getCaseDetail } from "@/lib/data";
import { formatMinor, formatSignedMinor } from "@/lib/format";

// S3's expected/observed/variance/gross/fee are derived from the
// authoritative demo dataset (not hardcoded) so they can never drift out of
// sync with each other, or with what /cases/set_72d8894a05e4 itself shows,
// or with the same case's numbers already used elsewhere on this landing
// page (Hero, HeroReconciliationArtifact, DiscrepancyReveal). Throws rather
// than falling back to a fabricated value if the checked-in demo data is
// ever missing this case.
function requireCaseDetail(settlementId: string) {
  const detail = getCaseDetail(settlementId);
  if (!detail) {
    throw new Error(`ScenarioChronicle: expected case ${settlementId} to exist in demo-data.json`);
  }
  return detail;
}

interface Scenario {
  id: string;
  code: string;
  name: string;
  caseId: string;
  expected: string;
  gross: string;
  fee: string;
  observed: string;
  variance: string;
  evidence: string;
  checks: { name: string; pass: boolean }[];
  outcome: "AUTO_RESOLVED" | "HUMAN_REVIEW" | "UNRESOLVED";
  reason: string;
}

export function ScenarioChronicle() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Scrub active scenario with scroll progress
  useMotionValueEvent(scrollYProgress, "change", (latest) => {
    const idx = Math.min(5, Math.max(0, Math.floor(latest * 6)));
    setSelectedIdx(idx);
  });

  const s3Case = requireCaseDetail("set_72d8894a05e4");

  const scenarios: Scenario[] = [
    {
      id: "S1",
      code: "01",
      name: "CLEAN EXACT MATCH",
      caseId: "set_001ad56f0350",
      expected: "₹976.40",
      gross: "₹1,000.00",
      fee: "₹23.60",
      observed: "₹976.40",
      variance: "₹0.00",
      evidence: "Gateway ref 'PAY_001' matched bank statement reference 1:1 within +/- 7 days.",
      checks: [
        { name: "IDENTITY", pass: true },
        { name: "BRIDGE", pass: true },
        { name: "CURRENCY", pass: true },
        { name: "UNIQUENESS", pass: true },
      ],
      outcome: "AUTO_RESOLVED",
      reason: "All 9 invariants pass. Zero monetary variance or candidate conflict.",
    },
    {
      id: "S2",
      code: "02",
      name: "AMBIGUOUS DUPLICATE REFERENCE",
      caseId: "set_02b31b1f2eb1",
      expected: "₹4,833.54",
      gross: "₹5,000.00",
      fee: "₹166.46",
      observed: "₹4,833.54",
      variance: "₹0.00",
      evidence: "Two identical ledger entries share exact amount and reference. Matcher halts.",
      checks: [
        { name: "IDENTITY", pass: false },
        { name: "BRIDGE", pass: true },
        { name: "CURRENCY", pass: true },
        { name: "UNIQUENESS", pass: false },
      ],
      outcome: "HUMAN_REVIEW",
      reason: "Duplicate candidate conflict. Deterministic code refuses to guess.",
    },
    {
      id: "S3",
      code: "03",
      name: "AMOUNT MISMATCH / BRIDGE VARIANCE",
      caseId: "set_72d8894a05e4",
      // Sourced from the authoritative demo case, not hardcoded - expected,
      // observed, and variance are guaranteed mathematically consistent
      // (variance = expected - observed) because all three come from the
      // same CaseDetail record instead of independently typed literals.
      expected: formatMinor(s3Case.expected_net_minor, s3Case.currency),
      gross: formatMinor(s3Case.bridge.gross_minor, s3Case.currency),
      fee: formatMinor(s3Case.bridge.fee_minor, s3Case.currency),
      observed: formatMinor(s3Case.observed_net_minor, s3Case.currency),
      variance: formatSignedMinor(s3Case.delta_minor, s3Case.currency),
      evidence: "Gateway reference matches, but bank deposit deviates from calculated bridge.",
      checks: [
        { name: "IDENTITY", pass: true },
        { name: "BRIDGE", pass: false },
        { name: "CURRENCY", pass: true },
        { name: "UNIQUENESS", pass: true },
      ],
      outcome: "HUMAN_REVIEW",
      reason: "Gross minus fees does not balance to bank credit. Gate halts automation.",
    },
    {
      id: "S4",
      code: "04",
      name: "UNSTRUCTURED EXTERNAL REFERENCE",
      caseId: "set_25d97fae69e5",
      expected: "₹1,845.20",
      gross: "₹1,900.00",
      fee: "₹54.80",
      observed: "₹1,845.20",
      variance: "₹0.00",
      evidence: "Reference extracted from unstructured bank narration string: 'CMS/RZP98234/CORP'.",
      checks: [
        { name: "IDENTITY", pass: true },
        { name: "BRIDGE", pass: true },
        { name: "POLICY", pass: false },
        { name: "UNIQUENESS", pass: true },
      ],
      outcome: "HUMAN_REVIEW",
      reason: "Policy check mandates human sign-off on text regex / narration heuristics.",
    },
    {
      id: "S5",
      code: "05",
      name: "CUSTOMER ALIAS HEURISTIC",
      caseId: "set_37ad5781a700",
      expected: "₹12,450.00",
      gross: "₹12,800.00",
      fee: "₹350.00",
      observed: "₹12,450.00",
      variance: "₹0.00",
      evidence: "Fuzzy alias match: 'ACME ENTERPRISES PVT' correlated to merchant account.",
      checks: [
        { name: "IDENTITY", pass: true },
        { name: "BRIDGE", pass: true },
        { name: "POLICY", pass: false },
        { name: "UNIQUENESS", pass: true },
      ],
      outcome: "HUMAN_REVIEW",
      reason: "Fuzzy text associations require human controller authorization.",
    },
    {
      id: "S6",
      code: "06",
      name: "MISSING RECORD (FAIL-CLOSED)",
      caseId: "set_0f9c7aa1c567",
      expected: "₹720.00",
      gross: "₹750.00",
      fee: "₹30.00",
      observed: "None",
      variance: "-₹720.00",
      evidence: "Zero bank credits found within +/- 7 days matching either amount or reference.",
      checks: [
        { name: "IDENTITY", pass: false },
        { name: "BRIDGE", pass: false },
        { name: "TARGET SET", pass: false },
        { name: "UNIQUENESS", pass: true },
      ],
      outcome: "UNRESOLVED",
      reason: "Empty target set. Fails closed to avoid phantom ledger balances.",
    },
  ];

  const active = scenarios[selectedIdx];

  return (
    <section
      id="scenarios"
      ref={containerRef}
      className="relative h-[380vh] bg-[#F3F0E8] text-[#171816] scroll-mt-20"
    >
      {/* Pinned Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Header */}
        <div className="mx-auto w-full max-w-6xl space-y-2">
          <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-xs font-mono text-[#62635C] uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#A47C52]" />
              ADVERSARIAL SUITE // 6 CONTROLLED SCENARIOS
            </span>
            <span className="hidden sm:inline">SCROLL TO SCRUB SCENARIOS (S1 &rarr; S6)</span>
            <span className="text-[#A47C52] font-semibold">SCENARIO {active.id}</span>
          </div>

          <div className="pt-1">
            <h2 className="font-display text-2xl sm:text-4xl font-medium tracking-tight text-[#171816]">
              Inspect Each Scenario in Motion
            </h2>
            <p className="font-mono text-xs text-[#62635C]">
              Scrolling scrubs through edge cases. Observe how identity, bridge, policy, and target-set invariants evaluate real settlement cases.
            </p>
          </div>
        </div>

        {/* Center Main Stage */}
        <div className="mx-auto w-full max-w-6xl my-auto space-y-5">
          {/* 6 Scenario Selector Buttons / Scrubbing Indicators */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 font-mono text-xs">
            {scenarios.map((s, idx) => {
              const isSelected = idx === selectedIdx;

              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setSelectedIdx(idx)}
                  className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer space-y-1 shadow-xs ${
                    isSelected
                      ? "border-[#A47C52] bg-[#EEEAE0] ring-1 ring-[#A47C52]/50"
                      : "border-[#D9D5CA] bg-[#F8F6F0] hover:border-[#A47C52]/40 text-[#62635C]"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px]">
                    <span className={isSelected ? "text-[#A47C52] font-bold" : "text-[#62635C]"}>
                      {s.id}
                    </span>
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        s.outcome === "AUTO_RESOLVED"
                          ? "bg-[#65745F]"
                          : s.outcome === "HUMAN_REVIEW"
                          ? "bg-[#A47C52]"
                          : "bg-[#A85F59]"
                      }`}
                    />
                  </div>
                  <div
                    className={`text-[11px] font-bold truncate ${
                      isSelected ? "text-[#171816]" : "text-[#62635C]"
                    }`}
                  >
                    {s.name}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Real Controller Case Artifact */}
          <motion.div
            key={active.id}
            initial={{ opacity: 0.6, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 sm:p-6 space-y-5 font-mono shadow-xs"
          >
            {/* Artifact Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#D9D5CA] pb-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-[#A47C52] font-bold">CASE ARTIFACT // {active.id}</span>
                  <span className="text-[#62635C]">&middot;</span>
                  <span className="text-[#171816] font-semibold">{active.name}</span>
                </div>
                <div className="text-xs text-[#62635C]">
                  Case ID: <strong className="text-[#171816]">{active.caseId}</strong>
                </div>
              </div>

              <div
                className={`px-3 py-1 rounded-md border text-xs font-bold ${
                  active.outcome === "AUTO_RESOLVED"
                    ? "border-[#65745F]/40 bg-[#65745F]/10 text-[#65745F]"
                    : active.outcome === "HUMAN_REVIEW"
                    ? "border-[#A47C52]/40 bg-[#A47C52]/10 text-[#A47C52]"
                    : "border-[#A85F59]/40 bg-[#A85F59]/10 text-[#A85F59]"
                }`}
              >
                {active.outcome}
              </div>
            </div>

            {/* Financial Telemetry Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                <span className="text-[10px] text-[#62635C] block">EXPECTED NET</span>
                <span className="text-sm font-bold text-[#171816] tabular-nums">
                  {active.expected}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                <span className="text-[10px] text-[#62635C] block">OBSERVED CREDIT</span>
                <span className="text-sm font-bold text-[#171816] tabular-nums">
                  {active.observed}
                </span>
              </div>
              <div
                className={`p-3 rounded-xl bg-[#EEEAE0] border ${
                  active.variance !== "₹0.00" ? "border-[#A85F59]/50" : "border-[#D9D5CA]"
                }`}
              >
                <span
                  className={`text-[10px] block ${
                    active.variance !== "₹0.00" ? "text-[#A85F59] font-bold" : "text-[#62635C]"
                  }`}
                >
                  VARIANCE
                </span>
                <span
                  className={`text-sm font-bold tabular-nums ${
                    active.variance !== "₹0.00" ? "text-[#A85F59]" : "text-[#65745F]"
                  }`}
                >
                  {active.variance}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                <span className="text-[10px] text-[#62635C] block">GROSS / FEE</span>
                <span className="text-xs font-bold text-[#171816] tabular-nums">
                  {active.gross} / {active.fee}
                </span>
              </div>
            </div>

            {/* Evidence & Gate Firewall Strip */}
            <div className="p-3.5 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA] space-y-2.5 text-xs">
              <div className="flex items-start gap-2.5">
                <FileText className="h-4 w-4 text-[#A47C52] shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <span className="font-bold text-[#171816]">PROVENANCE EVIDENCE</span>
                  <p className="text-[#62635C] leading-relaxed">{active.evidence}</p>
                </div>
              </div>

              <div className="pt-2 border-t border-[#D9D5CA] flex flex-wrap items-center justify-between gap-3 text-[11px]">
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                  {active.checks.map((c) => (
                    <span key={c.name} className="flex items-center gap-1.5">
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          c.pass ? "bg-[#65745F]" : "bg-[#A85F59]"
                        }`}
                      />
                      <span className={c.pass ? "text-[#62635C]" : "text-[#A85F59] font-bold"}>
                        {c.name}: {c.pass ? "PASS" : "FAIL"}
                      </span>
                    </span>
                  ))}
                </div>

                <span className="text-[#A47C52] font-semibold">{active.reason}</span>
              </div>
            </div>

            {/* Controller Case Link */}
            <div className="pt-1 flex items-center justify-between text-xs border-t border-[#D9D5CA]">
              <Link
                href={`/cases/${active.caseId}`}
                className="text-[#A47C52] hover:text-[#171816] transition-colors font-semibold"
              >
                Inspect Case in Controller &rarr;
              </Link>
              <Link href="/scenarios" className="text-[#62635C] hover:text-[#171816] transition-colors">
                View All 6 Controlled Scenarios &rarr;
              </Link>
            </div>
          </motion.div>
        </div>

        {/* Bottom Pinned Footer */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between text-[11px] font-mono text-[#62635C] border-t border-[#D9D5CA] pt-3">
          <span>SCENARIO SCRUBBING: DETERMINISTIC GROUND TRUTH ADVERSARIAL MATRIX</span>
          <span>CASES {active.id} OF 6</span>
        </div>
      </div>
    </section>
  );
}
