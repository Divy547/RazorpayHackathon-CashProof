"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";

interface PipelineStep {
  num: string;
  name: string;
  tag: string;
  accent: string;
  items: string[];
  invariants: string;
}

export function SystemArchitectureFlow() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const steps: PipelineStep[] = [
    {
      num: "01",
      name: "SOURCE RECORDS",
      tag: "IMMUTABLE FACTS",
      accent: "#4E6870",
      items: ["Gateway Settlements", "Payment Transactions", "Refund Records", "Bank Statement Feeds"],
      invariants: "Append-only source ingestion. No decoy labels or synthetic noise exposed.",
    },
    {
      num: "02",
      name: "NORMALIZE",
      tag: "DETERMINISTIC CAST",
      accent: "#65745F",
      items: ["Integer Minor Units (Paise)", "ISO 4217 Currency Explicit", "ISO 8601 Timestamps", "Zero Float Math"],
      invariants: "Eliminates IEEE 754 precision drift. Currencies explicit across all legs.",
    },
    {
      num: "03",
      name: "RECONCILE",
      tag: "CANDIDATE WINDOWS",
      accent: "#A47C52",
      items: ["Structured Ref Window (+/- 7d)", "Narration Text Window (+/- 3d)", "Amount Pairing", "Deduplication"],
      invariants: "Time windows filter candidates; they are never proof of settlement.",
    },
    {
      num: "04",
      name: "EVIDENCE",
      tag: "PROVENANCE GRAPH",
      accent: "#4E6870",
      items: ["Gateway Reference Links", "Narration Text Extraction", "Alias Association Receipts", "Audit Logs"],
      invariants: "Every material assertion links to immutable source transaction hashes.",
    },
    {
      num: "05",
      name: "GATE FIREWALL",
      tag: "SOLE AUTHORIZATION",
      accent: "#65745F",
      items: ["Identity Verification", "Bridge Equation Balance", "Uniqueness Enforcement", "Human Policy Check"],
      invariants: "Fails closed. AI confidence is never an authorization input.",
    },
  ];

  // Progressive highlights based on scroll
  const step1 = useTransform(scrollYProgress, [0.05, 0.2], [0.35, 1]);
  const step2 = useTransform(scrollYProgress, [0.22, 0.38], [0.35, 1]);
  const step3 = useTransform(scrollYProgress, [0.40, 0.58], [0.35, 1]);
  const step4 = useTransform(scrollYProgress, [0.60, 0.78], [0.35, 1]);
  const step5 = useTransform(scrollYProgress, [0.80, 0.98], [0.35, 1]);

  const stepOpacities = [step1, step2, step3, step4, step5];

  return (
    <section
      id="architecture"
      ref={containerRef}
      className="relative h-[300vh] bg-[#F3F0E8] text-[#171816]"
    >
      {/* Sticky Fullscreen Diagram */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Header */}
        <div className="mx-auto w-full max-w-6xl">
          <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-xs font-mono text-[#62635C] uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />
              SYSTEM PIPELINE // MONETARY ARTIFACT PROGRESSION
            </span>
            <span className="hidden sm:inline">SCROLL TO TRACE DATA FLOW</span>
            <span className="text-[#A47C52] font-semibold">DETERMINISTIC BACKBONE</span>
          </div>
        </div>

        {/* Center: System Flow Diagram */}
        <div className="mx-auto w-full max-w-6xl my-auto space-y-6">
          <div className="space-y-2">
            <span className="font-mono text-xs uppercase tracking-widest text-[#A47C52]">
              PIPELINE ARCHITECTURE
            </span>
            <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-medium tracking-tight text-[#171816]">
              The Reconciliation Vector
            </h2>
            <p className="font-mono text-xs sm:text-sm text-[#62635C] max-w-2xl">
              Financial data moves through a unidirectional state machine. Every stage enforces strict
              invariants before handing off to the next.
            </p>
          </div>

          {/* 5-Stage System Sequence */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-4">
            {steps.map((step, idx) => {
              const opacity = stepOpacities[idx];

              return (
                <motion.div
                  key={step.num}
                  style={{ opacity }}
                  className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 flex flex-col justify-between space-y-3 transition-colors relative shadow-xs"
                >
                  {/* Step Header */}
                  <div className="space-y-1">
                    <div className="flex items-center justify-between font-mono text-[10px]">
                      <span className="text-[#62635C]">{step.num}</span>
                      <span
                        className="px-1.5 py-0.5 rounded-md border border-[#D9D5CA] bg-[#EEEAE0] uppercase tracking-wider font-semibold"
                        style={{ color: step.accent }}
                      >
                        {step.tag}
                      </span>
                    </div>
                    <div className="font-mono text-sm font-bold text-[#171816] tracking-tight">
                      {step.name}
                    </div>
                  </div>

                  {/* Component Items */}
                  <ul className="space-y-1.5 font-mono text-[11px] text-[#62635C] pt-1">
                    {step.items.map((item, i) => (
                      <li key={i} className="flex items-center gap-1.5">
                        <span className="h-1 w-1 rounded-full bg-[#D9D5CA]" />
                        <span className="line-clamp-1">{item}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Enforced Invariant */}
                  <div className="pt-2 border-t border-[#D9D5CA] text-[10px] font-mono text-[#62635C] leading-relaxed">
                    <span className="text-[#171816] font-semibold">Invariant:</span> {step.invariants}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Bottom Metadata */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between text-[11px] font-mono text-[#62635C] border-t border-[#D9D5CA] pt-3">
          <span>PIPELINE CONTRACT: MONOTONIC STATE TRANSITIONS</span>
          <span>INGEST &rarr; NORMALIZE &rarr; RECONCILE &rarr; EVIDENCE &rarr; GATE</span>
        </div>
      </div>
    </section>
  );
}
