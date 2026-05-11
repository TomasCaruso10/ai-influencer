"""Audit log estructurado para EU AI Act compliance.

Cada evento del pipeline emite un `AuditEvent` con:
- piece_id, timestamp
- node_name, action
- prompt + seed + modelo + LoRAs
- safety_scores
- outcome (approved/rejected/quarantined)
- reviewer (si HITL)

Retention mínimo: 6 años (EU AI Act technical documentation).

Backends:
- Logfire (siempre): structured logs con template strings
- MongoDB (cuando disponible): persistencia long-term en `audit_events`
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import logfire
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Una entrada del audit log.

    Schema MongoDB equivalente: collection `audit_events`, index por
    (piece_id, timestamp) ascending.
    """

    piece_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    node_name: str
    action: str  # ej "safety_check_passed", "human_approved", "rejected"
    payload: dict[str, Any] = Field(default_factory=dict)
    reviewer_id: str | None = None  # set si fue HITL


async def emit(
    event: AuditEvent,
    mongo_client: Any | None = None,
) -> None:
    """Emit event a Logfire (siempre) + Mongo (si client provided).

    Logfire usa template strings con kwargs para indexar correctamente.
    """
    logfire.info(
        "audit piece_id={piece_id} node={node} action={action}",
        piece_id=event.piece_id,
        node=event.node_name,
        action=event.action,
        payload=event.payload,
        reviewer_id=event.reviewer_id,
    )
    if mongo_client is not None:
        await mongo_client.append_audit(event.model_dump(mode="json"))
