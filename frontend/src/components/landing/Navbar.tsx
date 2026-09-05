"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#F3F0E8]/90 backdrop-blur-md border-b border-[#D9D5CA] py-3.5"
          : "bg-transparent py-5"
      }`}
    >
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        <div className="flex items-center justify-between">
          {/* Brand Identity */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#D9D5CA] bg-[#F8F6F0] font-mono text-xs font-bold text-[#171816] transition-colors group-hover:border-[#A47C52]/60 shadow-xs">
              CP
            </div>
            <div className="flex flex-col">
              <span className="font-medium text-sm text-[#171816] tracking-tight">
                CashProof
              </span>
              <span className="font-mono text-[9px] uppercase tracking-widest text-[#62635C]">
                EVIDENCE-FIRST CONTROL
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8 text-xs font-mono tracking-wider uppercase text-[#62635C]">
            <Link
              href="#thesis"
              className="transition-colors hover:text-[#171816]"
            >
              Thesis
            </Link>
            <Link
              href="#architecture"
              className="transition-colors hover:text-[#171816]"
            >
              Architecture
            </Link>
            <Link
              href="#gate"
              className="transition-colors hover:text-[#171816]"
            >
              Gate Firewall
            </Link>
            <Link
              href="#benchmark"
              className="transition-colors hover:text-[#171816]"
            >
              Benchmark
            </Link>
            <Link
              href="#scenarios"
              className="transition-colors hover:text-[#171816]"
            >
              Scenarios
            </Link>
          </nav>

          {/* Controller Action */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-[10px] border border-[#D9D5CA] bg-[#F8F6F0] px-3.5 py-1.5 font-mono text-xs uppercase tracking-wider text-[#171816] transition-all hover:bg-[#EEEAE0] hover:border-[#A47C52]/60 shadow-xs"
            >
              <span>OPEN CONTROLLER</span>
              <ArrowRight className="h-3.5 w-3.5 text-[#A47C52]" />
            </Link>
          </div>

          {/* Mobile Menu Trigger */}
          <div className="flex md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 text-[#62635C] hover:text-[#171816]"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[#D9D5CA] bg-[#F3F0E8]/95 backdrop-blur-xl px-6 py-6 space-y-4 font-mono text-xs uppercase tracking-wider shadow-md">
          <Link
            href="#thesis"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-[#62635C] hover:text-[#171816]"
          >
            Thesis
          </Link>
          <Link
            href="#architecture"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-[#62635C] hover:text-[#171816]"
          >
            Architecture
          </Link>
          <Link
            href="#gate"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-[#62635C] hover:text-[#171816]"
          >
            Gate Firewall
          </Link>
          <Link
            href="#benchmark"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-[#62635C] hover:text-[#171816]"
          >
            Benchmark
          </Link>
          <Link
            href="#scenarios"
            onClick={() => setMobileMenuOpen(false)}
            className="block text-[#62635C] hover:text-[#171816]"
          >
            Scenarios
          </Link>
          <div className="pt-2 border-t border-[#D9D5CA]">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded border border-[#D9D5CA] bg-[#F8F6F0] px-4 py-2 text-xs uppercase text-[#171816]"
            >
              <span>OPEN CONTROLLER</span>
              <ArrowRight className="h-3.5 w-3.5 text-[#A47C52]" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
