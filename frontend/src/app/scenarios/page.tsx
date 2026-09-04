import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Badge } from "@/components/Badge";
import { getCaseDetail, getScenarioExamples } from "@/lib/data";
import { dispositionLabel, dispositionTone, exceptionLabel, scenarioLabel } from "@/lib/format";
import type { ScenarioFamily } from "@/lib/types";

const SCENARIO_NARRATIVE: Record<ScenarioFamily, string> = {
  S1: "A structured payment_ref links the settlement to exactly one ledger entry within the +-7 day window, and the amount matches exactly. All nine gate checks pass -> the case resolves without a human in the loop.",
  S2: "Two ledger entries share the same structured reference, amount, currency, and direction. The matcher deterministically surfaces both as top-scoring candidates, so the classifier proposes no single target. IDENTITY fails -> routed to a human.",
  S3: "The structured reference correctly links to one ledger entry, but its amount differs from the expected settlement net. The candidate exists and evidence contradicts on amount -> BRIDGE fails -> routed to a human.",
  S4: "No structured payment_ref exists. The matcher finds the settlement's order reference embedded as text inside a ledger narration, within the +-3 day unstructured window. Policy requires a human to confirm any unstructured/narration-derived hypothesis -> POLICY fails.",
  S5: "No structured payment_ref exists. The matcher finds the settlement's customer-name alias embedded as text inside a ledger narration. Same unstructured policy applies -> POLICY fails -> routed to a human.",
  S6: "No ledger entry corresponds to this settlement at all. The matcher returns zero candidates. The system fails closed with IDENTITY failing on an empty proposed set -> UNRESOLVED, not silently ignored.",
};

const SCENARIO_EXPECTATION: Record<ScenarioFamily, string> = {
  S1: "Expect: AUTO_RESOLVED",
  S2: "Expect: HUMAN_REVIEW",
  S3: "Expect: HUMAN_REVIEW",
  S4: "Expect: HUMAN_REVIEW",
  S5: "Expect: HUMAN_REVIEW",
  S6: "Expect: UNRESOLVED",
};

export default function ScenariosPage() {
  const examples = getScenarioExamples();
  const families = (Object.keys(examples) as ScenarioFamily[]).sort();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-100">Scenario Demo</h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-400">
          Six representative settlements, one per scenario family, selected from the same batch
          run shown on the Overview page. The production pipeline never sees these labels &mdash;
          they are attached here only for narration, by cross-referencing evaluator-only ground
          truth after the fact.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {families.map((family) => {
          const settlementId = examples[family];
          const detail = getCaseDetail(settlementId);
          if (!detail) return null;

          return (
            <div key={family} className="flex flex-col rounded-lg border border-slate-800 bg-[#0d1219] p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-lg font-semibold text-slate-100">
                    {family} &middot; {scenarioLabel(family)}
                  </div>
                  <div className="mt-0.5 text-xs font-medium text-slate-500">
                    {SCENARIO_EXPECTATION[family]}
                  </div>
                </div>
                <Badge tone={dispositionTone(detail.disposition)}>
                  {dispositionLabel(detail.disposition)}
                </Badge>
              </div>

              <p className="mt-3 flex-1 text-sm leading-relaxed text-slate-400">
                {SCENARIO_NARRATIVE[family]}
              </p>

              <dl className="mt-4 grid grid-cols-3 gap-3 border-t border-slate-800 pt-3 text-xs">
                <div>
                  <dt className="text-slate-500">Candidates</dt>
                  <dd className="mt-0.5 font-mono tabular-nums text-slate-200">
                    {detail.candidates.length}
                  </dd>
                </div>
                <div>
                  <dt className="text-slate-500">Exception</dt>
                  <dd className="mt-0.5 text-slate-200">{exceptionLabel(detail.exception_type)}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Failing check</dt>
                  <dd className="mt-0.5 text-slate-200">{detail.gate.failing_check ?? "None"}</dd>
                </div>
              </dl>

              <Link
                href={`/cases/${settlementId}`}
                className="mt-4 flex items-center justify-center gap-1.5 rounded-md border border-slate-700 py-2 text-sm font-medium text-slate-200 transition-colors hover:border-emerald-500/50 hover:text-emerald-400"
              >
                Walk through this case <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
}
