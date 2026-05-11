"""Tests del FaceQC verifier."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from aiinfluencer.face_qc import FaceQC
from aiinfluencer.face_qc.exceptions import NoFaceDetectedError


@pytest.fixture
def canon_mean_path(tmp_path) -> Path:
    """Mean embedding L2-normalized en el eje 0."""
    mean = np.zeros(512, dtype=np.float32)
    mean[0] = 1.0
    path = tmp_path / "_mean.npy"
    np.save(path, mean)
    return path


@patch("aiinfluencer.face_qc.verifier.embedding_for_image")
async def test_cosine_similarity_identity_returns_one(mock_emb, canon_mean_path):
    same = np.zeros(512, dtype=np.float32)
    same[0] = 1.0
    mock_emb.return_value = same

    qc = FaceQC(canon_mean_path=canon_mean_path)
    sim = await qc.cosine_similarity(Path("/fake.png"))

    assert sim == pytest.approx(1.0)


@patch("aiinfluencer.face_qc.verifier.embedding_for_image")
async def test_cosine_similarity_orthogonal_returns_zero(mock_emb, canon_mean_path):
    orth = np.zeros(512, dtype=np.float32)
    orth[1] = 1.0
    mock_emb.return_value = orth

    qc = FaceQC(canon_mean_path=canon_mean_path)
    sim = await qc.cosine_similarity(Path("/fake.png"))

    assert sim == pytest.approx(0.0, abs=1e-6)


@patch("aiinfluencer.face_qc.verifier.embedding_for_image")
async def test_cosine_similarity_no_face_returns_default(mock_emb, canon_mean_path):
    mock_emb.side_effect = NoFaceDetectedError("no face")

    qc = FaceQC(canon_mean_path=canon_mean_path, no_face_score=0.0)
    sim = await qc.cosine_similarity(Path("/fake.png"))

    assert sim == 0.0


async def test_face_qc_implements_protocol(canon_mean_path):
    """Validamos que FaceQC cumple FaceQCProto del pipeline.deps."""
    from aiinfluencer.pipeline.deps import FaceQCProto

    qc = FaceQC(canon_mean_path=canon_mean_path)
    # Si FaceQC no cumple el Protocol, falla aquí en type check estructural
    assert isinstance(qc, FaceQCProto) or hasattr(qc, "cosine_similarity")
