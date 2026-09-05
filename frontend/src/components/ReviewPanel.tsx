"use client";

import { useState } from "react";
import { AlertTriangle, Bot, CheckCircle2, XCircle } from "lucide-react";
import { ApiError, submitReview } from "@/lib/api";
import type { CaseDetail } from "@/lib/types";
import { Panel } from "@/components/Panel";
import { Badge } from "@/components/Badge";

export function ReviewPanel({
  detail,
  selectedTargetIds,
  onSelectedTargetIdsChange,
  appliedNotice,
  onClearNotice,
  onUpdated,
}: {
  detail: CaseDetail;
  selectedTargetIds: Set<string>;
  onSelectedTargetIdsChange: (ids: Set<string>) => void;
  appliedNotice?: string | null;
  onClearNotice?: () => void;
  onUpdated: (updated: CaseDetail) => void;
}) {
  const [reviewer, setReviewer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState<"approve" | "reject" | "pending" | null>(null);

  if (detail.disposition !== "HUMAN_REVIEW") {
    return null;
  }

  if (detail.resolution.review_outcome === "APPROVED") {
    return (
      <Panel
        id="review-panel"
        title="Human Review Finalized"
        subtitle="This case has been reviewed and approved. Review decisions are immutable."
      >
        <div className="flex items-start gap-3 rounded-xl border border-[#3B5145]/30 bg-[#3B5145]/10 p-5 text-[#3B5145]">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[#3B5145]" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#171816]">
                HUMAN_REVIEW APPROVED
              </span>
              <Badge tone="success">APPROVED</Badge>
            </div>
            <p className="text-xs text-[#4F514A]">
              Approved by{" "}
              <span className="font-mono font-semibold text-[#3B5145]">{detail.resolution.reviewer || "reviewer"}</span>
              {detail.resolution.reviewed_at
                ? ` at ${new Date(detail.resolution.reviewed_at).toLocaleString()}`
                : ""}
              .
            </p>
            <p className="font-mono text-xs text-[#4F514A]">
              Resolved target ledger entries:{" "}
              <span className="font-bold text-[#171816]">
                {detail.resolution.target_ledger_entry_ids.join(", ") || "None"}
              </span>
            </p>
          </div>
        </div>
      </Panel>
    );
  }

  if (detail.resolution.review_outcome === "REJECTED") {
    return (
      <Panel
        id="review-panel"
        title="Human Review Finalized"
        subtitle="This case has been reviewed and rejected. Review decisions are immutable."
      >
        <div className="flex items-start gap-3 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 p-5 text-[#9A514C]">
          <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-[#9A514C]" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#171816]">
                HUMAN_REVIEW REJECTED
              </span>
              <Badge tone="danger">REJECTED</Badge>
            </div>
            <p className="text-xs text-[#4F514A]">
              Rejected by{" "}
              <span className="font-mono font-semibold text-[#9A514C]">{detail.resolution.reviewer || "reviewer"}</span>
              {detail.resolution.reviewed_at
                ? ` at ${new Date(detail.resolution.reviewed_at).toLocaleString()}`
                : ""}
              .
            </p>
            <p className="text-xs text-[#4F514A]">
              This case was closed without resolving against candidate ledger entries.
            </p>
          </div>
        </div>
      </Panel>
    );
  }

  function toggle(id: string) {
    const next = new Set(selectedTargetIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    onSelectedTargetIdsChange(next);
  }

  async function act(decision: "approve" | "reject" | "pending") {
    if (!reviewer.trim()) {
      setError("Enter a reviewer name before submitting a decision.");
      return;
    }
    if (decision === "approve" && selectedTargetIds.size === 0) {
      setError("Select at least one candidate to approve.");
      return;
    }
    setSubmitting(true);
    setError(null);
    setLastAction(decision);
    try {
      const updated = await submitReview(
        detail.settlement_id,
        decision,
        Array.from(selectedTargetIds),
        reviewer.trim(),
      );
      onUpdated(updated);
      if (updated.gate.failing_check && decision === "approve") {
        setError(
          `Approval refused by the deterministic gate: ${updated.gate.failing_check} failed. ` +
            "The case remains HUMAN_REVIEW / PENDING.",
        );
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Request failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Panel
      id="review-panel"
      title="Reviewer Action Workspace"
      subtitle="Select only from candidates the deterministic matcher already found. The gate independently re-evaluates the selection — it is never bypassed."
    >
      <div className="space-y-4">
        {appliedNotice && (
          <div className="flex items-start justify-between gap-2 rounded-xl border border-[#3B5145]/30 bg-[#3B5145]/10 px-4 py-3 text-xs font-mono text-[#3B5145]">
            <div className="flex items-start gap-2">
              <Bot className="mt-0.5 h-4 w-4 shrink-0 text-[#3B5145]" />
              <span>{appliedNotice}</span>
            </div>
            {onClearNotice && (
              <button
                type="button"
                onClick={onClearNotice}
                className="font-mono text-xs font-semibold text-[#3B5145] underline hover:text-[#171816]"
              >
                Dismiss
              </button>
            )}
          </div>
        )}

        <div>
          <label className="mb-2 block font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
            Candidate selection
          </label>
          {detail.candidates.length === 0 ? (
            <p className="font-mono text-xs text-[#6B6D64]">No candidates available to select.</p>
          ) : (
            <div className="space-y-2">
              {detail.candidates.map((c) => (
                <label
                  key={c.ledger_entry_id}
                  className="flex cursor-pointer flex-wrap items-center justify-between gap-2 rounded-xl border border-[#CFC9BC] bg-[#EEEAE0] p-3 text-xs transition-colors hover:bg-[#E5DFD1]"
                >
                  <div className="flex min-w-0 items-center gap-2.5">
                    <input
                      type="checkbox"
                      checked={selectedTargetIds.has(c.ledger_entry_id)}
                      onChange={() => toggle(c.ledger_entry_id)}
                      className="h-4 w-4 shrink-0 accent-[#171816]"
                    />
                    <span className="font-mono font-bold text-[#171816] truncate">{c.ledger_entry_id}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone="info">{c.provenance.replaceAll("_", " ")}</Badge>
                    <span className="font-mono text-xs font-semibold tabular-nums text-[#4F514A]">
                      score {c.score.toFixed(2)}
                    </span>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="mb-1.5 block font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
            Reviewer Identity
          </label>
          <input
            type="text"
            value={reviewer}
            onChange={(e) => setReviewer(e.target.value)}
            placeholder="Sign reviewer name / badge ID"
            className="w-full max-w-sm rounded-lg border border-[#CFC9BC] bg-[#F8F6F0] px-3.5 py-2 font-mono text-xs font-medium text-[#171816] placeholder-[#6B6D64] transition-colors focus:border-[#171816] focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap gap-2.5 pt-1">
          <button
            type="button"
            disabled={submitting}
            onClick={() => act("approve")}
            className="rounded-lg border border-[#3B5145] bg-[#3B5145] px-4 py-2 font-mono text-xs font-bold text-[#F8F6F0] transition-colors hover:bg-[#2C3E34] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting && lastAction === "approve" ? "Submitting..." : "Approve Resolution"}
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => act("reject")}
            className="rounded-lg border border-[#9A514C] bg-transparent px-4 py-2 font-mono text-xs font-bold text-[#9A514C] transition-colors hover:bg-[#9A514C]/10 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting && lastAction === "reject" ? "Submitting..." : "Reject Resolution"}
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => act("pending")}
            className="rounded-lg border border-[#CFC9BC] bg-[#EEEAE0] px-4 py-2 font-mono text-xs font-semibold text-[#171816] transition-colors hover:bg-[#E5DFD1] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting && lastAction === "pending" ? "Submitting..." : "Leave Pending"}
          </button>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-3.5 py-2.5 text-xs font-mono text-[#9A514C]">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </Panel>
  );
}
