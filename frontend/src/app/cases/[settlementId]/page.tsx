"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, ArrowRight, Layers, ShieldAlert } from "lucide-react";
import { Badge, type Tone } from "@/components/Badge";
import { Panel } from "@/components/Panel";
import { GateChecklist } from "@/components/GateChecklist";
import { InvestigationPanel } from "@/components/InvestigationPanel";
import { ReviewPanel } from "@/components/ReviewPanel";
import { ApiError, fetchCaseCluster, fetchCaseDetail, fetchCaseGateOutcome } from "@/lib/api";
import {
  dispositionLabel,
  dispositionTone,
  exceptionLabel,
  formatDateTime,
  formatMinor,
  formatSignedMinor,
  scenarioLabel,
  stanceTone,
} from "@/lib/format";
import type { CaseCluster, CaseDetail, ControllerGateOutcome } from "@/lib/types";

export default function CaseDetailPage() {
  const params = useParams<{ settlementId: string }>();
  const settlementId = params.settlementId;

  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [caseCluster, setCaseCluster] = useState<CaseCluster | null>(null);
  const [gateOutcome, setGateOutcome] = useState<ControllerGateOutcome | null>(null);
  const [selectedTargetIds, setSelectedTargetIds] = useState<Set<string>>(new Set());
  const [recommendationNotice, setRecommendationNotice] = useState<string | null>(null);

  const [prevSettlementId, setPrevSettlementId] = useState(settlementId);
  if (prevSettlementId !== settlementId) {
    setPrevSettlementId(settlementId);
    setSelectedTargetIds(new Set());
    setRecommendationNotice(null);
    setCaseCluster(null);
    setGateOutcome(null);
  }

  useEffect(() => {
    let cancelled = false;

    fetchCaseDetail(settlementId)
      .then((data) => {
        if (cancelled) return;
        setDetail(data);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError) {
          setError(
            err.status === 404
              ? `Case ${settlementId} was not found.`
              : `Failed to load case: ${err.message}`,
          );
        } else {
          setError(
            "Could not reach the CashProof API. Start it with `uv run python scripts/run_api.py`.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    fetchCaseCluster(settlementId)
      .then((cluster) => {
        if (!cancelled) setCaseCluster(cluster);
      })
      .catch(() => {
        // Silently ignore if not in an exception cluster (e.g. clean match)
      });

    fetchCaseGateOutcome(settlementId)
      .then((outcome) => {
        if (!cancelled) setGateOutcome(outcome);
      })
      .catch(() => {
        // Silently ignore if gate outcome not available
      });

    return () => {
      cancelled = true;
    };
  }, [settlementId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <BackLink />
        <p className="text-sm text-slate-500">Loading case {settlementId}...</p>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="space-y-6">
        <BackLink />
        <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{error ?? "Case not found."}</span>
        </div>
      </div>
    );
  }

  const { bridge } = detail;

  return (
    <div className="space-y-6">
      <BackLink />

      <div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-mono text-xl font-semibold tracking-tight text-slate-100">
              {detail.settlement_id}
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {exceptionLabel(detail.exception_type)} &middot; {detail.candidates.length} candidate
              {detail.candidates.length === 1 ? "" : "s"}
              {detail.scenario_family && (
                <>
                  {" "}
                  &middot; demo label: {detail.scenario_family} ({scenarioLabel(detail.scenario_family)})
                </>
              )}
            </p>
          </div>
          <Badge tone={dispositionTone(detail.disposition)} className="px-3 py-1 text-sm">
            {dispositionLabel(detail.disposition)}
          </Badge>
        </div>
      </div>

      {caseCluster && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-sky-500/30 bg-sky-500/[0.05] px-4 py-3 text-sm">
          <div className="flex items-center gap-2.5 text-slate-200">
            <Layers className="h-4 w-4 text-sky-400 shrink-0" />
            <span>
              Part of recurring exception pattern:{" "}
              <strong className="font-medium text-slate-100">{caseCluster.cluster_name}</strong>
              <span className="ml-2 text-xs text-slate-400">
                ({caseCluster.case_count} cases in cluster)
              </span>
            </span>
          </div>
          <Link
            href="/exceptions"
            className="inline-flex items-center gap-1 text-xs font-semibold text-sky-400 hover:text-sky-300"
          >
            View Exception Intelligence <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <SummaryStat label="Expected Settlement" value={formatMinor(detail.expected_net_minor, detail.currency)} />
        <SummaryStat label="Observed Ledger" value={formatMinor(detail.observed_net_minor, detail.currency)} />
        <SummaryStat
          label="Delta"
          value={formatSignedMinor(detail.delta_minor, detail.currency)}
          tone={detail.delta_minor === 0 ? "success" : "warning"}
        />
        <SummaryStat
          label="Disposition"
          value={dispositionLabel(detail.disposition)}
          tone={dispositionTone(detail.disposition)}
        />
      </div>

      <Panel title="Cash Bridge" subtitle="Settlement-level derivation of the expected net amount">
        <div className="grid gap-6 lg:grid-cols-2">
          <ol className="space-y-2 text-sm">
            <BridgeLine label="Gross" value={bridge.gross_minor} currency={detail.currency} />
            <BridgeLine label="- Fee" value={-bridge.fee_minor} currency={detail.currency} />
            <BridgeLine label="- Tax" value={-bridge.tax_on_fee_minor} currency={detail.currency} />
            <BridgeLine
              label="- Refund (netted)"
              value={-bridge.netted_refund_minor}
              currency={detail.currency}
            />
            <BridgeLine label="+ Adjustment" value={bridge.adjustment_minor} currency={detail.currency} />
            <li className="flex items-center justify-between border-t border-slate-800 pt-2 font-semibold text-slate-100">
              <span>= Expected Net</span>
              <span className="font-mono tabular-nums">
                {formatMinor(bridge.expected_net_minor, detail.currency)}
              </span>
            </li>
          </ol>

          <div className="flex flex-col justify-center gap-4 rounded-md border border-slate-800 bg-[#0b0f16] p-4">
            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Case-Level Observation &middot; authoritative structural ledger state
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Expected Settlement</span>
                  <span className="font-mono tabular-nums text-slate-100">
                    {formatMinor(detail.expected_net_minor, detail.currency)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Observed Ledger</span>
                  <span className="font-mono tabular-nums text-slate-100">
                    {formatMinor(detail.observed_net_minor, detail.currency)}
                  </span>
                </div>
                <div
                  className={`flex items-center justify-between border-t border-slate-800 pt-2 text-sm font-semibold ${
                    detail.delta_minor === 0 ? "text-emerald-400" : "text-amber-400"
                  }`}
                >
                  <span>Delta</span>
                  <span className="font-mono tabular-nums">
                    {formatSignedMinor(detail.delta_minor, detail.currency)}
                  </span>
                </div>
              </div>
            </div>

            <div className="border-t border-slate-800 pt-4">
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Gate-Level Observation &middot; net of the proposed target set only
              </div>
              {detail.gate.proposed_target_ids.length === 0 ? (
                <p className="text-sm text-slate-500">No proposed target selected.</p>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Proposed Target Net</span>
                    <span className="font-mono tabular-nums text-slate-100">
                      {detail.gate.proposed_target_net_minor === null
                        ? "n/a"
                        : formatMinor(detail.gate.proposed_target_net_minor, detail.currency)}
                    </span>
                  </div>
                  <div
                    className={`flex items-center justify-between text-sm font-semibold ${
                      detail.gate.variance_minor === 0 ? "text-emerald-400" : "text-amber-400"
                    }`}
                  >
                    <span>Variance</span>
                    <span className="font-mono tabular-nums">
                      {detail.gate.variance_minor === null
                        ? "n/a"
                        : formatSignedMinor(detail.gate.variance_minor, detail.currency)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </Panel>

      <Panel
        title="Match Candidates"
        subtitle="Deterministic candidates found by the matcher. Score ranks only; it never authorizes a resolution."
      >
        {detail.candidates.length === 0 ? (
          <p className="text-sm text-slate-500">
            No candidates found in the ledger pool within the candidate window.
          </p>
        ) : (
          <div className="space-y-3">
            {detail.candidates.map((candidate) => (
              <div
                key={candidate.ledger_entry_id}
                className="rounded-md border border-slate-800 bg-[#0b0f16] p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-mono text-xs text-slate-300">
                    {candidate.ledger_entry_id}
                  </span>
                  <div className="flex items-center gap-2">
                    <Badge tone="info">{candidate.provenance.replaceAll("_", " ")}</Badge>
                    <span className="font-mono text-xs tabular-nums text-slate-400">
                      score {candidate.score.toFixed(2)}
                    </span>
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {candidate.matched_signals.map((signal) => (
                    <span
                      key={signal}
                      className="rounded bg-slate-800/70 px-1.5 py-0.5 text-[11px] text-slate-400"
                    >
                      {signal}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="Evidence" subtitle="Field-level evidence and whether the gate consumed it">
        {detail.evidence.length === 0 ? (
          <p className="text-sm text-slate-500">No evidence was constructed for this case.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4">Source</th>
                  <th className="py-2 pr-4">Field</th>
                  <th className="py-2 pr-4">Stance</th>
                  <th className="py-2 pr-4 text-right">Relevance</th>
                  <th className="py-2">Consumed by gate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {detail.evidence.map((item, idx) => (
                  <tr key={`${item.entity_id}-${item.field}-${idx}`}>
                    <td className="py-2 pr-4 font-mono text-xs text-slate-400">
                      {item.entity_type}:{item.entity_id}
                    </td>
                    <td className="py-2 pr-4 text-xs text-slate-300">{item.field}</td>
                    <td className="py-2 pr-4">
                      <Badge tone={stanceTone(item.stance)}>{item.stance}</Badge>
                    </td>
                    <td className="py-2 pr-4 text-right font-mono text-xs tabular-nums text-slate-400">
                      {item.relevance.toFixed(2)}
                    </td>
                    <td className="py-2 text-xs text-slate-400">
                      {item.decision_consumed ? "Yes" : "No"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title="Deterministic Gate" subtitle="evaluate_gate() &mdash; the sole financial firewall">
        <div className="space-y-4">
          <GateChecklist gate={detail.gate} />

          {gateOutcome && !gateOutcome.passed && gateOutcome.explanation && (
            <div className="space-y-3 rounded-md border border-amber-500/30 bg-amber-500/[0.04] p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-500/20 pb-2.5">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-amber-300">
                    Automation Blocked &middot; Check: {gateOutcome.failing_check}
                  </span>
                </div>
                {gateOutcome.failing_check && (
                  <Link
                    href={`/gate?check=${gateOutcome.failing_check}`}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-amber-400 hover:text-amber-300"
                  >
                    Inspect in Gate Diagnostics <ArrowRight className="h-3 w-3" />
                  </Link>
                )}
              </div>

              <div className="space-y-1 text-xs">
                <div className="font-semibold text-slate-200">
                  {gateOutcome.explanation.summary}
                </div>
                <p className="leading-relaxed text-slate-400">
                  {gateOutcome.explanation.description}
                </p>
              </div>

              <div className="rounded border border-amber-500/20 bg-amber-500/10 p-2.5 text-xs">
                <div className="font-semibold text-amber-300">
                  Deterministic Eligibility Requirement (&quot;What Must Change&quot;):
                </div>
                <div className="mt-1 leading-relaxed text-amber-200">
                  {gateOutcome.explanation.eligibility_requirement}
                </div>
              </div>

              <div className="flex items-center justify-between pt-1 text-[11px] text-slate-500">
                <span>Belief vs Authorization: Hypothesis confidence never bypasses Gate firewall.</span>
                <Link href="/confidence" className="text-indigo-400 hover:text-indigo-300">
                  View Calibration Analysis &rarr;
                </Link>
              </div>
            </div>
          )}
        </div>
      </Panel>

      <InvestigationPanel
        detail={detail}
        onApplyRecommendation={(targetIds) => {
          setSelectedTargetIds(new Set(targetIds));
          setRecommendationNotice(
            `Recommendation applied to review selection (${targetIds.join(", ")}). No approval has been submitted. Review evidence and gate below before approving.`,
          );
        }}
      />

      <ReviewPanel
        detail={detail}
        selectedTargetIds={selectedTargetIds}
        onSelectedTargetIdsChange={setSelectedTargetIds}
        appliedNotice={recommendationNotice}
        onClearNotice={() => setRecommendationNotice(null)}
        onUpdated={(updated) => {
          setDetail(updated);
          setRecommendationNotice(null);
        }}
      />

      <Panel title="Audit Timeline" subtitle="Chronological, append-only record of this case's pipeline">
        <ol className="space-y-3 border-l border-slate-800 pl-4">
          {detail.audit_events.map((event) => (
            <li key={event.event_id} className="relative">
              <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-slate-600" />
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
                <span className="text-sm font-medium text-slate-200">
                  {event.event_type.replaceAll("_", " ")}
                </span>
                <span className="text-xs text-slate-500">{formatDateTime(event.timestamp)}</span>
              </div>
              <div className="text-xs text-slate-500">
                {event.entity_type} &middot; actor: {event.actor}
              </div>
              {Object.keys(event.metadata).length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {Object.entries(event.metadata).map(([key, value]) => (
                    <span
                      key={key}
                      className="rounded bg-slate-800/70 px-1.5 py-0.5 text-[11px] text-slate-400"
                    >
                      {key}={value}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ol>
      </Panel>
    </div>
  );
}

function BackLink() {
  return (
    <Link href="/cases" className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300">
      <ArrowLeft className="h-3 w-3" /> Back to Case Explorer
    </Link>
  );
}

function SummaryStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: Tone;
}) {
  const TONE_TEXT: Record<Tone, string> = {
    success: "text-emerald-400",
    warning: "text-amber-400",
    danger: "text-red-400",
    neutral: "text-slate-100",
    info: "text-sky-400",
  };
  const toneClass = tone ? TONE_TEXT[tone] : "text-slate-100";
  return (
    <div className="rounded-lg border border-slate-800 bg-[#0d1219] p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1.5 font-mono text-lg font-semibold tabular-nums ${toneClass}`}>
        {value}
      </div>
    </div>
  );
}

function BridgeLine({
  label,
  value,
  currency,
}: {
  label: string;
  value: number;
  currency: string;
}) {
  return (
    <li className="flex items-center justify-between text-slate-300">
      <span>{label}</span>
      <span className="font-mono tabular-nums">{formatSignedMinor(value, currency).replace("+", "")}</span>
    </li>
  );
}
