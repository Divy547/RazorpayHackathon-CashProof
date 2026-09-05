import { ShieldCheck } from "lucide-react";

export function CoreThesis() {
  const steps = [
    {
      code: "01",
      pillar: "CERTAINTY",
      system: "Deterministic reconciliation",
      detail:
        "Exact arithmetic bridge equations, explicit currency checks, integer paise, and strict candidate windows. Math owns monetary truth.",
      borderTone: "border-[#DDE2E7]",
      accentTone: "text-[#3157D5]",
    },
    {
      code: "02",
      pillar: "AMBIGUITY",
      system: "Bounded investigation",
      detail:
        "When narrations diverge or deductions create variance, bounded AI inspects evidence and formulates a hypothesis. It proposes; it never decides.",
      borderTone: "border-[#D98B20]/40",
      accentTone: "text-[#D98B20]",
    },
    {
      code: "03",
      pillar: "AUTHORIZATION",
      system: "Deterministic gate",
      detail:
        "Every proposal must satisfy all 9 invariant checks. If an arithmetic bridge fails or a reference is ambiguous, the system halts automation and fails closed.",
      borderTone: "border-[#3157D5]/40",
      accentTone: "text-[#3157D5]",
    },
    {
      code: "04",
      pillar: "AUDIT",
      system: "Evidence-backed decision",
      detail:
        "An immutable audit receipt binds settlement IDs, candidate sources, gate logs, and reviewer outcomes. Zero black-box mutations reach the ledger.",
      borderTone: "border-[#12A67A]/40",
      accentTone: "text-[#12A67A]",
    },
  ];

  return (
    <section id="thesis" className="py-20 bg-[#FFFFFF] border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#F4F6F8] px-2.5 py-1 text-[11px] font-mono text-[#475467]">
            SYSTEM PRINCIPLES
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-[#101828] sm:text-4xl leading-tight">
            Use deterministic software for certainty.
            <br />
            Use AI for ambiguity.
            <br />
            Use evidence to explain the decision.
          </h2>
          <p className="text-base sm:text-lg text-[#475467] leading-relaxed">
            Most automated finance software treats AI as an autonomous decision-maker.
            CashProof treats AI as a bounded investigator and deterministic software as the sole financial gatekeeper.
          </p>
        </div>

        {/* System Hierarchy Architecture (Flowing Column Layout) */}
        <div className="mt-14 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {steps.map((step) => (
              <div
                key={step.pillar}
                className={`relative rounded-lg border ${step.borderTone} bg-[#F4F6F8]/60 p-6 flex flex-col justify-between transition-all hover:bg-[#FFFFFF] hover:shadow-xs`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between font-mono text-xs text-[#475467]">
                    <span>{step.code}</span>
                    <span className={`font-bold ${step.accentTone}`}>{step.pillar}</span>
                  </div>
                  <h3 className="text-base font-semibold text-[#101828] leading-snug">
                    {step.system}
                  </h3>
                  <p className="text-xs text-[#475467] leading-relaxed pt-1">
                    {step.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Architectural Comparison Statement */}
          <div className="rounded-lg border border-[#DDE2E7] bg-[#F4F6F8] p-6 sm:p-7 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="space-y-1 max-w-2xl">
              <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#3157D5]">
                ARCHITECTURAL RULE
              </span>
              <p className="text-sm font-medium text-[#101828] leading-relaxed">
                The AI investigator has read-only tools and zero write-access to source facts.
                Every resolution path terminates at a deterministic gate check that computes monetary equality down to the single paise.
              </p>
            </div>
            <div className="shrink-0 flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#FFFFFF] px-4 py-2 text-xs font-mono text-[#101828] shadow-2xs">
              <ShieldCheck className="h-4 w-4 text-[#12A67A]" />
              <span>FAIL_CLOSED = TRUE</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
