"""Face Quality Control. InsightFace ArcFace cosine similarity vs canon mean.

Quick reference:
    from aiinfluencer.face_qc import FaceQC, compute_canon_mean

    # One-time setup: compute mean embedding from canon dataset
    mean = compute_canon_mean(Path("outputs/canon"))
    np.save("outputs/canon/_mean_embedding.npy", mean)

    # Runtime: verifier
    verifier = FaceQC(canon_mean_path="outputs/canon/_mean_embedding.npy")
    similarity = await verifier.cosine_similarity(Path("output.png"))  # 0-1
"""

from aiinfluencer.face_qc.embeddings import (
    compute_canon_mean,
    embedding_for_image,
    load_canon_mean,
)
from aiinfluencer.face_qc.exceptions import AmbiguousFaceError, NoFaceDetectedError
from aiinfluencer.face_qc.verifier import FaceQC

__all__ = [
    "FaceQC",
    "compute_canon_mean",
    "embedding_for_image",
    "load_canon_mean",
    "NoFaceDetectedError",
    "AmbiguousFaceError",
]
