import Link from "next/link";
import { ArrowRight, Layers, ShieldAlert, ShieldCheck, TrendingUp } from "lucide-react";
import { KpiCard } from "@/components/KpiCard";
import { getCases, getMeta, getOverview, getScenarioExamples } from "@/lib/data";
import { scenarioLabel } from "@/lib/format";

export default function OverviewPage() {
  const overview = getOverview();
  const meta = getMeta();
  const cases = getCases();
  const scenarioExamples = getScenarioExamples();

  const autoPct = Math.round((overview.auto_resolved / overview.total_settlements) * 100);
  const humanPct = Math.round((overview.human_review / overview.total_settlements) * 100);
  const unresolvedPct = 100 - autoPct - humanPct;

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">CashProof</h1>
        <p className="mt-1 text-sm text-slate-400">Evidence-First Settlement Control</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <KpiCard label="Settlements" value={overview.total_settlements} />
        <KpiCard
          label="Auto Resolved"
          value={overview.auto_resolved}
          tone="success"
          hint={`${autoPct}% of batch`}
        />
        <KpiCard
          label="Human Review"
          value={overview.human_review}
          tone="warning"
          hint={`${humanPct}% of batch`}
        />
        <KpiCard
          label="Unresolved"
          value={overview.unresolved}
          tone="danger"
          hint={`${unresolvedPct}% of batch`}
        />
        <KpiCard
          label="False Auto-Resolution"
          value={overview.false_auto_resolutions}
          tone="success"
          hint="verified against evaluator truth"
          emphasize
        />
      </div>

      <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-5">
        <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-500">
          <span>Disposition breakdown</span>
          <span>{overview.total_settlements} settlements</span>
        </div>
        <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-900">
          <div className="bg-emerald-500" style={{ width: `${autoPct}%` }} />
          <div className="bg-amber-500" style={{ width: `${humanPct}%` }} />
          <div className="bg-red-500" style={{ width: `${unresolvedPct}%` }} />
        </div>
        <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" /> Auto Resolved (
            {overview.auto_resolved})
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-500" /> Human Review (
            {overview.human_review})
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-red-500" /> Unresolved (
            {overview.unresolved})
          </span>
        </div>
      </div>

      <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/[0.03] p-6">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
          <div>
            <p className="text-base font-medium text-slate-100">
              Deterministic software owns financial truth.
              <br />
              AI investigates ambiguity.
            </p>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Every AUTO_RESOLVED disposition below passed all nine mandatory checks of the
              deterministic gate. No candidate score, narration match, or model output can
              authorize a resolution on its own &mdash; only <code className="text-slate-300">evaluate_gate()</code> can.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="flex flex-col justify-between rounded-lg border border-slate-800 bg-[#0d1219] p-6">
          <div className="flex items-start gap-3">
            <Layers className="mt-0.5 h-5 w-5 text-sky-400 shrink-0" />
            <div>
              <h2 className="text-base font-medium text-slate-100">
                Exception Intelligence & Recurring Patterns
              </h2>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Exceptions deterministically grouped into recurring operational patterns
                (Reference Ambiguity, Bridge Discrepancies, Unstructured Text, Missing Records) with
                monetary impact tracking and actionable remediation guidance.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80">
            <Link
              href="/exceptions"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-400 hover:text-sky-300"
            >
              Explore Exception Patterns <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        <div className="flex flex-col justify-between rounded-lg border border-slate-800 bg-[#0d1219] p-6">
          <div className="flex items-start gap-3">
            <ShieldAlert className="mt-0.5 h-5 w-5 text-amber-400 shrink-0" />
            <div>
              <h2 className="text-base font-medium text-slate-100">
                Gate Intelligence & Controller Explainability
              </h2>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Authoritative diagnostics for CashProof&apos;s 9-check financial firewall. Understand pass/fail
                rates, ranked automation blockers, blocked settlement net volume, and deterministic eligibility requirements.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80">
            <Link
              href="/gate"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-400 hover:text-amber-300"
            >
              Inspect Gate Diagnostics <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        <div className="flex flex-col justify-between rounded-lg border border-slate-800 bg-[#0d1219] p-6">
          <div className="flex items-start gap-3">
            <TrendingUp className="mt-0.5 h-5 w-5 text-indigo-400 shrink-0" />
            <div>
              <h2 className="text-base font-medium text-slate-100">
                Confidence Calibration & Automation Quality
              </h2>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                Expected Calibration Error (ECE) and Brier metrics prove belief vs authorization separation.
                Shows why high hypothesis confidence never bypasses the deterministic Gate.
              </p>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80">
            <Link
              href="/confidence"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300"
            >
              Analyze Calibration <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-300">
            Scenario coverage
          </h2>
          <Link
            href="/scenarios"
            className="flex items-center gap-1 text-xs font-medium text-emerald-400 hover:text-emerald-300"
          >
            Run scenario demo <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {(Object.keys(scenarioExamples) as Array<keyof typeof scenarioExamples>)
            .sort()
            .map((family) => {
              const settlementId = scenarioExamples[family];
              const row = cases.find((c) => c.settlement_id === settlementId);
              return (
                <Link
                  key={family}
                  href={`/cases/${settlementId}`}
                  className="rounded-lg border border-slate-800 bg-[#0d1219] p-3 transition-colors hover:border-slate-700 hover:bg-slate-900"
                >
                  <div className="text-sm font-semibold text-slate-200">{family}</div>
                  <div className="mt-0.5 text-[11px] leading-tight text-slate-500">
                    {scenarioLabel(family)}
                  </div>
                  {row && (
                    <div className="mt-2 text-[11px] font-medium text-slate-400">
                      {row.disposition.replace("_", " ")}
                    </div>
                  )}
                </Link>
              );
            })}
        </div>
      </div>

      <p className="text-xs text-slate-600">
        Run {meta.run_id} &middot; seed {meta.seed} &middot; generator v{meta.generator_version}
      </p>
    </div>
  );
}
