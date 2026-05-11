"""Face embedding extraction + canon mean computation.

InsightFace `buffalo_l` model:
    - Detección: SCRFD-10GF
    - Recognition: ResNet50 @ WebFace600K
    - Output: 512-dim L2-normalized embedding
    - ~326 MB total, auto-download on first use
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np

from aiinfluencer.face_qc.exceptions import NoFaceDetectedError

logger = logging.getLogger(__name__)

# Insightface model name. buffalo_l outperforms antelopev2 in benchmarks.
_MODEL_NAME = "buffalo_l"


@lru_cache(maxsize=1)
def _get_face_analysis():
    """Lazy load del FaceAnalysis app. Una sola instancia por proceso.

    Auto-downloads ~326 MB la primera vez a `~/.insightface/models/buffalo_l/`.
    """
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(
        name=_MODEL_NAME,
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def embedding_for_image(image_path: Path) -> np.ndarray:
    """Extrae el embedding facial de la cara principal de una imagen.

    Si hay múltiples caras, toma la del bbox más grande (la "principal").
    Si no hay ninguna, raise `NoFaceDetectedError`.

    Returns:
        np.ndarray de shape (512,), L2-normalized (cosine sim == dot product).
    """
    import cv2  # lazy: requires opencv-python-headless (optional dep face-qc)

    img = cv2.imread(str(image_path))
    if img is None:
        raise NoFaceDetectedError(f"Cannot read image: {image_path}")

    app = _get_face_analysis()
    faces = app.get(img)
    if not faces:
        raise NoFaceDetectedError(f"No faces detected in {image_path}")

    # Tomar la cara con bbox más grande
    main = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

    embedding: np.ndarray = main.normed_embedding
    if embedding is None:
        raise NoFaceDetectedError(f"Face detected but no embedding extracted: {image_path}")

    return embedding.astype(np.float32)


def compute_canon_mean(canon_dir: Path) -> np.ndarray:
    """Compute mean embedding del canon dataset.

    Procesa todas las imágenes .png/.jpg en `canon_dir`, promedia los
    embeddings (excluyendo imágenes sin cara), y L2-normaliza el resultado.

    Returns:
        np.ndarray (512,), L2-normalized.

    Raises:
        RuntimeError si no se pudo extraer embedding de ninguna imagen.
    """
    canon_dir = Path(canon_dir)
    image_paths = sorted(
        p for p in canon_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    if not image_paths:
        raise RuntimeError(f"No images found in {canon_dir}")

    embeddings: list[np.ndarray] = []
    failed: list[Path] = []
    for path in image_paths:
        try:
            embeddings.append(embedding_for_image(path))
        except NoFaceDetectedError as exc:
            logger.warning("skipping %s: %s", path.name, exc)
            failed.append(path)

    if not embeddings:
        raise RuntimeError(
            f"Could not extract embedding from any image in {canon_dir}. "
            f"Tried {len(image_paths)}, all failed."
        )

    mean = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(mean)
    if norm < 1e-8:
        raise RuntimeError("Mean embedding has zero norm — embeddings cancelled out")

    mean_normalized = (mean / norm).astype(np.float32)
    logger.info(
        "computed canon mean from %d/%d images (failed: %d)",
        len(embeddings),
        len(image_paths),
        len(failed),
    )
    return mean_normalized


def load_canon_mean(path: Path) -> np.ndarray:
    """Carga mean embedding pre-computado desde `.npy`. Verifica shape + norm."""
    mean = np.load(path)
    if mean.shape != (512,):
        raise ValueError(f"Expected shape (512,), got {mean.shape} from {path}")
    norm = float(np.linalg.norm(mean))
    if not (0.99 <= norm <= 1.01):
        raise ValueError(f"Canon mean not L2-normalized (norm={norm:.4f}) at {path}")
    return mean.astype(np.float32)
