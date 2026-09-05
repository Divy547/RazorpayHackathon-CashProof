"use client";

import { useRef } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Gauge, ShieldCheck } from "lucide-react";
import { motion, useScroll, useTransform } from "motion/react";

export function BenchmarkReport() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Stage 1: Header and audit strip
  const headerOpacity = useTransform(scrollYProgress, [0, 0.15], [0.3, 1]);

  // Stage 2: 4 metrics cards sequentially reveal
  const metricsOpacity = useTransform(scrollYProgress, [0.15, 0.35], [0, 1]);
  const metricsY = useTransform(scrollYProgress, [0.15, 0.35], [25, 0]);

  // Stage 3: Distribution strip expands smoothly
  const stripWidth = useTransform(scrollYProgress, [0.38, 0.58], ["0%", "100%"]);
  const stripOpacity = useTransform(scrollYProgress, [0.35, 0.45], [0, 1]);

  // Stage 4: Climax reveal: 0 FALSE AUTO-RESOLUTIONS and 100% TARGET SET ACCURACY
  const climaxOpacity = useTransform(scrollYProgress, [0.55, 0.75, 1], [0, 1, 1]);
  const climaxScale = useTransform(scrollYProgress, [0.55, 0.75], [0.96, 1]);

  const metrics = [
    { label: "Total Settlements", val: "100", hint: "Controlled benchmark batch", code: "SEED 42", color: "text-[#171816]" },
    { label: "Auto Resolved", val: "39", hint: "Clean 1:1 automation", code: "39.0%", color: "text-[#65745F]" },
    { label: "Human Review", val: "51", hint: "Routed with evidence", code: "51.0%", color: "text-[#A47C52]" },
    { label: "Unresolved", val: "10", hint: "Non-provable / missing", code: "10.0%", color: "text-[#A85F59]" },
  ];

  return (
    <section
      id="benchmark"
      ref={containerRef}
      className="relative h-[320vh] bg-[#F3F0E8] text-[#171816] scroll-mt-20"
    >
      {/* Pinned Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Header */}
        <motion.div style={{ opacity: headerOpacity }} className="mx-auto w-full max-w-6xl space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
            <div className="max-w-2xl space-y-2">
              <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#62635C]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />
                <span>MEASUREMENT REPORT // SEED 42</span>
              </div>
              <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#171816]">
                Proven Against Hidden Ground Truth
              </h2>
              <p className="font-mono text-xs sm:text-sm text-[#62635C] leading-relaxed">
                Audited by an isolated evaluator with access to hidden synthetic ground truth.
                Evaluated across 100 settlements and 18,838 candidate ledger entries.
              </p>
            </div>

            <div className="shrink-0">
              <Link
                href="/benchmark"
                className="inline-flex items-center gap-2 rounded-[10px] border border-[#D9D5CA] bg-[#F8F6F0] px-4 py-2.5 font-mono text-xs uppercase tracking-widest text-[#171816] transition-all hover:bg-[#EEEAE0] hover:border-[#A47C52]/50 shadow-xs"
              >
                <Gauge className="h-3.5 w-3.5 text-[#A47C52]" />
                <span>OPEN BENCHMARK RUNNER</span>
                <ArrowRight className="h-3.5 w-3.5 text-[#62635C]" />
              </Link>
            </div>
          </div>

          {/* Metadata Audit Strip */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] px-5 py-2.5 font-mono text-xs text-[#62635C] shadow-xs">
            <div className="flex flex-wrap items-center gap-6">
              <span>
                <strong className="text-[#171816]">SUITE:</strong> SEED-42
              </span>
              <span>
                <strong className="text-[#171816]">POOL:</strong> 18,838 ENTRIES
              </span>
              <span>
                <strong className="text-[#171816]">EVALUATION:</strong> 100 SETTLEMENTS
              </span>
            </div>
            <div className="flex items-center gap-2 text-[#65745F]">
              <ShieldCheck className="h-4 w-4" />
              <span className="font-semibold text-[11px] uppercase tracking-wider">
                EVALUATOR ISOLATION: FAIL-CLOSED
              </span>
            </div>
          </div>
        </motion.div>

        {/* Center Main Stage: Pinned Sequential Revelation */}
        <div className="mx-auto w-full max-w-6xl my-auto space-y-6">
          {/* Stage 2: 4 Measurement Cards */}
          <motion.div
            style={{ opacity: metricsOpacity, y: metricsY }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {metrics.map((m) => (
              <div
                key={m.label}
                className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 sm:p-5 space-y-1 font-mono shadow-xs"
              >
                <div className="flex items-center justify-between text-[10px] text-[#62635C] uppercase">
                  <span>{m.label}</span>
                  <span className="font-semibold">{m.code}</span>
                </div>
                <div className={`text-2xl sm:text-3xl font-bold tabular-nums ${m.color}`}>
                  {m.val}
                </div>
                <div className="text-[10px] text-[#62635C] pt-0.5">{m.hint}</div>
              </div>
            ))}
          </motion.div>

          {/* Stage 3: Dynamic Distribution Progress Strip */}
          <motion.div
            style={{ opacity: stripOpacity }}
            className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 space-y-2.5 font-mono shadow-xs"
          >
            <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-[#62635C]">
              <span>Disposition Distribution</span>
              <span className="font-semibold text-[#171816]">100 Settlements Evaluated</span>
            </div>

            <div className="h-2.5 w-full rounded-md bg-[#EEEAE0] overflow-hidden flex relative">
              <motion.div
                style={{ width: stripWidth }}
                className="h-full flex shrink-0"
              >
                <div style={{ width: "39%" }} className="bg-[#65745F] h-full" title="39% Auto Resolved" />
                <div style={{ width: "51%" }} className="bg-[#A47C52] h-full" title="51% Human Review" />
                <div style={{ width: "10%" }} className="bg-[#A85F59] h-full" title="10% Unresolved" />
              </motion.div>
            </div>

            <div className="flex flex-wrap items-center justify-between text-[11px] text-[#62635C] pt-0.5">
              <span className="flex items-center gap-1.5 font-semibold text-[#65745F]">
                <span className="h-2 w-2 rounded-full bg-[#65745F]" />
                39 AUTO RESOLVED (39%)
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-[#A47C52]">
                <span className="h-2 w-2 rounded-full bg-[#A47C52]" />
                51 HUMAN REVIEW (51%)
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-[#A85F59]">
                <span className="h-2 w-2 rounded-full bg-[#A85F59]" />
                10 UNRESOLVED (10%)
              </span>
            </div>
          </motion.div>

          {/* Stage 4: Focal Hero Metric Card */}
          <motion.div
            style={{ opacity: climaxOpacity, scale: climaxScale }}
            className="rounded-2xl border border-[#65745F]/40 bg-[#F8F6F0] p-6 sm:p-8 space-y-4 shadow-sm"
          >
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
              <div className="md:col-span-8 space-y-2">
                <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#65745F] font-bold">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>SAFETY INVARIANT GUARANTEED</span>
                </div>
                <div className="flex items-baseline gap-4">
                  <span className="font-mono text-5xl sm:text-7xl lg:text-8xl font-bold text-[#171816] tabular-nums">
                    0
                  </span>
                  <span className="font-display text-2xl sm:text-3xl lg:text-4xl font-medium text-[#171816] tracking-tight">
                    FALSE AUTO-RESOLUTIONS
                  </span>
                </div>
                <p className="font-mono text-xs sm:text-sm text-[#62635C] leading-relaxed max-w-2xl">
                  In settlement reconciliation, a false auto-resolution pollutes general ledgers. CashProof&apos;s
                  deterministic gate guarantees that zero incorrect target record sets were auto-resolved
                  across all 100 evaluation cases.
                </p>
              </div>

              <div className="md:col-span-4 rounded-xl border border-[#D9D5CA] bg-[#EEEAE0] p-5 text-center space-y-1.5 font-mono shadow-xs">
                <div className="text-[10px] uppercase tracking-widest text-[#62635C] font-semibold">
                  Target Set Accuracy
                </div>
                <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#65745F] tabular-nums">
                  100%
                </div>
                <div className="text-[11px] text-[#62635C] pt-1">
                  Zero incorrect target records committed to ledger
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Bottom Status */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between text-[11px] font-mono text-[#62635C] border-t border-[#D9D5CA] pt-3">
          <span>EVALUATED ON 100 SETTLEMENT BENCHMARK (SEED 42)</span>
          <span>100% TARGET SET ACCURACY &middot; 0 FALSE POSITIVES</span>
        </div>
      </div>
    </section>
  );
}
