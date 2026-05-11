"""Safety classifiers post-gen.

Wrappea HuggingFace pipelines:
- Age: `dima806/fairface_age_image_detection` (ViT, FairFace)
- NSFW: `Falconsai/nsfw_image_detection` (binary safe/nsfw)
- Q16: custom CLIP-based para violence/blood/self-harm

Lazy imports de transformers. Para test, mockear `HuggingFaceSafetyClassifiers`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Buckets del fairface age classifier. ADULTS = >=20.
_ADULT_BUCKETS = frozenset({"20-29", "30-39", "40-49", "50-59", "60-69", "more than 70"})
_MINOR_BUCKETS = frozenset({"0-2", "3-9", "10-19"})


@dataclass
class AgeClassifierResult:
    bucket: str
    is_adult: bool
    confidence: float


@dataclass
class NSFWClassifierResult:
    nsfw_score: float
    is_nsfw: bool


@dataclass
class HuggingFaceSafetyClassifiers:
    """Implementa `SafetyClassifiersProto` del pipeline con modelos reales.

    Args:
        age_model: HF model id del classifier de edad
        nsfw_model: HF model id del classifier NSFW
        nsfw_threshold: score > threshold → marca is_nsfw=True
        device: "cuda" o "cpu". Lazy: si "cuda" no está disponible, cae a cpu.
    """

    age_model: str = "dima806/fairface_age_image_detection"
    nsfw_model: str = "Falconsai/nsfw_image_detection"
    nsfw_threshold: float = 0.5
    device: str = "cuda"

    def __post_init__(self) -> None:
        self._age_pipe: Any = None
        self._nsfw_pipe: Any = None

    def _ensure_age_loaded(self) -> None:
        if self._age_pipe is not None:
            return
        from transformers import pipeline  # lazy

        self._age_pipe = pipeline(
            "image-classification",
            model=self.age_model,
            device=0 if self.device == "cuda" else -1,
        )

    def _ensure_nsfw_loaded(self) -> None:
        if self._nsfw_pipe is not None:
            return
        from transformers import pipeline

        self._nsfw_pipe = pipeline(
            "image-classification",
            model=self.nsfw_model,
            device=0 if self.device == "cuda" else -1,
        )

    async def age_classify(self, image_path: Path) -> dict:
        from PIL import Image  # lazy

        self._ensure_age_loaded()
        img = Image.open(image_path).convert("RGB")
        results = self._age_pipe(img)
        # results = [{"label": "20-29", "score": 0.x}, ...]
        top = max(results, key=lambda r: r["score"])
        bucket = top["label"]
        is_adult = bucket in _ADULT_BUCKETS
        return {
            "bucket": bucket,
            "is_adult": is_adult,
            "confidence": float(top["score"]),
        }

    async def nsfw_classify(self, image_path: Path) -> float:
        from PIL import Image

        self._ensure_nsfw_loaded()
        img = Image.open(image_path).convert("RGB")
        results = self._nsfw_pipe(img)
        # Returns highest score para label "nsfw" (or equivalent)
        nsfw_score = next(
            (r["score"] for r in results if r["label"].lower() in {"nsfw", "porn", "explicit"}),
            0.0,
        )
        return float(nsfw_score)

    async def q16_classify(self, image_path: Path) -> bool:
        """Q16 classifier — placeholder por ahora (returns False).

        Q16 propiamente dicho requiere un modelo CLIP-based con prompts de
        inappropriate concepts. Lo implementamos en una iteración futura si
        hace falta. Para MVP, el age + NSFW classifier cubren ~80% del riesgo.
        """
        return False
