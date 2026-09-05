"use client";

import { useRef } from "react";
import { Lock } from "lucide-react";
import { motion, useScroll, useTransform } from "motion/react";

export function SafetyConstitution() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Stage 1: Eyebrow and first half of assertion
  const headerOpacity = useTransform(scrollYProgress, [0, 0.15], [0.3, 1]);
  const title1Opacity = useTransform(scrollYProgress, [0.05, 0.25], [0.4, 1]);

  // Stage 2: Second half of assertion "IT CANNOT REDEFINE THE CASE"
  const title2Opacity = useTransform(scrollYProgress, [0.22, 0.42], [0.2, 1]);

  // Stage 3: The AI CAN and AI CANNOT columns reveal
  const cardsOpacity = useTransform(scrollYProgress, [0.40, 0.65], [0, 1]);
  const cardsY = useTransform(scrollYProgress, [0.40, 0.65], [25, 0]);

  const aiCan = [
    "Inspect allowed source financial facts, bank feeds, and candidate pools",
    "Retrieve related gateway settlement items within defined candidate windows",
    "Compare candidate entries across timestamps, amounts, and references",
    "Investigate ambiguity in fee deductions, GST schedules, and taxes",
    "Explain discrepancies in plain English for financial controllers",
    "Propose a candidate target record set with explicit confidence score",
    "Abstain explicitly when evidence is insufficient, ambiguous, or conflicting",
  ];

  const aiCannot = [
    "Change immutable source facts, bank statements, or ingested feed rows",
    "Change monetary values (amounts, gross, fees, taxes, or expected nets)",
    "Override, bypass, or relax any of the nine deterministic gate checks",
    "Approve or authorize its own resolution proposal",
    "Move money, initiate bank transfers, or trigger gateway settlements",
    "Issue refunds or credit adjustments to reconcile discrepancies",
    "Post arbitrary journals or mutate ledger state outside Gate approval",
  ];

  return (
    <section
      id="safety"
      ref={containerRef}
      className="relative h-[280vh] bg-[#F3F0E8] text-[#171816] scroll-mt-20"
    >
      {/* Pinned Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Massive Typographic Assertion */}
        <div className="mx-auto w-full max-w-6xl space-y-3">
          <motion.div
            style={{ opacity: headerOpacity }}
            className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#62635C]"
          >
            <Lock className="h-3.5 w-3.5 text-[#A47C52]" />
            <span>OPERATIONAL BOUNDARIES // PERMISSION FIREWALL</span>
          </motion.div>

          <h2 className="font-display text-2xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#171816] leading-[1.08]">
            <motion.span style={{ opacity: title1Opacity }} className="block">
              THE MODEL CAN REASON ABOUT THE CASE.
            </motion.span>
            <motion.span style={{ opacity: title2Opacity }} className="block text-[#62635C]">
              IT CANNOT REDEFINE THE CASE.
            </motion.span>
          </h2>

          <p className="font-mono text-xs text-[#62635C] leading-relaxed max-w-2xl">
            In CashProof, AI never touches the ledger directly. Its role is strictly forensic and investigative.
            Monetary authorization remains the sole property of deterministic code and verified human controllers.
          </p>
        </div>

        {/* Clean Typographic Split (AI CAN vs AI CANNOT) */}
        <motion.div
          style={{ opacity: cardsOpacity, y: cardsY }}
          className="mx-auto w-full max-w-6xl my-auto grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs"
        >
          {/* AI CAN */}
          <div className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 sm:p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-2.5">
              <span className="text-xs font-bold tracking-wider uppercase text-[#65745F]">
                AI CAN // FORENSIC SCOPE
              </span>
              <span className="text-[10px] text-[#62635C] px-2 py-0.5 rounded-md bg-[#EEEAE0] border border-[#D9D5CA] font-semibold">
                READ-ONLY ACCESS
              </span>
            </div>

            <ul className="space-y-2.5">
              {aiCan.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#65745F] mt-1.5 shrink-0" />
                  <span className="text-[#171816] leading-relaxed text-[11px]">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* AI CANNOT */}
          <div className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 sm:p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-2.5">
              <span className="text-xs font-bold tracking-wider uppercase text-[#A85F59]">
                AI CANNOT // STRICT FIREWALL
              </span>
              <span className="text-[10px] text-[#A85F59] px-2 py-0.5 rounded-md bg-[#A85F59]/10 border border-[#A85F59]/30 font-bold">
                ZERO AUTHORIZATION
              </span>
            </div>

            <ul className="space-y-2.5">
              {aiCannot.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#A85F59] mt-1.5 shrink-0" />
                  <span className="text-[#62635C] leading-relaxed text-[11px]">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </motion.div>

        {/* Bottom Safety Guarantee Strip */}
        <div className="mx-auto w-full max-w-6xl flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] px-4 py-2.5 text-[11px] font-mono text-[#62635C] shadow-xs">
          <span className="text-[#171816] font-semibold">
            FAIL-CLOSED GUARANTEE: SYSTEM TERMINATES CLOSED ON ANY GATE INVARIANT FAILURE
          </span>
          <span>CASHPROOF AGENTS CONSTITUTION v1.0.0</span>
        </div>
      </div>
    </section>
  );
}
