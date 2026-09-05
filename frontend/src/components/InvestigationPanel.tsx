"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, ShieldCheck, XCircle } from "lucide-react";
import { ApiError, fetchInvestigation, triggerInvestigation } from "@/lib/api";
import { Badge } from "@/components/Badge";
import type { Tone } from "@/components/Badge";
import { Panel } from "@/components/Panel";
import { GateChecklist } from "@/components/GateChecklist";
import type { CaseDetail, Investigation, InvestigationResult, StopReason } from "@/lib/types";

const STOP_REASON_LABEL: Record<string, string> = {
  COMPLETED: "Completed",
  BUDGET_EXHAUSTED: "Budget Exhausted",
  TIMEOUT: "Timed Out",
  TOOL_FAILURE: "Provider/Tool Failure",
  MALFORMED_OUTPUT: "Malformed Output",
};

// One-line, non-financial conclusions for every terminal state that produces
// no proposal. COMPLETED is handled separately below (it always means an
// explicit abstain when there is no proposal - AIInvestigationUseCase
// downgrades stop_reason away from COMPLETED whenever a proposal is rejected
// as out-of-pool, so COMPLETED + no proposal is never ambiguous here).
const NON_PROPOSAL_CONCLUSION: Record<Exclude<StopReason, "COMPLETED">, string> = {
  TOOL_FAILURE: "Investigation could not complete.",
  MALFORMED_OUTPUT: "Investigation returned an invalid result.",
  BUDGET_EXHAUSTED: "Investigation reached its safety budget.",
  TIMEOUT: "Investigation timed out before completing.",
};

const NON_PROPOSAL_STATE_LABEL: Record<Exclude<StopReason, "COMPLETED">, string> = {
  TOOL_FAILURE: "PROVIDER FAILURE",
  MALFORMED_OUTPUT: "MALFORMED OUTPUT",
  BUDGET_EXHAUSTED: "BUDGET EXHAUSTED",
  TIMEOUT: "TIMED OUT",
};

const NON_PROPOSAL_TONE: Record<Exclude<StopReason, "COMPLETED">, Tone> = {
  TOOL_FAILURE: "danger",
  MALFORMED_OUTPUT: "danger",
  BUDGET_EXHAUSTED: "warning",
  TIMEOUT: "warning",
};

/**
 * The abstain reason is not a dedicated API field - it is the last tool
 * call's response_summary when that call is "abstain", verbatim as the
 * backend authored it ("Abstained: <reason>"). Only the known literal prefix
 * is stripped for display; nothing is inferred or heuristically summarized.
 */
function getAbstainReason(investigation: Investigation): string | null {
  if (investigation.stop_reason !== "COMPLETED") return null;
  const last = investigation.tool_calls[investigation.tool_calls.length - 1];
  if (!last || last.tool_name !== "abstain") return null;
  const prefix = "Abstained: ";
  return last.response_summary.startsWith(prefix)
    ? last.response_summary.slice(prefix.length)
    : last.response_summary;
}

type SummaryItem = { label: string; value: string };

function buildSummaryItems(result: InvestigationResult): SummaryItem[] {
  const toolCalls = String(result.investigation.tool_calls.length);
  const candidatesInvestigated = String(result.investigation.candidates_considered.length);

  if (result.proposal) {
    const items: SummaryItem[] = [
      { label: "Recommendation", value: "Human review / approval" },
      { label: "Confidence", value: result.proposal.confidence.toFixed(2) },
      {
        label: "Gate status",
        value: result.preview_gate ? (result.preview_gate.passed ? "PASS" : "FAIL") : "Pending",
      },
    ];
    if (result.preview_gate && !result.preview_gate.passed) {
      items.push({
        label: "Failing check",
        value: result.preview_gate.failing_check ?? "Unknown",
      });
    }
    items.push({ label: "Tool calls", value: toolCalls });
    items.push({ label: "Candidates investigated", value: candidatesInvestigated });
    return items;
  }

  return [
    { label: "Recommendation", value: "Human review" },
    { label: "Gate status", value: "Not applicable — no proposal was made" },
    { label: "Tool calls", value: toolCalls },
    { label: "Candidates investigated", value: candidatesInvestigated },
  ];
}

