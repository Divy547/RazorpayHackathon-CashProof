"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function CinematicCta() {
  return (
    <section className="py-28 sm:py-36 bg-[#F3F0E8] text-[#171816] relative overflow-hidden border-b border-[#D9D5CA]">
      <div className="mx-auto max-w-5xl px-6 sm:px-8 text-center space-y-10">
        <div className="space-y-6 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#62635C]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#A47C52]" />
            <span>FINANCIAL CONTROLLER RUNTIME</span>
          </div>

          <h2 className="font-display text-4xl sm:text-6xl lg:text-7xl font-medium tracking-tight text-[#171816] leading-[1.05]">
            SEE THE CONTROLLER
            <br />
            IN ACTION.
          </h2>

          <p className="font-mono text-xs sm:text-sm text-[#62635C] leading-relaxed max-w-xl mx-auto">
            Run a reconciliation batch. Inspect the evidence. Challenge an exception. Watch the gate
            decide.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-3 rounded-[10px] border border-[#A47C52]/50 bg-[#F8F6F0] px-8 py-4 font-mono text-xs font-bold uppercase tracking-widest text-[#171816] transition-all hover:bg-[#EEEAE0] hover:border-[#A47C52] shadow-xs"
          >
            <span>OPEN CONTROLLER</span>
            <ArrowRight className="h-4 w-4 text-[#A47C52]" />
          </Link>

          <Link
            href="/cases"
            className="inline-flex items-center gap-2 rounded-[10px] border border-[#D9D5CA] bg-[#F8F6F0] px-6 py-4 font-mono text-xs uppercase tracking-widest text-[#62635C] transition-all hover:text-[#171816] hover:border-[#A47C52]/40 shadow-xs"
          >
            EXPLORE CASES
          </Link>
        </div>

        <div className="pt-8 flex flex-wrap justify-center items-center gap-8 text-[11px] font-mono text-[#62635C]">
          <span className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />
            Deterministic Invariants
          </span>
          <span className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />
            Bounded AI Budgets
          </span>
          <span className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />
            Fails Closed by Default
          </span>
        </div>
      </div>
    </section>
  );
}
