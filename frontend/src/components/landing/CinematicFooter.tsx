"use client";

import Link from "next/link";

export function CinematicFooter() {
  return (
    <footer className="bg-[#F3F0E8] py-16 text-[#62635C] border-t border-[#D9D5CA]">
      <div className="mx-auto max-w-6xl px-6 sm:px-8 space-y-12">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
          {/* Brand Identity */}
          <div className="md:col-span-5 space-y-3">
            <Link href="/" className="flex items-center gap-3">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#D9D5CA] bg-[#F8F6F0] font-mono text-xs font-bold text-[#171816] shadow-xs">
                CP
              </div>
              <span className="font-medium text-sm text-[#171816] tracking-tight">
                CashProof
              </span>
            </Link>
            <p className="font-mono text-xs text-[#62635C] leading-relaxed max-w-sm">
              Evidence-First Settlement Controller. Deterministic software owns monetary truth. AI
              investigates ambiguity. Every decision is explainable.
            </p>
            <div className="font-mono text-[11px] text-[#4E6870] pt-1">
              Razorpay Buildathon 2026 &middot; Track 4
            </div>
          </div>

          {/* Links 1: Operational Controller */}
          <div className="md:col-span-3 space-y-3 font-mono text-xs">
            <div className="text-[10px] uppercase tracking-widest text-[#171816] font-semibold">
              Operational Controller
            </div>
            <ul className="space-y-2">
              <li>
                <Link href="/dashboard" className="hover:text-[#171816] transition-colors">
                  Overview Dashboard
                </Link>
              </li>
              <li>
                <Link href="/cases" className="hover:text-[#171816] transition-colors">
                  Reconciliation Cases
                </Link>
              </li>
              <li>
                <Link href="/exceptions" className="hover:text-[#171816] transition-colors">
                  Exception Intelligence
                </Link>
              </li>
              <li>
                <Link href="/ingestion" className="hover:text-[#171816] transition-colors">
                  Source Feed Ingestion
                </Link>
              </li>
            </ul>
          </div>

          {/* Links 2: Verification & Audit */}
          <div className="md:col-span-4 space-y-3 font-mono text-xs">
            <div className="text-[10px] uppercase tracking-widest text-[#171816] font-semibold">
              Audit &amp; Verification
            </div>
            <ul className="space-y-2">
              <li>
                <Link href="/benchmark" className="hover:text-[#171816] transition-colors">
                  Benchmark Suite (Seed 42)
                </Link>
              </li>
              <li>
                <Link href="/scenarios" className="hover:text-[#171816] transition-colors">
                  Controlled Scenarios (S1-S6)
                </Link>
              </li>
              <li>
                <Link href="/gate" className="hover:text-[#171816] transition-colors">
                  Deterministic Gate Firewall
                </Link>
              </li>
              <li>
                <Link href="/confidence" className="hover:text-[#171816] transition-colors">
                  Confidence Intelligence
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[#D9D5CA] flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-[11px] text-[#62635C]">
          <span>
            &copy; {new Date().getFullYear()} CashProof &middot; Built for Razorpay Buildathon 2026
          </span>
          <span>Invariant Engine v1.0.0 &middot; Fails Closed by Default</span>
        </div>
      </div>
    </footer>
  );
}
