"use client";

import { motion, MotionValue, useTransform } from "motion/react";
import { AlertCircle, ArrowDown, Lock, ShieldAlert } from "lucide-react";

interface HeroReconciliationArtifactProps {
  scrollProgress: MotionValue<number>;
}

export function HeroReconciliationArtifact({
  scrollProgress,
}: HeroReconciliationArtifactProps) {
  // Container motion tied to hero scroll progression
  const containerOpacity = useTransform(
    scrollProgress,
    [0, 0.35, 0.7],
    [1, 0.95, 0.15]
  );
  const containerY = useTransform(scrollProgress, [0, 0.7], [0, -40]);

  // Subtle internal step revelation as user scrolls
  const step2Opacity = useTransform(scrollProgress, [0, 0.1], [0.85, 1]);
  const varianceOpacity = useTransform(scrollProgress, [0.03, 0.16], [0.7, 1]);
  const varianceScale = useTransform(scrollProgress, [0.03, 0.16], [0.98, 1]);
  const gateOpacity = useTransform(scrollProgress, [0.08, 0.24], [0.8, 1]);

  return (
    <motion.div
      style={{ opacity: containerOpacity, y: containerY }}
      className="relative w-full max-w-[360px] mx-auto lg:mx-0 lg:ml-auto select-none"
    >
      {/* Editorial Registration Corner Marks */}
      <div className="absolute -top-1.5 -left-1.5 w-3 h-3 border-t border-l border-[#A47C52]/50 pointer-events-none" />
      <div className="absolute -top-1.5 -right-1.5 w-3 h-3 border-t border-r border-[#A47C52]/50 pointer-events-none" />
      <div className="absolute -bottom-1.5 -left-1.5 w-3 h-3 border-b border-l border-[#A47C52]/50 pointer-events-none" />
      <div className="absolute -bottom-1.5 -right-1.5 w-3 h-3 border-b border-r border-[#A47C52]/50 pointer-events-none" />

      {/* Main Schematic Surface */}
      <div className="relative rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 sm:p-5 shadow-[0_4px_24px_-4px_rgba(23,24,22,0.06)] space-y-3.5">
        {/* Fine Schematic Grid Background Overlay */}
        <div
          className="absolute inset-0 pointer-events-none rounded-2xl opacity-[0.035]"
          style={{
            backgroundImage: `linear-gradient(#171816 1px, transparent 1px), linear-gradient(90deg, #171816 1px, transparent 1px)`,
            backgroundSize: "16px 16px",
          }}
        />

        {/* Top Artifact Header */}
        <div className="relative z-10 flex items-center justify-between border-b border-[#D9D5CA] pb-2 text-[10px] font-mono">
          <div className="flex items-center gap-1.5 text-[#62635C] tracking-wider uppercase">
            <span className="h-1.5 w-1.5 rounded-full bg-[#A47C52]" />
            <span>RECONCILIATION VECTOR</span>
          </div>
          <span className="text-[#A47C52] bg-[#EEEAE0] border border-[#D9D5CA] px-2 py-0.5 rounded-md font-semibold text-[9px]">
            CASE #09
          </span>
        </div>

        {/* Node 1: Ingested Settlement Fact */}
        <div className="relative z-10 rounded-xl border border-[#D9D5CA] bg-[#F3F0E8] p-3 space-y-1">
          <div className="flex items-center justify-between text-[9px] font-mono uppercase text-[#62635C]">
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />
              SOURCE FACT // BANK FEED
            </span>
            <span className="font-semibold text-[#171816]">IMMUTABLE</span>
          </div>
          <div className="flex items-baseline justify-between pt-0.5">
            <span className="font-mono text-[10px] text-[#62635C] uppercase tracking-wider">
              OBSERVED DEPOSIT
            </span>
            <span className="font-mono text-lg font-bold text-[#171816] tabular-nums tracking-tight">
              ₹4,883.54
            </span>
          </div>
          <div className="text-[9px] font-mono text-[#4E6870] truncate">
            REF: HDFC_CMS_9823412 &middot; 09:14 IST
          </div>
        </div>

        {/* Connecting Vector 1 */}
        <div className="relative z-10 flex items-center justify-center my-[-4px]">
          <div className="flex flex-col items-center">
            <div className="w-px h-3 bg-[#D9D5CA]" />
            <ArrowDown className="h-3 w-3 text-[#A47C52] my-[-2px]" />
          </div>
        </div>

        {/* Node 2: Calculated Expected Net */}
        <motion.div
          style={{ opacity: step2Opacity }}
          className="relative z-10 rounded-xl border border-[#D9D5CA] bg-[#EEEAE0]/70 p-3 space-y-1"
        >
          <div className="flex items-center justify-between text-[9px] font-mono uppercase text-[#62635C]">
            <span>GATEWAY SETTLEMENT ITEM</span>
            <span className="text-[#4E6870]">CALCULATED NET</span>
          </div>
          <div className="flex items-baseline justify-between pt-0.5">
            <span className="font-mono text-[10px] text-[#62635C] uppercase tracking-wider">
              EXPECTED NET
            </span>
            <span className="font-mono text-lg font-bold text-[#171816] tabular-nums tracking-tight">
              ₹4,833.54
            </span>
          </div>
          <div className="text-[9px] font-mono text-[#62635C] flex items-center justify-between border-t border-[#D9D5CA]/70 pt-1 mt-1">
            <span>GROSS: ₹5,000.00</span>
            <span>FEE+TAX: ₹166.46</span>
          </div>
        </motion.div>

        {/* Node 3: Detected Variance Delta */}
        <motion.div
          style={{ opacity: varianceOpacity, scale: varianceScale }}
          className="relative z-10 flex items-center justify-between rounded-lg border border-[#A85F59]/40 bg-[#A85F59]/5 px-3 py-2 font-mono text-[11px]"
        >
          <div className="flex items-center gap-1.5 text-[#A85F59]">
            <AlertCircle className="h-3 w-3 shrink-0" />
            <span className="text-[10px] font-semibold uppercase tracking-wider">
              VARIANCE DELTA
            </span>
          </div>
          <div className="font-bold text-[#A85F59] tabular-nums">
            -₹50.00
          </div>
        </motion.div>

        {/* Connecting Vector 2 */}
        <div className="relative z-10 flex items-center justify-center my-[-4px]">
          <div className="flex flex-col items-center">
            <div className="w-px h-3 bg-[#A85F59]/40" />
            <ArrowDown className="h-3 w-3 text-[#A85F59] my-[-2px]" />
          </div>
        </div>

        {/* Node 4: Deterministic Gate Firewall Check */}
        <motion.div
          style={{ opacity: gateOpacity }}
          className="relative z-10 rounded-xl border border-[#A85F59]/40 bg-[#F3F0E8] p-3 space-y-1.5"
        >
          <div className="flex items-center justify-between text-[9px] font-mono uppercase">
            <span className="flex items-center gap-1 text-[#171816] font-semibold">
              <Lock className="h-2.5 w-2.5 text-[#A47C52]" />
              GATE CHECK 02 // BRIDGE
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-[#A85F59]/15 border border-[#A85F59]/30 px-2 py-0.5 text-[9px] font-bold text-[#A85F59]">
              <ShieldAlert className="h-2.5 w-2.5" />
              BLOCKED
            </span>
          </div>
          <div className="text-[9px] font-mono text-[#62635C] leading-snug">
            Formula invariant violated: gross - deductions &ne; deposit.
            <span className="block text-[#A85F59] font-medium pt-0.5">
              &rarr; AI AUTO-RESOLUTION REFUSED. ROUTED TO REVIEW.
            </span>
          </div>
        </motion.div>

        {/* Bottom Schematic Verification Hash */}
        <div className="relative z-10 pt-1 flex items-center justify-between text-[8px] sm:text-[9px] font-mono text-[#62635C] border-t border-[#D9D5CA]">
          <span>FAIL-CLOSED BY DEFAULT</span>
          <span className="truncate max-w-[120px] text-right">HASH: 7e4a&hellip;8a02</span>
        </div>
      </div>
    </motion.div>
  );
}
