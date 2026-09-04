# CashProof — Phase 2 Implementation Plan
## Synthetic Dataset Generator

**Status:** Final corrected plan — ready for adversarial review before implementation  
**Phase:** 2  
**Scope:** Synthetic dataset generation only

---

## 1. Objective

Phase 2 builds the synthetic financial world that CashProof will later reconcile.

The generator must create realistic, internally consistent source records:

- `Payment`
- `Refund`
- `Settlement`
- `SettlementItem`
- `LedgerEntry`

It must also create benchmark-only evaluator artifacts:

- `GroundTruth`
- `ScenarioFamily`
- `Resolvability`

The generator must **not** perform production reconciliation. `ReconciliationCase`, `MatchCandidate`, `Evidence`, `Investigation`, `ResolutionProposal`, `GateEvaluation`, and `Resolution` are derived processing artifacts and belong to later phases.

### Core principle

> Generate a realistic financial world first. Then create controlled benchmark scenarios without leaking their labels or truth into production source records.

---

## 2. Phase 2 Boundary

### Included

- Synthetic source-world generation
- S1–S6 benchmark scenario construction
- Background ledger activity/distractors
- GroundTruth generation
- Deterministic seed/configuration
- Dataset validation
- Leakage tests
- Reproducibility tests
- Property-based generator tests
- Benchmark package APIs needed to produce an in-memory dataset

### Explicitly excluded

- Database/persistence
- FastAPI
- Frontend
- LLM/Anthropic integration
- AI investigator
- Production reconciliation runner
- `ReconciliationCase` creation
- `MatchCandidate` generation
- Evidence generation
- Gate evaluation
- Resolution
- Redis/Celery
- External Razorpay APIs

---

## 3. Architecture

```text
GeneratorConfig
      |
      v
DeterministicRNG
      |
      v
Clean Baseline World
      |
      +--> Payments
      +--> Refunds
      +--> Settlements
      +--> SettlementItems
      +--> LedgerEntries
      |
      v
Scenario Transformation
      |
      +--> S1
      +--> S2
      +--> S3
      +--> S4
      +--> S5
      +--> S6
      |
      v
Background Ledger Noise
      |
      v
Validation
      |
      +--------------------+
      |                    |
      v                    v
Production Source      Evaluator Artifact
Records                GroundTruth
```

The production source side contains no benchmark metadata.

GroundTruth remains benchmark/evaluator-only.

---

## 4. Existing Phase 1 Domain Rules

The generator must use the existing Phase 1 domain types and pure functions rather than duplicating financial logic.

### Monetary representation

All money is:

- integer minor units
- INR for the MVP
- non-negative magnitude where required by the domain
- explicit currency
- no floating-point monetary arithmetic

### Settlement item bridge

```text
net =
    gross
    - fee
    - tax_on_fee
    - netted_refund
    + adjustment
```

### GST

GST applies to the gateway fee.

The generator must use the existing Phase 1 `calculate_gst_on_fee()` implementation.

It must not independently implement a competing rounding rule.

### Settlement aggregation

```text
Settlement.net_deposited_minor
=
sum(SettlementItem.computed_net_minor)
```

Every generated clean settlement must satisfy this invariant.

### Refund netting

Only refunds marked as netted into settlement contribute to settlement refund amounts.

A refund must not be consumed/claimed by multiple settlement items.

### Ledger

`LedgerEntry.amount_minor` represents an unsigned magnitude.

`Direction.CREDIT` and `Direction.DEBIT` determine aggregation sign.

---

## 5. Generator Configuration

Create an immutable strongly typed configuration.

```python
@dataclass(frozen=True, slots=True)
class ScenarioDistribution:
    s1_structured_exact: float = 0.40
    s2_structured_ambiguous: float = 0.15
    s3_financial_mismatch: float = 0.15
    s4_external_ref_text: float = 0.10
    s5_narration_alias_text: float = 0.10
    s6_non_provable_conflict: float = 0.10
```

