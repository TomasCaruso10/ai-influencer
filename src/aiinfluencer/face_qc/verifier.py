"""FaceQC verifier. Implementa el Protocol `FaceQCProto` del pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from aiinfluencer.face_qc.embeddings import embedding_for_image, load_canon_mean
from aiinfluencer.face_qc.exceptions import NoFaceDetectedError


@dataclass
class FaceQC:
    """Compara una imagen contra el canon mean embedding.

    Args:
        canon_mean_path: path al `.npy` con el mean embedding pre-computado.
        no_face_score: score a devolver si la imagen no tiene cara detectable.
                       Default 0.0 (fuerza rechazo). Cambiar a None si querés
                       que el pipeline rechace con motivo distinto.
    """

    canon_mean_path: Path | str
    no_face_score: float = 0.0

    def __post_init__(self) -> None:
        self._canon_mean = load_canon_mean(Path(self.canon_mean_path))

    async def cosine_similarity(self, image_path: Path) -> float:
        """Returns cosine similarity 0-1 vs canon mean.

        Como ambos embeddings son L2-normalized, cosine sim = dot product.

        Si la imagen no tiene cara, devuelve `no_face_score` (default 0.0).
        """
        try:
            emb = embedding_for_image(Path(image_path))
        except NoFaceDetectedError:
            return self.no_face_score

        return float(np.dot(emb, self._canon_mean))
