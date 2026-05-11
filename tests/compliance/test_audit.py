"""Tests del audit log."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aiinfluencer.compliance.audit import AuditEvent, emit


def test_audit_event_construction():
    event = AuditEvent(
        piece_id="piece_abc",
        node_name="SafetyFilterNode",
        action="safety_check_passed",
        payload={"nsfw_score": 0.3},
    )
    assert event.piece_id == "piece_abc"
    assert event.action == "safety_check_passed"
    assert event.payload["nsfw_score"] == 0.3
    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo == UTC


def test_audit_event_serializable():
    event = AuditEvent(
        piece_id="piece_abc",
        node_name="HumanReviewNode",
        action="approved",
        reviewer_id="user_tomas",
    )
    dumped = event.model_dump(mode="json")
    assert dumped["piece_id"] == "piece_abc"
    assert dumped["reviewer_id"] == "user_tomas"
    assert "timestamp" in dumped


async def test_emit_to_mongo_calls_append(monkeypatch):
    """Emit con mongo_client llama append_audit."""
    captured: list[dict] = []

    class FakeMongo:
        async def append_audit(self, ev: dict) -> None:
            captured.append(ev)

    event = AuditEvent(piece_id="p1", node_name="N", action="A")
    await emit(event, mongo_client=FakeMongo())

    assert len(captured) == 1
    assert captured[0]["piece_id"] == "p1"


async def test_emit_without_mongo_still_logs():
    """Sin mongo, solo logfire — no debe levantar."""
    event = AuditEvent(piece_id="p1", node_name="N", action="A")
    await emit(event, mongo_client=None)  # no raise
