"""Metrics para eval de LoRA outputs.

Cada metric implementa el Protocol `Metric`. Convención: scores normalizados
0-1 cuando posible (higher = better). Aesthetic puede ir 0-10.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Metric(Protocol):
    """Una métrica que evalúa una imagen generada."""

    name: str

    async def score(self, image_path: Path, context: dict) -> float:
        """Returns score. Higher = better.

        `context` puede contener `prompt`, `seed`, `checkpoint`, etc. — útil
        para métricas que necesitan el prompt original (CLIP adherence).
        """
        ...


@dataclass
class FaceSimilarityMetric:
    """Wrappea `aiinfluencer.face_qc.FaceQC`. Score = cosine similarity 0-1."""

    canon_mean_path: Path | str
    name: str = "face_similarity"

    def __post_init__(self) -> None:
        from aiinfluencer.face_qc import FaceQC
        self._face_qc = FaceQC(canon_mean_path=self.canon_mean_path)

    async def score(self, image_path: Path, context: dict) -> float:
        return await self._face_qc.cosine_similarity(image_path)


@dataclass
class AestheticMetric:
    """LAION aesthetic predictor v2.5 (vía HuggingFace transformers).

    Optional dep: face-qc (transformers + torch). Lazy import.

    Score: 0-10. Higher = better.
    """

    model_name: str = "shadowlilac/aesthetic-shadow-v2"
    name: str = "aesthetic"

    def __post_init__(self) -> None:
        self._pipeline = None  # lazy load

    def _ensure_loaded(self) -> None:
        if self._pipeline is not None:
            return
        from transformers import pipeline  # lazy

        self._pipeline = pipeline("image-classification", model=self.model_name)

    async def score(self, image_path: Path, context: dict) -> float:
        self._ensure_loaded()
        from PIL import Image  # PIL es dep base, OK

        img = Image.open(image_path).convert("RGB")
        results = self._pipeline(img)
        # results = [{"label": "hq", "score": 0.x}, {"label": "lq", "score": 0.y}]
        # mapear a 0-10
        hq_score = next((r["score"] for r in results if r["label"] == "hq"), 0.0)
        return float(hq_score * 10.0)


@dataclass
class CLIPPromptAdherenceMetric:
    """CLIP cosine similarity entre prompt y output.

    Optional dep: face-qc (open_clip o transformers). Lazy import.

    Score: 0-1. Higher = mejor adherencia al prompt.
    """

    model_name: str = "openai/clip-vit-base-patch32"
    name: str = "clip_adherence"

    def __post_init__(self) -> None:
        self._model = None
        self._processor = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        from transformers import CLIPModel, CLIPProcessor  # lazy

        self._model = CLIPModel.from_pretrained(self.model_name)
        self._processor = CLIPProcessor.from_pretrained(self.model_name)

    async def score(self, image_path: Path, context: dict) -> float:
        import torch
        from PIL import Image

        self._ensure_loaded()
        prompt = context.get("prompt", "")
        if not prompt:
            return 0.0

        img = Image.open(image_path).convert("RGB")
        inputs = self._processor(
            text=[prompt],
            images=img,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        with torch.no_grad():
            outputs = self._model(**inputs)

        # logits_per_image: shape (1, 1); softmax sobre 1 elemento da 1.0, no útil
        # Usamos cosine similarity entre image_embeds y text_embeds
        img_emb = outputs.image_embeds
        txt_emb = outputs.text_embeds
        img_emb = img_emb / img_emb.norm(dim=-1, keepdim=True)
        txt_emb = txt_emb / txt_emb.norm(dim=-1, keepdim=True)
        sim = (img_emb * txt_emb).sum(dim=-1).item()
        return float(sim)


@dataclass
class DummyMetric:
    """Para tests. Returns un score fijo o función de la imagen."""

    name: str = "dummy"
    constant_score: float = 0.7

    async def score(self, image_path: Path, context: dict) -> float:
        return self.constant_score
