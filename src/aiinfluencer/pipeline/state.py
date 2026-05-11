"""State del workflow. BaseModel para snapshot serialization.

Wrapper pattern: `PieceRecord` es el flat DB model (lo que persiste a Mongo),
`WorkflowState` lo envuelve + agrega in-memory entities (imágenes locales, scores).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field, PrivateAttr

from aiinfluencer.pipeline.output import RejectionReason


class SafetyScores(BaseModel):
    """Scores de los classifiers de safety post-gen."""

    age_predicted_bucket: str | None = None  # ej "20-29", "30-39"
    age_is_adult: bool | None = None
    nsfw_score: float | None = None  # 0-1, >0.5 = NSFW
    q16_inappropriate: bool | None = None  # True = violence/gore/etc detected


class PieceRecord(BaseModel):
    """Flat DB record. Una fila en collection `pieces` de Mongo.

    Solo este modelo persiste cross-snapshot. Lo demás del WorkflowState es
    in-memory para la corrida actual.
    """

    piece_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = "pending"  # pending|generating|reviewing|approved|rejected|failed

    # Input
    prompt_seed: str
    model_choice: str  # ej "flux+lora_a1", "chroma+lora_a1", "sdxl_bigasp+lora_sdxl_a1"
    character_id: str = "aiinfluencer1"
    seed: int | None = None

    # Outputs (paths o keys)
    raw_image_key: str | None = None  # path local o r2 key
    processed_image_key: str | None = None

    # Flags de pipeline (Optional[bool] — None = no evaluado todavía)
    safety_passed: bool | None = None
    face_qc_passed: bool | None = None
    human_approved: bool | None = None
    c2pa_signed: bool | None = None
    publishable: bool | None = None

    # Resultado final
    rejection_reason: RejectionReason | None = None
    rejection_detail: str = ""


class WorkflowState(BaseModel):
    """State serializable del grafo. Wrappea `PieceRecord` + in-memory data."""

    record: PieceRecord

    # In-memory durante la corrida (no persisten cross-snapshot necesariamente)
    raw_image_path: Path | None = None
    processed_image_path: Path | None = None
    expanded_prompt_positive: str | None = None
    expanded_prompt_negative: str | None = None
    safety_scores: SafetyScores | None = None
    face_qc_score: float | None = None
    caption: str | None = None

    # Cache interno (no serializa)
    _runtime_cache: dict[str, object] = PrivateAttr(default_factory=dict)

    # ─── Proxy properties al record ─────────────────────────────────────────

    @property
    def piece_id(self) -> str:
        return self.record.piece_id

    @property
    def status(self) -> str:
        return self.record.status

    @status.setter
    def status(self, value: str) -> None:
        self.record.status = value

    @property
    def model_choice(self) -> str:
        return self.record.model_choice

    @property
    def seed(self) -> int | None:
        return self.record.seed

    # ─── Setters de flags (proxy) ───────────────────────────────────────────

    def set_safety_passed(self, value: bool) -> None:
        self.record.safety_passed = value

    def set_face_qc_passed(self, value: bool) -> None:
        self.record.face_qc_passed = value

    def set_human_approved(self, value: bool) -> None:
        self.record.human_approved = value

    def set_c2pa_signed(self, value: bool) -> None:
        self.record.c2pa_signed = value

    def set_publishable(self, value: bool) -> None:
        self.record.publishable = value

    def set_rejection(self, reason: RejectionReason, detail: str = "") -> None:
        self.record.rejection_reason = reason
        self.record.rejection_detail = detail
        self.record.status = "rejected"
        self.record.publishable = False

    # ─── Typed accessors con guards ─────────────────────────────────────────

    def require_raw_image(self) -> Path:
        if self.raw_image_path is None:
            raise RuntimeError("raw_image_path not set yet — generate node didn't run")
        return self.raw_image_path

    def require_processed_image(self) -> Path:
        if self.processed_image_path is None:
            raise RuntimeError("processed_image_path not set yet — post_process didn't run")
        return self.processed_image_path

    def require_safety_scores(self) -> SafetyScores:
        if self.safety_scores is None:
            raise RuntimeError("safety_scores not set yet — safety_filter didn't run")
        return self.safety_scores
