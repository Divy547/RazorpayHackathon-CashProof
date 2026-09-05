"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { AlertOctagon, ArrowDown } from "lucide-react";
import { getCaseDetail } from "@/lib/data";
import { formatMinor, formatSignedMinor } from "@/lib/format";

// Sourced from the same authoritative S3 case as ScenarioChronicle, Hero,
// and HeroReconciliationArtifact - not hardcoded, so all four can never
// display conflicting numbers for the same real case again. Throws rather
// than falling back to a fabricated value if the checked-in demo data is
// ever missing this case.
function requireCaseDetail(settlementId: string) {
  const detail = getCaseDetail(settlementId);
  if (!detail) {
    throw new Error(`DiscrepancyReveal: expected case ${settlementId} to exist in demo-data.json`);
  }
  return detail;
}

const S3_CASE_ID = "set_72d8894a05e4";

export function DiscrepancyReveal() {
  const containerRef = useRef<HTMLDivElement>(null);
  const s3Case = requireCaseDetail(S3_CASE_ID);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Stage 1: EXPECTED
  const expectedOpacity = useTransform(scrollYProgress, [0.05, 0.15, 0.85, 0.95], [0, 1, 1, 0.3]);
  const expectedY = useTransform(scrollYProgress, [0.05, 0.18], [30, 0]);

  // Stage 2: OBSERVED
  const observedOpacity = useTransform(scrollYProgress, [0.22, 0.32, 0.85, 0.95], [0, 1, 1, 0.3]);
  const observedY = useTransform(scrollYProgress, [0.22, 0.35], [30, 0]);

  // Stage 3: VARIANCE
  const varianceOpacity = useTransform(scrollYProgress, [0.42, 0.52, 0.85, 0.95], [0, 1, 1, 0.3]);
  const varianceY = useTransform(scrollYProgress, [0.42, 0.55], [30, 0]);

  // Stage 4: THE NUMBERS DON'T AGREE.
  const statementOpacity = useTransform(scrollYProgress, [0.60, 0.72, 0.92, 1], [0, 1, 1, 0.6]);
  const statementScale = useTransform(scrollYProgress, [0.60, 0.75], [0.95, 1]);

  // Stage 5: DO NOT AUTHORIZE. -> INVESTIGATE.
  const commandOpacity = useTransform(scrollYProgress, [0.78, 0.88, 1], [0, 1, 1]);
  const commandY = useTransform(scrollYProgress, [0.78, 0.9], [25, 0]);

  return (
    <section
      id="discrepancy"
      ref={containerRef}
      className="relative h-[320vh] bg-[#F3F0E8] text-[#171816]"
    >
      {/* Pinned Fullscreen Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Header */}
        <div className="mx-auto w-full max-w-6xl">
          <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-xs font-mono text-[#62635C] uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#A85F59]" />
              SCENARIO S3 // DISCREPANCY DETECTED
            </span>
            <span className="hidden sm:inline">SCROLL TO ADVANCE SEQUENCE</span>
            <span className="text-[#A47C52] font-semibold">BRIDGE EVALUATION</span>
          </div>
        </div>

        {/* Center Main Stage */}
        <div className="mx-auto w-full max-w-6xl my-auto space-y-12">
          {/* Row of 3 Financial Figures appearing sequentially */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
            {/* Stage 1: EXPECTED */}
            <motion.div
              style={{ opacity: expectedOpacity, y: expectedY }}
              className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-6 sm:p-8 space-y-2 relative shadow-xs"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-[#62635C]">
                01 // EXPECTED
              </div>
              <div className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#171816] tabular-nums">
                {formatMinor(s3Case.expected_net_minor, s3Case.currency)}
              </div>
              <p className="font-mono text-xs text-[#62635C] pt-1">
                Gateway calculated net: gross - fee - tax.
              </p>
            </motion.div>

            {/* Stage 2: OBSERVED */}
            <motion.div
              style={{ opacity: observedOpacity, y: observedY }}
              className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-6 sm:p-8 space-y-2 relative shadow-xs"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-[#62635C]">
                02 // OBSERVED
              </div>
              <div className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#171816] tabular-nums">
                {formatMinor(s3Case.observed_net_minor, s3Case.currency)}
              </div>
              <p className="font-mono text-xs text-[#62635C] pt-1">
                Authoritative bank credit entry in statement.
              </p>
            </motion.div>

            {/* Stage 3: VARIANCE */}
            <motion.div
              style={{ opacity: varianceOpacity, y: varianceY }}
              className="rounded-2xl border border-[#A85F59]/50 bg-[#F8F6F0] p-6 sm:p-8 space-y-2 relative shadow-xs"
            >
              <div className="font-mono text-xs uppercase tracking-widest text-[#A85F59] flex items-center justify-between">
                <span>03 // VARIANCE</span>
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-[#A85F59]/15 border border-[#A85F59]/30 font-bold">
                  MISMATCH
                </span>
              </div>
              <div className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-[#A85F59] tabular-nums">
                {formatSignedMinor(s3Case.delta_minor, s3Case.currency)}
              </div>
              <p className="font-mono text-xs text-[#62635C] pt-1">
                Paise imbalance violates monetary bridge.
              </p>
            </motion.div>
          </div>

          {/* Stage 4: THE NUMBERS DON'T AGREE. */}
          <motion.div
            style={{ opacity: statementOpacity, scale: statementScale }}
            className="text-center space-y-3 pt-4"
          >
            <h2 className="font-display text-3xl sm:text-5xl lg:text-6xl font-medium tracking-tight text-[#171816]">
              THE NUMBERS DON&apos;T AGREE.
            </h2>
            <p className="font-mono text-xs sm:text-sm uppercase tracking-widest text-[#62635C]">
              ARITHMETIC INVARIANT FAILED: gross - fee - tax &ne; observed bank net
            </p>
          </motion.div>

          {/* Stage 5: DO NOT AUTHORIZE. INVESTIGATE. */}
          <motion.div
            style={{ opacity: commandOpacity, y: commandY }}
            className="flex flex-col items-center justify-center space-y-4 pt-2"
          >
            <div className="inline-flex items-center gap-2 rounded-xl border border-[#A85F59]/60 bg-[#A85F59]/10 px-5 py-2 text-sm font-mono font-bold tracking-widest text-[#A85F59]">
              <AlertOctagon className="h-4 w-4" />
              <span>DO NOT AUTHORIZE.</span>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-[#A47C52] font-semibold">
              <ArrowDown className="h-4 w-4 animate-pulse text-[#A47C52]" />
              <span>COMMENCE INVESTIGATION &middot; ASSEMBLE EVIDENCE</span>
            </div>
          </motion.div>
        </div>

        {/* Bottom Pinned Footer */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between text-[11px] font-mono text-[#62635C] border-t border-[#D9D5CA] pt-3">
          <span>MONETARY TRUTH OWNED BY DETERMINISTIC CODE</span>
          <span>CASHPROOF FINANCIAL ENGINE</span>
        </div>
      </div>
    </section>
  );
}
