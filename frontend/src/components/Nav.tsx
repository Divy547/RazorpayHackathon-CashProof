"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { cn } from "@/lib/cn";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/cases", label: "Case Explorer" },
  { href: "/exceptions", label: "Exception Intelligence" },
  { href: "/gate", label: "Gate Intelligence" },
  { href: "/confidence", label: "Confidence" },
  { href: "/scenarios", label: "Scenario Demo" },
  { href: "/benchmark", label: "Benchmark" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-slate-800 bg-[#0b0f16]/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="flex items-center gap-1.5 text-sm font-semibold tracking-tight text-slate-100">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            CashProof
          </span>
          <span className="hidden text-xs text-slate-500 sm:inline">
            Evidence-First Settlement Control
          </span>
        </Link>
        <nav className="flex gap-1">
          {LINKS.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded px-3 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-slate-800 text-slate-100"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
