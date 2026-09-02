"""Tests for ReconciliationCase lifecycle state machine."""

from __future__ import annotations

import pytest
from cashproof.domain.exceptions import InvalidStateTransitionError
from cashproof.domain.state import transition_state
from cashproof.domain.types import ProcessingState


def test_full_lifecycle_state_transitions() -> None:
    # INGESTED -> RECONCILED -> CLASSIFIED -> INVESTIGATED -> GATED -> CLOSED
    s1 = transition_state(ProcessingState.INGESTED, ProcessingState.RECONCILED)
    assert s1 == ProcessingState.RECONCILED

    s2 = transition_state(s1, ProcessingState.CLASSIFIED)
    assert s2 == ProcessingState.CLASSIFIED

    s3 = transition_state(s2, ProcessingState.INVESTIGATED)
    assert s3 == ProcessingState.INVESTIGATED

    s4 = transition_state(s3, ProcessingState.GATED)
    assert s4 == ProcessingState.GATED

    s5 = transition_state(s4, ProcessingState.CLOSED)
    assert s5 == ProcessingState.CLOSED


def test_investigation_skip_transition() -> None:
    # CLASSIFIED -> GATED (Direct skip when deterministic evidence is sufficient)
    s1 = transition_state(ProcessingState.CLASSIFIED, ProcessingState.GATED)
    assert s1 == ProcessingState.GATED


def test_illegal_state_transitions_raise() -> None:
    # Cannot jump from INGESTED directly to CLOSED
    with pytest.raises(InvalidStateTransitionError, match="Illegal state transition"):
        transition_state(ProcessingState.INGESTED, ProcessingState.CLOSED)

    # Cannot go backwards
    with pytest.raises(InvalidStateTransitionError, match="Illegal state transition"):
        transition_state(ProcessingState.GATED, ProcessingState.INVESTIGATED)

    # Cannot transition out of CLOSED
    with pytest.raises(InvalidStateTransitionError, match="Illegal state transition"):
        transition_state(ProcessingState.CLOSED, ProcessingState.INGESTED)
