import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Panel({
  title,
  subtitle,
  children,
  className,
  id,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn("rounded-lg border border-slate-800 bg-[#0d1219]", className)}>
      <div className="border-b border-slate-800 px-5 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-200">{title}</h2>
        {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}
