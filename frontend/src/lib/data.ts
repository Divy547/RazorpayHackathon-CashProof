import raw from "@/data/demo-data.json";
import type { CaseDetail, CaseRow, DemoData } from "@/lib/types";

const demoData = raw as unknown as DemoData;

export function getMeta() {
  return demoData.meta;
}

export function getOverview() {
  return demoData.overview;
}

export function getCases(): CaseRow[] {
  return demoData.cases;
}

export function getCaseDetail(settlementId: string): CaseDetail | undefined {
  return demoData.case_detail[settlementId];
}

export function getScenarioExamples() {
  return demoData.scenario_examples;
}