export function InvestigationPanel({
  detail,
  onApplyRecommendation,
}: {
  detail: CaseDetail;
  onApplyRecommendation?: (targetIds: string[]) => void;
}) {
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applyNotice, setApplyNotice] = useState<string | null>(null);

  const isFinalized =
    detail.resolution.review_outcome === "APPROVED" ||
    detail.resolution.review_outcome === "REJECTED";

  const [prevSettlementId, setPrevSettlementId] = useState(detail.settlement_id);
  if (prevSettlementId !== detail.settlement_id) {
    setPrevSettlementId(detail.settlement_id);
    setApplyError(null);
    setApplyNotice(null);
  }

  useEffect(() => {
    let cancelled = false;
    fetchInvestigation(detail.settlement_id)
      .then((existing) => {
        if (!cancelled) setResult(existing);
      })
      .catch(() => {
        // No prior investigation is not an error state for this panel.
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [detail.settlement_id]);

  if (detail.disposition !== "HUMAN_REVIEW") {
    return null;
  }

  async function runInvestigation() {
    setRunning(true);
    setError(null);
    setApplyError(null);
    setApplyNotice(null);
    try {
      const outcome = await triggerInvestigation(detail.settlement_id);
      setResult(outcome);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Investigation request failed.");
    } finally {
      setRunning(false);
    }
  }

  function handleApplyRecommendation() {
    setApplyError(null);
    setApplyNotice(null);

    if (isFinalized) {
      setApplyError(
        `Case review is already finalized (${detail.resolution.review_outcome}). Recommendations cannot be applied.`,
      );
      return;
    }

    if (!result?.proposal) {
      setApplyError("No AI recommendation available to apply.");
      return;
    }

    const proposedIds = result.proposal.target_ledger_entry_ids;
    if (!proposedIds || proposedIds.length === 0) {
      setApplyError("AI proposal contains no target ledger entry IDs to apply.");
      return;
    }

    // Validate that all proposed IDs exist in this case's candidate pool
    const candidateIds = new Set(detail.candidates.map((c) => c.ledger_entry_id));
    const outOfPool = proposedIds.filter((id) => !candidateIds.has(id));
    if (outOfPool.length > 0) {
      setApplyError(
        `AI proposed target ID(s) ${outOfPool.join(", ")} do not exist in this case's candidate pool. Recommendation cannot be applied.`,
      );
      return;
    }

    // Apply recommendation to parent selection
    if (onApplyRecommendation) {
      onApplyRecommendation(proposedIds);
    }

    setApplyNotice(
      `Recommendation applied to review selection (${proposedIds.join(", ")}). No approval has been submitted. Reviewer must still verify evidence and explicitly approve below.`,
    );

    // Scroll to review panel smoothly
    setTimeout(() => {
      const panel = document.getElementById("review-panel");
      if (panel) {
        panel.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 50);
  }

  const abstainReason = result ? getAbstainReason(result.investigation) : null;
  const isNonProposalTerminal =
    result && !result.proposal && result.investigation.stop_reason !== "COMPLETED";

  return (
    <Panel
      title="AI Investigation"
      subtitle="A bounded investigator reasons over this case's existing candidates and evidence only. It can never resolve a case — any proposal is independently re-verified by the same deterministic gate, and a human must still approve it."
    >
      <div className="space-y-4">
        <button
          type="button"
          disabled={running || isFinalized}
          onClick={() => void runInvestigation()}
          className="inline-flex items-center gap-2 rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-4 py-2 font-mono text-xs font-semibold text-[#171816] transition-colors hover:border-[#171816] hover:bg-[#E5DFD1] disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Bot className="h-4 w-4 text-[#3B5145]" />
          {running
            ? "Investigating..."
            : isFinalized
              ? "Investigation Unavailable (Review Finalized)"
              : result
                ? "Re-investigate with AI"
                : "Investigate with AI"}
        </button>

        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-3.5 py-2.5 text-xs font-mono text-[#9A514C]">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !result && !running && (
          <p className="font-mono text-xs text-[#6B6D64]">No investigation has been run for this case yet.</p>
        )}

        {result && (
          <div className="space-y-4">
            {/* AI Conclusion - the primary interface. A judge/operator should
                understand the outcome from this card alone, without opening
                the technical trace below. */}
            <div className="space-y-4 rounded-xl border border-[#CFC9BC] bg-[#F8F6F0] p-5">
              <div className="flex items-center gap-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                <ShieldCheck className="h-3.5 w-3.5" />
                AI Conclusion
              </div>

              {result.proposal ? (
                <>
                  <Badge tone="warning">Proposal &mdash; Awaiting Review</Badge>
                  <p className="text-sm leading-relaxed text-[#171816]">
                    AI proposed linking this settlement to{" "}
                    {result.proposal.target_ledger_entry_ids.length === 1
                      ? "one candidate ledger entry"
                      : `${result.proposal.target_ledger_entry_ids.length} candidate ledger entries`}
                    . This is a non-authoritative recommendation &mdash; it cannot resolve the case on its own.
                  </p>
                  <div>
                    <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                      Proposed candidate(s)
                    </div>
                    <div className="mt-1.5 flex flex-wrap gap-2">
                      {result.proposal.target_ledger_entry_ids.map((id) => {
                        const candidate = detail.candidates.find((c) => c.ledger_entry_id === id);
                        return (
                          <span
                            key={id}
                            className="rounded-md border border-[#CFC9BC] bg-[#EEEAE0] px-2.5 py-1 font-mono text-xs font-semibold text-[#171816]"
                          >
                            {id}
                            {candidate ? ` · score ${candidate.score.toFixed(2)}` : ""}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                </>
              ) : result.investigation.stop_reason === "COMPLETED" ? (
                <>
                  <Badge tone="success">Abstained</Badge>
                  <p className="text-sm leading-relaxed text-[#171816]">
                    AI could not establish a safe resolution. Do not auto-resolve this case.
                  </p>
                  {abstainReason && (
                    <p className="rounded-lg border border-[#CFC9BC]/70 bg-[#EEEAE0] p-3 text-xs leading-relaxed text-[#4F514A]">
                      {abstainReason}
                    </p>
                  )}
                </>
              ) : (
                isNonProposalTerminal && (
                  <>
                    <Badge tone={NON_PROPOSAL_TONE[result.investigation.stop_reason as Exclude<StopReason, "COMPLETED">]}>
                      {NON_PROPOSAL_STATE_LABEL[result.investigation.stop_reason as Exclude<StopReason, "COMPLETED">]}
                    </Badge>
                    <p className="text-sm leading-relaxed text-[#171816]">
                      {NON_PROPOSAL_CONCLUSION[result.investigation.stop_reason as Exclude<StopReason, "COMPLETED">]}
                    </p>
                  </>
                )
              )}

              <dl className="grid grid-cols-2 gap-x-6 gap-y-2.5 border-t border-[#D9D5CA] pt-3.5 font-mono text-xs sm:grid-cols-4">
                {buildSummaryItems(result).map((item) => (
                  <div key={item.label}>
                    <dt className="text-[#6B6D64]">{item.label}</dt>
                    <dd className="mt-0.5 font-semibold text-[#171816]">{item.value}</dd>
                  </div>
                ))}
              </dl>
            </div>

            {result.proposal && (
              <div className="space-y-4 rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-5">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#D9D5CA] pb-3">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#171816]">
                    Rationale &amp; Evidence
                  </span>
                  <span className="rounded-md border border-[#CFC9BC] bg-[#F8F6F0] px-2.5 py-1 font-mono text-xs font-semibold tabular-nums text-[#4F514A]">
                    confidence {result.proposal.confidence.toFixed(2)}
                  </span>
                </div>

                <div>
                  <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                    Rationale
                  </div>
                  <p className="mt-1.5 rounded-lg border border-[#CFC9BC]/70 bg-[#F8F6F0] p-3 text-xs leading-relaxed text-[#171816]">
                    {result.proposal.rationale}
                  </p>
                </div>

                {result.proposal.evidence.length > 0 && (
                  <div>
                    <div className="font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
                      Evidence (deterministically rebuilt, not model-asserted)
                    </div>
                    <ul className="mt-1.5 space-y-1.5">
                      {result.proposal.evidence.map((e, idx) => (
                        <li key={`${e.entity_id}-${e.field}-${idx}`} className="font-mono text-xs text-[#4F514A]">
                          <Badge tone={e.stance === "SUPPORTS" ? "success" : "danger"} className="mr-1.5">
                            {e.stance}
                          </Badge>
                          {e.entity_type}:{e.entity_id}.{e.field}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="pt-2">
                  <button
                    type="button"
                    disabled={isFinalized}
                    onClick={handleApplyRecommendation}
                    className="inline-flex items-center gap-2 rounded-lg border border-[#171816] bg-[#171816] px-4 py-2 font-mono text-xs font-bold text-[#F8F6F0] transition-colors hover:bg-[#3F413B] disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Use AI Recommendation
                  </button>
                  {isFinalized && (
                    <p className="mt-1.5 font-mono text-xs text-[#6B6D64]">
                      Case review is already finalized ({detail.resolution.review_outcome}). Recommendation cannot be applied.
                    </p>
                  )}
                </div>

                {applyError && (
                  <div className="flex items-start gap-2 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-3.5 py-2.5 text-xs font-mono text-[#9A514C]">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{applyError}</span>
                  </div>
                )}

                {applyNotice && (
                  <div className="flex items-start gap-2 rounded-xl border border-[#3B5145]/30 bg-[#3B5145]/10 px-3.5 py-2.5 text-xs font-mono text-[#3B5145]">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#3B5145]" />
                    <span>{applyNotice}</span>
                  </div>
                )}
              </div>
            )}

            {result.preview_gate && (
              <div className="space-y-3 pt-2">
                <div className="font-mono text-xs font-bold uppercase tracking-wider text-[#171816]">
                  Deterministic Safety Gate Validation (Independent Firewall)
                </div>
                <div
                  className={`flex items-center gap-2 rounded-xl border px-4 py-3 font-mono text-xs font-semibold ${
                    result.preview_gate.passed
                      ? "border-[#3B5145]/30 bg-[#3B5145]/10 text-[#3B5145]"
                      : "border-[#9A514C]/30 bg-[#9A514C]/10 text-[#9A514C]"
                  }`}
                >
                  {result.preview_gate.passed ? (
                    <CheckCircle2 className="h-4 w-4 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 shrink-0" />
                  )}
                  {result.preview_gate.passed ? (
                    <span>
                      Deterministic Preview Gate: <strong>PASS</strong>. Proposal satisfies all 9 deterministic safety checks. Human approval is still strictly required.
                    </span>
                  ) : (
                    <span>
                      Deterministic Preview Gate: <strong>FAIL &mdash; {result.preview_gate.failing_check}</strong>. Deterministic gate refuses this proposal.
                    </span>
                  )}
                </div>
                <GateChecklist gate={result.preview_gate} />
              </div>
            )}

            {result.investigation.tool_calls.length > 0 && (
              <details className="rounded-xl border border-[#CFC9BC] bg-[#F8F6F0]">
                <summary className="cursor-pointer px-4 py-3 font-mono text-xs font-semibold uppercase tracking-wider text-[#6B6D64] hover:text-[#171816]">
                  Technical investigation trace &mdash; {result.investigation.tool_calls.length} calls
                </summary>
                <div className="border-t border-[#D9D5CA] p-4">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <Badge tone={result.investigation.stop_reason === "COMPLETED" ? "success" : "warning"}>
                      {STOP_REASON_LABEL[result.investigation.stop_reason] ?? result.investigation.stop_reason}
                    </Badge>
                    {result.investigation.candidates_considered.length > 0 && (
                      <span className="font-mono text-xs text-[#6B6D64]">
                        considered {result.investigation.candidates_considered.join(", ")}
                      </span>
                    )}
                  </div>
                  <ol className="space-y-2">
                    {result.investigation.tool_calls.map((call, idx) => (
                      <li key={idx} className="text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-semibold text-[#171816]">{call.tool_name}</span>
                          <span className="font-mono text-[#6B6D64]">({call.duration_ms}ms)</span>
                        </div>
                        <div className="mt-0.5 break-words font-mono text-[11px] text-[#4F514A]">{call.response_summary}</div>
                      </li>
                    ))}
                  </ol>
                </div>
              </details>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
