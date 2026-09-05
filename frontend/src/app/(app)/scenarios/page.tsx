import Link from "next/link";
import { ArrowRight, Layers, ShieldAlert, Cpu } from "lucide-react";
import { Badge } from "@/components/Badge";
import { getCaseDetail, getScenarioExamples } from "@/lib/data";
import { dispositionLabel, dispositionTone, exceptionLabel, scenarioLabel } from "@/lib/format";
import { cn } from "@/lib/cn";
import type { ScenarioFamily } from "@/lib/types";

const SCENARIO_NARRATIVE: Record<ScenarioFamily, string> = {
  S1: "A structured payment_ref links the settlement to exactly one ledger entry within the ±7 day window, and the amount matches exactly. All nine gate checks pass → the case resolves without a human in the loop.",
  S2: "Two ledger entries share the same structured reference, amount, currency, and direction. The matcher deterministically surfaces both as top-scoring candidates, so the classifier proposes no single target. IDENTITY fails → routed to a human.",
  S3: "The structured reference correctly links to one ledger entry, but its amount differs from the expected settlement net. The candidate exists and evidence contradicts on amount → BRIDGE fails → routed to a human.",
  S4: "No structured payment_ref exists. The matcher finds the settlement's order reference embedded as text inside a ledger narration, within the ±3 day unstructured window. Policy requires a human to confirm any unstructured/narration-derived hypothesis → POLICY fails.",
  S5: "No structured payment_ref exists. The matcher finds the settlement's customer-name alias embedded as text inside a ledger narration. Same unstructured policy applies → POLICY fails → routed to a human.",
  S6: "No ledger entry corresponds to this settlement at all. The matcher returns zero candidates. The system fails closed with IDENTITY failing on an empty proposed set → UNRESOLVED, not silently ignored.",
};

const SCENARIO_EXPECTATION_VALUE: Record<ScenarioFamily, string> = {
  S1: "AUTO_RESOLVED",
  S2: "HUMAN_REVIEW",
  S3: "HUMAN_REVIEW",
  S4: "HUMAN_REVIEW",
  S5: "HUMAN_REVIEW",
  S6: "UNRESOLVED",
};

const SCENARIO_INDEX: Record<ScenarioFamily, string> = {
  S1: "01",
  S2: "02",
  S3: "03",
  S4: "04",
  S5: "05",
  S6: "06",
};

const SCENARIO_SUBTITLE: Record<ScenarioFamily, string> = {
  S1: "Structured Evidence · Clean Baseline",
  S2: "Ambiguous Identity · Refuses to Guess",
  S3: "Financial Mismatch · Amount Contradiction",
  S4: "Unstructured Reference · Narration Order ID",
  S5: "Narration Alias · Customer Name Match",
  S6: "Non-Provable / Missing · Fail-Closed Safeguard",
};

const SCENARIO_THEME: Record<
  ScenarioFamily,
  {
    borderTop: string;
    textAccent: string;
    badgeBg: string;
    dotColor: string;
    expectedTone: string;
  }
> = {
  S1: {
    borderTop: "border-t-[#3B5145]",
    textAccent: "text-[#3B5145]",
    badgeBg: "bg-[#65745F]/10 border-[#65745F]/30",
    dotColor: "bg-[#3B5145]",
    expectedTone: "text-[#3B5145]",
  },
  S2: {
    borderTop: "border-t-[#8C6843]",
    textAccent: "text-[#8C6843]",
    badgeBg: "bg-[#A47C52]/10 border-[#A47C52]/30",
    dotColor: "bg-[#8C6843]",
    expectedTone: "text-[#8C6843]",
  },
  S3: {
    borderTop: "border-t-[#9A514C]",
    textAccent: "text-[#9A514C]",
    badgeBg: "bg-[#A85F59]/10 border-[#A85F59]/30",
    dotColor: "bg-[#9A514C]",
    expectedTone: "text-[#8C6843]",
  },
  S4: {
    borderTop: "border-t-[#8C6843]",
    textAccent: "text-[#8C6843]",
    badgeBg: "bg-[#A47C52]/10 border-[#A47C52]/30",
    dotColor: "bg-[#8C6843]",
    expectedTone: "text-[#8C6843]",
  },
  S5: {
    borderTop: "border-t-[#8C6843]",
    textAccent: "text-[#8C6843]",
    badgeBg: "bg-[#A47C52]/10 border-[#A47C52]/30",
    dotColor: "bg-[#8C6843]",
    expectedTone: "text-[#8C6843]",
  },
  S6: {
    borderTop: "border-t-[#9A514C]",
    textAccent: "text-[#9A514C]",
    badgeBg: "bg-[#A85F59]/10 border-[#A85F59]/30",
    dotColor: "bg-[#9A514C]",
    expectedTone: "text-[#9A514C]",
  },
};

const FAMILIES: ScenarioFamily[] = ["S1", "S2", "S3", "S4", "S5", "S6"];

