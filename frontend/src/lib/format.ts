import type { Disposition } from "@/lib/types";
import type { Tone } from "@/components/Badge";

export function formatMinor(minor: number, currency = "INR"): string {
  const value = minor / 100;
  const symbol = currency === "INR" ? "₹" : `${currency} `;
  const sign = value < 0 ? "-" : "";
  const magnitude = Math.abs(value).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${sign}${symbol}${magnitude}`;
}

export function formatSignedMinor(minor: number, currency = "INR"): string {
  if (minor === 0) return formatMinor(0, currency);
  const formatted = formatMinor(Math.abs(minor), currency);
  return minor > 0 ? `+${formatted}` : `-${formatted}`;
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "medium",
  });
}

export function dispositionTone(disposition: Disposition): Tone {
  switch (disposition) {
    case "AUTO_RESOLVED":
      return "success";
    case "HUMAN_REVIEW":
      return "warning";
    case "UNRESOLVED":
      return "danger";
  }
}

export function dispositionLabel(disposition: Disposition): string {
  switch (disposition) {
    case "AUTO_RESOLVED":
      return "Auto Resolved";
    case "HUMAN_REVIEW":
      return "Human Review";
    case "UNRESOLVED":
      return "Unresolved";
  }
}

export function exceptionLabel(exceptionType: string): string {
  return exceptionType
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function stanceTone(stance: "SUPPORTS" | "CONTRADICTS"): Tone {
  return stance === "SUPPORTS" ? "success" : "danger";
}

const SCENARIO_LABELS: Record<string, string> = {
  S1: "Structured Exact Match",
  S2: "Structured Ambiguous",
  S3: "Financial Mismatch",
  S4: "External Reference (Text)",
  S5: "Narration Alias (Text)",
  S6: "Non-Provable / Missing",
};

export function scenarioLabel(family: string): string {
  return SCENARIO_LABELS[family] ?? family;
}

const CATEGORY_LABELS: Record<string, string> = {
  REFERENCE_AMBIGUITY: "Reference Ambiguity",
  AMOUNT_INCONSISTENCY: "Amount Inconsistency",
  UNSTRUCTURED_REFERENCE: "Unstructured Reference",
  MISSING_RECORD: "Missing Record",
  EVIDENCE_CONFLICT: "Evidence Conflict",
  POLICY_REVIEW: "Policy Review",
  OTHER: "Other Exception",
};

export function operationalCategoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category.replace(/_/g, " ");
}

export function operationalCategoryTone(category: string): Tone {
  switch (category) {
    case "REFERENCE_AMBIGUITY":
      return "warning";
    case "AMOUNT_INCONSISTENCY":
      return "danger";
    case "UNSTRUCTURED_REFERENCE":
      return "info";
    case "MISSING_RECORD":
      return "neutral";
    case "EVIDENCE_CONFLICT":
      return "danger";
    case "POLICY_REVIEW":
      return "warning";
    default:
      return "neutral";
  }
}

