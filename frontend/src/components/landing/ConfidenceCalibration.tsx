"use client";

import { useRef } from "react";
import Link from "next/link";
import { ArrowRight, Lock, ShieldAlert, ShieldCheck } from "lucide-react";
import { motion, useScroll, useTransform } from "motion/react";

export function ConfidenceCalibration() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Stage 1: Header and big statement
  const headerOpacity = useTransform(scrollYProgress, [0, 0.15], [0.3, 1]);

  // Stage 2: 3 calibration metric cards reveal
  const metricsOpacity = useTransform(scrollYProgress, [0.15, 0.35], [0, 1]);
  const metricsY = useTransform(scrollYProgress, [0.15, 0.35], [20, 0]);

  // Stage 3 & 4: Invariant Matrix reveal & State B Climax emphasis
  const matrixOpacity = useTransform(scrollYProgress, [0.35, 0.55], [0, 1]);
  const stateBHighlight = useTransform(scrollYProgress, [0.55, 0.75], [0.4, 1]);
  const stateBScale = useTransform(scrollYProgress, [0.55, 0.75], [0.98, 1]);

  return (
    <section
      id="confidence"
      ref={containerRef}
      className="relative h-[280vh] bg-[#F3F0E8] text-[#171816] scroll-mt-20"
    >
      {/* Pinned Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Header & Main Statement */}
        <motion.div style={{ opacity: headerOpacity }} className="mx-auto w-full max-w-6xl space-y-2">
          <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-xs font-mono text-[#62635C] uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#A47C52]" />
              RISK CALIBRATION // PROBABILITY VS INVARIANT
            </span>
            <span>SCROLL TO TRACE INVARIANT LOGIC</span>
            <span className="text-[#A47C52] font-semibold">GATE AS SUPREME AUTHORITY</span>
          </div>

          <div className="pt-2">
            <h2 className="font-display text-2xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#171816] leading-[1.08]">
              CONFIDENCE IS BELIEF. THE GATE IS AUTHORITY.
            </h2>
            <p className="font-mono text-xs sm:text-sm text-[#62635C] leading-relaxed max-w-3xl pt-1">
              Model certainty is an input to investigation, never an authorization.
              Even when an LLM is 100% confident, if the arithmetic bridge fails by one paisa, automation halts.
            </p>
          </div>
        </motion.div>

        {/* Center Main Stage */}
        <div className="mx-auto w-full max-w-6xl my-auto space-y-5">
          {/* Stage 2: 3 Calibration Metrics */}
          <motion.div
            style={{ opacity: metricsOpacity, y: metricsY }}
            className="grid grid-cols-1 md:grid-cols-3 gap-3.5 font-mono"
          >
            <div className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 sm:p-5 space-y-1.5 shadow-xs">
              <div className="flex items-center justify-between text-[10px] text-[#62635C] uppercase">
                <span>Expected Calibration Error</span>
                <span className="text-[#65745F] font-semibold">WELL-CALIBRATED</span>
              </div>
              <div className="text-3xl sm:text-4xl font-bold text-[#171816] tabular-nums">12.4%</div>
              <p className="text-[11px] text-[#62635C] leading-relaxed pt-0.5">
                Low calibration error across 10-bin evaluation ensures model predicted probabilities match empirical reality.
              </p>
            </div>

            <div className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 sm:p-5 space-y-1.5 shadow-xs">
              <div className="flex items-center justify-between text-[10px] text-[#62635C] uppercase">
                <span>Brier Score</span>
                <span className="text-[#65745F] font-semibold">STRICT SCORING</span>
              </div>
              <div className="text-3xl sm:text-4xl font-bold text-[#171816] tabular-nums">0.0332</div>
              <p className="text-[11px] text-[#62635C] leading-relaxed pt-0.5">
                Proper scoring rule for binary outcomes. Near-zero score demonstrates decisive probability predictions.
              </p>
            </div>

            <div className="rounded-xl border border-[#65745F]/40 bg-[#F8F6F0] p-4 sm:p-5 space-y-1.5 shadow-xs">
              <div className="flex items-center justify-between text-[10px] text-[#65745F] font-semibold uppercase">
                <span>High-Conf Precision</span>
                <span className="text-[#65745F]">PERFECT SAFETY</span>
              </div>
              <div className="text-3xl sm:text-4xl font-bold text-[#65745F] tabular-nums">100%</div>
              <p className="text-[11px] text-[#62635C] leading-relaxed pt-0.5">
                When investigator confidence &ge; 0.90, the deterministic Gate ensures zero false claims ever reach the ledger.
              </p>
            </div>
          </motion.div>

          {/* Stage 3 & 4: The Crucial Distinction Grid: High Conf Pass vs High Conf Fail */}
          <motion.div
            style={{ opacity: matrixOpacity }}
            className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] overflow-hidden font-mono text-xs shadow-xs"
          >
            <div className="border-b border-[#D9D5CA] bg-[#EEEAE0] px-5 py-2.5 flex items-center justify-between text-[#62635C]">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-[#A47C52]" />
                <span className="font-bold text-[#171816] uppercase tracking-wider">
                  DETERMINISTIC FIREWALL GUARANTEE
                </span>
              </div>
              <span className="text-[10px]">INVARIANT EVALUATION MATRIX</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#D9D5CA]">
              {/* Left: High Conf + Gate Pass */}
              <div className="p-5 sm:p-6 space-y-3 bg-[#F8F6F0]">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5 text-[10px] text-[#65745F] uppercase font-bold">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>STATE A</span>
                  </div>
                  <div className="text-sm sm:text-base font-bold text-[#171816]">
                    HIGH CONFIDENCE (1.00) + GATE PASS
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-[#EEEAE0] border border-[#65745F]/30 flex items-center justify-between">
                  <span className="text-[#62635C]">DISPOSITION:</span>
                  <span className="font-bold text-[#65745F] uppercase tracking-wider">
                    POTENTIALLY AUTOMATABLE
                  </span>
                </div>

                <p className="text-[#62635C] leading-relaxed text-[11px]">
                  Both investigator confidence and all 9 deterministic invariants align. Arithmetic bridge balances
                  to the exact paisa, currency matches, reference provenance is verified. Safe auto-resolution.
                </p>
              </div>

              {/* Right: High Conf + Gate Fail (Dynamically highlighted on scroll) */}
              <motion.div
                style={{ opacity: stateBHighlight, scale: stateBScale }}
                className="p-5 sm:p-6 space-y-3 bg-[#EEEAE0]/60"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-1.5 text-[10px] text-[#A85F59] uppercase font-bold">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    <span>STATE B // CRITICAL INVARIANT</span>
                  </div>
                  <div className="text-sm sm:text-base font-bold text-[#171816]">
                    HIGH CONFIDENCE (1.00) + GATE FAIL
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-[#F8F6F0] border border-[#A85F59]/50 flex items-center justify-between shadow-xs">
                  <span className="text-[#62635C]">DISPOSITION:</span>
                  <span className="font-bold text-[#A85F59] uppercase tracking-wider">
                    STILL BLOCKED &rarr; HUMAN REVIEW
                  </span>
                </div>

                <p className="text-[#62635C] leading-relaxed text-[11px]">
                  The model is 100% sure, but gross &minus; fee &minus; tax &ne; observed deposit or duplicate records
                  exist. The Gate halts automation immediately. AI confidence is never a gate bypass.
                </p>
              </motion.div>
            </div>
          </motion.div>
        </div>

        {/* Bottom Pinned Footer */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between pt-2 border-t border-[#D9D5CA] text-xs font-mono text-[#62635C]">
          <span>CONFIDENCE METRICS CALCULATED ON 100 SETTLEMENT BENCHMARK</span>
          <Link
            href="/confidence"
            className="inline-flex items-center gap-1.5 text-[#171816] hover:text-[#A47C52] transition-colors font-semibold"
          >
            <span>EXPLORE CONFIDENCE INTELLIGENCE</span>
            <ArrowRight className="h-3.5 w-3.5 text-[#A47C52]" />
          </Link>
        </div>
      </div>
    </section>
  );
}
