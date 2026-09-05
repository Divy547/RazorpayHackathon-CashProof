"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, RefreshCw, Shield, UploadCloud, XCircle } from "lucide-react";
import {
  ApiError,
  triggerRazorpayIngestion,
  triggerReconcile,
  uploadBankStatement,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import type { IngestionRun, IngestionStatusResponse, ReconcileResponse } from "@/lib/types";

function RunResultCard({ run }: { run: IngestionRun }) {
  const ok = run.status === "COMPLETED";
  return (
    <div
      className={cn(
        "space-y-2.5 rounded-xl border p-4 text-sm transition-colors",
        ok
          ? "border-[#3B5145]/30 bg-[#3B5145]/10 text-[#171816]"
          : "border-[#9A514C]/30 bg-[#9A514C]/10 text-[#171816]",
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wider">
          {ok ? (
            <CheckCircle2 className="h-4 w-4 text-[#3B5145]" />
          ) : (
            <XCircle className="h-4 w-4 text-[#9A514C]" />
          )}
          <span className={ok ? "text-[#3B5145]" : "text-[#9A514C]"}>
            {run.status} &middot; {run.run_id}
          </span>
        </div>
        <span className="font-mono text-[11px] text-[#6B6D64]">
          {new Date(run.completed_at || run.started_at).toLocaleTimeString("en-IN")}
        </span>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 font-mono text-xs text-[#4F514A]">
        <span>
          Fetched: <strong className="font-semibold text-[#171816]">{run.fetched_count}</strong>
        </span>
        <span>
          Accepted: <strong className="font-semibold text-[#3B5145]">{run.accepted_count}</strong>
        </span>
        <span>
          Rejected: <strong className={cn("font-semibold", run.rejected_count > 0 ? "text-[#9A514C]" : "text-[#171816]")}>{run.rejected_count}</strong>
        </span>
        <span>
          Duplicate: <strong className="font-semibold text-[#171816]">{run.duplicate_count}</strong>
        </span>
      </div>

      {run.failure_reason && (
        <p className="font-mono text-xs font-medium text-[#9A514C]">
          Reason: {run.failure_reason}
        </p>
      )}

      {run.validation_errors.length > 0 && (
        <ul className="list-inside list-disc space-y-0.5 font-mono text-xs text-[#9A514C]">
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
  const [reconcileResult, setReconcileResult] = useState<ReconcileResponse | null>(null);

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
      const response = await triggerReconcile();
      setReconcileResult(response);
    } catch (err) {
      setReconcileError(err instanceof ApiError ? err.message : "Reconciliation failed.");
    } finally {
      setReconcileBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Safety Policy Bar */}
      <div className="rounded-xl border border-[#CFC9BC] bg-[#EEEAE0]/60 p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="flex items-start gap-2.5">
            <Shield className="mt-0.5 h-4 w-4 shrink-0 text-[#3B5145]" />
            <div>
              <span className="block font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
                FAIL-CLOSED INGESTION
              </span>
              <p className="mt-0.5 text-xs text-[#4F514A]">
                Malformed bank CSV rows reject the entire file. No silent corruption.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-2.5">
            <Shield className="mt-0.5 h-4 w-4 shrink-0 text-[#3B5145]" />
            <div>
              <span className="block font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
                READ-ONLY RAZORPAY
              </span>
              <p className="mt-0.5 text-xs text-[#4F514A]">
                GET-only endpoints. The system never writes or creates live charges.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-2.5">
            <Shield className="mt-0.5 h-4 w-4 shrink-0 text-[#3B5145]" />
            <div>
              <span className="block font-mono text-xs font-semibold uppercase tracking-wider text-[#171816]">
                DETERMINISTIC PIPELINE
              </span>
              <p className="mt-0.5 text-xs text-[#4F514A]">
                Previously finalized reviewer decisions are immutable and untouched.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Source 1: Razorpay Connector */}
      <section className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
              <span>SOURCE CONNECTOR // 01</span>
              <span className="text-[#CFC9BC]">&middot;</span>
              <span>TEST MODE</span>
              <span className="text-[#CFC9BC]">&middot;</span>
              <span>READ ONLY</span>
            </div>
            <h2 className="mt-1 text-lg font-bold tracking-tight text-[#171816]">
              Razorpay Connector
            </h2>
            <p className="mt-0.5 text-sm text-[#4F514A]">
              Reads <code className="font-mono text-xs font-semibold text-[#171816]">/payments</code>,{" "}
              <code className="font-mono text-xs font-semibold text-[#171816]">/refunds</code>,{" "}
              <code className="font-mono text-xs font-semibold text-[#171816]">/settlements</code>, and{" "}
              <code className="font-mono text-xs font-semibold text-[#171816]">/settlements/recon/combined</code>. Never writes to Razorpay.
            </p>
          </div>

          <span
            className={cn(
              "inline-flex shrink-0 items-center gap-1.5 rounded-md border px-2.5 py-1 font-mono text-xs font-semibold uppercase tracking-wide",
              razorpay?.configured
                ? "border-[#3B5145]/30 bg-[#3B5145]/10 text-[#3B5145]"
                : "border-[#8C6843]/30 bg-[#8C6843]/10 text-[#8C6843]",
            )}
          >
            <span
              className={cn(
                "h-1.5 w-1.5 rounded-full",
                razorpay?.configured ? "bg-[#3B5145]" : "bg-[#8C6843]",
              )}
            />
            {razorpay?.configured ? "Configured" : "Unconfigured"}
          </span>
        </div>

        <div className="mt-4 space-y-4">
          <p className="font-mono text-xs text-[#6B6D64]">
            {razorpay?.detail || "Razorpay test-mode API integration."}
          </p>

          <div className="flex flex-wrap items-end gap-3 pt-1">
            <label className="flex flex-col gap-1.5 font-mono text-xs font-semibold uppercase tracking-wider text-[#4F514A]">
              <span>Year</span>
              <input
                type="number"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                className="w-28 rounded-lg border border-[#CFC9BC] bg-[#F8F6F0] px-3 py-2 font-mono text-sm font-medium text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
              />
            </label>

            <label className="flex flex-col gap-1.5 font-mono text-xs font-semibold uppercase tracking-wider text-[#4F514A]">
              <span>Month</span>
              <input
                type="number"
                min={1}
                max={12}
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
                className="w-24 rounded-lg border border-[#CFC9BC] bg-[#F8F6F0] px-3 py-2 font-mono text-sm font-medium text-[#171816] transition-colors focus:border-[#171816] focus:outline-none"
              />
            </label>

            <button
              type="button"
              disabled={razorpayBusy}
              onClick={() => void runRazorpayIngestion()}
              className="inline-flex items-center gap-2 rounded-[10px] border border-[#171816] bg-[#171816] px-4 py-2.5 font-mono text-xs font-semibold uppercase tracking-wider text-[#F8F6F0] shadow-sm transition-colors hover:bg-[#30322D] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", razorpayBusy && "animate-spin")} />
              <span>{razorpayBusy ? "Ingesting..." : "Ingest from Razorpay →"}</span>
            </button>
          </div>

          {razorpayError && (
            <div className="flex items-start gap-3 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-4 py-3 text-sm text-[#9A514C]">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#9A514C]" />
              <span className="font-mono text-xs font-medium">{razorpayError}</span>
            </div>
          )}

          {razorpayRun && <RunResultCard run={razorpayRun} />}
        </div>
      </section>

      {/* Source 2: Bank Statement CSV */}
      <section className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
              <span>SOURCE CONNECTOR // 02</span>
              <span className="text-[#CFC9BC]">&middot;</span>
              <span>CSV IMPORT</span>
              <span className="text-[#CFC9BC]">&middot;</span>
              <span>FAIL-CLOSED</span>
            </div>
            <h2 className="mt-1 text-lg font-bold tracking-tight text-[#171816]">
              Bank Statement CSV
            </h2>
            <p className="mt-0.5 text-sm text-[#4F514A]">
              Fail-closed: any malformed row (missing column, invalid amount/timestamp/currency/direction) rejects the entire file.
            </p>
          </div>

          <span className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-[#3B5145]/30 bg-[#3B5145]/10 px-2.5 py-1 font-mono text-xs font-semibold uppercase tracking-wide text-[#3B5145]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#3B5145]" />
            Strict Schema
          </span>
        </div>

        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <label className="relative inline-flex cursor-pointer items-center gap-2 rounded-[10px] border border-[#CFC9BC] bg-[#EEEAE0] px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-[#171816] transition-colors hover:bg-[#E5DFD1]">
              <span>SELECT BANK STATEMENT</span>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="sr-only"
              />
            </label>

            <span className="font-mono text-xs text-[#4F514A]">
              {file ? (
                <span className="font-semibold text-[#171816]">{file.name}</span>
              ) : (
                <span className="text-[#6B6D64]">No file selected</span>
              )}
            </span>

            <button
              type="button"
              disabled={!file || bankBusy}
              onClick={() => void runBankUpload()}
              className="inline-flex items-center gap-2 rounded-[10px] border border-[#171816] bg-[#171816] px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-[#F8F6F0] shadow-sm transition-colors hover:bg-[#30322D] disabled:cursor-not-allowed disabled:opacity-40"
            >
              <UploadCloud className="h-3.5 w-3.5" />
              <span>{bankBusy ? "Uploading..." : "Upload & Ingest →"}</span>
            </button>
          </div>

          {bankError && (
            <div className="flex items-start gap-3 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-4 py-3 text-sm text-[#9A514C]">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#9A514C]" />
              <span className="font-mono text-xs font-medium">{bankError}</span>
            </div>
          )}

          {bankRun && <RunResultCard run={bankRun} />}
        </div>
      </section>

      {/* Reconciliation Action */}
      <section className="rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] p-6 shadow-sm">
        <div>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] font-semibold uppercase tracking-wider text-[#6B6D64]">
            <span>DETERMINISTIC CONTROLLER</span>
            <span className="text-[#CFC9BC]">&middot;</span>
            <span>PIPELINE DISPATCH</span>
          </div>
          <h2 className="mt-1 text-lg font-bold tracking-tight text-[#171816]">
            Reconcile Ingested Data
          </h2>
          <p className="mt-0.5 text-sm text-[#4F514A]">
            Runs the existing <code className="font-mono text-xs font-semibold text-[#171816]">BatchReconciler</code> over every currently stored source record. Cases a reviewer has already finalized (APPROVED/REJECTED) are left untouched.
          </p>
        </div>

        <div className="mt-5 space-y-4">
          <button
            type="button"
            disabled={reconcileBusy}
            onClick={() => void runReconcile()}
            className="inline-flex items-center gap-2 rounded-[10px] border border-[#171816] bg-[#171816] px-5 py-2.5 font-mono text-xs font-semibold uppercase tracking-wider text-[#F8F6F0] shadow-sm transition-colors hover:bg-[#30322D] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", reconcileBusy && "animate-spin")} />
            <span>{reconcileBusy ? "Reconciling Pipeline..." : "Reconcile Now →"}</span>
          </button>

          {reconcileError && (
            <div className="flex items-start gap-3 rounded-xl border border-[#9A514C]/30 bg-[#9A514C]/10 px-4 py-3 text-sm text-[#9A514C]">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#9A514C]" />
              <span className="font-mono text-xs font-medium">{reconcileError}</span>
            </div>
          )}

          {reconcileResult && (
            <div className="space-y-3 rounded-xl border border-[#3B5145]/30 bg-[#3B5145]/10 p-4">
              <p className="font-mono text-xs text-[#4F514A]">
                Reconciled <strong className="font-semibold text-[#171816]">{reconcileResult.cases.length}</strong> case(s). See{" "}
                <Link
                  href="/cases"
                  className="font-semibold text-[#3B5145] underline decoration-[#CFC9BC] underline-offset-2 transition-colors hover:decoration-[#3B5145]"
                >
                  Case Explorer
                </Link>{" "}
                for updated dispositions.
              </p>

              {reconcileResult.failed_settlements.length > 0 && (
                <div className="space-y-2 rounded-lg border border-[#8C6843]/30 bg-[#8C6843]/10 p-3 text-sm text-[#171816]">
                  <div className="flex items-center gap-2 font-mono text-xs font-semibold text-[#8C6843]">
                    <AlertTriangle className="h-4 w-4 shrink-0 text-[#8C6843]" />
                    <span>
                      {reconcileResult.failed_settlements.length} settlement(s) could not be reconciled
                    </span>
                  </div>
                  <ul className="list-inside list-disc space-y-1 font-mono text-xs text-[#4F514A]">
                    {reconcileResult.failed_settlements.map((f) => (
                      <li key={f.settlement_id}>
                        <span className="font-semibold text-[#171816]">{f.settlement_id}</span> ({f.error_type}):{" "}
                        {f.message}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Section 4: Ingestion History Table */}
      <section className="overflow-hidden rounded-2xl border border-[#CFC9BC] bg-[#F8F6F0] shadow-sm">
        <div className="flex flex-col gap-2 border-b border-[#CFC9BC] bg-[#EEEAE0]/50 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-bold tracking-tight text-[#171816]">
              Ingestion History
            </h2>
            <p className="text-xs text-[#4F514A]">
              Every ingestion run this API process has recorded.
            </p>
          </div>
          <span className="font-mono text-xs text-[#6B6D64]">
            {runs.length} RUNS RECORDED
          </span>
        </div>

        {runs.length === 0 ? (
          <div className="p-8 text-center font-mono text-xs uppercase tracking-wider text-[#6B6D64]">
            No ingestion runs recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-[#CFC9BC] bg-[#EEEAE0] font-mono text-[11px] font-semibold uppercase tracking-wider text-[#3F413B]">
                  <th scope="col" className="px-5 py-3.5 text-left text-[#3F413B]">
                    Run ID
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-left text-[#3F413B]">
                    Source
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-left text-[#3F413B]">
                    Status
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                    Fetched
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                    Accepted
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                    Rejected
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-right text-[#3F413B]">
                    Duplicate
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-left text-[#3F413B]">
                    Started
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9D5CA]">
                {runs.map((run) => (
                  <tr
                    key={run.run_id}
                    className="transition-colors duration-100 hover:bg-[#F2ECE1]"
                  >
                    <td className="px-5 py-3.5 font-mono text-xs font-semibold text-[#171816]">
                      {run.run_id}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs font-medium uppercase text-[#4F514A]">
                      {run.source}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border px-2.5 py-0.5 font-mono text-xs font-semibold tracking-tight",
                          run.status === "COMPLETED"
                            ? "border-[#3B5145]/30 bg-[#3B5145]/10 text-[#3B5145]"
                            : "border-[#9A514C]/30 bg-[#9A514C]/10 text-[#9A514C]",
                        )}
                      >
                        <span
                          className={cn(
                            "h-1.5 w-1.5 rounded-full",
                            run.status === "COMPLETED" ? "bg-[#3B5145]" : "bg-[#9A514C]",
                          )}
                        />
                        {run.status}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-xs font-medium tabular-nums text-[#4B4D46]">
                      {run.fetched_count}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-xs font-medium tabular-nums text-[#3B5145]">
                      {run.accepted_count}
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-xs font-semibold tabular-nums text-[#4B4D46]">
                      <span className={run.rejected_count > 0 ? "text-[#9A514C]" : "text-[#4B4D46]"}>
                        {run.rejected_count}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-right font-mono text-xs font-medium tabular-nums text-[#4B4D46]">
                      {run.duplicate_count}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs text-[#6B6D64]">
                      {new Date(run.started_at).toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