Weights must be validated to sum to 1.

```python
@dataclass(frozen=True, slots=True)
class GeneratorConfig:
    seed: int
    dataset_version: str = "v1.0.0"

    # Number of benchmark reconciliation scenarios.
    num_cases: int = 100

    min_items_per_settlement: int = 1
    max_items_per_settlement: int = 6

    refund_probability: float = 0.20
    noise_ledger_entries_ratio: float = 0.30

    currency: Currency = Currency.INR

    scenario_distribution: ScenarioDistribution = field(default_factory=ScenarioDistribution)
```

`num_cases` means benchmark reconciliation scenarios, not total entities. The default must therefore guarantee at least 50 benchmark scenarios.

---

## 6. Reproducibility

Use an isolated deterministic PRNG:

```python
random.Random(seed)
```

wrapped by a small `DeterministicRNG` abstraction.

Never modify Python's global random state.

The reproducibility contract is:

```text
same seed
+ same configuration
+ same generator version
=
same logical dataset
```

Tests should compare canonical serialized representations or structural equality.

Do not make an unconditional claim that output is bit-for-bit identical across every operating system unless serialization is explicitly controlled.

IDs must be random-looking and contain no scenario information.

Examples:

```text
pay_<16 hex chars>
rf_<16 hex chars>
set_<16 hex chars>
item_<16 hex chars>
le_<16 hex chars>
```

No identifiers such as `pay_s1_*`, `pay_decoy_*`, or `le_missing_*` are allowed.

---

## 7. Baseline World Generation

The generator must first construct a clean, internally consistent world.

### Generation order

1. Initialize configuration.
2. Initialize isolated PRNG.
3. Generate customer/payment attributes.
4. Generate payments.
5. Generate refunds.
6. Group payments into settlements.
7. Generate settlement items.
8. Calculate fees.
9. Calculate GST using the domain function.
10. Calculate item net using the domain function.
11. Calculate settlement net from item nets.
12. Generate the baseline ledger representation.
13. Validate the baseline world.
14. Assign benchmark scenarios.
15. Apply scenario transformations.
16. Generate ordinary background ledger activity.
17. Validate the final source world.
18. Generate evaluator-only GroundTruth.
19. Deterministically shuffle output collections.
20. Return the immutable dataset.

---

## 8. Payment Generation

Payments should resemble ordinary merchant payment data.

Generate:

- realistic random payment IDs
- order references
- customer references
- customer names
- captured timestamps
- gross amounts
- `CAPTURED` status
- INR currency

### Amount distribution

Use a mixture of:

- common merchant price points
- randomized values
- a log-normal tail

Example price points:

```text
₹99
₹149
₹499
₹1,299
₹4,999
```

Avoid making scenario families use different amount distributions.

All scenario types must share the same underlying amount generation process.

---

## 9. Refund Generation

For a configured fraction of payments:

- generate full or partial refunds
- link each refund to exactly one payment
- use valid refund status
- determine whether it is netted into settlement

A refund may be:

```text
netted_into_settlement = True
```

or:

```text
netted_into_settlement = False
```

The generator must ensure that each netted refund is consumed by at most one settlement item.

If multiple refunds exist for one payment, the aggregate amount claimed by settlement items must not exceed the available applicable netted refunds.

---

## 10. Settlement Generation

Generate at least one settlement for every benchmark scenario.

Each settlement contains one or more settlement items.

Preferred baseline model:

```text
Settlement
    |
    +-- SettlementItem -> Payment
    |
    +-- SettlementItem -> Payment
    |
    +-- SettlementItem -> Payment
```

A settlement may therefore require multiple ledger entries.

### Settlement-level truth

The settlement's deposited amount is:

```text
sum(all SettlementItem.computed_net_minor)
```

The generator must not create a separate contradictory settlement total.

---

## 11. Ledger Representation