export default function ScenariosPage() {
  const examples = getScenarioExamples();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 font-mono text-[11px] font-semibold tracking-wider text-[#3B5145] uppercase">
          <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
          Controlled Scenario Lab / S1–S6
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#171816]">
          Scenario Demo
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-[#4F514A]">
          Six representative settlements, one per scenario family, selected from the same batch
          run shown on the Overview page. The production pipeline never sees these scenario labels
          &mdash; they are attached here only for narration, by cross-referencing evaluator-only
          ground truth after the fact.
        </p>
      </div>

      {/* Header Information Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 rounded-2xl border border-[#D9D5CA] bg-[#EEEAE0]/70 p-3.5 sm:p-4 text-xs">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#D9D5CA] bg-[#F8F6F0] text-[#171816]">
            <Cpu className="h-4 w-4 text-[#3B5145]" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
              S1–S6 Coverage
            </div>
            <div className="font-semibold text-[#171816]">6 Controlled Failure Scenarios</div>
          </div>
        </div>

        <div className="flex items-center gap-3 border-t md:border-t-0 md:border-l border-[#D9D5CA] pt-3 md:pt-0 md:pl-3.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#D9D5CA] bg-[#F8F6F0] text-[#171816]">
            <Layers className="h-4 w-4 text-[#8C6843]" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
              Same Batch Run
            </div>
            <div className="font-semibold text-[#171816]">Representative Settlements</div>
          </div>
        </div>

        <div className="flex items-center gap-3 border-t md:border-t-0 md:border-l border-[#D9D5CA] pt-3 md:pt-0 md:pl-3.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#D9D5CA] bg-[#F8F6F0] text-[#171816]">
            <ShieldAlert className="h-4 w-4 text-[#9A514C]" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
              Evaluator Labels
            </div>
            <div className="font-semibold text-[#171816]">Isolated from Production Matcher</div>
          </div>
        </div>
      </div>

      {/* 6 Scenarios Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {FAMILIES.map((family) => {
          const settlementId = examples[family];
          if (!settlementId) return null;
          const detail = getCaseDetail(settlementId);
          if (!detail) return null;

          const theme = SCENARIO_THEME[family];
          const hasFailingCheck = Boolean(detail.gate.failing_check);

          return (
            <div
              key={family}
              className={cn(
                "flex flex-col justify-between rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 sm:p-6 transition-all duration-150 border-t-[3px]",
                theme.borderTop,
              )}
            >
              <div>
                {/* Scenario Header: Numbering, Family Tag, Category, and Disposition */}
                <div className="flex items-start justify-between gap-2.5">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-[#6B6D64]">
                        {SCENARIO_INDEX[family]}
                      </span>
                      <span className="h-1 w-1 rounded-full bg-[#CFC9BC]" />
                      <span
                        className={cn(
                          "font-mono text-xs font-bold uppercase tracking-wider",
                          theme.textAccent,
                        )}
                      >
                        {family}
                      </span>
                      <span className="hidden sm:inline-block h-1 w-1 rounded-full bg-[#CFC9BC]" />
                      <span className="hidden sm:inline-block font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
                        {SCENARIO_SUBTITLE[family]}
                      </span>
                    </div>

                    <h2 className="text-base sm:text-lg font-bold tracking-tight text-[#171816]">
                      {scenarioLabel(family)}
                    </h2>

                    <div className="sm:hidden font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
                      {SCENARIO_SUBTITLE[family]}
                    </div>
                  </div>

                  <Badge tone={dispositionTone(detail.disposition)} className="shrink-0">
                    {dispositionLabel(detail.disposition)}
                  </Badge>
                </div>

                {/* Expected Disposition Technical Line */}
                <div className="mt-2.5 inline-flex items-center gap-2 rounded-lg border border-[#D9D5CA] bg-[#EEEAE0]/60 px-2.5 py-1 text-xs">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
                    Expected Disposition
                  </span>
                  <span className={cn("font-mono text-xs font-bold", theme.expectedTone)}>
                    {SCENARIO_EXPECTATION_VALUE[family]}
                  </span>
                </div>

                {/* Scenario Technical Narrative */}
                <p className="mt-3.5 text-sm leading-relaxed text-[#4F514A]">
                  {SCENARIO_NARRATIVE[family]}
                </p>
              </div>

              {/* Bottom Section: Technical Facts Strip & Action CTA */}
              <div className="mt-5 pt-3.5 border-t border-[#D9D5CA]">
                <dl className="grid grid-cols-3 gap-2 sm:gap-3 text-xs">
                  <div>
                    <dt className="font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
                      Candidates
                    </dt>
                    <dd
                      className={cn(
                        "mt-0.5 font-mono text-sm font-bold",
                        detail.candidates.length === 0 ? "text-[#9A514C]" : "text-[#171816]",
                      )}
                    >
                      {detail.candidates.length}
                    </dd>
                  </div>

                  <div>
                    <dt className="font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
                      Exception
                    </dt>
                    <dd
                      className="mt-0.5 text-xs font-semibold text-[#171816] truncate"
                      title={exceptionLabel(detail.exception_type)}
                    >
                      {exceptionLabel(detail.exception_type)}
                    </dd>
                  </div>

                  <div>
                    <dt className="font-mono text-[10px] uppercase tracking-wider text-[#6B6D64]">
                      Failing check
                    </dt>
                    <dd
                      className={cn(
                        "mt-0.5 font-mono text-xs font-bold",
                        hasFailingCheck ? "text-[#9A514C]" : "text-[#3B5145]",
                      )}
                    >
                      {detail.gate.failing_check ?? "None"}
                    </dd>
                  </div>
                </dl>

                {/* Walk through CTA */}
                <Link
                  href={`/cases/${settlementId}`}
                  className="group mt-4 flex items-center justify-between rounded-xl border border-[#D9D5CA] bg-[#EEEAE0]/70 px-3.5 py-2.5 text-xs sm:text-sm font-medium text-[#171816] transition-all hover:bg-[#EEEAE0] hover:border-[#CFC9BC]"
                >
                  <div className="flex items-center gap-2 truncate">
                    <span>Walk through this case</span>
                    <span className="font-mono text-[11px] text-[#6B6D64] truncate">
                      ({settlementId})
                    </span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-[#4F514A] transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
