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
        <div className="flex flex-col items-center justify-center rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] py-24 text-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#CFC9BC] border-t-[#3B5145]" />
          <p className="mt-4 font-mono text-xs font-medium uppercase tracking-wider text-[#4F514A]">
            Loading forensic case file {settlementId}...
          </p>
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="space-y-6">
        <BackLink />
        <div className="flex items-start gap-3 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-4 py-3.5 text-sm text-[#9A514C]">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#9A514C]" />
          <div className="font-mono text-xs">
            <strong className="block font-semibold uppercase tracking-wide">Case Access Error</strong>
            <span>{error ?? "Case not found."}</span>
          </div>
        </div>
      </div>
    );
  }

  const { bridge } = detail;

  return (
    <div className="space-y-6">
      {/* 1. Back Action */}
      <BackLink />

      {/* 2. Operational Case Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3B5145]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
            <span>CASE DETAIL</span>
            <span className="text-[#CFC9BC]">/</span>
            <span className="text-[#4F514A]">FORENSIC SETTLEMENT AUDIT</span>
          </div>
          <h1 className="mt-1.5 font-mono text-2xl font-bold tracking-tight text-[#171816] sm:text-3xl">
            {detail.settlement_id}
          </h1>
          <p className="mt-1 font-mono text-xs text-[#4F514A]">
            <span className="font-bold text-[#171816]">{exceptionLabel(detail.exception_type)}</span>
            <span className="mx-2 text-[#CFC9BC]">&middot;</span>
            <span>{detail.candidates.length} candidate{detail.candidates.length === 1 ? "" : "s"}</span>
            {detail.scenario_family && (
              <>
                <span className="mx-2 text-[#CFC9BC]">&middot;</span>
                <span className="text-[#6B6D64]">demo scenario: {scenarioLabel(detail.scenario_family)} ({detail.scenario_family})</span>
              </>
            )}
          </p>
        </div>

        <div>
          <Badge tone={dispositionTone(detail.disposition)} className="px-3.5 py-1.5 font-mono text-xs font-bold uppercase tracking-wider">
            {dispositionLabel(detail.disposition)}
          </Badge>
        </div>
      </div>

      {/* Recurring Exception Pattern Alert */}
      {caseCluster && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] text-[#8C6843]">
              <Layers className="h-4 w-4" />
            </div>
            <div>
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Recurring Exception Pattern
              </div>
              <div className="font-mono text-xs font-bold text-[#171816]">
                {caseCluster.cluster_name}
                <span className="ml-2 font-normal text-[#6B6D64]">({caseCluster.case_count} cases in cluster)</span>
              </div>
            </div>
          </div>
          <Link
            href="/exceptions"
            className="inline-flex items-center gap-1.5 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-3 py-1.5 font-mono text-xs font-semibold text-[#171816] transition-colors hover:border-[#171816] hover:bg-[#E5DFD1]"
          >
            <span>View Exception Intelligence</span>
            <ArrowRight className="h-3 w-3 text-[#6B6D64]" />
          </Link>
        </div>
      )}

      {/* 3. Financial Summary KPI Cards */}
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

      {/* 4. Cash Bridge & Dual Observation */}
      <Panel
        title="Cash Bridge &amp; Dual Ledger Observation"
        subtitle="Settlement-level derivation of the expected net amount and dual-layer ledger observation."
      >
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left Column: Mathematical Cash Bridge Proof */}
          <div className="flex flex-col justify-between rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-5">
            <div>
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Mathematical Settlement Bridge Proof
              </div>
              <p className="mt-0.5 text-xs text-[#4F514A]">
                Authoritative formula: gross &minus; fee &minus; tax &minus; refund + adj = net
              </p>

              <ol className="mt-4 space-y-2.5">
                <BridgeLine label="Gross Amount" value={bridge.gross_minor} currency={detail.currency} prefix="  " />
                <BridgeLine label="&minus; Processing Fee" value={-bridge.fee_minor} currency={detail.currency} prefix="&minus; " />
                <BridgeLine label="&minus; Tax on Fee (18% GST)" value={-bridge.tax_on_fee_minor} currency={detail.currency} prefix="&minus; " />
                <BridgeLine
                  label="&minus; Netted Refund"
                  value={-bridge.netted_refund_minor}
                  currency={detail.currency}
                  prefix="&minus; "
                />
                <BridgeLine label="+ Settlement Adjustment" value={bridge.adjustment_minor} currency={detail.currency} prefix="+ " />
                
                <li className="flex items-center justify-between border-t-2 border-[#171816] pt-2.5 font-bold text-[#171816]">
                  <span className="font-mono text-xs uppercase tracking-wider">= Expected Net</span>
                  <span className="font-mono text-base tabular-nums">
                    {formatMinor(bridge.expected_net_minor, detail.currency)}
                  </span>
                </li>
              </ol>
            </div>

            <div className="mt-5 border-t border-[#D9D5CA] pt-3 font-mono text-[10px] text-[#6B6D64]">
              GST is computed once at 18% using half-up paise rounding. Ingestion never re-computes stored tax.
            </div>
          </div>

          {/* Right Column: Case-Level vs Gate-Level Observations */}
          <div className="flex flex-col gap-4">
            {/* Case-Level Observation */}
            <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-4">
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Case-Level Observation &middot; Authoritative Structural Ledger State
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[#4F514A]">Expected Settlement</span>
                  <span className="font-mono font-semibold tabular-nums text-[#171816]">
                    {formatMinor(detail.expected_net_minor, detail.currency)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[#4F514A]">Observed Ledger Pool</span>
                  <span className="font-mono font-semibold tabular-nums text-[#171816]">
                    {formatMinor(detail.observed_net_minor, detail.currency)}
                  </span>
                </div>
                <div
                  className={`flex items-center justify-between border-t border-[#D9D5CA] pt-2 font-mono font-bold ${
                    detail.delta_minor === 0 ? "text-[#3B5145]" : "text-[#9A514C]"
                  }`}
                >
                  <span>Pool Delta</span>
                  <span className="tabular-nums">
                    {formatSignedMinor(detail.delta_minor, detail.currency)}
                  </span>
                </div>
              </div>
            </div>

            {/* Gate-Level Observation */}
            <div className="rounded-xl border border-[#CFC9BC] bg-[#F2ECE1] p-4">
              <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                Gate-Level Observation &middot; Net of the Proposed Target Set Only
              </div>
              {detail.gate.proposed_target_ids.length === 0 ? (
                <p className="mt-3 font-mono text-xs text-[#6B6D64]">No proposed target selected.</p>
              ) : (
                <div className="mt-3 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[#4F514A]">Proposed Target Net</span>
                    <span className="font-mono font-semibold tabular-nums text-[#171816]">
                      {detail.gate.proposed_target_net_minor === null
                        ? "n/a"
                        : formatMinor(detail.gate.proposed_target_net_minor, detail.currency)}
                    </span>
                  </div>
                  <div
                    className={`flex items-center justify-between border-t border-[#D9D5CA] pt-2 font-mono font-bold ${
                      detail.gate.variance_minor === 0 ? "text-[#3B5145]" : "text-[#9A514C]"
                    }`}
                  >
                    <span>Target Variance</span>
                    <span className="tabular-nums">
                      {detail.gate.variance_minor === null
                        ? "n/a"
                        : formatSignedMinor(detail.gate.variance_minor, detail.currency)}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="font-mono text-[10px] text-[#6B6D64] leading-relaxed">
              Observation &ne; Hypothesis: Case-level reflects immutable ledger pool facts; Gate-level evaluates proposed candidate targets.
            </div>
          </div>
        </div>
      </Panel>

      {/* 5. Match Candidates */}
      <Panel
        title="Match Candidates"
        subtitle="Deterministic candidates found by the matcher. Score ranks only; it never authorizes a resolution."
      >
        <div className="space-y-4">
          <div className="rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-4 py-2.5 font-mono text-xs text-[#4F514A]">
            <span className="font-bold text-[#171816]">Candidate Invariant:</span> Score ranks candidate relevance for reviewer inspection. Score never authorizes money movement or resolution.
          </div>

          {detail.candidates.length === 0 ? (
            <p className="font-mono text-xs text-[#6B6D64]">
              No candidates found in the ledger pool within the candidate window.
            </p>
          ) : (
            <div className="space-y-3">
              {detail.candidates.map((candidate) => (
                <div
                  key={candidate.ledger_entry_id}
                  className="rounded-xl border border-[#D9D5CA] bg-[#F8F6F0] p-4 shadow-sm transition-colors hover:border-[#171816]"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold text-[#171816]">
                      {candidate.ledger_entry_id}
                    </span>
                    <div className="flex items-center gap-2">
                      <Badge tone="info">{candidate.provenance.replaceAll("_", " ")}</Badge>
                      <span className="inline-flex items-center gap-1 rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2 py-0.5 font-mono text-xs font-semibold tabular-nums text-[#171816]">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#6B6D64]" />
                        <span>score {candidate.score.toFixed(2)}</span>
                      </span>
                    </div>
                  </div>
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {candidate.matched_signals.map((signal) => (
                      <span
                        key={signal}
                        className="rounded-md border border-[#D9D5CA] bg-[#EEEAE0] px-2 py-0.5 font-mono text-[11px] text-[#4F514A]"
                      >
                        {signal}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Panel>

      {/* 6. Evidence Ledger */}
      <Panel title="Evidence Ledger" subtitle="Field-level evidence constructed for matching and whether the gate consumed it">
        {detail.evidence.length === 0 ? (
          <p className="font-mono text-xs text-[#6B6D64]">No evidence was constructed for this case.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-[#CFC9BC] bg-[#F8F6F0]">
            <table className="w-full min-w-[640px] border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                  <th className="py-3 pl-4 pr-3">Source</th>
                  <th className="px-3 py-3">Field</th>
                  <th className="px-3 py-3">Stance</th>
                  <th className="px-3 py-3 text-right">Relevance</th>
                  <th className="py-3 pl-3 pr-4 text-center">Consumed by Gate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D5CA]">
                {detail.evidence.map((item, idx) => (
                  <tr key={`${item.entity_id}-${item.field}-${idx}`} className="hover:bg-[#F2ECE1]/50">
                    <td className="py-2.5 pl-4 pr-3 font-mono text-xs text-[#171816] break-all max-w-[240px]">
                      {item.entity_type}:{item.entity_id}
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-[#4F514A]">{item.field}</td>
                    <td className="px-3 py-2.5">
                      <Badge tone={stanceTone(item.stance)}>{item.stance}</Badge>
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-xs tabular-nums text-[#171816]">
                      {item.relevance.toFixed(2)}
                    </td>
                    <td className="py-2.5 pl-3 pr-4 text-center font-mono text-xs font-semibold text-[#171816]">
                      {item.decision_consumed ? (
                        <span className="text-[#3B5145]">Yes</span>
                      ) : (
                        <span className="text-[#6B6D64]">No</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      {/* 7. Deterministic Gate Section */}
      <Panel
        title="Deterministic Resolution Gate"
        subtitle="evaluate_gate() &mdash; the non-negotiable financial firewall. Confidence does not authorize."
      >
        <div className="space-y-5">
          <GateChecklist gate={detail.gate} />

          {gateOutcome && !gateOutcome.passed && gateOutcome.explanation && (
            <div className="space-y-3.5 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 p-5">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#9A514C]/20 pb-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-[#9A514C]" />
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#9A514C]">
                    Automation Blocked &middot; Check: {gateOutcome.failing_check}
                  </span>
                </div>
                {gateOutcome.failing_check && (
                  <Link
                    href={`/gate?check=${gateOutcome.failing_check}`}
                    className="inline-flex items-center gap-1 font-mono text-xs font-semibold text-[#171816] underline hover:text-[#9A514C]"
                  >
                    <span>Inspect in Gate Diagnostics</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                )}
              </div>

              <div className="space-y-1 text-xs">
                <div className="font-semibold text-[#171816]">
                  {gateOutcome.explanation.summary}
                </div>
                <p className="leading-relaxed text-[#4F514A]">
                  {gateOutcome.explanation.description}
                </p>
              </div>

              <div className="rounded-lg border border-[#CFC9BC] bg-[#F8F6F0] p-3 text-xs">
                <div className="font-mono font-bold text-[#9A514C]">
                  Deterministic Eligibility Requirement (&quot;What Must Change&quot;):
                </div>
                <div className="mt-1 leading-relaxed font-mono text-[#171816]">
                  {gateOutcome.explanation.eligibility_requirement}
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 pt-1 font-mono text-[11px] text-[#6B6D64]">
                <span>Belief vs Authorization: Hypothesis confidence never bypasses Gate firewall.</span>
                <Link href="/confidence" className="text-[#8C6843] underline hover:text-[#171816]">
                  View Calibration Analysis &rarr;
                </Link>
              </div>
            </div>
          )}
        </div>
      </Panel>

      {/* 8. AI Investigation Panel */}
      <InvestigationPanel
        detail={detail}
        onApplyRecommendation={(targetIds) => {
          setSelectedTargetIds(new Set(targetIds));
          setRecommendationNotice(
            `Recommendation applied to review selection (${targetIds.join(", ")}). No approval has been submitted. Review evidence and gate below before approving.`,
          );
        }}
      />

      {/* 9. Human Review Panel */}
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

      {/* 10. Audit Timeline */}
      <Panel title="Audit Timeline" subtitle="Chronological, append-only record of this case's pipeline lifecycle">
        <ol className="relative space-y-4 border-l-2 border-[#D9D5CA] pl-5 ml-2">
          {detail.audit_events.map((event) => (
            <li key={event.event_id} className="relative">
              <span className="absolute -left-[27px] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-[#F8F6F0] bg-[#8C6843]" />
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
                <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#171816]">
                  {event.event_type.replaceAll("_", " ")}
                </span>
                <span className="font-mono text-xs text-[#6B6D64]">{formatDateTime(event.timestamp)}</span>
              </div>
              <div className="font-mono text-xs text-[#4F514A]">
                {event.entity_type} &middot; actor: {event.actor}
              </div>
              {Object.keys(event.metadata).length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {Object.entries(event.metadata).map(([key, value]) => (
                    <span
                      key={key}
                      className="rounded-md border border-[#D9D5CA] bg-[#EEEAE0] px-2 py-0.5 font-mono text-[11px] text-[#4F514A]"
                    >
                      {key}={String(value)}
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
    <Link
      href="/cases"
      className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-[#4F514A] transition-colors hover:text-[#171816]"
    >
      <ArrowLeft className="h-3.5 w-3.5" />
      <span>Back to Case Explorer</span>
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
  const TONE_COLORS: Record<Tone, string> = {
    success: "text-[#3B5145]",
    warning: "text-[#8C6843]",
    danger: "text-[#9A514C]",
    neutral: "text-[#171816]",
    info: "text-[#4E6870]",
  };
  const valColor = tone ? TONE_COLORS[tone] : "text-[#171816]";
  return (
    <div className="rounded-2xl border border-[#D9D5CA] bg-[#F8F6F0] p-5 shadow-[0_2px_8px_rgba(0,0,0,0.03)]">
      <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">{label}</div>
      <div className={`mt-2 font-mono text-xl sm:text-2xl font-bold tabular-nums tracking-tight ${valColor}`}>
        {value}
      </div>
    </div>
  );
}

function BridgeLine({
  label,
  value,
  currency,
  prefix = "",
}: {
  label: string;
  value: number;
  currency: string;
  prefix?: string;
}) {
  return (
    <li className="flex items-center justify-between font-mono text-xs text-[#4F514A]">
      <span className="font-medium">{label}</span>
      <span className="tabular-nums font-semibold text-[#171816]">
        {prefix}
        {formatSignedMinor(value, currency).replace("+", "").replace("-", "")}
      </span>
    </li>
  );
}