The benchmark ledger represents settlement deposits at the settlement level while allowing grouped target sets.

The generator must support:

```text
Settlement -> one LedgerEntry
```

and, where configured:

```text
Settlement -> multiple LedgerEntries
```

For a multi-entry settlement:

```text
Settlement
  expected net = ₹10,000
       |
       +--> LedgerEntry A = ₹6,000 CREDIT
       +--> LedgerEntry B = ₹4,000 CREDIT
```

The target set is:

```text
{A, B}
```

and the aggregate ledger value equals the settlement expected net.

This supports meaningful grouped-target and target-set evaluation later.

All target entries are ordinary `LedgerEntry` objects.

No field may indicate that an entry is a target, decoy, or scenario artifact.

---

## 12. Background Ledger Activity

Generate normal-looking unrelated ledger transactions.

Examples:

- vendor payouts
- hosting expenses
- salary debits
- rent
- tax debits
- direct bank transfers
- unrelated credits

Noise must use the same:

- date ranges
- amount ranges
- currency
- ID generation
- ordinary narration style

as legitimate records wherever applicable.

Noise records must be indistinguishable at the source-data schema level from normal ledger entries.

Do not add a `noise=True` field or equivalent.

---

# 13. S1–S6 Scenario Definitions

Every scenario is represented by evaluator-only metadata.

The production source records must not contain `ScenarioFamily`.

---

## S1 — Structured Exact

### Goal

Test the easy deterministic reconciliation path.

### Source construction

The correct ledger target has:

- valid structured payment reference
- correct amount
- correct currency
- valid direction
- appropriate settlement timing

The target is uniquely identifiable.

For grouped settlements, every target entry required for the settlement is represented.

### GroundTruth

```text
Resolvability = PROVABLE
exact_target_set = correct ledger entry IDs
ScenarioFamily = S1_STRUCTURED_EXACT
```

The later reconciliation/gate system should be able to reach `AUTO_RESOLVED` when all mandatory checks pass.

---

## S2 — Structured Ambiguous

### Goal

Test candidate ambiguity and uniqueness.

### Source construction

Create multiple ordinary ledger entries that are genuinely plausible candidates.

Candidates should overlap on relevant deterministic signals such as:

- amount
- currency
- direction
- timing
- partial/reference information

Do not create a special decoy type.

Candidate entries must be indistinguishable from ordinary ledger entries.

### Required property

The deterministic candidate engine should find multiple plausible targets.

Do not rely merely on identical text.

The implementation must ensure ambiguity survives the actual Phase 1/Phase 3 candidate-generation semantics.

### GroundTruth

Two variants may exist:

1. `PROVABLE` when a legitimate source signal uniquely identifies the correct target.
2. `NOT_PROVABLE` when candidates are genuinely indistinguishable.

The exact variant must be represented explicitly in GroundTruth.

---

## S3 — Financial Mismatch

### Goal

Test the situation where the relationship is identifiable but the observed money does not reconcile.

### Critical rule

Do NOT corrupt authoritative `SettlementItem` financial arithmetic.

The following must remain valid:

```text
gross - fee - tax - refund + adjustment = net
```

Instead, create the mismatch in the observed ledger side.

Example:

```text
Expected settlement = ₹10,000
Observed ledger      = ₹9,950
Delta                = -₹50
```

The structured relationship may still be obvious, but the financial bridge fails.

### GroundTruth

The evaluator must explicitly define the scenario's resolvability according to the benchmark contract. It must not silently invent a meaning.

---

## S4 — External Reference Text

### Goal

Test reconciliation requiring an unstructured external reference.

### Source construction

The target ledger entry has:

```text
payment_ref = None
```

but contains an external reference in narration.

Example:

```text
UPI/987654/CUST-PO-98712/SETTLEMENT
```

The external reference is legitimate source data.

It must be sufficient for a later bounded investigation to form a human-review proposal.

### GroundTruth

