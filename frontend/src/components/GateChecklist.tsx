import { CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/cn";
import type { GateResult } from "@/lib/types";

const CHECK_LABELS: Record<string, string> = {
  IDENTITY: "Identity",
  BRIDGE: "Bridge",
  CURRENCY: "Currency",
  UNIQUENESS: "Uniqueness",
  EVIDENCE_COMPLETENESS: "Evidence Completeness",
  CONFLICT: "Conflict",
  POLICY: "Policy",
  STATE_TRANSITION: "State Transition",
  TARGET_SET_EQUALITY: "Target Set Equality",
};

export function GateChecklist({ gate }: { gate: GateResult }) {
  return (
    <div className="space-y-3">
      <div
        className={cn(
          "flex items-center justify-between rounded-xl border px-4 py-3",
          gate.passed
            ? "border-[#3B5145]/30 bg-[#3B5145]/10"
            : "border-[#9A514C]/30 bg-[#9A514C]/10",
        )}
      >
        <span
          className={cn(
            "flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider",
            gate.passed ? "text-[#3B5145]" : "text-[#9A514C]",
          )}
        >
          {gate.passed ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
          {gate.passed ? "GATE PASSED" : "GATE BLOCKED"}
        </span>
        {gate.failing_check && (
          <span className="font-mono text-xs font-semibold text-[#9A514C]">
            Failing check: {CHECK_LABELS[gate.failing_check] ?? gate.failing_check}
          </span>
        )}
      </div>

      <ul className="divide-y divide-[#D9D5CA] rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] overflow-hidden">
        {gate.checks.map((check) => (
          <li
            key={check.name}
            className={cn(
              "flex items-start gap-3 px-4 py-3 transition-colors",
              check.passed ? "hover:bg-[#F2ECE1]/50" : "bg-[#9A514C]/5 hover:bg-[#9A514C]/10",
            )}
          >
            {check.passed ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#3B5145]" />
            ) : (
              <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-[#9A514C]" />
            )}
            <div className="min-w-0">
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#171816]">
                {CHECK_LABELS[check.name] ?? check.name}
              </div>
              <div className="mt-0.5 text-xs text-[#4F514A] leading-relaxed">{check.reason}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
