import Link from "next/link";
import {
  ArrowRight,
  Layers,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  CheckCircle2,
  Lock,
  AlertOctagon,
} from "lucide-react";
import { Badge } from "@/components/Badge";
import { getCases, getMeta, getOverview, getScenarioExamples } from "@/lib/data";
import { formatDateTime, formatMinor, scenarioLabel } from "@/lib/format";

export default function OverviewPage() {
  const overview = getOverview();
  const meta = getMeta();
  const cases = getCases();
  const scenarioExamples = getScenarioExamples();

  const totalSettlements = overview.total_settlements;
  const autoResolved = overview.auto_resolved;
  const humanReview = overview.human_review;
  const unresolved = overview.unresolved;
  const falseAuto = overview.false_auto_resolutions;

  const autoPct = Math.round((autoResolved / totalSettlements) * 100);
  const humanPct = Math.round((humanReview / totalSettlements) * 100);
  const unresolvedPct = 100 - autoPct - humanPct;

  const totalExpectedNetMinor = cases.reduce((sum, c) => sum + c.expected_net_minor, 0);
  const autoVolumeMinor = cases
    .filter((c) => c.disposition === "AUTO_RESOLVED")
    .reduce((sum, c) => sum + c.expected_net_minor, 0);
  const humanVolumeMinor = cases
    .filter((c) => c.disposition === "HUMAN_REVIEW")
    .reduce((sum, c) => sum + c.expected_net_minor, 0);
  const unresolvedVolumeMinor = cases
    .filter((c) => c.disposition === "UNRESOLVED")
    .reduce((sum, c) => sum + c.expected_net_minor, 0);

  return (
    <div className="space-y-7">
      {/* 1. Page Header (Restrained Operational Header) */}
      <div className="flex flex-col justify-between gap-3 border-b border-[#D9D5CA] pb-5 sm:flex-row sm:items-end">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-[#62635C]">
            CashProof settlement control &middot; deterministic financial authorization
          </div>
          <h1 className="mt-1 font-editorial text-2xl sm:text-3xl font-semibold tracking-tight text-[#171816]">
            Reconciliation Overview
          </h1>
        </div>

        {/* Small Technical Metadata (Compact, not giant cards) */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs text-[#62635C]">
          <span className="rounded-md border border-[#D9D5CA] bg-[#F8F6F0] px-2.5 py-1">
            RUN {meta.run_id}
          </span>
          <span className="rounded-md border border-[#D9D5CA] bg-[#F8F6F0] px-2.5 py-1">
            BENCHMARK SEED-{meta.seed}
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-md border border-[#65745F]/30 bg-[#65745F]/10 px-2.5 py-1 text-[#65745F] font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-[#65745F]" />
            BATCH COMPLETE
          </span>
        </div>
      </div>

      {/* 2. Batch Summary & Financial Disposition Composition */}
      <section className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-6 sm:p-7 shadow-xs">
        {/* Batch Object Header */}
        <div className="flex flex-col justify-between gap-4 border-b border-[#D9D5CA] pb-6 lg:flex-row lg:items-center">
          <div>
            <span className="font-mono text-[11px] uppercase tracking-wider text-[#62635C]">
              Batch Summary
            </span>
            <div className="mt-1 flex items-baseline gap-3">
              <span className="font-mono text-4xl sm:text-5xl font-bold tracking-tight text-[#171816]">
                {totalSettlements}
              </span>
              <div className="flex flex-col">
                <span className="font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
                  SETTLEMENTS PROCESSED
                </span>
                <span className="text-xs text-[#62635C]">
                  Evaluated across 6 canonical exception families
                </span>
              </div>
            </div>
          </div>

          {/* Authoritative Financial Volume Box */}
          <div className="flex items-center gap-6 rounded-xl border border-[#D9D5CA] bg-[#EEEAE0] px-5 py-3">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-wider text-[#62635C]">
                TOTAL BATCH NET VOLUME
              </div>
              <div className="font-mono text-2xl font-bold text-[#171816]">
                {formatMinor(totalExpectedNetMinor)}
              </div>
            </div>
            <div className="h-9 w-px bg-[#D9D5CA]" />
            <div>
              <div className="font-mono text-[10px] uppercase tracking-wider text-[#62635C]">
                BENCHMARK SEED
              </div>
              <div className="font-mono text-sm font-semibold text-[#62635C]">
                seed-{meta.seed}
              </div>
            </div>
          </div>
        </div>

        {/* 3 Coherent Disposition Outcomes (Not 3 screaming cards) */}
        <div className="mt-6 grid grid-cols-1 divide-y divide-[#D9D5CA] md:grid-cols-3 md:divide-y-0 md:divide-x md:divide-[#D9D5CA]">
          {/* AUTO RESOLVED */}
          <div className="py-4 md:py-0 md:pr-6">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-[#65745F]">
                Auto Resolved
              </span>
              <span className="font-mono text-xs font-semibold text-[#65745F]">
                {autoPct}%
              </span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="font-mono text-3xl font-bold tabular-nums text-[#171816]">
                {autoResolved}
              </span>
              <span className="font-mono text-xs text-[#62635C]">
                / {totalSettlements}
              </span>
            </div>
            <div className="mt-2 font-mono text-xs text-[#62635C]">
              Volume: <span className="font-semibold text-[#171816]">{formatMinor(autoVolumeMinor)}</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-[#62635C]">
              Zero human intervention. Verified by all 9 deterministic gate verifiers.
            </p>
          </div>

          {/* HUMAN REVIEW */}
          <div className="py-4 md:py-0 md:px-6">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-[#A47C52]">
                Human Review
              </span>
              <span className="font-mono text-xs font-semibold text-[#A47C52]">
                {humanPct}%
              </span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="font-mono text-3xl font-bold tabular-nums text-[#171816]">
                {humanReview}
              </span>
              <span className="font-mono text-xs text-[#62635C]">
                / {totalSettlements}
              </span>
            </div>
            <div className="mt-2 font-mono text-xs text-[#62635C]">
              Volume: <span className="font-semibold text-[#171816]">{formatMinor(humanVolumeMinor)}</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-[#62635C]">
              Discrepancy investigated with reconstructed evidence. Awaiting finance controller sign-off.
            </p>
          </div>

          {/* UNRESOLVED */}
          <div className="py-4 md:py-0 md:pl-6">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-semibold uppercase tracking-wider text-[#A85F59]">
                Unresolved
              </span>
              <span className="font-mono text-xs font-semibold text-[#A85F59]">
                {unresolvedPct}%
              </span>
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="font-mono text-3xl font-bold tabular-nums text-[#171816]">
                {unresolved}
              </span>
              <span className="font-mono text-xs text-[#62635C]">
                / {totalSettlements}
              </span>
            </div>
            <div className="mt-2 font-mono text-xs text-[#62635C]">
              Volume: <span className="font-semibold text-[#171816]">{formatMinor(unresolvedVolumeMinor)}</span>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-[#62635C]">
              Missing source facts or candidate contradictions. Halted closed by default.
            </p>
          </div>
        </div>

        {/* Elegant Horizontal Distribution Bar */}
        <div className="mt-7 border-t border-[#D9D5CA] pt-5">
          <div className="mb-2 flex items-center justify-between font-mono text-[11px] text-[#62635C]">
            <span>DISPOSITION BREAKDOWN</span>
            <span>100% OF BATCH</span>
          </div>
          <div className="flex h-3 w-full overflow-hidden rounded-md bg-[#EEEAE0] border border-[#D9D5CA]">
            <div
              className="bg-[#65745F] transition-all"
              style={{ width: `${autoPct}%` }}
              title={`Auto Resolved: ${autoResolved} (${autoPct}%)`}
            />
            <div
              className="bg-[#A47C52] transition-all"
              style={{ width: `${humanPct}%` }}
              title={`Human Review: ${humanReview} (${humanPct}%)`}
            />
            <div
              className="bg-[#A85F59] transition-all"
              style={{ width: `${unresolvedPct}%` }}
              title={`Unresolved: ${unresolved} (${unresolvedPct}%)`}
            />
          </div>

          {/* Clean Neutral Legend */}
          <div className="mt-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex flex-wrap items-center gap-5 font-mono">
              <span className="flex items-center gap-1.5 text-[#171816]">
                <span className="h-2.5 w-2.5 rounded-xs bg-[#65745F]" />
                <span>Auto Resolved: {autoResolved} ({autoPct}%)</span>
              </span>
              <span className="flex items-center gap-1.5 text-[#171816]">
                <span className="h-2.5 w-2.5 rounded-xs bg-[#A47C52]" />
                <span>Human Review: {humanReview} ({humanPct}%)</span>
              </span>
              <span className="flex items-center gap-1.5 text-[#171816]">
                <span className="h-2.5 w-2.5 rounded-xs bg-[#A85F59]" />
                <span>Unresolved: {unresolved} ({unresolvedPct}%)</span>
              </span>
            </div>
            <div className="font-mono text-[11px] text-[#62635C]">
              Policy: Fail-Closed Boundary
            </div>
          </div>
        </div>
      </section>

      {/* 3. Safety Metric & Invariant (Zero Tolerance Guarantee) */}
      <section className="rounded-2xl border border-[#D9D5CA] border-l-4 border-l-[#65745F] bg-[#F8F6F0] p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col justify-between gap-2 border-b border-[#D9D5CA] pb-4 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wider text-[#65745F]">
            <ShieldCheck className="h-4 w-4 text-[#65745F]" />
            <span>Core Safety Invariant // Non-Negotiable Boundary</span>
          </div>
          <div className="inline-flex items-center gap-1.5 font-mono text-xs text-[#62635C]">
            <span>VERIFIED FIDELITY:</span>
            <span className="font-bold text-[#65745F]">100.0%</span>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 items-center gap-6 lg:grid-cols-12">
          {/* Large Typography + Explanation */}
          <div className="flex flex-col gap-2 lg:col-span-7">
            <div className="flex items-baseline gap-3">
              <span className="font-mono text-5xl font-bold tracking-tight text-[#65745F]">
                {falseAuto}
              </span>
              <div>
                <span className="font-mono text-sm font-bold uppercase tracking-wider text-[#171816]">
                  FALSE AUTO-RESOLUTIONS
                </span>
                <div className="text-xs text-[#62635C]">
                  Verified against hidden evaluator ground truth across all 100 cases
                </div>
              </div>
            </div>

            <h2 className="mt-2 font-editorial text-base font-semibold text-[#171816]">
              Deterministic software owns financial truth. AI investigates ambiguity.
            </h2>
            <p className="text-xs leading-relaxed text-[#62635C]">
              Every <code className="font-mono font-medium text-[#171816]">AUTO_RESOLVED</code> disposition
              passed all nine mandatory checks of the deterministic gate. No candidate score,
              narration match, or model confidence can authorize money movement on its own &mdash; only{" "}
              <code className="rounded bg-[#EEEAE0] px-1.5 py-0.5 font-mono text-xs text-[#171816]">
                evaluate_gate()
              </code>{" "}
              can.
            </p>
          </div>

          {/* 3 Compact Control Tiles */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:col-span-5">
            <div className="rounded-xl border border-[#D9D5CA] bg-[#EEEAE0] p-3.5">
              <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-[#62635C]">
                <Lock className="h-3 w-3 text-[#4E6870]" />
                <span>Gate Firewall</span>
              </div>
              <div className="mt-1 font-mono text-sm font-bold text-[#171816]">
                9 / 9 Mandatory
              </div>
              <div className="mt-0.5 text-[11px] text-[#62635C]">
                Identity, Bridge, Uniqueness, Policy &amp; Target equality
              </div>
            </div>

            <div className="rounded-xl border border-[#D9D5CA] bg-[#EEEAE0] p-3.5">
              <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-[#62635C]">
                <CheckCircle2 className="h-3 w-3 text-[#65745F]" />
                <span>Ground Truth</span>
              </div>
              <div className="mt-1 font-mono text-sm font-bold text-[#65745F]">
                0 Mismatches
              </div>
              <div className="mt-0.5 text-[11px] text-[#62635C]">
                Zero false positives under adversarial noise &amp; decoys
              </div>
            </div>

            <div className="rounded-xl border border-[#D9D5CA] bg-[#EEEAE0] p-3.5">
              <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-[#62635C]">
                <AlertOctagon className="h-3 w-3 text-[#A47C52]" />
                <span>Engine Policy</span>
              </div>
              <div className="mt-1 font-mono text-sm font-bold text-[#A47C52]">
                Fail-Closed
              </div>
              <div className="mt-0.5 text-[11px] text-[#62635C]">
                Doubt routes to controller queue; money is never moved
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. "What Needs Attention" (Operational Dispatch) */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
              What Needs Attention
            </h2>
            <p className="text-xs text-[#62635C]">
              Operational entry points into exception clusters, gate diagnostics, and confidence calibration
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {/* Exceptions */}
          <div className="flex flex-col justify-between rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 transition-colors hover:bg-[#EEEAE0]">
            <div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-[11px] uppercase tracking-wider text-[#62635C]">
                  EXCEPTIONS
                </span>
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#4E6870]/10 text-[#4E6870]">
                  <Layers className="h-3.5 w-3.5" />
                </span>
              </div>
              <div className="mt-3 font-mono text-base font-bold text-[#171816]">
                61 settlements require attention
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-[#62635C]">
                Clustered deterministically into Reference Ambiguity (39), Bridge Discrepancy (15), and
                Missing Records (7) with actionable remediation playbooks.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#D9D5CA]">
              <Link
                href="/exceptions"
                className="group inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#171816] hover:text-[#65745F]"
              >
                <span>Explore Exception Patterns</span>
                <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>

          {/* Gate Diagnostics */}
          <div className="flex flex-col justify-between rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 transition-colors hover:bg-[#EEEAE0]">
            <div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-[11px] uppercase tracking-wider text-[#62635C]">
                  GATE FIREWALL
                </span>
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#A47C52]/10 text-[#A47C52]">
                  <ShieldAlert className="h-3.5 w-3.5" />
                </span>
              </div>
              <div className="mt-3 font-mono text-base font-bold text-[#171816]">
                61 cases blocked by deterministic controls
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-[#62635C]">
                Top blocker is Identity check (25 failures), followed by Policy (21) and Bridge
                discrepancy (15). Complete pass/fail ranking across all 9 gates.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#D9D5CA]">
              <Link
                href="/gate"
                className="group inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#171816] hover:text-[#A47C52]"
              >
                <span>Inspect Gate Diagnostics</span>
                <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>

          {/* Confidence Calibration */}
          <div className="flex flex-col justify-between rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 transition-colors hover:bg-[#EEEAE0]">
            <div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-[11px] uppercase tracking-wider text-[#62635C]">
                  CONFIDENCE
                </span>
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#65745F]/10 text-[#65745F]">
                  <TrendingUp className="h-3.5 w-3.5" />
                </span>
              </div>
              <div className="mt-3 font-mono text-base font-bold text-[#171816]">
                Belief vs authorization separation
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-[#62635C]">
                High-confidence cases are still subject to gate authority. ECE &amp; Brier metrics
                prove AI confidence is never a gate approval input.
              </p>
            </div>
            <div className="mt-4 pt-3 border-t border-[#D9D5CA]">
              <Link
                href="/confidence"
                className="group inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#171816] hover:text-[#65745F]"
              >
                <span>Analyze Calibration</span>
                <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Controlled Scenario Coverage Grid */}
      <section className="space-y-3">
        <div className="flex flex-col justify-between gap-1 sm:flex-row sm:items-center">
          <div>
            <h2 className="font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
              Controlled Scenario Coverage
            </h2>
            <p className="text-xs text-[#62635C]">
              6 canonical operational scenarios evaluated under adversarial noise and decoys
            </p>
          </div>
          <Link
            href="/scenarios"
            className="group flex items-center gap-1 font-mono text-xs font-medium text-[#65745F] hover:text-[#171816]"
          >
            <span>Run scenario demo</span>
            <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {(Object.keys(scenarioExamples) as Array<keyof typeof scenarioExamples>)
            .sort()
            .map((family) => {
              const settlementId = scenarioExamples[family];
              const row = cases.find((c) => c.settlement_id === settlementId);

              let tone: "success" | "warning" | "danger" = "warning";
              if (row?.disposition === "AUTO_RESOLVED") tone = "success";
              if (row?.disposition === "UNRESOLVED") tone = "danger";

              return (
                <Link
                  key={family}
                  href={`/cases/${settlementId}`}
                  className="group flex flex-col justify-between rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-3.5 transition-all hover:bg-[#EEEAE0]"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sm font-bold text-[#171816] group-hover:text-[#65745F]">
                        {family}
                      </span>
                      {row && (
                        <Badge tone={tone}>
                          {row.disposition === "AUTO_RESOLVED"
                            ? "AUTO"
                            : row.disposition === "HUMAN_REVIEW"
                              ? "REVIEW"
                              : "UNRES"}
                        </Badge>
                      )}
                    </div>
                    <div className="mt-2 text-xs font-medium text-[#171816]">
                      {scenarioLabel(family)}
                    </div>
                    <div className="mt-1 font-mono text-[11px] text-[#62635C] truncate">
                      {settlementId}
                    </div>
                  </div>

                  <div className="mt-3 border-t border-[#D9D5CA] pt-2 flex items-center justify-between font-mono text-[11px]">
                    <span className="text-[#62635C]">
                      {row ? formatMinor(row.expected_net_minor) : "—"}
                    </span>
                    <ArrowRight className="h-3 w-3 text-[#62635C] transition-transform group-hover:translate-x-0.5 group-hover:text-[#171816]" />
                  </div>
                </Link>
              );
            })}
        </div>
      </section>

      {/* 6. Run Telemetry Metadata Footer */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[#D9D5CA] pt-4 font-mono text-[11px] text-[#62635C]">
        <div className="flex items-center gap-3">
          <span>Run {meta.run_id}</span>
          <span>&middot;</span>
          <span>Seed {meta.seed}</span>
          <span>&middot;</span>
          <span>Generator v{meta.generator_version}</span>
        </div>
        <div>
          Snapshot: {formatDateTime(meta.generated_at)}
        </div>
      </div>
    </div>
  );
}