```text
Resolvability = PROVABLE
exact_target_set = {target ledger ID}
ScenarioFamily = S4_EXTERNAL_REF_TEXT
```

### Policy expectation

S4 must remain `HUMAN_REVIEW`, even if the bridge balances.

---

## S5 — Narration/Alias Text

### Goal

Test reconciliation based on weaker unstructured textual evidence.

The target has:

```text
payment_ref = None
external_ref = None
```

and its narration contains a legitimate customer-name alias or other weak textual relation.

Example:

```text
Customer:
Rohan Sharma

Narration:
UPI-P2M-ROHANS-PAYMENT
```

The generator must not make S5 trivially detectable through a unique narration template.

Narrations must come from shared realistic pools.

### GroundTruth

```text
Resolvability = PROVABLE
exact_target_set = {target ledger ID}
ScenarioFamily = S5_NARRATION_ALIAS_TEXT
```

### Policy expectation

S5 must remain `HUMAN_REVIEW`.

---

## S6 — Non-Provable / Conflict

S6 must contain distinct variants.

### Variant A — Missing Record

Create a valid settlement/source world where the expected ledger target is absent.

The rest of the source data remains valid.

GroundTruth:

```text
Resolvability = NOT_PROVABLE
exact_target_set = empty
not_provable_reason = missing ledger record
```

### Variant B — Conflicting Evidence

Create a valid observation where evidence is insufficient or contradictory.

Do not create malformed domain entities merely to create conflict.

For example, multiple ordinary records can produce conflicting candidate evidence without adding a `conflict=True` field.

GroundTruth:

```text
Resolvability = NOT_PROVABLE
not_provable_reason = conflicting or insufficient evidence
```

S6 should ultimately be expected to produce `UNRESOLVED`.

---

# 14. Scenario Transformation Rules

Scenario transformations must preserve all source-domain invariants unless the benchmark explicitly requires an observation-side discrepancy.

The preferred construction strategy is:

```text
valid baseline
    |
    +--> controlled transformation
            |
            +--> still-valid source world
            +--> altered observable relationship
```

A transformation must never silently violate a Phase 1 domain invariant.

After every scenario transformation, run validation.

---

# 15. GroundTruth Isolation

GroundTruth is evaluator-only.

Production reconciliation code must not depend on it.

The generated dataset should expose two conceptual views:

```text
ProductionDataset
    payments
    refunds
    settlements
    settlement_items
    ledger_entries
```

and:

```text
EvaluatorDataset
    ground_truths
    scenario metadata
```

If a single in-memory wrapper is used for convenience, it must provide an explicit separation so production-facing APIs cannot accidentally consume evaluator artifacts.

No production domain entity may contain:

- scenario family
- ground-truth ID
- correct target ID
- decoy flag
- noise flag
- benchmark-only reason
- benchmark-only resolvability

---

# 16. Leakage Prevention

The generator must actively avoid synthetic tells.

Check at least:

### IDs

No scenario-specific prefixes/suffixes.

### Timestamps

S1–S6 share the same timestamp generation process.

### Amounts

S1–S6 share the same amount distributions.

### Narrations

Use shared realistic narration pools.

### Customer names

Do not reserve names for particular scenarios.

### Entity counts

Do not make scenario families structurally obvious by having a unique fixed number of records.

### Ordering

Shuffle all emitted collections deterministically.

### Reference patterns

Do not use a scenario-specific reference syntax.

### Missing fields

Only fields required by the actual source-world scenario should be missing.

Do not create a universal "S5 shape."

### Candidate counts

Avoid fixed scenario-specific candidate counts where possible.

---

# 17. Generator Output

The public API should return an immutable in-memory dataset.

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class GeneratedDataset:
    payments: tuple[Payment, ...]
    refunds: tuple[Refund, ...]
    settlements: tuple[Settlement, ...]
    settlement_items: tuple[SettlementItem, ...]
    ledger_entries: tuple[LedgerEntry, ...]

    # Evaluator-only access boundary.
    ground_truths: tuple[GroundTruth, ...]

    config: GeneratorConfig
    metadata: tuple[tuple[str, str], ...]
