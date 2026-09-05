import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-[#DDE2E7] bg-[#FFFFFF] py-14 text-[#475467]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
          {/* Brand Column */}
          <div className="md:col-span-4 space-y-3">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#3157D5] text-white">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="font-semibold text-base text-[#101828] tracking-tight">
                CashProof
              </span>
            </Link>
            <p className="text-xs text-[#475467] leading-relaxed max-w-sm">
              Evidence-First Settlement Controller. Deterministic software owns monetary truth. AI
              investigates ambiguity. Every decision is explainable.
            </p>
            <div className="font-mono text-[11px] text-[#475467] pt-1">
              Razorpay Buildathon 2026 &middot; Track 4
            </div>
          </div>

          {/* Links Column 1: Controller */}
          <div className="md:col-span-3 space-y-2.5">
            <div className="text-xs font-mono font-semibold uppercase tracking-wider text-[#101828]">
              Operational Controller
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/dashboard" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Overview Dashboard
                </Link>
              </li>
              <li>
                <Link href="/cases" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Reconciliation Cases
                </Link>
              </li>
              <li>
                <Link href="/exceptions" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Exception Intelligence
                </Link>
              </li>
              <li>
                <Link href="/ingestion" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Source Feed Ingestion
                </Link>
              </li>
            </ul>
          </div>

          {/* Links Column 2: Audit & Proof */}
          <div className="md:col-span-3 space-y-2.5">
            <div className="text-xs font-mono font-semibold uppercase tracking-wider text-[#101828]">
              Audit & Verification
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/benchmark" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Benchmark Suite (Seed 42)
                </Link>
              </li>
              <li>
                <Link href="/scenarios" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Controlled Scenarios (S1-S6)
                </Link>
              </li>
              <li>
                <Link href="/gate" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Deterministic Gate Firewall
                </Link>
              </li>
              <li>
                <Link href="/confidence" className="text-[#475467] hover:text-[#3157D5] transition-colors">
                  Confidence Intelligence
                </Link>
              </li>
            </ul>
          </div>

          {/* Invariant Guarantees Column */}
          <div className="md:col-span-2 space-y-2.5">
            <div className="text-xs font-mono font-semibold uppercase tracking-wider text-[#101828]">
              Guarantees
            </div>
            <div className="space-y-1.5 font-mono text-[11px] text-[#475467]">
              <div>&bull; Integer Minor Units</div>
              <div>&bull; GST 18% Immutability</div>
              <div>&bull; Fail-Closed Default</div>
              <div>&bull; Zero Model Writes</div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-6 border-t border-[#DDE2E7] flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#475467] font-mono">
          <span>
            &copy; {new Date().getFullYear()} CashProof &middot; Built for Razorpay Buildathon 2026
          </span>
          <span>Invariant Engine v1.0.0 &middot; Fails Closed by Default</span>
        </div>
      </div>
    </footer>
  );
}
