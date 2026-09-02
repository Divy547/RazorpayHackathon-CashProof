# Benchmark

## Goal

Measure safe reconciliation performance.

Primary KPI:
correctly resolved records per minute subject to zero false auto-resolution.

The benchmark must support at least 50 synthetic records and should scale beyond that.

## Scenario taxonomy

| Label | Family | Covered exception types |
|---|---|---|
| S1 | Structured Exact | clean/reference match |
| S2 | Structured Ambiguous | ambiguous match, duplicate |
| S3 | Financial Mismatch | amount mismatch, fee mismatch, tax mismatch |
| S4 | External-Reference Text | timing gap or linkage requiring external-reference/text interpretation |
| S5 | Narration/Alias Text | customer-name aliasing, narration-based linkage |
| S6 | Non-Provable / Conflict | missing record, conflicting evidence, malformed data, tool failure, insufficient evidence |

S4 and S5 are always human-review families in the MVP, even if the financial bridge balances.

## Dataset

Synthetic source data includes payments, refunds, settlements, settlement items and ledger entries.

GroundTruth stores:
- provability
- exact target set
- justifying evidence
- scenario label
- not-provable reason

GroundTruth is evaluator-only.

Generator output must not leak scenario labels through artificial ID ranges, timestamp ordering, formatting, narration templates, or other correlated artifacts.

## Arms

CLI supports benchmark arms, including:
- deterministic baseline
- deterministic + AI investigation
- additional arms as implementation matures

UI initially exposes only the primary A/B comparison.

## Reproducibility

Persist:
- seed
- dataset version
- rule version
- deterministic code revision
- model version
- prompt version
- policy version
- arm
- max_tool_calls
- max_tokens
- timeout
- decoding parameters relevant to the model run

Same seed and versions reproduce the deterministic dataset and decision path.

Do not claim exact LLM output reproducibility.

## Metrics

At minimum:
- auto-resolution precision
- auto-resolution recall
- human-review rate
- unresolved rate
- false auto-resolution count
- correct resolution count
- elapsed time
- cases processed
- investigation cost
- evidence completeness

Unsafe auto-resolution must be visible rather than hidden in aggregate match rate.

## Isolation

Production inference never receives GroundTruth.

Benchmark evaluation happens outside the production decision path.

Benchmark and production call the same application use cases. There is no benchmark-only reconciliation implementation.