```

Do not include `ReconciliationCase`.

GroundTruth access must remain benchmark-only.

The exact wrapper may be adapted to the existing Phase 1 benchmark package structure.

---

# 18. File Layout

```text
packages/benchmark/src/cashproof/benchmark/
├── __init__.py
├── models.py
└── generator/
    ├── __init__.py
    ├── config.py
    ├── prng.py
    ├── world.py
    ├── scenarios.py
    ├── noise.py
    └── builder.py
```

Tests:

```text
tests/benchmark/
├── test_benchmark_boundary.py
├── test_generator_config.py
├── test_generator_invariants.py
├── test_generator_reproducibility.py
├── test_scenario_distribution.py
└── test_leakage_guards.py
```

Additional regression/property tests may be added where required.

---

# 19. Generator Responsibilities by Module

## `config.py`

Owns:

- immutable configuration
- scenario weights
- validation
- parameter validation

## `prng.py`

Owns:

- isolated seeded randomness
- deterministic choice helpers
- deterministic shuffling
- random-looking ID generation

## `world.py`

Owns:

- baseline payments
- refunds
- settlements
- settlement items
- baseline legitimate ledger entries

It must reuse Phase 1 financial functions.

## `scenarios.py`

Owns:

- S1–S6 controlled transformations
- evaluator metadata construction

It must not implement reconciliation.

## `noise.py`

Owns:

- ordinary unrelated ledger activity

## `builder.py`

Owns:

- orchestration
- dataset assembly
- validation
- deterministic shuffling
- public generator function

---

# 20. Validation Requirements

Generation must fail closed.

The generator must validate:

1. All IDs are unique within their entity type.
2. All amounts satisfy domain requirements.
3. All currencies are valid.
4. Every settlement item belongs to its settlement.
5. Every settlement total equals its item totals.
6. Every item bridge is correct.
7. Refund netting invariants hold.
8. No refund is claimed by multiple settlement items.
9. Ledger entries have valid amount/direction semantics.
10. Every benchmark scenario has exactly one corresponding GroundTruth.
11. Every GroundTruth references valid source entities where applicable.
12. No production source entity contains benchmark metadata.
13. At least 50 benchmark scenarios exist in the default configuration.
14. Scenario distribution is within the configured tolerance.
15. Output collections are deterministically shuffled.

---

# 21. Testing Strategy

## Configuration tests

Verify:

- invalid probability values fail
- weights must sum to 1
- item bounds are valid
- `num_cases >= 50` for benchmark configurations
- configuration is immutable

## Invariant tests

Generate multiple seeds and verify:

- settlement-item bridge
- settlement aggregation
- GST
- refund netting
- ID uniqueness
- currency consistency
- ledger semantics

## Property-based tests

Use Hypothesis where useful to generate configurations/seeds and verify invariants across many generated worlds.

## Reproducibility tests

Same:

```text
seed + config + version
```

must produce equivalent datasets.

Different seeds should normally produce different datasets.

## Scenario tests

Verify:

- S1 has unique structured resolution
- S2 has genuine ambiguity
- S3 has an observed financial mismatch without corrupting source arithmetic
- S4 uses external-reference text
- S5 uses narration/alias evidence
- S6 is genuinely non-provable

## Leakage tests

Verify source entities contain no:

- scenario metadata
- truth metadata
- decoy/noise flags

Also test that scenario-specific fingerprints are not intentionally introduced through:

- ID format
- timestamp generation
- amount generation
- narration format
- ordering
- entity counts

Tests should focus on structural guarantees rather than pretending a small synthetic sample can prove statistical indistinguishability.

## GroundTruth tests

Verify:

- one GroundTruth per benchmark scenario
- target sets are correct
- resolvability is correct
- scenario family is correct
- evaluator artifacts remain isolated

---

# 22. Phase 2 Does Not Solve Reconciliation

A critical boundary:

```text
Phase 2:
"Here is the world."

