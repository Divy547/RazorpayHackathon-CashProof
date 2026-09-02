"""CashProof Lifecycle State Machine.

Enforces valid processing state progression for reconciliation cases:
INGESTED -> RECONCILED -> CLASSIFIED -> [INVESTIGATED] -> GATED -> CLOSED.
"""

from __future__ import annotations

from cashproof.domain.exceptions import InvalidStateTransitionError
from cashproof.domain.types import ProcessingState

VALID_TRANSITIONS: dict[ProcessingState, frozenset[ProcessingState]] = {
    ProcessingState.INGESTED: frozenset({ProcessingState.RECONCILED}),
    ProcessingState.RECONCILED: frozenset({ProcessingState.CLASSIFIED}),
    ProcessingState.CLASSIFIED: frozenset(
        {
            ProcessingState.INVESTIGATED,
            ProcessingState.GATED,  # Direct skip when deterministic evidence is sufficient
        }
    ),
    ProcessingState.INVESTIGATED: frozenset({ProcessingState.GATED}),
    ProcessingState.GATED: frozenset({ProcessingState.CLOSED}),
    ProcessingState.CLOSED: frozenset(),
}


def transition_state(
    current: ProcessingState,
    next_state: ProcessingState,
) -> ProcessingState:
    """Validate and perform a state transition for a ReconciliationCase.

    Raises InvalidStateTransitionError if the transition is illegal.
    """
    allowed = VALID_TRANSITIONS.get(current, frozenset())
    if next_state not in allowed:
        raise InvalidStateTransitionError(
            f"Illegal state transition from '{current}' to '{next_state}'. "
            f"Allowed: {sorted(allowed)}"
        )
    return next_state
