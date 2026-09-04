"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, RefreshCw, UploadCloud, XCircle } from "lucide-react";
import {
  ApiError,
  triggerRazorpayIngestion,
  triggerReconcile,
  uploadBankStatement,
} from "@/lib/api";
import { Badge } from "@/components/Badge";
import { Panel } from "@/components/Panel";
import type { CaseRow, IngestionRun, IngestionStatusResponse } from "@/lib/types";

function RunResultCard({ run }: { run: IngestionRun }) {
  const ok = run.status === "COMPLETED";
  return (
    <div
      className={`space-y-2 rounded-md border px-4 py-3 text-sm ${
        ok
          ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
          : "border-red-500/30 bg-red-500/10 text-red-300"
      }`}
    >
      <div className="flex items-center gap-2 font-medium">
        {ok ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
        {run.status} &middot; {run.run_id}
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-300">
        <span>Fetched: {run.fetched_count}</span>
        <span>Accepted: {run.accepted_count}</span>
        <span>Rejected: {run.rejected_count}</span>
        <span>Duplicate: {run.duplicate_count}</span>
      </div>
      {run.failure_reason && <p className="text-xs">{run.failure_reason}</p>}
      {run.validation_errors.length > 0 && (
        <ul className="list-inside list-disc space-y-0.5 text-xs">
          {run.validation_errors.map((err, idx) => (
            <li key={idx}>{err}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function IngestionClient({
  status,
  runs,
  onRefresh,
}: {
  status: IngestionStatusResponse;
  runs: IngestionRun[];
  onRefresh: () => void;
}) {
  const razorpay = status.connectors.find((c) => c.connector_name === "razorpay");
  const now = new Date();
  const [year, setYear] = useState(now.getUTCFullYear());
  const [month, setMonth] = useState(now.getUTCMonth() + 1);
  const [razorpayRun, setRazorpayRun] = useState<IngestionRun | null>(null);
  const [razorpayBusy, setRazorpayBusy] = useState(false);
  const [razorpayError, setRazorpayError] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [bankRun, setBankRun] = useState<IngestionRun | null>(null);
  const [bankBusy, setBankBusy] = useState(false);
  const [bankError, setBankError] = useState<string | null>(null);

  const [reconcileBusy, setReconcileBusy] = useState(false);
  const [reconcileError, setReconcileError] = useState<string | null>(null);
  const [reconcileResult, setReconcileResult] = useState<CaseRow[] | null>(null);

  async function runRazorpayIngestion() {
    setRazorpayBusy(true);
    setRazorpayError(null);
    try {
      const result = await triggerRazorpayIngestion(year, month);
      setRazorpayRun(result);
      onRefresh();
    } catch (err) {
      setRazorpayError(err instanceof ApiError ? err.message : "Razorpay ingestion failed.");
    } finally {
      setRazorpayBusy(false);
    }
  }

  async function runBankUpload() {
    if (!file) return;
    setBankBusy(true);
    setBankError(null);
    try {
      const result = await uploadBankStatement(file);
      setBankRun(result);
      onRefresh();
    } catch (err) {
      setBankError(err instanceof ApiError ? err.message : "Bank statement upload failed.");
    } finally {
      setBankBusy(false);
    }
  }

  async function runReconcile() {
    setReconcileBusy(true);
    setReconcileError(null);
    try {
      const cases = await triggerReconcile();
      setReconcileResult(cases);
    } catch (err) {
      setReconcileError(err instanceof ApiError ? err.message : "Reconciliation failed.");
    } finally {
      setReconcileBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <Panel
        title="Razorpay Connector (Test Mode, Read-Only)"
        subtitle="Reads GET /payments, /refunds, /settlements, and /settlements/recon/combined. Never writes to Razorpay."
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge tone={razorpay?.configured ? "success" : "warning"}>
              {razorpay?.configured ? "Configured" : "Unconfigured"}
            </Badge>
            <span className="text-xs text-slate-400">{razorpay?.detail}</span>
          </div>

          <div className="flex flex-wrap items-end gap-3">
            <label className="flex flex-col gap-1 text-xs text-slate-400">
              Year
              <input
                type="number"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                className="w-24 rounded border border-slate-700 bg-[#0b0f16] px-2 py-1 text-sm text-slate-200"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-slate-400">
              Month
              <input
                type="number"
                min={1}
                max={12}
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
                className="w-20 rounded border border-slate-700 bg-[#0b0f16] px-2 py-1 text-sm text-slate-200"
              />
            </label>
            <button
              type="button"
              disabled={razorpayBusy}
              onClick={() => void runRazorpayIngestion()}
              className="flex items-center gap-2 rounded-md border border-sky-500/40 bg-sky-500/10 px-4 py-2 text-sm font-medium text-sky-400 transition-colors hover:bg-sky-500/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${razorpayBusy ? "animate-spin" : ""}`} />
              {razorpayBusy ? "Ingesting..." : "Ingest from Razorpay"}
            </button>
          </div>

          {razorpayError && (
            <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{razorpayError}</span>
            </div>
          )}
          {razorpayRun && <RunResultCard run={razorpayRun} />}
        </div>
      </Panel>

      <Panel
        title="Bank Statement CSV"
        subtitle="Fail-closed: any malformed row (missing column, invalid amount/timestamp/currency/direction) rejects the entire file."
      >
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="text-sm text-slate-300 file:mr-3 file:rounded file:border file:border-slate-700 file:bg-[#0b0f16] file:px-3 file:py-1.5 file:text-xs file:text-slate-300"
            />
            <button
              type="button"
              disabled={!file || bankBusy}
              onClick={() => void runBankUpload()}
              className="flex items-center gap-2 rounded-md border border-sky-500/40 bg-sky-500/10 px-4 py-2 text-sm font-medium text-sky-400 transition-colors hover:bg-sky-500/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <UploadCloud className="h-4 w-4" />
              {bankBusy ? "Uploading..." : "Upload & Ingest"}
            </button>
          </div>

          {bankError && (
            <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{bankError}</span>
            </div>
          )}
          {bankRun && <RunResultCard run={bankRun} />}
        </div>
      </Panel>

      <Panel
        title="Reconcile Ingested Data"
        subtitle="Runs the EXISTING BatchReconciler over every currently stored source record. Cases a reviewer has already finalized (APPROVED/REJECTED) are left untouched."
      >
        <div className="space-y-3">
          <button
            type="button"
            disabled={reconcileBusy}
            onClick={() => void runReconcile()}
            className="flex items-center gap-2 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-400 transition-colors hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${reconcileBusy ? "animate-spin" : ""}`} />
            {reconcileBusy ? "Reconciling..." : "Reconcile Now"}
          </button>
          {reconcileError && (
            <div className="flex items-start gap-2 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{reconcileError}</span>
            </div>
          )}
          {reconcileResult && (
            <p className="text-sm text-slate-400">
              Reconciled {reconcileResult.length} case(s). See{" "}
              <Link href="/cases" className="text-sky-400 hover:underline">
                Case Explorer
              </Link>{" "}
              for updated dispositions.
            </p>
          )}
        </div>
      </Panel>

      <Panel title="Ingestion History" subtitle="Every ingestion run this API process has recorded.">
        {runs.length === 0 ? (
          <p className="text-sm text-slate-500">No ingestion runs yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-500">
                <tr className="border-b border-slate-800">
                  <th className="py-2 pr-4">Run</th>
                  <th className="py-2 pr-4">Source</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Fetched</th>
                  <th className="py-2 pr-4">Accepted</th>
                  <th className="py-2 pr-4">Rejected</th>
                  <th className="py-2 pr-4">Duplicate</th>
                  <th className="py-2 pr-4">Started</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.run_id} className="border-b border-slate-800/60">
                    <td className="py-2 pr-4 font-mono text-xs text-slate-400">{run.run_id}</td>
                    <td className="py-2 pr-4">{run.source}</td>
                    <td className="py-2 pr-4">
                      <Badge tone={run.status === "COMPLETED" ? "success" : "danger"}>
                        {run.status}
                      </Badge>
                    </td>
                    <td className="py-2 pr-4">{run.fetched_count}</td>
                    <td className="py-2 pr-4">{run.accepted_count}</td>
                    <td className="py-2 pr-4">{run.rejected_count}</td>
                    <td className="py-2 pr-4">{run.duplicate_count}</td>
                    <td className="py-2 pr-4 text-xs text-slate-500">
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
