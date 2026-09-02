"""Background distractor ledger entries generation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.generator.prng import DeterministicRNG
from cashproof.domain.source import LedgerEntry
from cashproof.domain.types import Direction

NOISE_DEBITS: tuple[str, ...] = (
    "ACH/AWS-EMEA/INV-98124",
    "GOOGLE*WORKSPACE-AUG",
    "SLACK-TECH-SUBSCRIPTION",
    "RTGS-COMMERCIAL-RENT",
    "OFFICE-FACILITIES-MGT",
    "SALARY-BATCH-AUG26",
    "CONTRACTOR-DISBURSEMENT-TECH",
    "GST-PAYMENT-GOV",
    "BANK-ACCOUNT-CHARGES-Q2",
)

NOISE_CREDITS: tuple[str, ...] = (
    "IMPS/P2A/6281920/DIRECT-INVOICE",
    "NEFT-ENTERPRISE-CLIENT-PAYMENT",
    "FIXED-DEPOSIT-INTEREST",
    "VENDOR-REFUND-CREDIT-SERVICES",
    "DIRECT-CLIENT-DEPOSIT-OVERSEAS",
)


def generate_background_noise(
    config: GeneratorConfig,
    num_target_entries: int,
    rng: DeterministicRNG,
) -> tuple[LedgerEntry, ...]:
    """Generate background distractor ledger entries indistinguishable from true source records."""
    num_noise = max(1, int(num_target_entries * config.noise_ratio))
    base_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
    noise_entries: list[LedgerEntry] = []

    for _ in range(num_noise):
        le_id = rng.hex_id("le", 12)
        # 60% debits, 40% credits
        is_debit = rng.uniform(0.0, 1.0) < 0.6
        if is_debit:
            direction = Direction.DEBIT
            narration = rng.choice(NOISE_DEBITS)
            amount_minor = rng.integer(500_00, 10000_00)
        else:
            direction = Direction.CREDIT
            narration = rng.choice(NOISE_CREDITS)
            amount_minor = rng.integer(1000_00, 25000_00)

        # Spread across 14-day window
        offset_seconds = rng.integer(0, 14 * 86400)
        entry_time = base_time + timedelta(seconds=offset_seconds)

        entry = LedgerEntry(
            id=le_id,
            amount_minor=amount_minor,
            currency=config.currency,
            timestamp=entry_time,
            direction=direction,
            payment_ref=None,
            external_ref=None,
            narration=narration,
            customer_name=None,
        )
        noise_entries.append(entry)

    return tuple(noise_entries)
