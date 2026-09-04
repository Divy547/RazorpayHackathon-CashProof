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
          "flex items-center justify-between rounded-md border px-4 py-2.5",
          gate.passed
            ? "border-emerald-500/30 bg-emerald-500/10"
            : "border-red-500/30 bg-red-500/10",
        )}
      >
        <span
          className={cn(
            "flex items-center gap-2 text-sm font-semibold",
            gate.passed ? "text-emerald-400" : "text-red-400",
          )}
        >
          {gate.passed ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
          {gate.passed ? "GATE PASSED" : "GATE FAILED"}
        </span>
        {gate.failing_check && (
          <span className="text-xs font-medium text-red-300">
            Failing check: {CHECK_LABELS[gate.failing_check] ?? gate.failing_check}
          </span>
        )}
      </div>

      <ul className="divide-y divide-slate-800 rounded-md border border-slate-800">
        {gate.checks.map((check) => (
          <li key={check.name} className="flex items-start gap-3 px-4 py-2.5">
            {check.passed ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
            ) : (
              <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
            )}
            <div className="min-w-0">
              <div className="text-sm font-medium text-slate-200">
                {CHECK_LABELS[check.name] ?? check.name}
              </div>
              <div className="text-xs text-slate-500">{check.reason}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
