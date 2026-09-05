import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type Tone = "success" | "warning" | "danger" | "neutral" | "info";

const TONE_CLASSES: Record<Tone, string> = {
  success: "bg-[#65745F]/12 text-[#65745F] border-[#65745F]/25",
  warning: "bg-[#A47C52]/12 text-[#A47C52] border-[#A47C52]/25",
  danger: "bg-[#A85F59]/12 text-[#A85F59] border-[#A85F59]/25",
  neutral: "bg-[#EEEAE0] text-[#62635C] border-[#D9D5CA]",
  info: "bg-[#4E6870]/12 text-[#4E6870] border-[#4E6870]/25",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border px-2 py-0.5 text-xs font-mono font-medium tracking-tight",
        TONE_CLASSES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
