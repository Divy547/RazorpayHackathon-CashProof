"""CashProof Domain Exceptions.

Hierarchy of domain-specific errors representing monetary, invariant, and governance violations.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all CashProof domain errors."""


class MonetaryInvariantError(DomainError):
    """Raised when a monetary calculation or financial invariant is violated."""


class CurrencyMismatchError(DomainError):
    """Raised when records with incompatible currencies are aggregated or compared."""


class SettlementItemBridgeError(MonetaryInvariantError):
    """Raised when a SettlementItem computed_net does not match the arithmetic bridge."""


class SettlementItemSumMismatchError(MonetaryInvariantError):
    """Raised when Settlement net_deposited does not equal the sum of its items."""


class SettlementAssociationError(DomainError):
    """Raised when a SettlementItem is associated with an incorrect Settlement ID."""


class RefundNettingMismatchError(MonetaryInvariantError):
    """Raised when netted refunds in a settlement item do not equal applicable refunds."""


class DuplicateRefundNettingError(MonetaryInvariantError):
    """Raised when a single refund is claimed across multiple settlement items."""


class EmptySettlementItemsError(DomainError):
    """Raised when validating a settlement that contains no settlement items."""


class LedgerEntryAlreadyResolvedError(DomainError):
    """Raised when a LedgerEntry is proposed that has already been resolved elsewhere."""


class DirectConstructionForbiddenError(DomainError):
    """Raised when an entity with a protected construction path is instantiated directly."""


class GateEvaluationIntegrityError(DomainError):
    """Raised when GateEvaluation internal invariants (such as derived pass state) fail."""


class ResolutionGovernanceError(DomainError):
    """Raised when a Resolution violates governance rules (e.g. invalid reviewer fields)."""


class ResolutionGateViolationError(DomainError):
    """Raised when AUTO_RESOLVED is attempted with a non-passing GateEvaluation."""


class ResolutionTargetMismatchError(DomainError):
    """Raised when a Resolution target set does not match its governing GateEvaluation."""


class ResolutionScopeMismatchError(DomainError):
    """Raised when a Resolution case_id or run_id differs from its governing GateEvaluation."""


class InvalidStateTransitionError(DomainError):
    """Raised when an illegal lifecycle state transition is attempted."""
