"""Tests for immutable append-only AuditEvent."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest
from cashproof.domain.decision import AuditEvent
from cashproof.domain.types import AuditActor


def test_audit_event_creation_and_defensive_freeze() -> None:
    now = datetime.now(UTC)
    meta = {"rule_name": "exact_ref_match", "score": "1.0"}

    event = AuditEvent(
        event_id="evt_100",
        case_id="case_1",
        run_id="run_1",
        entity_type="ReconciliationCase",
        entity_id="case_1",
        event_type="CASE_CLASSIFIED",
        actor=AuditActor.SYSTEM,
        timestamp=now,
        metadata=meta,
    )

    assert event.event_id == "evt_100"
    assert event.actor == AuditActor.SYSTEM
    assert event.metadata == (("rule_name", "exact_ref_match"), ("score", "1.0"))

    # Mutating caller metadata dict
    meta["injected"] = "val"
    assert "injected" not in [k for k, _ in event.metadata]

    with pytest.raises(FrozenInstanceError):
        event.event_type = "MUTATED"  # type: ignore[misc]


def test_audit_event_validation() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="event_id must not be empty"):
        AuditEvent("", "c_1", "r_1", "Type", "id", "EVT", AuditActor.AI, now)
    with pytest.raises(ValueError, match="case_id must not be empty"):
        AuditEvent("e_1", "", "r_1", "Type", "id", "EVT", AuditActor.AI, now)
    with pytest.raises(ValueError, match="run_id must not be empty"):
        AuditEvent("e_1", "c_1", "", "Type", "id", "EVT", AuditActor.AI, now)
