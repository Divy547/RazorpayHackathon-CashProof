"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, XCircle } from "lucide-react";
import { ApiError, fetchInvestigation, triggerInvestigation } from "@/lib/api";
import { Badge } from "@/components/Badge";
import { Panel } from "@/components/Panel";
import { GateChecklist } from "@/components/GateChecklist";
import type { CaseDetail, InvestigationResult } from "@/lib/types";

const STOP_REASON_LABEL: Record<string, string> = {
  COMPLETED: "Completed",
  BUDGET_EXHAUSTED: "Budget Exhausted",
  TIMEOUT: "Timed Out",
  TOOL_FAILURE: "Provider/Tool Failure",
  MALFORMED_OUTPUT: "Malformed Output",
};

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

  return (
    <Panel
      title="AI Investigation"
      subtitle="A bounded investigator reasons over this case's existing candidates/evidence only. It can never resolve a case - any proposal is independently re-verified by the same deterministic gate, and a human must still approve it."
    >
      <div className="space-y-4">
        <button
          type="button"
          disabled={running || isFinalized}
          onClick={() => void runInvestigation()}
          className="flex items-center gap-2 rounded-md border border-sky-500/40 bg-sky-500/10 px-4 py-2 text-sm font-medium text-sky-400 transition-colors hover:bg-sky-500/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Bot className="h-4 w-4" />
          {running
            ? "Investigating..."
            : isFinalized
              ? "Investigation Unavailable (Review Finalized)"
              : result
                ? "Re-investigate with AI"
                : "Investigate with AI"}
        </button>

        {error && (
          <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !result && !running && (
          <p className="text-sm text-slate-500">No investigation has been run for this case yet.</p>
        )}

        {result && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={result.investigation.stop_reason === "COMPLETED" ? "success" : "warning"}>
                {STOP_REASON_LABEL[result.investigation.stop_reason] ?? result.investigation.stop_reason}
              </Badge>
              <span className="text-xs text-slate-500">
                {result.investigation.tool_calls.length} tool call
                {result.investigation.tool_calls.length === 1 ? "" : "s"}
              </span>
              {result.investigation.candidates_considered.length > 0 && (
                <span className="text-xs text-slate-500">
                  &middot; considered{" "}
                  {result.investigation.candidates_considered.join(", ")}
                </span>
              )}
            </div>

            {result.proposal ? (
              <div className="space-y-3 rounded-md border border-slate-800 bg-[#0b0f16] p-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wide text-sky-400">
                      AI Recommendation (Proposed Targets, Rationale, Confidence)
                    </span>
                    <p className="text-xs text-slate-400">
                      Non-authoritative proposal. AI cannot resolve cases or authorize money movement.
                    </p>
                  </div>
                  <span className="font-mono text-xs tabular-nums text-slate-400">
                    confidence {result.proposal.confidence.toFixed(2)}
                  </span>
                </div>

                <div>
                  <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Proposed target ledger entries
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {result.proposal.target_ledger_entry_ids.map((id) => (
                      <span
                        key={id}
                        className="rounded bg-slate-800/70 px-1.5 py-0.5 font-mono text-[11px] text-slate-300"
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Rationale
                  </div>
                  <p className="mt-1 text-sm text-slate-300">{result.proposal.rationale}</p>
                </div>

                {result.proposal.evidence.length > 0 && (
                  <div>
                    <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      Evidence (deterministically rebuilt, not model-asserted)
                    </div>
                    <ul className="mt-1 space-y-1">
                      {result.proposal.evidence.map((e, idx) => (
                        <li key={`${e.entity_id}-${e.field}-${idx}`} className="text-xs text-slate-400">
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
                    className="flex items-center gap-2 rounded-md border border-sky-500/40 bg-sky-500/10 px-4 py-2 text-sm font-medium text-sky-400 transition-colors hover:bg-sky-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Use AI Recommendation
                  </button>
                  {isFinalized && (
                    <p className="mt-1 text-xs text-slate-500">
                      Case review is already finalized ({detail.resolution.review_outcome}). Recommendation cannot be applied.
                    </p>
                  )}
                </div>

                {applyError && (
                  <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{applyError}</span>
                  </div>
                )}

                {applyNotice && (
                  <div className="flex items-start gap-2 rounded-md border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-sm text-sky-300">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-sky-400" />
                    <span>{applyNotice}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-md border border-slate-800 bg-[#0b0f16] p-4">
                <p className="text-sm text-slate-400">
                  AI abstained &mdash; no proposal was produced (
                  {STOP_REASON_LABEL[result.investigation.stop_reason]?.toLowerCase() ??
                    result.investigation.stop_reason}
                  ). Manual candidate inspection and selection is required.
                </p>
              </div>
            )}

            {result.preview_gate && (
              <div className="space-y-3">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Deterministic Safety Gate Validation (Independent Firewall)
                </div>
                <div
                  className={`flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium ${
                    result.preview_gate.passed
                      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                      : "border-amber-500/30 bg-amber-500/10 text-amber-400"
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
              <details className="rounded-md border border-slate-800">
                <summary className="cursor-pointer px-3 py-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                  Tool call trace
                </summary>
                <ol className="space-y-2 border-t border-slate-800 p-3">
                  {result.investigation.tool_calls.map((call, idx) => (
                    <li key={idx} className="text-xs text-slate-400">
                      <span className="font-mono text-slate-300">{call.tool_name}</span>{" "}
                      <span className="text-slate-600">({call.duration_ms}ms)</span>
                      <div className="mt-0.5 break-words text-slate-500">{call.response_summary}</div>
                    </li>
                  ))}
                </ol>
              </details>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
