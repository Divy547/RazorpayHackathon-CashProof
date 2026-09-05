import type {
  BenchmarkConfidenceResponse,
  BenchmarkRunResponse,
  CaseCluster,
  CaseDetail,
  CaseRow,
  ControllerGateOutcome,
  ExceptionClusterDetail,
  ExceptionIntelligenceResponse,
  GateCheckBreakdown,
  GateIntelligenceResponse,
  IngestionRun,
  IngestionStatusResponse,
  InvestigationResult,
  OperationalConfidenceResponse,
  ReconcileResponse,
} from "@/lib/types";

const LOCAL_API_BASE_URL = "http://localhost:8000";
const PRODUCTION_API_BASE_URL = "https://razorpayhackathon-cashproof.onrender.com";

export function getApiBaseUrl(): string {
  // 1. Explicit environment variable takes precedence
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (envUrl) {
    return envUrl.replace(/\/+$/, "");
  }

  // 2. In browser runtime, check if accessing locally or on deployed host
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (
      hostname === "localhost" ||
      hostname === "127.0.0.1" ||
      hostname === "0.0.0.0" ||
      hostname.endsWith(".local")
    ) {
      return LOCAL_API_BASE_URL;
    }
    return PRODUCTION_API_BASE_URL;
  }

  // 3. In server / build-time environment, fall back based on NODE_ENV
  return process.env.NODE_ENV === "production" ? PRODUCTION_API_BASE_URL : LOCAL_API_BASE_URL;
}

const API_BASE_URL = getApiBaseUrl();

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail?: unknown }).detail;
      if (typeof detail === "string") return detail;
    }
  } catch {
    // fall through to generic message
  }
  return `Request failed with status ${response.status}`;
}

export async function fetchCases(): Promise<CaseRow[]> {
  const response = await fetch(`${API_BASE_URL}/api/cases`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as CaseRow[];
}

export async function fetchCaseDetail(settlementId: string): Promise<CaseDetail> {
  const response = await fetch(`${API_BASE_URL}/api/cases/${settlementId}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as CaseDetail;
}

export type ReviewDecision = "approve" | "reject" | "pending";

export async function submitReview(
  settlementId: string,
  decision: ReviewDecision,
  selectedTargetIds: string[],
  reviewer: string,
): Promise<CaseDetail> {
  const response = await fetch(`${API_BASE_URL}/api/cases/${settlementId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      decision,
      selected_target_ids: selectedTargetIds,
      reviewer,
    }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as CaseDetail;
}

export async function triggerInvestigation(settlementId: string): Promise<InvestigationResult> {
  const response = await fetch(`${API_BASE_URL}/api/cases/${settlementId}/investigate`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as InvestigationResult;
}

export async function fetchInvestigation(settlementId: string): Promise<InvestigationResult | null> {
  const response = await fetch(`${API_BASE_URL}/api/cases/${settlementId}/investigation`, {
    cache: "no-store",
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as InvestigationResult;
}

// Phase 4: Benchmark API client helpers
export async function runBenchmark(
  seed: number = 42,
  numSettlements: number = 100,
  arm: string = "deterministic",
): Promise<BenchmarkRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/benchmarks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      seed,
      num_settlements: numSettlements,
      arm,
    }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as BenchmarkRunResponse;
}

export async function fetchBenchmark(runId: string): Promise<BenchmarkRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/benchmarks/${encodeURIComponent(runId)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as BenchmarkRunResponse;
}

// Phase 6: Exception Intelligence fetch functions
export async function fetchExceptionClusters(params?: {
  category?: string;
  failing_gate?: string;
  disposition?: string;
}): Promise<ExceptionIntelligenceResponse> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.failing_gate) query.set("failing_gate", params.failing_gate);
  if (params?.disposition) query.set("disposition", params.disposition);

  const qs = query.toString();
  const url = `${API_BASE_URL}/api/exceptions/clusters${qs ? `?${qs}` : ""}`;
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as ExceptionIntelligenceResponse;
}

export async function fetchExceptionClusterDetail(
  clusterKey: string,
): Promise<ExceptionClusterDetail> {
  const response = await fetch(
    `${API_BASE_URL}/api/exceptions/clusters/${encodeURIComponent(clusterKey)}`,
    { cache: "no-store" },
  );
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as ExceptionClusterDetail;
}

export async function fetchCaseCluster(
  settlementId: string,
): Promise<CaseCluster | null> {
  const response = await fetch(
    `${API_BASE_URL}/api/cases/${encodeURIComponent(settlementId)}/cluster`,
    { cache: "no-store" },
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as CaseCluster;
}

// Phase 7: Gate Intelligence fetch functions
export async function fetchGateIntelligence(params?: {
  check?: string;
  disposition?: string;
}): Promise<GateIntelligenceResponse> {
  const query = new URLSearchParams();
  if (params?.check) query.set("check", params.check);
  if (params?.disposition) query.set("disposition", params.disposition);

  const qs = query.toString();
  const url = `${API_BASE_URL}/api/gate/intelligence${qs ? `?${qs}` : ""}`;
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as GateIntelligenceResponse;
}

export async function fetchGateCheckDetail(check: string): Promise<GateCheckBreakdown> {
  const response = await fetch(
    `${API_BASE_URL}/api/gate/intelligence/${encodeURIComponent(check)}`,
    { cache: "no-store" },
  );
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as GateCheckBreakdown;
}

export async function fetchCaseGateOutcome(
  settlementId: string,
): Promise<ControllerGateOutcome | null> {
  const response = await fetch(
    `${API_BASE_URL}/api/cases/${encodeURIComponent(settlementId)}/gate-outcome`,
    { cache: "no-store" },
  );
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as ControllerGateOutcome;
}

// Phase 8: Confidence Intelligence fetch functions
export async function fetchOperationalConfidence(): Promise<OperationalConfidenceResponse> {
  const response = await fetch(`${API_BASE_URL}/api/confidence`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as OperationalConfidenceResponse;
}

// Phase 9: Ingestion API client helpers
export async function fetchIngestionStatus(): Promise<IngestionStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/ingestion/status`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as IngestionStatusResponse;
}

export async function fetchIngestionRuns(): Promise<IngestionRun[]> {
  const response = await fetch(`${API_BASE_URL}/api/ingestion/runs`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as IngestionRun[];
}

export async function fetchIngestionRun(runId: string): Promise<IngestionRun> {
  const response = await fetch(`${API_BASE_URL}/api/ingestion/runs/${encodeURIComponent(runId)}`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as IngestionRun;
}

export async function triggerRazorpayIngestion(year: number, month: number): Promise<IngestionRun> {
  const response = await fetch(`${API_BASE_URL}/api/ingestion/razorpay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ year, month }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as IngestionRun;
}

export async function uploadBankStatement(file: File): Promise<IngestionRun> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/ingestion/bank-statement`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as IngestionRun;
}

export async function triggerReconcile(): Promise<ReconcileResponse> {
  const response = await fetch(`${API_BASE_URL}/api/reconcile`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as ReconcileResponse;
}

export async function fetchBenchmarkConfidence(
  runId?: string,
): Promise<BenchmarkConfidenceResponse> {
  const endpoint = runId
    ? `${API_BASE_URL}/api/benchmarks/${encodeURIComponent(runId)}/confidence`
    : `${API_BASE_URL}/api/benchmark/confidence`;
  const response = await fetch(endpoint, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }
  return (await response.json()) as BenchmarkConfidenceResponse;
}
