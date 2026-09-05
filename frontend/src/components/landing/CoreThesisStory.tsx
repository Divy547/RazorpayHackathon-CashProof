"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { Lock } from "lucide-react";

export function CoreThesisStory() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Moment 1: Certainty
  const m1Opacity = useTransform(scrollYProgress, [0, 0.1, 0.28, 0.35], [0, 1, 1, 0]);
  const m1Scale = useTransform(scrollYProgress, [0, 0.1, 0.28, 0.35], [0.95, 1, 1, 0.95]);

  // Moment 2: Ambiguity
  const m2Opacity = useTransform(scrollYProgress, [0.33, 0.42, 0.62, 0.69], [0, 1, 1, 0]);
  const m2Scale = useTransform(scrollYProgress, [0.33, 0.42, 0.62, 0.69], [0.95, 1, 1, 0.95]);

  // Moment 3: Evidence
  const m3Opacity = useTransform(scrollYProgress, [0.67, 0.75, 0.88, 0.93], [0, 1, 1, 0]);
  const m3Scale = useTransform(scrollYProgress, [0.67, 0.75, 0.88, 0.93], [0.95, 1, 1, 0.95]);

  // Climax: AI Investigates. Deterministic Software Authorizes.
  const climaxOpacity = useTransform(scrollYProgress, [0.91, 0.97, 1], [0, 1, 1]);
  const climaxScale = useTransform(scrollYProgress, [0.91, 0.98], [0.96, 1]);

  return (
    <section
      id="thesis"
      ref={containerRef}
      className="relative h-[380vh] bg-[#F3F0E8] text-[#171816]"
    >
      {/* Sticky Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Eyebrow */}
        <div className="mx-auto w-full max-w-6xl">
          <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-xs font-mono text-[#62635C] uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#A47C52]" />
              THE CASHPROOF CONSTITUTION // THREE PILLARS
            </span>
            <span>SCROLL TO UNPACK PHILOSOPHY</span>
          </div>
        </div>

        {/* Center: 3 Sequential Moments + Climax */}
        <div className="relative mx-auto w-full max-w-5xl my-auto h-[480px] flex items-center justify-center">
          {/* MOMENT 1: CERTAINTY */}
          <motion.div
            style={{ opacity: m1Opacity, scale: m1Scale }}
            className="absolute inset-0 flex flex-col justify-center space-y-6 text-center sm:text-left"
          >
            <div className="space-y-2">
              <span className="font-mono text-xs uppercase tracking-widest text-[#65745F] font-bold">
                MOMENT 01 // CERTAINTY
              </span>
              <h2 className="font-display text-3xl sm:text-5xl lg:text-6xl font-medium tracking-tight text-[#171816]">
                USE DETERMINISTIC SOFTWARE FOR CERTAINTY.
              </h2>
              <p className="font-mono text-xs sm:text-sm text-[#62635C] max-w-2xl">
                Monetary truth belongs to exact integer arithmetic. Zero floats. Zero probabilistic drift.
              </p>
            </div>

            {/* Interactive Settlement Bridge Visualization */}
            <div className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-6 sm:p-8 space-y-4 font-mono shadow-xs">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#62635C] border-b border-[#D9D5CA] pb-3">
                <span>AUTHORITATIVE SETTLEMENT BRIDGE</span>
                <span className="text-[#65745F] font-semibold">GST 18% IMMUTABLE</span>
              </div>

              <div className="text-sm sm:text-lg text-[#171816] font-bold tracking-tight">
                gross &minus; fee &minus; tax_on_fee &minus; netted_refund + adjustment = net
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 text-xs">
                <div className="p-2.5 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                  <span className="text-[#62635C] block text-[10px]">GROSS</span>
                  <span className="font-bold text-[#171816]">₹5,000.00</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                  <span className="text-[#62635C] block text-[10px]">FEE</span>
                  <span className="font-bold text-[#171816]">-₹141.07</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                  <span className="text-[#62635C] block text-[10px]">TAX (18%)</span>
                  <span className="font-bold text-[#171816]">-₹25.39</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                  <span className="text-[#62635C] block text-[10px]">REFUNDS</span>
                  <span className="font-bold text-[#171816]">-₹0.00</span>
                </div>
                <div className="p-2.5 rounded-xl bg-[#EEEAE0] border border-[#65745F]/40 col-span-2 sm:col-span-1">
                  <span className="text-[#65745F] font-bold block text-[10px]">NET DEPOSIT</span>
                  <span className="font-bold text-[#65745F]">₹4,833.54</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* MOMENT 2: AMBIGUITY */}
          <motion.div
            style={{ opacity: m2Opacity, scale: m2Scale }}
            className="absolute inset-0 flex flex-col justify-center space-y-6 text-center sm:text-left"
          >
            <div className="space-y-2">
              <span className="font-mono text-xs uppercase tracking-widest text-[#A47C52] font-bold">
                MOMENT 02 // AMBIGUITY
              </span>
              <h2 className="font-display text-3xl sm:text-5xl lg:text-6xl font-medium tracking-tight text-[#171816]">
                USE AI FOR AMBIGUITY.
              </h2>
              <p className="font-mono text-xs sm:text-sm text-[#62635C] max-w-2xl">
                When multiple bank entries share identical amounts or references are buried in narration text,
                deterministic software halts. Bounded AI investigates.
              </p>
            </div>

            {/* Ambiguous Records Pool Visual */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
              <div className="rounded-xl border border-[#A47C52]/40 bg-[#F8F6F0] p-4 space-y-2 text-left shadow-xs">
                <div className="flex items-center justify-between text-[10px] text-[#A47C52] font-bold">
                  <span>CANDIDATE 01</span>
                  <span>CONFLICT</span>
                </div>
                <div className="font-bold text-base text-[#171816]">₹4,833.54</div>
                <div className="text-[11px] text-[#62635C]">REF: PAY_982341 (HDFC)</div>
                <div className="text-[10px] text-[#4E6870]">Identical amount &amp; ref</div>
              </div>

              <div className="rounded-xl border border-[#A47C52]/40 bg-[#F8F6F0] p-4 space-y-2 text-left shadow-xs">
                <div className="flex items-center justify-between text-[10px] text-[#A47C52] font-bold">
                  <span>CANDIDATE 02</span>
                  <span>CONFLICT</span>
                </div>
                <div className="font-bold text-base text-[#171816]">₹4,833.54</div>
                <div className="text-[11px] text-[#62635C]">REF: PAY_982341 (HDFC)</div>
                <div className="text-[10px] text-[#4E6870]">Duplicate entry in statement</div>
              </div>

              <div className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 space-y-2 text-left shadow-xs">
                <div className="flex items-center justify-between text-[10px] text-[#62635C]">
                  <span>CANDIDATE 03</span>
                  <span>TEXT ALIAS</span>
                </div>
                <div className="font-bold text-base text-[#171816]">₹4,833.54</div>
                <div className="text-[11px] text-[#62635C]">CMS/ACME_CORP/9823</div>
                <div className="text-[10px] text-[#A47C52]">Narration heuristic match</div>
              </div>
            </div>
          </motion.div>

          {/* MOMENT 3: EVIDENCE */}
          <motion.div
            style={{ opacity: m3Opacity, scale: m3Scale }}
            className="absolute inset-0 flex flex-col justify-center space-y-6 text-center sm:text-left"
          >
            <div className="space-y-2">
              <span className="font-mono text-xs uppercase tracking-widest text-[#4E6870] font-bold">
                MOMENT 03 // EVIDENCE
              </span>
              <h2 className="font-display text-3xl sm:text-5xl lg:text-6xl font-medium tracking-tight text-[#171816]">
                USE EVIDENCE TO EXPLAIN THE DECISION.
              </h2>
              <p className="font-mono text-xs sm:text-sm text-[#62635C] max-w-2xl">
                Every settlement resolution generates an unalterable audit receipt linking source records,
                gate evaluations, and human sign-offs.
              </p>
            </div>

            {/* Cryptographic Provenance Chain Visual */}
            <div className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-6 space-y-4 font-mono text-xs shadow-xs">
              <div className="flex items-center justify-between text-[10px] text-[#62635C] border-b border-[#D9D5CA] pb-2">
                <span>AUDIT RECEIPT: rec_098234af</span>
                <span className="text-[#65745F] font-semibold">CRYPTOGRAPHIC PROVENANCE</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                  <span className="text-[#62635C] text-[10px] block">SOURCE FACT</span>
                  <span className="font-bold text-[#171816]">set_02b31b1f2eb1</span>
                  <span className="text-[10px] text-[#4E6870] block pt-1">Immutable Gateway Batch</span>
                </div>
                <div className="p-3 rounded-xl bg-[#EEEAE0] border border-[#D9D5CA]">
                  <span className="text-[#62635C] text-[10px] block">TARGET ENTRY</span>
                  <span className="font-bold text-[#171816]">ent_7a4b8812</span>
                  <span className="text-[10px] text-[#4E6870] block pt-1">Bank Statement Credit</span>
                </div>
                <div className="p-3 rounded-xl bg-[#EEEAE0] border border-[#65745F]/40">
                  <span className="text-[#65745F] font-bold text-[10px] block">GATE EVALUATION</span>
                  <span className="font-bold text-[#65745F]">ALL 9 PASSED</span>
                  <span className="text-[10px] text-[#62635C] block pt-1">Monetary Integrity Intact</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* VISUAL CLIMAX: AI INVESTIGATES. DETERMINISTIC SOFTWARE AUTHORIZES. */}
          <motion.div
            style={{ opacity: climaxOpacity, scale: climaxScale }}
            className="absolute inset-0 flex flex-col justify-center items-center text-center space-y-6"
          >
            <div className="inline-flex items-center gap-2 rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] px-4 py-1.5 font-mono text-xs uppercase tracking-widest text-[#A47C52] font-semibold shadow-xs">
              <Lock className="h-3.5 w-3.5" />
              <span>THE NON-NEGOTIABLE CORE LAW</span>
            </div>

            <div className="space-y-3">
              <h2 className="font-display text-4xl sm:text-6xl lg:text-7xl font-medium tracking-tight text-[#171816] leading-[1.08]">
                AI INVESTIGATES.
                <br />
                DETERMINISTIC SOFTWARE
                <br />
                AUTHORIZES.
              </h2>
              <p className="font-mono text-xs sm:text-sm uppercase tracking-widest text-[#62635C] max-w-xl mx-auto pt-2">
                The model can reason about the case. It cannot redefine the case.
              </p>
            </div>
          </motion.div>
        </div>

        {/* Bottom Pinned Footer */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between text-[11px] font-mono text-[#62635C] border-t border-[#D9D5CA] pt-3">
          <span>01 CERTAINTY &middot; 02 AMBIGUITY &middot; 03 EVIDENCE</span>
          <span>CASHPROOF ARCHITECTURE</span>
        </div>
      </div>
    </section>
  );
}
