"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, Menu, X } from "lucide-react";
import { cn } from "@/lib/cn";

const LINKS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/cases", label: "Case Explorer" },
  { href: "/exceptions", label: "Exception Intelligence" },
  { href: "/gate", label: "Gate Intelligence" },
  { href: "/confidence", label: "Confidence" },
  { href: "/scenarios", label: "Scenario Demo" },
  { href: "/benchmark", label: "Benchmark" },
  { href: "/ingestion", label: "Data Sources" },
];

export function Nav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-[#D9D5CA] bg-[#F8F6F0]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-2.5">
        <Link href="/dashboard" className="flex items-baseline gap-2">
          <span className="flex items-center gap-1.5 text-sm font-semibold tracking-tight text-[#171816]">
            <ShieldCheck className="h-4 w-4 text-[#65745F]" />
            CashProof
          </span>
          <span className="hidden text-xs text-[#62635C] md:inline">
            Evidence-First Settlement Control
          </span>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => {
            const active =
              link.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                  active
                    ? "border border-[#D9D5CA] bg-[#EEEAE0] text-[#171816]"
                    : "text-[#62635C] hover:bg-[#EEEAE0]/70 hover:text-[#171816]",
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Mobile menu toggle */}
        <div className="md:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-[#D9D5CA] bg-[#F8F6F0] text-[#62635C] hover:text-[#171816]"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="border-t border-[#D9D5CA] bg-[#F8F6F0] px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            {LINKS.map((link) => {
              const active =
                link.href === "/dashboard"
                  ? pathname === "/dashboard"
                  : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-colors",
                    active
                      ? "border border-[#D9D5CA] bg-[#EEEAE0] text-[#171816]"
                      : "text-[#62635C] hover:bg-[#EEEAE0]/70 hover:text-[#171816]",
                  )}
                >
                  <span>{link.label}</span>
                  {active && <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}
