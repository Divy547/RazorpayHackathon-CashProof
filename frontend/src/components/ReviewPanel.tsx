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
        <div className="flex items-start gap-3 rounded-md border border-emerald-500/30 bg-emerald-500/10 p-4 text-emerald-300">
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">HUMAN_REVIEW APPROVED</span>
              <Badge tone="success">APPROVED</Badge>
            </div>
            <p className="text-sm text-slate-300">
              Approved by{" "}
              <span className="font-mono text-emerald-300">{detail.resolution.reviewer || "reviewer"}</span>
              {detail.resolution.reviewed_at
                ? ` at ${new Date(detail.resolution.reviewed_at).toLocaleString()}`
                : ""}
              .
            </p>
            <p className="text-xs text-slate-400">
              Resolved target ledger entries:{" "}
              <span className="font-mono text-slate-200">
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
        <div className="flex items-start gap-3 rounded-md border border-red-500/30 bg-red-500/10 p-4 text-red-300">
          <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">HUMAN_REVIEW REJECTED</span>
              <Badge tone="danger">REJECTED</Badge>
            </div>
            <p className="text-sm text-slate-300">
              Rejected by{" "}
              <span className="font-mono text-red-300">{detail.resolution.reviewer || "reviewer"}</span>
              {detail.resolution.reviewed_at
                ? ` at ${new Date(detail.resolution.reviewed_at).toLocaleString()}`
                : ""}
              .
            </p>
            <p className="text-xs text-slate-400">
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
      title="Reviewer Action"
      subtitle="Select only from candidates the deterministic matcher already found. The gate independently re-evaluates the selection - it is never bypassed."
    >
      <div className="space-y-4">
        {appliedNotice && (
          <div className="flex items-start justify-between gap-2 rounded-md border border-sky-500/30 bg-sky-500/10 px-3 py-2 text-sm text-sky-300">
            <div className="flex items-start gap-2">
              <Bot className="mt-0.5 h-4 w-4 shrink-0 text-sky-400" />
              <span>{appliedNotice}</span>
            </div>
            {onClearNotice && (
              <button
                type="button"
                onClick={onClearNotice}
                className="text-xs text-sky-400/80 hover:text-sky-300"
              >
                Dismiss
              </button>
            )}
          </div>
        )}

        <div>
          <label className="mb-2 block text-xs font-medium uppercase tracking-wide text-slate-500">
            Candidate selection
          </label>
          {detail.candidates.length === 0 ? (
            <p className="text-sm text-slate-500">No candidates available to select.</p>
          ) : (
            <div className="space-y-2">
              {detail.candidates.map((c) => (
                <label
                  key={c.ledger_entry_id}
                  className="flex cursor-pointer items-center gap-3 rounded-md border border-slate-800 bg-[#0b0f16] px-3 py-2 text-sm hover:border-slate-700"
                >
                  <input
                    type="checkbox"
                    checked={selectedTargetIds.has(c.ledger_entry_id)}
                    onChange={() => toggle(c.ledger_entry_id)}
                    className="h-4 w-4 accent-emerald-500"
                  />
                  <span className="font-mono text-xs text-slate-300">{c.ledger_entry_id}</span>
                  <Badge tone="info">{c.provenance.replaceAll("_", " ")}</Badge>
                  <span className="ml-auto font-mono text-xs tabular-nums text-slate-500">
                    score {c.score.toFixed(2)}
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">
            Reviewer
          </label>
          <input
            type="text"
            value={reviewer}
            onChange={(e) => setReviewer(e.target.value)}
            placeholder="your name"
            className="w-full max-w-xs rounded-md border border-slate-700 bg-[#0b0f16] px-3 py-1.5 text-sm text-slate-200 placeholder:text-slate-600 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={submitting}
            onClick={() => act("approve")}
            className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-400 transition-colors hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting && lastAction === "approve" ? "Submitting..." : "Approve Resolution"}
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => act("reject")}
            className="rounded-md border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting && lastAction === "reject" ? "Submitting..." : "Reject"}
          </button>
          <button
            type="button"
            disabled={submitting}
            onClick={() => act("pending")}
            className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting && lastAction === "pending" ? "Submitting..." : "Leave Pending"}
          </button>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-300">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    </Panel>
  );
}
