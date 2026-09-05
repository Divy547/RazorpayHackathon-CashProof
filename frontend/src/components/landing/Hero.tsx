"use client";

import Link from "next/link";
import { ArrowRight, ArrowDown, ShieldAlert } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

export function Hero() {
  const shouldReduceMotion = useReducedMotion();

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: shouldReduceMotion ? 0 : 0.12,
        delayChildren: shouldReduceMotion ? 0 : 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 8 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
  };

  return (
    <section id="hero" className="relative overflow-hidden bg-[#F4F6F8] py-16 sm:py-24 border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        <div className="grid grid-cols-1 items-start gap-12 lg:grid-cols-12 lg:gap-16">
          {/* Left: Asymmetric Editorial Column (7 cols) */}
          <div className="lg:col-span-7 space-y-7">
            <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#FFFFFF] px-3 py-1 text-xs font-mono text-[#475467] shadow-2xs">
              <span className="flex h-1.5 w-1.5 rounded-full bg-[#3157D5]" />
              <span>EVIDENCE-FIRST SETTLEMENT CONTROLLER</span>
            </div>

            <div className="space-y-4">
              <h1 className="text-4xl font-semibold tracking-tight text-[#101828] sm:text-5xl lg:text-[3.5rem] leading-[1.08]">
                Financial reconciliation that can explain itself.
              </h1>
              <p className="max-w-2xl text-lg leading-relaxed text-[#475467] sm:text-xl">
                CashProof reconciles settlement data, investigates ambiguity, and refuses to
                authorize what evidence cannot prove.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-md bg-[#3157D5] px-5 py-2.5 text-sm font-semibold text-white shadow-xs transition-all hover:bg-[#2745B0] active:scale-[0.98]"
              >
                Open controller
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#thesis"
                className="inline-flex items-center gap-1.5 rounded-md border border-[#DDE2E7] bg-[#FFFFFF] px-4 py-2.5 text-sm font-medium text-[#475467] shadow-2xs transition-all hover:bg-[#F4F6F8] hover:text-[#101828]"
              >
                Inspect architecture
                <ArrowDown className="h-3.5 w-3.5 text-[#475467]" />
              </a>
            </div>

            {/* Core Credibility Proofs */}
            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-[#DDE2E7]">
              <div>
                <div className="font-mono text-xl font-bold text-[#101828]">0</div>
                <div className="text-xs text-[#475467] mt-0.5 font-medium">False Auto-Resolutions</div>
              </div>
              <div>
                <div className="font-mono text-xl font-bold text-[#101828]">100%</div>
                <div className="text-xs text-[#475467] mt-0.5 font-medium">Target Set Accuracy</div>
              </div>
              <div>
                <div className="font-mono text-xl font-bold text-[#101828]">9</div>
                <div className="text-xs text-[#475467] mt-0.5 font-medium">Deterministic Invariants</div>
              </div>
            </div>
          </div>

          {/* Right: Operational Instrument Artifact (5 cols) */}
          <div className="lg:col-span-5 w-full">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="rounded-lg border border-[#DDE2E7] bg-[#FFFFFF] shadow-xs overflow-hidden"
            >
              {/* Instrument Top Meta Bar */}
              <div className="flex items-center justify-between border-b border-[#DDE2E7] bg-[#F4F6F8] px-4 py-3">
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="font-semibold text-[#101828]">CASE</span>
                  <span className="text-[#475467]">set_02b31b1f2eb1</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-[#D98B20]/10 border border-[#D98B20]/30 px-2 py-0.5 font-mono text-[10px] font-bold text-[#D98B20]">
                    AMOUNT MISMATCH
                  </span>
                  <span className="rounded bg-[#F4F6F8] border border-[#DDE2E7] px-2 py-0.5 font-mono text-[10px] font-medium text-[#475467]">
                    MATCH 1.00
                  </span>
                </div>
              </div>

              {/* Instrument Body */}
              <div className="p-5 space-y-4">
                {/* Expected vs Observed vs Variance */}
                <div className="grid grid-cols-3 gap-2.5">
                  <motion.div
                    variants={itemVariants}
                    className="rounded border border-[#DDE2E7] bg-[#F4F6F8]/60 p-2.5"
                  >
                    <div className="text-[10px] uppercase font-mono tracking-wider text-[#475467]">
                      Expected
                    </div>
                    <div className="font-mono text-sm sm:text-base font-bold tabular-nums text-[#101828] mt-1">
                      ₹4,833.54
                    </div>
                    <div className="text-[10px] text-[#475467] mt-0.5">Gateway Net</div>
                  </motion.div>

                  <motion.div
                    variants={itemVariants}
                    className="rounded border border-[#DDE2E7] bg-[#F4F6F8]/60 p-2.5"
                  >
                    <div className="text-[10px] uppercase font-mono tracking-wider text-[#475467]">
                      Observed
                    </div>
                    <div className="font-mono text-sm sm:text-base font-bold tabular-nums text-[#101828] mt-1">
                      ₹4,883.54
                    </div>
                    <div className="text-[10px] text-[#475467] mt-0.5">Bank Statement</div>
                  </motion.div>

                  <motion.div
                    variants={itemVariants}
                    className="rounded border border-[#D64545]/30 bg-[#D64545]/5 p-2.5"
                  >
                    <div className="text-[10px] uppercase font-mono tracking-wider text-[#D64545]">
                      Variance
                    </div>
                    <div className="font-mono text-sm sm:text-base font-bold tabular-nums text-[#D64545] mt-1">
                      -₹50.00
                    </div>
                    <div className="text-[10px] text-[#D64545] mt-0.5 font-medium">Unbalanced</div>
                  </motion.div>
                </div>

                {/* Candidate & AI Investigation Evidence */}
                <motion.div
                  variants={itemVariants}
                  className="rounded border border-[#DDE2E7] bg-[#FFFFFF] p-3 text-xs space-y-1.5 font-mono"
                >
                  <div className="flex items-center justify-between text-[#475467]">
                    <span>Reference</span>
                    <span className="font-medium text-[#101828]">PAY_849204 (Exact)</span>
                  </div>
                  <div className="flex items-center justify-between text-[#475467]">
                    <span>AI Hypothesis</span>
                    <span className="text-[#3157D5] font-medium">₹50 Fee Deduction Identified</span>
                  </div>
                  <div className="flex items-center justify-between text-[#475467]">
                    <span>AI Confidence</span>
                    <span className="font-bold text-[#101828]">1.00 (Maximum Belief)</span>
                  </div>
                </motion.div>

                {/* Gate Firewall Decision */}
                <motion.div
                  variants={itemVariants}
                  className="rounded border border-[#D64545]/40 bg-[#D64545]/5 p-3.5 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-mono text-xs font-bold text-[#D64545]">
                      <ShieldAlert className="h-4 w-4" />
                      GATE: BRIDGE FAILED
                    </div>
                    <span className="rounded bg-[#D98B20] text-white px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider">
                      REVIEW REQUIRED
                    </span>
                  </div>
                  <p className="text-xs text-[#101828] leading-relaxed">
                    AI confidence was 1.00, but gross &minus; fee &minus; tax &ne; observed bank net.
                    The deterministic Gate halts automation and routes case to human controller.
                  </p>
                </motion.div>

                {/* Micro Invariant Principle */}
                <motion.div
                  variants={itemVariants}
                  className="flex items-center justify-between pt-2 text-[11px] font-mono text-[#475467]"
                >
                  <span>INVARIANT: FAILS CLOSED</span>
                  <Link
                    href="/cases/set_02b31b1f2eb1"
                    className="font-medium text-[#3157D5] hover:underline inline-flex items-center gap-1"
                  >
                    Inspect in Controller &rarr;
                  </Link>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
