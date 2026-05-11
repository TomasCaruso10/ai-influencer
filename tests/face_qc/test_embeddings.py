"""Tests del módulo face_qc.embeddings.

InsightFace + opencv son optional deps (face-qc extra). Los tests mockean
ambos así corren en cualquier env sin instalar la stack ML pesada.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def _stub_cv2(monkeypatch):
    """Stub `cv2` en sys.modules para que el lazy import en embeddings.py
    no falle en sistemas sin opencv instalado."""
    fake_cv2 = SimpleNamespace(imread=lambda _: None)
    monkeypatch.setitem(sys.modules, "cv2", fake_cv2)
    yield fake_cv2


from aiinfluencer.face_qc.embeddings import (  # noqa: E402
    compute_canon_mean,
    embedding_for_image,
    load_canon_mean,
)
from aiinfluencer.face_qc.exceptions import NoFaceDetectedError  # noqa: E402


def _make_fake_face(emb: np.ndarray, bbox_w: float = 100, bbox_h: float = 100) -> MagicMock:
    face = MagicMock()
    face.normed_embedding = emb
    face.bbox = (0.0, 0.0, bbox_w, bbox_h)
    return face


@patch("aiinfluencer.face_qc.embeddings._get_face_analysis")
def test_embedding_for_image_returns_normalized(mock_app, _stub_cv2):
    _stub_cv2.imread = lambda _: np.zeros((512, 512, 3), dtype=np.uint8)
    fake_emb = np.random.randn(512).astype(np.float32)
    fake_emb /= np.linalg.norm(fake_emb)
    mock_app.return_value.get.return_value = [_make_fake_face(fake_emb)]

    out = embedding_for_image(Path("/fake/path.png"))

    assert out.shape == (512,)
    assert np.allclose(np.linalg.norm(out), 1.0, atol=1e-3)


@patch("aiinfluencer.face_qc.embeddings._get_face_analysis")
def test_embedding_picks_largest_face(mock_app, _stub_cv2):
    _stub_cv2.imread = lambda _: np.zeros((512, 512, 3), dtype=np.uint8)
    small_emb = np.ones(512, dtype=np.float32) / np.sqrt(512)
    large_emb = -np.ones(512, dtype=np.float32) / np.sqrt(512)
    mock_app.return_value.get.return_value = [
        _make_fake_face(small_emb, bbox_w=10, bbox_h=10),
        _make_fake_face(large_emb, bbox_w=200, bbox_h=200),
    ]

    out = embedding_for_image(Path("/fake/path.png"))

    np.testing.assert_array_almost_equal(out, large_emb)


@patch("aiinfluencer.face_qc.embeddings._get_face_analysis")
def test_embedding_raises_on_no_face(mock_app, _stub_cv2):
    _stub_cv2.imread = lambda _: np.zeros((512, 512, 3), dtype=np.uint8)
    mock_app.return_value.get.return_value = []

    with pytest.raises(NoFaceDetectedError):
        embedding_for_image(Path("/fake/path.png"))


def test_embedding_raises_on_unreadable_image(_stub_cv2):
    _stub_cv2.imread = lambda _: None

    with pytest.raises(NoFaceDetectedError, match="Cannot read"):
        embedding_for_image(Path("/fake/path.png"))


@patch("aiinfluencer.face_qc.embeddings.embedding_for_image")
def test_compute_canon_mean_averages_embeddings(mock_emb, tmp_path):
    for i in range(3):
        (tmp_path / f"img{i}.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    e1 = np.array([1.0, 0.0] + [0.0] * 510, dtype=np.float32)
    e2 = np.array([0.0, 1.0] + [0.0] * 510, dtype=np.float32)
    e3 = np.array([1.0, 0.0] + [0.0] * 510, dtype=np.float32)
    mock_emb.side_effect = [e1, e2, e3]

    mean = compute_canon_mean(tmp_path)

    assert mean.shape == (512,)
    assert np.allclose(np.linalg.norm(mean), 1.0, atol=1e-3)
    # Mean dirección debería pesar más al eje 0 (2 ejemplos) que al 1 (1 ejemplo)
    assert mean[0] > mean[1]


@patch("aiinfluencer.face_qc.embeddings.embedding_for_image")
def test_compute_canon_mean_skips_no_face(mock_emb, tmp_path):
    for i in range(3):
        (tmp_path / f"img{i}.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    good = np.array([1.0] + [0.0] * 511, dtype=np.float32)
    mock_emb.side_effect = [good, NoFaceDetectedError("no face"), good]

    mean = compute_canon_mean(tmp_path)

    assert mean.shape == (512,)
    np.testing.assert_array_almost_equal(mean, good)


def test_compute_canon_mean_empty_dir_raises(tmp_path):
    with pytest.raises(RuntimeError, match="No images found"):
        compute_canon_mean(tmp_path)


def test_load_canon_mean_valid(tmp_path):
    emb = np.zeros(512, dtype=np.float32)
    emb[0] = 1.0
    path = tmp_path / "mean.npy"
    np.save(path, emb)

    loaded = load_canon_mean(path)

    np.testing.assert_array_equal(loaded, emb)


def test_load_canon_mean_invalid_shape(tmp_path):
    bad = np.zeros(256, dtype=np.float32)
    path = tmp_path / "mean.npy"
    np.save(path, bad)

    with pytest.raises(ValueError, match="Expected shape"):
        load_canon_mean(path)


def test_load_canon_mean_not_normalized(tmp_path):
    bad = np.zeros(512, dtype=np.float32)
    bad[0] = 2.0
    path = tmp_path / "mean.npy"
    np.save(path, bad)

    with pytest.raises(ValueError, match="not L2-normalized"):
        load_canon_mean(path)
