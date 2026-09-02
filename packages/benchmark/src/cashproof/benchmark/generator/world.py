"""Baseline clean financial world generation for synthetic datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cashproof.benchmark.generator.config import GeneratorConfig
from cashproof.benchmark.generator.prng import DeterministicRNG
from cashproof.domain.money import calculate_gst_on_fee, calculate_settlement_item_net
from cashproof.domain.source import (
    LedgerEntry,
    Payment,
    Refund,
    Settlement,
    SettlementItem,
)
from cashproof.domain.types import Direction, PaymentStatus, RefundStatus

NAMES: tuple[str, ...] = (
    "Aarav Patel",
    "Diya Sharma",
    "Aditya Verma",
    "Ananya Iyer",
    "Rohan Mehta",
    "Pooja Reddy",
    "Vikram Malhotra",
    "Neha Nair",
    "Kavya Deshmukh",
    "Arjun Sen",
    "Priya Kulkarni",
    "Siddharth Das",
    "Ishita Joshi",
    "Karan Gupta",
    "Rhea Singhania",
)

PRICE_POINTS_MINOR: tuple[int, ...] = (
    199_00,
    299_00,
    499_00,
    799_00,
    999_00,
    1499_00,
    1999_00,
    2499_00,
    4999_00,
    9999_00,
)


@dataclass(frozen=True, slots=True)
class BaselineSettlementCase:
    """Clean baseline settlement group before scenario transformations."""

    settlement: Settlement
    items: tuple[SettlementItem, ...]
    payments: tuple[Payment, ...]
    refunds: tuple[Refund, ...]
    target_ledger_entry: LedgerEntry


def build_baseline_world(
    config: GeneratorConfig,
    rng: DeterministicRNG,
) -> tuple[BaselineSettlementCase, ...]:
    """Build a completely valid baseline financial universe of settlements and ledger entries."""
    base_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
    cases: list[BaselineSettlementCase] = []

    for i in range(config.num_settlements):
        settlement_id = rng.hex_id("set", 12)
        # Advance baseline anchor across 14-day window
        settlement_offset_days = (i * 14) // config.num_settlements
        settlement_base_time = base_time + timedelta(
            days=settlement_offset_days,
            hours=rng.integer(0, 18),
            minutes=rng.integer(0, 59),
        )

        num_items = rng.integer(
            config.min_items_per_settlement,
            config.max_items_per_settlement,
        )

        payments: list[Payment] = []
        refunds: list[Refund] = []
        items: list[SettlementItem] = []

        for j in range(num_items):
            pay_id = rng.hex_id("pay", 12)
            hex_suffix = rng.hex_id("ref", 6).split("_")[1].upper()
            order_ref = f"ORD-202608-{hex_suffix}"
            customer_name = rng.choice(NAMES)
            customer_ref = f"cust_{rng.hex_id('c', 8).split('_')[1]}"

            # Draw gross amount from realistic price points or log-normal spread
            if rng.uniform(0.0, 1.0) < 0.7:
                gross_minor = rng.choice(PRICE_POINTS_MINOR)
            else:
                gross_minor = rng.integer(50_00, 25000_00)

            payment_time = settlement_base_time + timedelta(
                hours=j * 2,
                minutes=rng.integer(0, 50),
            )

            payment = Payment(
                id=pay_id,
                order_ref=order_ref,
                customer_ref=customer_ref,
                customer_name=customer_name,
                gross_minor=gross_minor,
                currency=config.currency,
                captured_at=payment_time,
                status=PaymentStatus.CAPTURED,
            )
            payments.append(payment)

            # Refund generation if applicable
            netted_refund_minor = 0
            if rng.uniform(0.0, 1.0) < config.refund_probability:
                rf_id = rng.hex_id("rf", 12)
                # When netted into settlement payout, partial refund ensures positive net
                refund_pct = rng.choice([20, 30, 40, 50])
                refund_amount = (gross_minor * refund_pct) // 100

                if refund_amount > 0:
                    refund_time = payment_time + timedelta(hours=rng.integer(1, 10))
                    refund = Refund(
                        refund_id=rf_id,
                        payment_id=pay_id,
                        amount_minor=refund_amount,
                        currency=config.currency,
                        created_at=refund_time,
                        status=RefundStatus.PROCESSED,
                        netted_into_settlement=True,
                    )
                    refunds.append(refund)
                    netted_refund_minor = refund_amount

            # 2.0% gateway fee
            fee_minor = (gross_minor * 200) // 10000
            tax_on_fee_minor = calculate_gst_on_fee(fee_minor)
            computed_net_minor = calculate_settlement_item_net(
                gross_minor=gross_minor,
                fee_minor=fee_minor,
                tax_on_fee_minor=tax_on_fee_minor,
                netted_refund_minor=netted_refund_minor,
                adjustment_minor=0,
            )

            item = SettlementItem(
                item_id=rng.hex_id("item", 12),
                settlement_id=settlement_id,
                payment_id=pay_id,
                gross_minor=gross_minor,
                fee_minor=fee_minor,
                tax_on_fee_minor=tax_on_fee_minor,
                netted_refund_minor=netted_refund_minor,
                adjustment_minor=0,
                computed_net_minor=computed_net_minor,
            )
            items.append(item)

        total_settlement_net = sum(it.computed_net_minor for it in items)
        latest_payment_time = max(p.captured_at for p in payments)
        settled_at = latest_payment_time + timedelta(days=1, hours=rng.integer(1, 6))

        settlement = Settlement(
            settlement_id=settlement_id,
            net_deposited_minor=total_settlement_net,
            currency=config.currency,
            settled_at=settled_at,
        )

        # Baseline matching target ledger entry
        target_entry = LedgerEntry(
            id=rng.hex_id("le", 12),
            amount_minor=total_settlement_net,
            currency=config.currency,
            timestamp=settled_at + timedelta(hours=rng.integer(2, 12)),
            direction=Direction.CREDIT,
            payment_ref=settlement_id,
            external_ref=None,
            narration=f"NEFT-RZPX-{settlement_id}-PAYOUT",
            customer_name=None,
        )

        cases.append(
            BaselineSettlementCase(
                settlement=settlement,
                items=tuple(items),
                payments=tuple(payments),
                refunds=tuple(refunds),
                target_ledger_entry=target_entry,
            )
        )

    return tuple(cases)