Phase 3:
"Given this world, determine what reconciles."

Phase 4:
"Investigate the ambiguous cases."

Phase 5+:
"Expose and operate the system."
```

The generator must never call a future reconciliation engine merely to decide what its output should be.

GroundTruth is created from the generator's controlled construction knowledge and is used only by the evaluator.

---

# 23. Acceptance Criteria

Phase 2 is complete only when:

### Generator

- [ ] Generates at least 50 benchmark scenarios by default.
- [ ] Generates realistic Payments, Refunds, Settlements, SettlementItems, and LedgerEntries.
- [ ] Supports multi-item settlements.
- [ ] Supports grouped ledger target sets.
- [ ] Uses Phase 1 financial functions.
- [ ] Preserves all source-domain invariants.

### Scenarios

- [ ] S1 is genuinely structured and exact.
- [ ] S2 creates genuine deterministic ambiguity.
- [ ] S3 creates observed financial mismatch without corrupting authoritative source arithmetic.
- [ ] S4 requires external-reference text.
- [ ] S5 requires narration/alias text.
- [ ] S6 contains genuinely non-provable cases.

### Isolation

- [ ] GroundTruth is evaluator-only.
- [ ] Production entities contain no benchmark metadata.
- [ ] No scenario/decoy/noise/truth flags exist in source records.
- [ ] No benchmark-specific fields leak into production types.

### Reproducibility

- [ ] Same seed/config/version gives equivalent output.
- [ ] Global random state is untouched.
- [ ] IDs are deterministic but scenario-neutral.

### Leakage

- [ ] No scenario-specific ID patterns.
- [ ] No scenario-specific timestamp patterns.
- [ ] No scenario-specific amount distributions by construction.
- [ ] No scenario-specific narration templates.
- [ ] Output ordering does not encode scenario.

### Quality

- [ ] Invariant tests pass.
- [ ] Property tests pass.
- [ ] Reproducibility tests pass.
- [ ] Scenario tests pass.
- [ ] Leakage tests pass.
- [ ] Architecture tests pass.
- [ ] Ruff passes.
- [ ] Mypy strict passes.
- [ ] Full existing Phase 0 + Phase 1 test suite remains green.

### Scope

- [ ] No database.
- [ ] No API.
- [ ] No frontend.
- [ ] No LLM.
- [ ] No AI investigator.
- [ ] No reconciliation engine.
- [ ] No GateEvaluation/Resolution execution.
- [ ] No Celery/Redis.
- [ ] No external Razorpay integration.

---

# 24. Risks

### Risk: synthetic scenario tells

Mitigation:

- shared distributions
- shared narration pools
- random IDs
- randomized ordering
- leakage regression tests

### Risk: source invariant corruption

Mitigation:

- reuse Phase 1 pure functions
- validate every generated world
- never corrupt authoritative settlement arithmetic for S3

### Risk: GroundTruth leakage

Mitigation:

- evaluator-only models
- explicit dataset access boundary
- architecture tests
- no production imports of benchmark truth

### Risk: trivial S2

Mitigation:

- construct ambiguity using actual candidate signals
- verify ambiguity against the future deterministic matching semantics

### Risk: underpowered benchmark

Mitigation:

- default to 100 benchmark scenarios
- require at least 50
- include grouped settlements
- include realistic ledger background activity

---

# 25. Final Phase 2 Design Principle

CashProof should not win because its generator makes the answer obvious.

It should win because the generated world forces the reconciliation system to reason about:

```text
source truth
    ↓
financial arithmetic
    ↓
candidate relationships
    ↓
evidence
    ↓
ambiguity
    ↓
deterministic validation
```

Phase 2 therefore exists to create the **world and controlled uncertainty**.

It does not solve the uncertainty itself.
