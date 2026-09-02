"""CashProof Domain Base Types and Enums.

Pure, framework-independent enums representing core financial and lifecycle states.
"""

from __future__ import annotations

import enum


class Currency(enum.StrEnum):
    """Explicit currency enumeration. MVP is INR."""

    INR = "INR"
    USD = "USD"
    EUR = "EUR"


class Direction(enum.StrEnum):
    """Ledger entry accounting direction."""

    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class PaymentStatus(enum.StrEnum):
    """Payment lifecycle status."""

    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class RefundStatus(enum.StrEnum):
    """Refund lifecycle status."""

    PROCESSED = "PROCESSED"
    PENDING = "PENDING"
    FAILED = "FAILED"


class ProcessingState(enum.StrEnum):
    """Reconciliation case lifecycle processing states."""

    INGESTED = "INGESTED"
    RECONCILED = "RECONCILED"
    CLASSIFIED = "CLASSIFIED"
    INVESTIGATED = "INVESTIGATED"
    GATED = "GATED"
    CLOSED = "CLOSED"


class ExceptionType(enum.StrEnum):
    """Operational exception classifications."""

    CLEAN_MATCH = "CLEAN_MATCH"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    DUPLICATE_PAYMENT = "DUPLICATE_PAYMENT"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    FEE_MISMATCH = "FEE_MISMATCH"
    TAX_MISMATCH = "TAX_MISMATCH"
    TIMING_GAP = "TIMING_GAP"
    NAME_ALIAS = "NAME_ALIAS"
    MISSING_RECORD = "MISSING_RECORD"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    NON_PROVABLE = "NON_PROVABLE"


class EvidenceStance(enum.StrEnum):
    """Evidence semantic stance relative to a hypothesis."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"


class Disposition(enum.StrEnum):
    """Final resolution governance disposition."""

    AUTO_RESOLVED = "AUTO_RESOLVED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    UNRESOLVED = "UNRESOLVED"


class ReviewOutcome(enum.StrEnum):
    """Human review decision outcome."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class AuditActor(enum.StrEnum):
    """Actors recorded in append-only audit events."""

    SYSTEM = "SYSTEM"
    AI = "AI"
    REVIEWER = "REVIEWER"


class StopReason(enum.StrEnum):
    """AI investigation termination reason."""

    COMPLETED = "COMPLETED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    TIMEOUT = "TIMEOUT"
    TOOL_FAILURE = "TOOL_FAILURE"
    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"


class HypothesisSource(enum.StrEnum):
    """Provenance source of a resolution hypothesis."""

    DETERMINISTIC_RULES = "DETERMINISTIC_RULES"
    AI_INVESTIGATION = "AI_INVESTIGATION"


class MatchProvenance(enum.StrEnum):
    """Production candidate provenance signal used by policy gate checks."""

    STRUCTURED_REFERENCE = "STRUCTURED_REFERENCE"
    EXTERNAL_REFERENCE_TEXT = "EXTERNAL_REFERENCE_TEXT"
    NARRATION_ALIAS_TEXT = "NARRATION_ALIAS_TEXT"
