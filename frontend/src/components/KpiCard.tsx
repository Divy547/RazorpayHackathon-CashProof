import { cn } from "@/lib/cn";
import type { Tone } from "@/components/Badge";

const TONE_TEXT: Record<Tone, string> = {
  success: "text-[#65745F]",
  warning: "text-[#A47C52]",
  danger: "text-[#A85F59]",
  neutral: "text-[#171816]",
  info: "text-[#4E6870]",
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
        "rounded-xl border bg-[#F8F6F0] p-4 transition-colors",
        emphasize
          ? "border-[#65745F]/40 ring-1 ring-[#65745F]/20 bg-[#EEEAE0]"
          : "border-[#D9D5CA]",
      )}
    >
      <div className="text-[11px] font-medium uppercase tracking-wider text-[#62635C]">{label}</div>
      <div className={cn("mt-2 font-mono text-3xl font-semibold tabular-nums", TONE_TEXT[tone])}>
        {value}
      </div>
      {hint && <div className="mt-1.5 text-xs text-[#62635C]">{hint}</div>}
    </div>
  );
}
