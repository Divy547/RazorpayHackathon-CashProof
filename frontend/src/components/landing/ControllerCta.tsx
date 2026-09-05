import Link from "next/link";
import { ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";

export function ControllerCta() {
  return (
    <section className="py-20 bg-[#101828] text-white relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 sm:px-8 text-center space-y-8">
        <div className="max-w-2xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 rounded border border-white/20 bg-white/5 px-3 py-1 text-xs font-mono text-white/80">
            <ShieldCheck className="h-4 w-4 text-[#12A67A]" />
            <span>FINANCIAL CONTROLLER RUNTIME</span>
          </div>

          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl lg:text-5xl text-white">
            See the controller in action.
          </h2>

          <p className="text-base sm:text-lg text-[#DDE2E7] leading-relaxed max-w-xl mx-auto">
            Run a reconciliation batch. Inspect the evidence. Challenge an exception. Watch the gate
            decide.
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-[#3157D5] px-7 py-3.5 text-sm font-semibold text-white shadow-md transition-all hover:bg-[#2747B5] hover:shadow-lg active:scale-[0.98]"
          >
            <span>Open CashProof</span>
            <ArrowRight className="h-4 w-4" />
          </Link>

          <Link
            href="/cases"
            className="inline-flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-6 py-3.5 text-sm font-medium text-white transition-all hover:bg-white/15"
          >
            Explore Cases
          </Link>
        </div>

        {/* Guarantees */}
        <div className="pt-6 flex flex-wrap justify-center items-center gap-8 text-xs text-[#DDE2E7]/80 font-mono">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-[#12A67A]" />
            Deterministic Invariants
          </span>
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-[#12A67A]" />
            Bounded AI Budgets
          </span>
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-[#12A67A]" />
            Fails Closed by Default
          </span>
        </div>
      </div>
    </section>
  );
}
