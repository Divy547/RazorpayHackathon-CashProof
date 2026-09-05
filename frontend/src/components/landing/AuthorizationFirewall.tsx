"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { AlertTriangle, Bot, Lock, ShieldCheck } from "lucide-react";

export function AuthorizationFirewall() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Scroll transforms for the gate sequence
  const aiSectionOpacity = useTransform(scrollYProgress, [0, 0.25, 0.45], [1, 1, 0.3]);
  const boundaryOpacity = useTransform(scrollYProgress, [0.15, 0.35], [0.3, 1]);

  // Blocked message appearance
  const blockedOpacity = useTransform(scrollYProgress, [0.72, 0.85, 1], [0, 1, 1]);
  const blockedScale = useTransform(scrollYProgress, [0.72, 0.85], [0.95, 1]);

  const gateChecks = [
    { num: "01", name: "IDENTITY", req: "Target entry exists in authoritative pool", status: "PASS" },
    { num: "02", name: "BRIDGE", req: "Gross - Fee - Tax - Refund + Adj == Net", status: "FAIL" },
    { num: "03", name: "CURRENCY", req: "ISO currency code exact match across legs", status: "PASS" },
    { num: "04", name: "UNIQUENESS", req: "Target not resolved by another case", status: "PASS" },
    { num: "05", name: "EVIDENCE", req: "Structured provenance link verified", status: "PASS" },
    { num: "06", name: "CONFLICT", req: "No contradictory records present", status: "PASS" },
    { num: "07", name: "POLICY", req: "Unstructured text requires human sign-off", status: "PASS" },
    { num: "08", name: "STATE", req: "Monotonic progression: CLASSIFIED -> GATED", status: "PASS" },
    { num: "09", name: "TARGET SET", req: "Proposed set exactly matches evaluated set", status: "PASS" },
  ];

  return (
    <section
      id="gate"
      ref={containerRef}
      className="relative h-[340vh] bg-[#F3F0E8] text-[#171816]"
    >
      {/* Sticky Viewport */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between px-6 sm:px-8 py-20 overflow-hidden">
        {/* Top Header */}
        <div className="mx-auto w-full max-w-6xl">
          <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-xs font-mono text-[#62635C] uppercase tracking-widest">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-[#A85F59]" />
              THE AUTHORIZATION BOUNDARY // GATE EVALUATION
            </span>
            <span>SCROLL TO TRIGGER FIREWALL</span>
          </div>
        </div>

        {/* Center: The Physical Firewall & Check Sequence */}
        <div className="mx-auto w-full max-w-5xl my-auto space-y-6">
          {/* Upper Zone: AI Investigator Output */}
          <motion.div
            style={{ opacity: aiSectionOpacity }}
            className="rounded-xl border border-[#A47C52]/40 bg-[#F8F6F0] p-4 font-mono text-xs space-y-2 shadow-xs"
          >
            <div className="flex items-center justify-between text-[#A47C52]">
              <div className="flex items-center gap-2">
                <Bot className="h-3.5 w-3.5" />
                <span className="font-bold text-[#171816]">AI INVESTIGATOR (HYPOTHESIS GENERATOR)</span>
              </div>
              <span className="text-[10px] uppercase border border-[#A47C52]/40 bg-[#EEEAE0] px-2 py-0.5 rounded-md font-bold">
                PROPOSAL EMITTED
              </span>
            </div>
            <div className="text-[#62635C] text-[11px]">
              Inspected 3 candidates &rarr; Synthesized fee variance &rarr; Emitted ResolutionProposal (target: ent_7a4b, confidence: 0.94).
            </div>
          </motion.div>

          {/* THE PHYSICAL SYSTEM FIREWALL */}
          <motion.div
            style={{ opacity: boundaryOpacity }}
            className="rounded-xl border-2 border-[#D9D5CA] bg-[#EEEAE0] py-3.5 px-6 font-mono text-xs flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left shadow-xs"
          >
            <div className="flex items-center gap-2.5 text-[#171816]">
              <Lock className="h-4 w-4 text-[#A47C52]" />
              <span className="font-bold tracking-widest text-[11px] sm:text-xs">
                ================ AUTHORIZATION BOUNDARY ================
              </span>
            </div>
            <span className="text-[11px] uppercase tracking-widest text-[#A47C52] font-bold">
              FAIL-CLOSED FIREWALL
            </span>
          </motion.div>

          {/* Lower Zone: Deterministic Gate Evaluation Sequence */}
          <div className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-6 space-y-4 font-mono text-xs shadow-xs">
            <div className="flex items-center justify-between border-b border-[#D9D5CA] pb-3 text-[#62635C]">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-[#65745F]" />
                <span className="font-bold text-[#171816]">DETERMINISTIC GATE EVALUATION</span>
              </div>
              <span className="text-[10px] text-[#62635C]">evaluate_gate(proposal)</span>
            </div>

            {/* Check Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {gateChecks.map((check) => {
                const isFail = check.status === "FAIL";

                return (
                  <div
                    key={check.name}
                    className={`p-2.5 rounded-lg border transition-colors flex items-center justify-between text-xs ${
                      isFail
                        ? "border-[#A85F59]/60 bg-[#A85F59]/10 text-[#171816]"
                        : "border-[#D9D5CA] bg-[#EEEAE0] text-[#62635C]"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-[#62635C]">{check.num}</span>
                      <span className="font-bold">{check.name}</span>
                    </div>

                    {isFail ? (
                      <span className="font-mono text-[10px] font-bold text-[#A85F59] px-2 py-0.5 rounded-md bg-[#A85F59]/20 border border-[#A85F59]/40">
                        FAIL
                      </span>
                    ) : (
                      <span className="font-mono text-[10px] font-bold text-[#65745F] px-2 py-0.5 rounded-md bg-[#65745F]/15 border border-[#65745F]/30">
                        PASS
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* The System Halts: BLOCKED. REVIEW REQUIRED. */}
          <motion.div
            style={{ opacity: blockedOpacity, scale: blockedScale }}
            className="rounded-2xl border border-[#A85F59]/60 bg-[#F8F6F0] p-6 text-center space-y-3 shadow-xs"
          >
            <div className="inline-flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-[#A85F59] font-bold">
              <AlertTriangle className="h-4 w-4" />
              <span>BRIDGE INVARIANT VIOLATION: gross - fee - tax &ne; net</span>
            </div>

            <h3 className="font-display text-3xl sm:text-5xl font-medium tracking-tight text-[#A85F59]">
              BLOCKED.
            </h3>

            <div className="text-sm sm:text-base font-mono font-semibold text-[#171816] tracking-widest uppercase">
              REVIEW REQUIRED &middot; AUTOMATION HALTED
            </div>

            <p className="font-mono text-xs text-[#62635C] max-w-lg mx-auto leading-relaxed">
              The AI proposal had 94% confidence, but the deterministic gate refused authorization.
              Zero incorrect ledger postings. The case is safely routed to a human controller.
            </p>
          </motion.div>
        </div>

        {/* Bottom Pinned Footer */}
        <div className="mx-auto w-full max-w-6xl flex items-center justify-between text-[11px] font-mono text-[#62635C] border-t border-[#D9D5CA] pt-3">
          <span>AI CAN INVESTIGATE. DETERMINISTIC SOFTWARE AUTHORIZES.</span>
          <span>SYSTEM FAILS CLOSED</span>
        </div>
      </div>
    </section>
  );
}
