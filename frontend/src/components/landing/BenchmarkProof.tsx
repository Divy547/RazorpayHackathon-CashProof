import Link from "next/link";
import { ArrowRight, CheckCircle2, Gauge, ShieldCheck, Zap } from "lucide-react";

export function BenchmarkProof() {
  const metrics = [
    {
      label: "Total Settlements",
      value: "100",
      hint: "Controlled benchmark batch",
      badge: "Seed 42",
      tone: "ink",
    },
    {
      label: "Target Set Accuracy",
      value: "100%",
      hint: "Zero incorrect records committed",
      badge: "Audited",
      tone: "verified",
    },
    {
      label: "Human Review Routing",
      value: "51",
      hint: "51% routed with complete evidence",
      badge: "No Silent Drops",
      tone: "review",
    },
    {
      label: "Fails-Closed Unresolved",
      value: "10",
      hint: "10% missing or non-provable",
      badge: "Strict Safety",
      tone: "failure",
    },
  ];

  return (
    <section id="benchmark" className="py-20 bg-[#FFFFFF] border-b border-[#DDE2E7]">
      <div className="mx-auto max-w-7xl px-6 sm:px-8">
        {/* Section Header */}
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 rounded border border-[#DDE2E7] bg-[#F4F6F8] px-2.5 py-1 text-[11px] font-mono text-[#475467]">
              <span>BENCHMARK REPORT // EVALUATOR RUN</span>
            </div>
            <h2 className="text-3xl font-semibold tracking-tight text-[#101828] sm:text-4xl">
              Proven Against Hidden Ground Truth
            </h2>
            <p className="text-base sm:text-lg text-[#475467] leading-relaxed">
              Every CashProof release is audited by an isolated evaluator with access to hidden
              synthetic ground truth. We benchmark across 100 settlements and 18,838 candidate ledger
              entries under seed 42.
            </p>
          </div>

          <div className="shrink-0">
            <Link
              href="/benchmark"
              className="inline-flex items-center gap-2 rounded-lg border border-[#DDE2E7] bg-[#FFFFFF] px-4 py-2.5 text-xs font-semibold text-[#101828] shadow-2xs transition-all hover:bg-[#F4F6F8] hover:border-[#475467]/30"
            >
              <Gauge className="h-4 w-4 text-[#3157D5]" />
              <span>Open Live Benchmark Runner</span>
              <ArrowRight className="h-3.5 w-3.5 text-[#475467]" />
            </Link>
          </div>
        </div>

        {/* Metadata Audit Strip */}
        <div className="mt-8 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-[#DDE2E7] bg-[#F4F6F8] px-5 py-3 font-mono text-xs text-[#475467]">
          <div className="flex flex-wrap items-center gap-6">
            <span>
              <strong className="text-[#101828]">SUITE:</strong> SEED-42
            </span>
            <span>
              <strong className="text-[#101828]">CANDIDATE POOL:</strong> 18,838 ENTRIES
            </span>
            <span>
              <strong className="text-[#101828]">SETTLEMENTS:</strong> 100
            </span>
          </div>
          <div className="flex items-center gap-2 text-[#12A67A]">
            <ShieldCheck className="h-4 w-4" />
            <span className="font-semibold text-[11px] uppercase tracking-wider">
              EVALUATOR ISOLATION: FAIL-CLOSED
            </span>
          </div>
        </div>

        {/* Hero Focal Metric Block */}
        <div className="mt-6 rounded-2xl border-2 border-[#12A67A]/30 bg-[#12A67A]/5 p-6 sm:p-8 shadow-2xs">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
            <div className="md:col-span-8 space-y-3">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-[#12A67A]/15 border border-[#12A67A]/30 px-3 py-1 text-xs font-semibold text-[#12A67A]">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>SAFETY INVARIANT VERIFIED</span>
              </div>
              <h3 className="text-2xl sm:text-3xl font-semibold text-[#101828] tracking-tight">
                0 False Auto-Resolutions &middot; 100% Target Accuracy
              </h3>
              <p className="text-sm text-[#475467] leading-relaxed max-w-2xl">
                In automated reconciliation, a single false positive costs 100x more than human
                review. CashProof&apos;s deterministic gate guarantees that zero incorrect target
                record sets were auto-resolved across all 100 benchmark test cases.
              </p>
            </div>

            <div className="md:col-span-4 flex flex-col items-center justify-center rounded-xl bg-[#FFFFFF] p-6 border border-[#DDE2E7] shadow-2xs text-center space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-mono font-semibold text-[#475467] uppercase tracking-wider">
                <Zap className="h-3.5 w-3.5 text-[#3157D5]" />
                Throughput
              </div>
              <div className="font-mono text-3xl sm:text-4xl font-bold text-[#101828] tabular-nums">
                1,380+
              </div>
              <span className="text-xs text-[#12A67A] font-medium">
                records / min on single core
              </span>
              <span className="text-[10px] text-[#475467] font-mono pt-1">
                Avg Gate Latency: 3.8ms
              </span>
            </div>
          </div>
        </div>

        {/* Visual Distribution Bar */}
        <div className="mt-8 rounded-xl border border-[#DDE2E7] bg-[#FFFFFF] p-6 shadow-2xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[#475467]">
              100-Settlement Benchmark Disposition Breakdown
            </span>
            <span className="text-xs font-mono text-[#475467]">
              Ground Truth Evaluated &middot; Seed 42
            </span>
          </div>

          {/* Stacked Progress Strip */}
          <div className="h-4 w-full rounded-full bg-[#F4F6F8] overflow-hidden flex shadow-inner">
            <div
              style={{ width: "39%" }}
              className="bg-[#12A67A] h-full transition-all"
              title="39% Auto-Resolved"
            />
            <div
              style={{ width: "51%" }}
              className="bg-[#D98B20] h-full transition-all"
              title="51% Human Review"
            />
            <div
              style={{ width: "10%" }}
              className="bg-[#D64545] h-full transition-all"
              title="10% Unresolved"
            />
          </div>

          {/* Distribution Legend */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="flex items-start gap-3">
              <div className="h-3 w-3 rounded-full bg-[#12A67A] mt-1 shrink-0" />
              <div>
                <div className="flex items-center gap-1.5 font-mono text-sm font-bold text-[#101828]">
                  <span>39%</span>
                  <span className="text-xs font-normal text-[#475467]">(39 cases)</span>
                </div>
                <div className="text-xs font-semibold text-[#101828]">AUTO RESOLVED</div>
                <div className="text-[11px] text-[#475467] leading-relaxed">
                  Clean 1:1 structured gateway references matching exactly.
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="h-3 w-3 rounded-full bg-[#D98B20] mt-1 shrink-0" />
              <div>
                <div className="flex items-center gap-1.5 font-mono text-sm font-bold text-[#101828]">
                  <span>51%</span>
                  <span className="text-xs font-normal text-[#475467]">(51 cases)</span>
                </div>
                <div className="text-xs font-semibold text-[#101828]">HUMAN REVIEW</div>
                <div className="text-[11px] text-[#475467] leading-relaxed">
                  Ambiguity, variance, or text matches routed with complete evidence receipts.
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="h-3 w-3 rounded-full bg-[#D64545] mt-1 shrink-0" />
              <div>
                <div className="flex items-center gap-1.5 font-mono text-sm font-bold text-[#101828]">
                  <span>10%</span>
                  <span className="text-xs font-normal text-[#475467]">(10 cases)</span>
                </div>
                <div className="text-xs font-semibold text-[#101828]">UNRESOLVED</div>
                <div className="text-[11px] text-[#475467] leading-relaxed">
                  Missing or corrupted bank records. Fails closed to avoid phantom ledger balances.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 4-Stat Metric Cards */}
        <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((m) => {
            const toneBorder =
              m.tone === "verified"
                ? "border-[#12A67A]/30"
                : m.tone === "review"
                ? "border-[#D98B20]/30"
                : m.tone === "failure"
                ? "border-[#D64545]/30"
                : "border-[#DDE2E7]";

            const toneText =
              m.tone === "verified"
                ? "text-[#12A67A]"
                : m.tone === "review"
                ? "text-[#D98B20]"
                : m.tone === "failure"
                ? "text-[#D64545]"
                : "text-[#101828]";

            return (
              <div
                key={m.label}
                className={`rounded-xl border ${toneBorder} bg-[#F4F6F8]/60 p-5 shadow-2xs space-y-1.5`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono uppercase tracking-wider text-[#475467]">
                    {m.label}
                  </span>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#FFFFFF] border border-[#DDE2E7] text-[#475467]">
                    {m.badge}
                  </span>
                </div>
                <div className={`font-mono text-3xl sm:text-4xl font-bold tabular-nums ${toneText}`}>
                  {m.value}
                </div>
                <div className="text-xs text-[#475467] pt-0.5">{m.hint}</div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 text-center text-xs text-[#475467]">
          Evaluated against ground truth dataset seed 42 under ruleset v1.0.0. No synthetic scenario
          labels are exposed to the reconciliation runtime.
        </div>
      </div>
    </section>
  );
}
