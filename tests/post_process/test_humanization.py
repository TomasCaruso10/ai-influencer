"""Tests del módulo post_process.humanization."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from aiinfluencer.post_process.humanization import (
    HumanizationConfig,
    _add_chromatic_aberration,
    _add_grain,
    _add_vignette,
    humanize,
)


@pytest.fixture
def sample_image(tmp_path) -> Path:
    """Crea una imagen sólida gris media (RGB 128,128,128) 256x256."""
    arr = np.full((256, 256, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)
    path = tmp_path / "sample.png"
    img.save(path)
    return path


def test_humanize_writes_output(sample_image, tmp_path):
    out = tmp_path / "humanized.jpg"
    result = humanize(sample_image, out, HumanizationConfig(seed=42))

    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_humanize_output_is_jpeg(sample_image, tmp_path):
    out = tmp_path / "humanized.jpg"
    humanize(sample_image, out, HumanizationConfig(seed=42))
    img = Image.open(out)
    assert img.format == "JPEG"
    assert img.size == (256, 256)


def test_humanize_reproducible_with_seed(sample_image, tmp_path):
    """Mismo seed → mismos bytes en output."""
    out1 = tmp_path / "a.jpg"
    out2 = tmp_path / "b.jpg"
    cfg = HumanizationConfig(seed=42)
    humanize(sample_image, out1, cfg)
    humanize(sample_image, out2, cfg)
    assert out1.read_bytes() == out2.read_bytes()


def test_humanize_different_seeds_differ(sample_image, tmp_path):
    out1 = tmp_path / "a.jpg"
    out2 = tmp_path / "b.jpg"
    humanize(sample_image, out1, HumanizationConfig(seed=1))
    humanize(sample_image, out2, HumanizationConfig(seed=2))
    assert out1.read_bytes() != out2.read_bytes()


def test_add_grain_changes_image():
    """Grain debería cambiar pixels respecto a uniform gray."""
    import random
    arr = np.full((64, 64, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)
    out = _add_grain(img, iso=800, rng=random.Random(42))
    out_arr = np.asarray(out)
    # Al menos algunos pixels cambiaron
    assert not np.array_equal(arr, out_arr)
    # Pero no demasiado (mean cerca de 128)
    assert 120 <= out_arr.mean() <= 136


def test_chromatic_aberration_zero_offset_noop():
    arr = np.full((32, 32, 3), 200, dtype=np.uint8)
    img = Image.fromarray(arr)
    out = _add_chromatic_aberration(img, offset_px=0)
    np.testing.assert_array_equal(np.asarray(out), arr)


def test_vignette_zero_strength_noop():
    arr = np.full((32, 32, 3), 200, dtype=np.uint8)
    img = Image.fromarray(arr)
    out = _add_vignette(img, strength=0)
    np.testing.assert_array_equal(np.asarray(out), arr)


def test_vignette_darkens_corners():
    """Con strength > 0, esquinas deberían ser más oscuras que el centro."""
    arr = np.full((128, 128, 3), 200, dtype=np.uint8)
    img = Image.fromarray(arr)
    out = _add_vignette(img, strength=0.5)
    out_arr = np.asarray(out)
    # Center pixel debería ser cercano a 200
    # Corner debería ser más oscuro
    center = out_arr[64, 64, 0]
    corner = out_arr[0, 0, 0]
    assert corner < center
