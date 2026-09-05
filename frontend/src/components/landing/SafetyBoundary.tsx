import {
  Ban,
  CheckCircle2,
  Lock,
  Shield,
  ShieldCheck,
  XCircle,
} from "lucide-react";

export function SafetyBoundary() {
  const gateChecks = [
    {
      num: "01",
      name: "IDENTITY",
      formula: "candidate.id in authoritative_pool",
      req: "Target bank ledger entry exists and matches candidate record ID",
      crit: "Mandatory",
    },
    {
      num: "02",
      name: "BRIDGE",
      formula: "gross - fee - tax - refund + adj == net",
      req: "Authoritative financial equation matches deposited net to the exact paisa",
      crit: "Mandatory",
    },
    {
      num: "03",
      name: "CURRENCY",
      formula: "settlement.currency == candidate.currency",
      req: "Exact ISO 4217 currency match across all transaction legs (INR)",
      crit: "Mandatory",
    },
    {
      num: "04",
      name: "UNIQUENESS",
      formula: "count(resolved_where(entry_id)) == 0",
      req: "Ledger entry not already consumed by another settlement across the system",
      crit: "Mandatory",
    },
    {
      num: "05",
      name: "EVIDENCE",
      formula: "provenance.verified == True",
      req: "Structured reference provenance or verified narration match confirmed",
      crit: "Mandatory",
    },
    {
      num: "06",
      name: "CONFLICT",
      formula: "len(contradictory_candidates) == 0",
      req: "No contradictory records or conflicting amounts present in candidate pool",
      crit: "Mandatory",
    },
    {
      num: "07",
      name: "POLICY",
      formula: "match_tier != TIER_UNSTRUCTURED or human_approved",
      req: "Unstructured text or heuristic alias matches require human controller sign-off",
      crit: "Mandatory",
    },
    {
      num: "08",
      name: "STATE_TRANSITION",
      formula: "CLASSIFIED -> GATED -> CLOSED",
      req: "Monotonic progression; no backwards transitions or silent side-effects",
      crit: "Mandatory",
    },
    {
      num: "09",
      name: "TARGET_SET_EQUALITY",
      formula: "proposal.target_ids == evaluated.target_ids",
      req: "Proposed target record set exactly equals the validated resolution set",
      crit: "Mandatory",
    },
  ];

  const aiPermissions = [
    { text: "Inspect allowed source financial facts, candidate pool, and narrations" },
    { text: "Retrieve related payment gateway items and bank transactions within time window" },
    { text: "Synthesize deduction discrepancies, fee schedules, and tax variances" },
    { text: "Explain ambiguous evidence in plain English for financial controllers" },
    { text: "Propose a candidate target record set with explicit confidence score" },
    { text: "Abstain explicitly when evidence is insufficient, contradictory, or missing" },
  ];

  const aiForbidden = [
    { text: "Cannot modify immutable source facts, bank statements, or ledger rows" },
    { text: "Cannot define or alter monetary truth (amounts, fees, taxes, or nets)" },
    { text: "Cannot bypass or relax any of the nine deterministic gate checks" },
    { text: "Cannot approve or authorize its own resolution proposal" },
    { text: "Cannot move money, initiate bank transfers, or issue credit adjustments" },
    { text: "Cannot access hidden ground truth or use confidence as an authorization input" },
  ];

  return (
    <section id="safety" className="py-20 bg-[#F4F6F8] border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#FFFFFF] px-2.5 py-1 text-[11px] font-mono text-[#475467]">
            <span>FIREWALL ENFORCEMENT // 9 INVARIANTS</span>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-[#101828] sm:text-4xl">
            The Deterministic Safety Boundary
          </h2>
          <p className="text-base sm:text-lg text-[#475467] leading-relaxed">
            In CashProof, AI is strictly sandboxed. Every resolution proposal must satisfy all nine
            mandatory checks of the deterministic gate before a single ledger entry is finalized.
          </p>
        </div>

        {/* Central Invariant Callout */}
        <div className="mt-8 rounded-xl border border-[#3157D5]/20 bg-[#FFFFFF] p-5 shadow-2xs flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Lock className="h-5 w-5 text-[#3157D5] shrink-0" />
            <p className="text-sm text-[#101828]">
              <strong className="font-semibold text-[#101828]">Core Law:</strong>{" "}
              <span className="text-[#475467]">
                The model can reason about the case. It cannot redefine the case.
              </span>
            </p>
          </div>
          <span className="hidden sm:inline-block font-mono text-[10px] uppercase font-bold text-[#3157D5] bg-[#3157D5]/10 px-2 py-0.5 rounded border border-[#3157D5]/20">
            Fail-Closed
          </span>
        </div>

        {/* Permissions vs Forbidden Grid */}
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* AI Sandbox: Allowed */}
          <div className="rounded-2xl border border-[#DDE2E7] bg-[#FFFFFF] p-6 sm:p-7 space-y-4 shadow-2xs">
            <div className="flex items-center justify-between border-b border-[#DDE2E7] pb-4">
              <div className="flex items-center gap-2 text-[#3157D5]">
                <Shield className="h-5 w-5" />
                <h3 className="text-base font-semibold text-[#101828]">What AI Is Permitted To Do</h3>
              </div>
              <span className="text-[10px] font-mono font-semibold text-[#3157D5] bg-[#3157D5]/10 border border-[#3157D5]/30 px-2 py-0.5 rounded">
                Investigator Scope
              </span>
            </div>
            <p className="text-xs text-[#475467]">
              Bounded to a strict budget of 5 tool calls and 4,000 tokens per investigation case.
            </p>
            <ul className="space-y-2.5 pt-1">
              {aiPermissions.map((p, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-[#101828]">
                  <CheckCircle2 className="h-4 w-4 text-[#12A67A] mt-0.5 shrink-0" />
                  <span className="leading-relaxed">{p.text}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Hard Constraints: Forbidden */}
          <div className="rounded-2xl border border-[#D64545]/30 bg-[#FFFFFF] p-6 sm:p-7 space-y-4 shadow-2xs">
            <div className="flex items-center justify-between border-b border-[#DDE2E7] pb-4">
              <div className="flex items-center gap-2 text-[#D64545]">
                <Ban className="h-5 w-5" />
                <h3 className="text-base font-semibold text-[#101828]">What AI Is Strictly Forbidden From Doing</h3>
              </div>
              <span className="text-[10px] font-mono font-semibold text-[#D64545] bg-[#D64545]/10 border border-[#D64545]/30 px-2 py-0.5 rounded">
                Zero Authority
              </span>
            </div>
            <p className="text-xs text-[#475467]">
              Zero write-access to the financial ledger. Hardcoded fail-closed boundary enforcement.
            </p>
            <ul className="space-y-2.5 pt-1">
              {aiForbidden.map((p, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-[#101828]">
                  <XCircle className="h-4 w-4 text-[#D64545] mt-0.5 shrink-0" />
                  <span className="font-medium leading-relaxed">{p.text}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* The 9 Deterministic Gate Checks Table */}
        <div className="mt-10 rounded-2xl border border-[#DDE2E7] bg-[#FFFFFF] shadow-2xs overflow-hidden">
          <div className="border-b border-[#DDE2E7] bg-[#F4F6F8] px-6 py-4 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-[#12A67A]" />
              <h3 className="text-sm font-semibold text-[#101828]">
                The Nine Mandatory Gate Checks
              </h3>
            </div>
            <span className="text-xs font-mono text-[#475467]">
              Function: <strong className="text-[#101828]">evaluate_gate(proposal, case)</strong>
            </span>
          </div>

          <div className="divide-y divide-[#DDE2E7]">
            {gateChecks.map((check) => (
              <div
                key={check.name}
                className="px-6 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:bg-[#F4F6F8]/60 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs font-bold text-[#475467] w-6">
                    {check.num}
                  </span>
                  <span className="font-mono text-xs font-bold text-[#101828] w-48">
                    {check.name}
                  </span>
                  <span className="font-mono text-[11px] text-[#3157D5] bg-[#3157D5]/10 px-2 py-0.5 rounded border border-[#3157D5]/20 hidden lg:inline-block">
                    {check.formula}
                  </span>
                </div>

                <div className="text-xs text-[#475467] md:text-right max-w-lg">
                  {check.req}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
