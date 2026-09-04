import { cn } from "@/lib/cn";
import type { Tone } from "@/components/Badge";

const TONE_TEXT: Record<Tone, string> = {
  success: "text-emerald-400",
  warning: "text-amber-400",
  danger: "text-red-400",
  neutral: "text-slate-100",
  info: "text-sky-400",
};

export function KpiCard({
  label,
  value,
  tone = "neutral",
  hint,
  emphasize = false,
}: {
  label: string;
  value: string | number;
  tone?: Tone;
  hint?: string;
  emphasize?: boolean;
}) {
  return (
    <div
      className={cn(
        "rounded-lg border bg-[#0d1219] p-4",
        emphasize ? "border-emerald-500/40 ring-1 ring-emerald-500/20" : "border-slate-800",
      )}
    >
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={cn("mt-2 text-3xl font-semibold tabular-nums", TONE_TEXT[tone])}>
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}
