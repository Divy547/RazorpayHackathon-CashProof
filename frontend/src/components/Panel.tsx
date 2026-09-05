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
    <section id={id} className={cn("rounded-xl border border-[#D9D5CA] bg-[#F8F6F0]", className)}>
      <div className="border-b border-[#D9D5CA] px-5 py-3.5 bg-[#F8F6F0]">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[#171816]">{title}</h2>
        {subtitle && <p className="mt-0.5 text-xs text-[#62635C]">{subtitle}</p>}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}
