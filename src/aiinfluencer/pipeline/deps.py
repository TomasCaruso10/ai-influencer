"""Dependencies del workflow. @dataclass.

Cada field es un cliente/servicio que los nodos usan. Mockeable para tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable


# ─── Protocols (interfaces que los clients deben cumplir) ──────────────────


@runtime_checkable
class ComfyClientProto(Protocol):
    """Cliente HTTP a ComfyUI. Implementación real en `clients/comfy.py`."""

    async def submit_workflow(self, workflow: dict, prompt: str, negative: str, seed: int) -> Path:
        """Ejecuta workflow, devuelve path local al output."""
        ...


@runtime_checkable
class MongoClientProto(Protocol):
    """Cliente a MongoDB para state persistence + audit log."""

    async def save_record(self, record: object) -> None: ...
    async def load_record(self, piece_id: str) -> object | None: ...
    async def append_audit(self, event: dict) -> None: ...


@runtime_checkable
class StorageClientProto(Protocol):
    """Cliente de storage (R2 o local fs)."""

    async def upload(self, local_path: Path, key: str) -> str:
        """Sube archivo, devuelve key/URL público."""
        ...


@runtime_checkable
class C2PASignerProto(Protocol):
    """Firma C2PA manifest en imagen."""

    async def sign(self, image_path: Path, manifest: dict) -> Path: ...


@runtime_checkable
class FaceQCProto(Protocol):
    """InsightFace embedding + similarity vs canon."""

    async def cosine_similarity(self, image_path: Path) -> float: ...


@runtime_checkable
class SafetyClassifiersProto(Protocol):
    """Clasificadores post-gen: age, NSFW, Q16."""

    async def age_classify(self, image_path: Path) -> dict: ...
    async def nsfw_classify(self, image_path: Path) -> float: ...
    async def q16_classify(self, image_path: Path) -> bool: ...


# ─── Dummy implementations para Fase 2.0 (placeholders) ────────────────────


@dataclass
class DummyComfyClient:
    """Placeholder. Devuelve un path falso sin generar nada."""

    output_dir: Path = field(default_factory=lambda: Path("outputs/pipeline_dummy"))

    async def submit_workflow(self, workflow: dict, prompt: str, negative: str, seed: int) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        fake_path = self.output_dir / f"dummy_seed{seed}.png"
        fake_path.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG header mínimo
        return fake_path


@dataclass
class DummyMongoClient:
    """Placeholder. In-memory dict."""

    _records: dict[str, object] = field(default_factory=dict)
    _audit: list[dict] = field(default_factory=list)

    async def save_record(self, record: object) -> None:
        piece_id = getattr(record, "piece_id", None)
        if piece_id:
            self._records[piece_id] = record

    async def load_record(self, piece_id: str) -> object | None:
        return self._records.get(piece_id)

    async def append_audit(self, event: dict) -> None:
        self._audit.append(event)


@dataclass
class DummyStorage:
    """Placeholder. No sube nada, devuelve el path mismo."""

    async def upload(self, local_path: Path, key: str) -> str:
        return f"local://{local_path}"


@dataclass
class DummyC2PASigner:
    """Placeholder. No firma, devuelve mismo path."""

    async def sign(self, image_path: Path, manifest: dict) -> Path:
        return image_path


@dataclass
class DummyFaceQC:
    """Placeholder. Siempre devuelve 0.8 (pass)."""

    async def cosine_similarity(self, image_path: Path) -> float:
        return 0.8


@dataclass
class DummySafetyClassifiers:
    """Placeholder. Siempre pasa todos los checks (adult, SFW, no Q16 flag)."""

    async def age_classify(self, image_path: Path) -> dict:
        return {"bucket": "20-29", "is_adult": True, "confidence": 0.95}

    async def nsfw_classify(self, image_path: Path) -> float:
        return 0.5  # neutral

    async def q16_classify(self, image_path: Path) -> bool:
        return False  # no inappropriate


# ─── WorkflowDeps ──────────────────────────────────────────────────────────


@dataclass
class WorkflowDeps:
    """Dependencies inyectadas a todos los nodos via ctx.deps.

    En tests/dev, los fields se inicializan con Dummy*. En prod, con
    implementaciones reales (ComfyClient real, MongoDB real, R2, etc.).
    """

    comfy: ComfyClientProto
    mongo: MongoClientProto
    storage: StorageClientProto
    c2pa: C2PASignerProto
    face_qc: FaceQCProto
    classifiers: SafetyClassifiersProto

    # Configuración runtime
    face_qc_threshold: float = 0.45
    auto_approve_in_review: bool = True  # True para dev/test, False para HITL real

    @classmethod
    def with_dummies(cls) -> "WorkflowDeps":
        """Construye deps con todos los placeholders dummy. Útil para smoke tests."""
        return cls(
            comfy=DummyComfyClient(),
            mongo=DummyMongoClient(),
            storage=DummyStorage(),
            c2pa=DummyC2PASigner(),
            face_qc=DummyFaceQC(),
            classifiers=DummySafetyClassifiers(),
        )

    @classmethod
    def with_production_face_qc(
        cls,
        canon_mean_path: str | Path,
        face_qc_threshold: float = 0.45,
    ) -> "WorkflowDeps":
        """Deps con InsightFace FaceQC real, resto dummies. Para integrar Bloque 2.2
        sin haber implementado el resto.
        """
        from aiinfluencer.face_qc import FaceQC

        return cls(
            comfy=DummyComfyClient(),
            mongo=DummyMongoClient(),
            storage=DummyStorage(),
            c2pa=DummyC2PASigner(),
            face_qc=FaceQC(canon_mean_path=canon_mean_path),
            classifiers=DummySafetyClassifiers(),
            face_qc_threshold=face_qc_threshold,
        )
