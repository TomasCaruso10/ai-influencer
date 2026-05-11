"""Output discriminated union para el grafo.

Cuando un nodo retorna `End[PieceOutput]`, el `node.data` es uno de los dos:
`PieceApproved` o `PieceRejected`. Discriminator field `result` con `Literal`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class RejectionReason(StrEnum):
    """Razones por las que una pieza se rechaza."""

    AGE_CLASSIFIER_FAILED = "age_classifier_failed"
    NSFW_CLASSIFIER_BLOCKED = "nsfw_classifier_blocked"
    Q16_INAPPROPRIATE = "q16_inappropriate"
    FACE_QC_BELOW_THRESHOLD = "face_qc_below_threshold"
    GENERATION_FAILED = "generation_failed"
    HUMAN_REJECTED = "human_rejected"
    POST_PROCESS_FAILED = "post_process_failed"


class PieceApproved(BaseModel):
    """La pieza pasó todas las validaciones y está publishable."""

    result: Literal["approved"] = "approved"
    piece_id: str
    r2_key: str | None = None  # None mientras storage sea local fs


class PieceRejected(BaseModel):
    """La pieza fue rechazada. `reason` indica el porqué para audit."""

    result: Literal["rejected"] = "rejected"
    piece_id: str
    reason: RejectionReason
    detail: str = ""


PieceOutput = Annotated[
    PieceApproved | PieceRejected,
    Field(discriminator="result"),
]
"""Resultado final del grafo. Lo que llega en `End[PieceOutput].data`."""
