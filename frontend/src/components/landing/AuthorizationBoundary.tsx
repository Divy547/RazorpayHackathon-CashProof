import {
  ArrowDown,
  Bot,
  CheckCircle2,
  Lock,
  Scale,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";

export function AuthorizationBoundary() {
  const aiActions = [
    { label: "Inspect", desc: "Examines allowed source facts, candidate pools, and narrations" },
    { label: "Retrieve Evidence", desc: "Searches related gateway items and bank records within window" },
    { label: "Investigate Ambiguity", desc: "Synthesizes fee deductions, customer aliases, and timestamps" },
    { label: "Propose / Abstain", desc: "Emits a candidate target set with explicit confidence score or abstains" },
  ];

  const gateChecks = [
    { name: "IDENTITY", req: "Candidate entry exists in authoritative pool" },
    { name: "BRIDGE", req: "Gross - Fee - Tax - Refund + Adj == Net" },
    { name: "CURRENCY", req: "ISO currency code exact match" },
    { name: "UNIQUENESS", req: "Target not already consumed by another case" },
    { name: "EVIDENCE", req: "Valid provenance links established" },
    { name: "CONFLICT", req: "No contradictory records present" },
    { name: "POLICY", req: "Unstructured text requires human approval" },
    { name: "STATE", req: "Valid monotonic case transition" },
  ];

  return (
    <section id="authorization" className="py-20 bg-[#FFFFFF] border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#F4F6F8] px-2.5 py-1 text-[11px] font-mono text-[#475467]">
            FIREWALL SEPARATION
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-[#101828] sm:text-4xl">
            The AI Authorization Boundary
          </h2>
          <p className="text-base sm:text-lg text-[#475467] leading-relaxed">
            In CashProof, the boundary between generating a hypothesis and committing a financial transaction
            is non-porous. AI proposals have zero monetary authority until validated by the deterministic Gate.
          </p>
        </div>

        {/* The Central Visual Diagram */}
        <div className="mt-14 max-w-4xl mx-auto space-y-0 rounded-xl border border-[#DDE2E7] bg-[#FFFFFF] shadow-sm overflow-hidden">
          {/* Top Zone: AI Investigator (Warm / Amber / Exploratory) */}
          <div className="bg-[#FFFBEB]/40 p-6 sm:p-8 space-y-5 border-b border-[#DDE2E7]">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded bg-[#D98B20]/15 text-[#D98B20] border border-[#D98B20]/30">
                  <Bot className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-mono text-sm font-bold text-[#101828]">
                    AI INVESTIGATOR (BOUNDED)
                  </h3>
                  <span className="text-xs text-[#475467]">
                    Probabilistic exploration &middot; 5 tool calls &middot; 4,000 tokens maximum
                  </span>
                </div>
              </div>
              <span className="font-mono text-[10px] uppercase font-bold text-[#D98B20] bg-[#D98B20]/10 border border-[#D98B20]/30 px-2.5 py-1 rounded">
                READ-ONLY SANDBOX
              </span>
            </div>

            {/* AI Steps Flow */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
              {aiActions.map((action, idx) => (
                <div
                  key={action.label}
                  className="rounded border border-[#D98B20]/20 bg-[#FFFFFF] p-3 space-y-1"
                >
                  <div className="flex items-center justify-between font-mono text-xs font-bold text-[#D98B20]">
                    <span>0{idx + 1}</span>
                    <span>{action.label}</span>
                  </div>
                  <p className="text-[11px] text-[#475467] leading-relaxed">{action.desc}</p>
                </div>
              ))}
            </div>

            <div className="text-center">
              <div className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-[#D98B20] bg-[#FFFFFF] border border-[#D98B20]/30 px-3 py-1 rounded shadow-2xs">
                <span>Output: ResolutionProposal(target_entry_ids, confidence, rationale)</span>
                <ArrowDown className="h-3.5 w-3.5" />
              </div>
            </div>
          </div>

          {/* THE HARD AUTHORIZATION BOUNDARY LINE */}
          <div className="bg-[#101828] text-white px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
            <div className="flex items-center gap-2 font-mono text-xs font-bold tracking-widest text-[#FFFFFF]">
              <Lock className="h-4 w-4 text-[#3157D5]" />
              <span>================ AUTHORIZATION BOUNDARY ================</span>
            </div>
            <div className="text-[11px] font-mono text-slate-300">
              AI CANNOT MOVE MONEY &middot; FAILS CLOSED
            </div>
          </div>

          {/* Bottom Zone: Deterministic Gate (Cobalt / Green / Authoritative) */}
          <div className="bg-[#F4F6F8]/60 p-6 sm:p-8 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded bg-[#3157D5]/15 text-[#3157D5] border border-[#3157D5]/30">
                  <Scale className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="font-mono text-sm font-bold text-[#101828]">
                    DETERMINISTIC GATE (FIREWALL)
                  </h3>
                  <span className="text-xs text-[#475467]">
                    Function: evaluate_gate() &middot; Absolute mathematical verification
                  </span>
                </div>
              </div>
              <span className="font-mono text-[10px] uppercase font-bold text-[#12A67A] bg-[#12A67A]/10 border border-[#12A67A]/30 px-2.5 py-1 rounded">
                SOLE AUTHORIZATION FIREWALL
              </span>
            </div>

            {/* Gate Checks Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs">
              {gateChecks.map((chk) => (
                <div
                  key={chk.name}
                  className="rounded border border-[#DDE2E7] bg-[#FFFFFF] p-2.5 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#101828]">{chk.name}</span>
                    <ShieldCheck className="h-3.5 w-3.5 text-[#12A67A]" />
                  </div>
                  <div className="text-[10px] text-[#475467] leading-tight font-sans">
                    {chk.req}
                  </div>
                </div>
              ))}
            </div>

            {/* Resolution Terminal */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2 font-mono text-xs">
              <div className="flex items-center gap-2 rounded border border-[#12A67A]/30 bg-[#12A67A]/10 px-4 py-2 font-bold text-[#12A67A]">
                <CheckCircle2 className="h-4 w-4" />
                ALL 9 CHECKS PASSED &rarr; AUTO_RESOLVED
              </div>
              <div className="flex items-center gap-2 rounded border border-[#D98B20]/30 bg-[#D98B20]/10 px-4 py-2 font-bold text-[#D98B20]">
                <ShieldAlert className="h-4 w-4" />
                ANY CHECK FAILED &rarr; HUMAN_REVIEW
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Epigram */}
        <div className="mt-8 text-center">
          <p className="font-mono text-xs font-semibold text-[#475467]">
            &ldquo;AI investigates. Deterministic software authorizes.&rdquo;
          </p>
        </div>
      </div>
    </section>
  );
}
