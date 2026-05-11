"""Tests de los safety classifiers wrappers. Mock de transformers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from aiinfluencer.compliance.classifiers import HuggingFaceSafetyClassifiers


@pytest.fixture
def classifiers():
    return HuggingFaceSafetyClassifiers()


@pytest.fixture
def fake_image(tmp_path) -> Path:
    """PNG real chico, leíble por PIL."""
    path = tmp_path / "img.png"
    Image.new("RGB", (32, 32), color=(128, 128, 128)).save(path)
    return path


@patch("aiinfluencer.compliance.classifiers.HuggingFaceSafetyClassifiers._ensure_age_loaded")
async def test_age_classify_adult(_mock_load, classifiers, fake_image):
    """Bucket "20-29" → is_adult=True."""
    classifiers._age_pipe = MagicMock(return_value=[
        {"label": "20-29", "score": 0.85},
        {"label": "30-39", "score": 0.10},
        {"label": "10-19", "score": 0.05},
    ])
    result = await classifiers.age_classify(fake_image)
    assert result["bucket"] == "20-29"
    assert result["is_adult"] is True
    assert result["confidence"] == pytest.approx(0.85)


@patch("aiinfluencer.compliance.classifiers.HuggingFaceSafetyClassifiers._ensure_age_loaded")
async def test_age_classify_minor(_mock_load, classifiers, fake_image):
    """Bucket "10-19" → is_adult=False."""
    classifiers._age_pipe = MagicMock(return_value=[
        {"label": "10-19", "score": 0.7},
        {"label": "20-29", "score": 0.3},
    ])
    result = await classifiers.age_classify(fake_image)
    assert result["is_adult"] is False


@patch("aiinfluencer.compliance.classifiers.HuggingFaceSafetyClassifiers._ensure_nsfw_loaded")
async def test_nsfw_classify_returns_score(_mock_load, classifiers, fake_image):
    classifiers._nsfw_pipe = MagicMock(return_value=[
        {"label": "nsfw", "score": 0.92},
        {"label": "safe", "score": 0.08},
    ])
    score = await classifiers.nsfw_classify(fake_image)
    assert score == pytest.approx(0.92)


async def test_q16_placeholder_returns_false(classifiers, fake_image):
    result = await classifiers.q16_classify(fake_image)
    assert result is False
