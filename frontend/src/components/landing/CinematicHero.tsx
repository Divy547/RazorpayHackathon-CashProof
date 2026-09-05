"use client";

import { useRef } from "react";
import Link from "next/link";
import { ArrowDown, ArrowRight } from "lucide-react";
import { motion, useScroll, useTransform } from "motion/react";
import { HeroReconciliationArtifact } from "./HeroReconciliationArtifact";

export function CinematicHero() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Headline transforms
  const headlineOpacity = useTransform(scrollYProgress, [0, 0.35, 0.7], [1, 0.9, 0.15]);
  const headlineY = useTransform(scrollYProgress, [0, 0.7], [0, -60]);

  return (
    <section ref={containerRef} className="relative h-[220vh] bg-[#F3F0E8] text-[#171816]">
      {/* Sticky Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 sm:py-24 overflow-hidden">
        {/* Subtle Background Structural Grid */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.035]"
          style={{
            backgroundImage: `linear-gradient(#171816 1px, transparent 1px), linear-gradient(90deg, #171816 1px, transparent 1px)`,
            backgroundSize: "64px 64px",
          }}
        />

        {/* Top Eyebrow */}
        <div className="relative z-10 mx-auto w-full max-w-6xl">
          <div className="inline-flex items-center gap-2.5 font-mono text-xs uppercase tracking-widest text-[#62635C]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#A47C52]" />
            <span>EVIDENCE-FIRST SETTLEMENT CONTROL</span>
          </div>
        </div>

        {/* Center: Editorial Typography on Left + Schematic Artifact on Right */}
        <div className="relative z-10 mx-auto w-full max-w-6xl my-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
            {/* Headline Block (Dominant Left) */}
            <motion.div
              style={{ opacity: headlineOpacity, y: headlineY }}
              className="lg:col-span-7 space-y-6"
            >
              <h1 className="font-display font-medium text-4xl sm:text-5xl lg:text-[4.25rem] xl:text-[4.75rem] tracking-tight leading-[1.04] text-[#171816]">
                FINANCIAL
                <br />
                RECONCILIATION
                <br />
                THAT CAN EXPLAIN ITSELF.
              </h1>

              <p className="max-w-xl text-base sm:text-lg leading-relaxed text-[#62635C] font-normal">
                CashProof reconciles settlement data, investigates ambiguity, and refuses to authorize
                what evidence cannot prove.
              </p>

              {/* CTAs */}
              <div className="pt-2 flex flex-wrap items-center gap-5">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center gap-2.5 rounded-[10px] border border-[#A47C52]/50 bg-[#F8F6F0] px-6 py-3 font-mono text-xs uppercase tracking-widest text-[#171816] transition-all hover:bg-[#EEEAE0] hover:border-[#A47C52] shadow-xs"
                >
                  <span>OPEN CONTROLLER</span>
                  <ArrowRight className="h-3.5 w-3.5 text-[#A47C52]" />
                </Link>

                <a
                  href="#discrepancy"
                  className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-[#62635C] hover:text-[#171816] transition-colors py-3"
                >
                  <span>SEE HOW IT WORKS</span>
                  <ArrowDown className="h-3.5 w-3.5 text-[#62635C]" />
                </a>
              </div>
            </motion.div>

            {/* Right-Side Editorial Financial Artifact */}
            <div className="lg:col-span-5 flex justify-center lg:justify-end">
              <HeroReconciliationArtifact scrollProgress={scrollYProgress} />
            </div>
          </div>
        </div>

        {/* Bottom Status Telemetry */}
        <div className="relative z-10 mx-auto w-full max-w-6xl pt-6 border-t border-[#D9D5CA] flex flex-wrap items-center justify-between text-[11px] font-mono text-[#62635C]">
          <span>INVARIANT RUNTIME: STRICT INTEGER MINOR UNITS</span>
          <span className="hidden sm:inline-block">SCROLL TO OBSERVE CONTROLLER &darr;</span>
          <span>EVALUATION: DETERMINISTIC GATE</span>
        </div>
      </div>
    </section>
  );
}
