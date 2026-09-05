"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { Bot } from "lucide-react";

export function InvestigatorExperience() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Scroll transforms for the investigation sequence
  const candOpacity = useTransform(scrollYProgress, [0.05, 0.25], [0.3, 1]);
  const toolsOpacity = useTransform(scrollYProgress, [0.25, 0.55], [0, 1]);
  const budgetOpacity = useTransform(scrollYProgress, [0.55, 0.75], [0, 1]);
  const proposalOpacity = useTransform(scrollYProgress, [0.75, 0.95], [0, 1]);

  const candidates = [
    {
      id: "Candidate A",
      ref: "PAY_982341",
      amount: "₹4,833.54",
      date: "2026-03-01",
      status: "Direct Ref Match",
    },
    {
      id: "Candidate B",
      ref: "PAY_982341",
      amount: "₹4,833.54",
      date: "2026-03-01",
      status: "Duplicate Statement Ref",
    },
    {
      id: "Candidate C",
      ref: "CMS_CORP_98",
      amount: "₹4,833.54",
      date: "2026-03-02",
      status: "Narration Heuristic",
    },
  ];

  const toolCalls = [
    { name: "GET CASE CONTEXT", result: "Expected net ₹4,833.54, 1 settlement item, status: CLASSIFIED" },
    { name: "GET CANDIDATES", result: "Found 3 candidate entries matching amount in +/- 7d candidate window" },
    { name: "GET LEDGER ENTRY", result: "Inspected Candidate A & B metadata: identical amounts, differing internal bank sequence" },
    { name: "GET EVIDENCE", result: "Identified UTR match on Candidate A corresponding to gateway batch reference" },
  ];

  return (
    <section
      id="investigator"
      ref={containerRef}
      className="relative h-[280vh] bg-[#F3F0E8] text-[#171816]"
    >
      {/* Sticky Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Header */}
        <div className="mx-auto w-full max-w-6xl">
          <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-xs font-mono text-[#62635C] uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#A47C52]" />
              AI INVESTIGATOR // BOUNDED INVESTIGATION RUNTIME
            </span>
            <span>BUDGET: 5 TOOLS &middot; 4,000 TOKENS</span>
          </div>
        </div>

        {/* Center: When the evidence isn't obvious */}
        <div className="mx-auto w-full max-w-6xl my-auto space-y-8">
          <div className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-widest text-[#A47C52] font-bold">
              AMBIGUOUS CASE RESOLUTION
            </span>
            <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#171816]">
              WHEN THE EVIDENCE ISN&apos;T OBVIOUS.
            </h2>
            <p className="font-mono text-xs sm:text-sm text-[#62635C] max-w-2xl">
              Deterministic software refuses to guess between identical candidates. Bounded AI calls
              read-only investigation tools to synthesize facts.
            </p>
          </div>

          {/* Main Investigation Canvas */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: 3 Ambiguous Candidates */}
            <motion.div
              style={{ opacity: candOpacity }}
              className="lg:col-span-5 space-y-3 font-mono"
            >
              <div className="text-[11px] uppercase tracking-wider text-[#62635C] flex items-center justify-between pb-1 border-b border-[#D9D5CA]">
                <span>Candidate Pool (3 Conflicting Entries)</span>
                <span className="text-[#A47C52] font-bold">AMBIGUOUS</span>
              </div>

              {candidates.map((c, i) => (
                <div
                  key={i}
                  className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-3.5 space-y-1.5 hover:border-[#A47C52]/60 transition-colors shadow-xs"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#171816]">{c.id}</span>
                    <span className="text-[10px] text-[#4E6870] font-semibold">{c.date}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#62635C] text-[11px]">{c.ref}</span>
                    <span className="font-bold text-[#171816] tabular-nums">{c.amount}</span>
                  </div>
                  <div className="text-[10px] text-[#A47C52] font-semibold pt-0.5">{c.status}</div>
                </div>
              ))}
            </motion.div>

            {/* Right: Bounded Tool Calling Loop & Proposal Output */}
            <div className="lg:col-span-7 space-y-4">
              {/* Tool Calling Execution */}
              <motion.div
                style={{ opacity: toolsOpacity }}
                className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 space-y-3 font-mono shadow-xs"
              >
                <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-[#62635C] border-b border-[#D9D5CA] pb-2">
                  <div className="flex items-center gap-2">
                    <Bot className="h-3.5 w-3.5 text-[#A47C52]" />
                    <span className="font-bold text-[#171816]">BOUNDED TOOL EXECUTION</span>
                  </div>
                  <span className="text-[#65745F] font-bold">READ-ONLY</span>
                </div>

                <div className="space-y-2 text-xs">
                  {toolCalls.map((t, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-[#EEEAE0] border border-[#D9D5CA] space-y-0.5"
                    >
                      <div className="flex items-center gap-2 text-[10px] text-[#A47C52]">
                        <span className="h-1 w-1 rounded-full bg-[#A47C52]" />
                        <span className="font-bold">CALL // {t.name}</span>
                      </div>
                      <p className="text-[11px] text-[#62635C] pl-3 leading-relaxed">{t.result}</p>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Proposal & Bounded Enforcement */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono">
                <motion.div
                  style={{ opacity: budgetOpacity }}
                  className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 space-y-1 text-xs shadow-xs"
                >
                  <span className="text-[10px] uppercase text-[#62635C] block">Budget Enforced</span>
                  <div className="font-bold text-[#65745F]">4 / 5 Tools &middot; 2,140 Tokens</div>
                  <p className="text-[10px] text-[#62635C] pt-1">
                    Strict caps prevent runaway execution or loop escalation.
                  </p>
                </motion.div>

                <motion.div
                  style={{ opacity: proposalOpacity }}
                  className="rounded-xl border border-[#A47C52]/40 bg-[#F8F6F0] p-4 space-y-1 text-xs shadow-xs"
                >
                  <span className="text-[10px] uppercase text-[#A47C52] font-bold block">Emitted Output</span>
                  <div className="font-bold text-[#171816]">PROPOSE (Target: Candidate A)</div>
                  <p className="text-[10px] text-[#62635C] pt-1">
                    AI can investigate. AI cannot authorize. Sent to Gate.
                  </p>
                </motion.div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Status */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between text-[11px] font-mono text-[#62635C] border-t border-[#D9D5CA] pt-3">
          <span>AI INVESTIGATION: ZERO WRITE PRIVILEGES</span>
          <span>NEXT: DETERMINISTIC GATE EVALUATION &darr;</span>
        </div>
      </div>
    </section>
  );
}
