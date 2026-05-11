"""Tests del block list pediátrico."""

from __future__ import annotations

import pytest

from aiinfluencer.compliance.block_list import (
    PEDIATRIC_KEYWORDS,
    contains_blocked_keyword,
    is_lora_filename_safe,
)


@pytest.mark.parametrize(
    "text",
    [
        "child",
        "CHILD",
        "young girl",
        "schoolgirl",
        "this prompt contains a teen which is bad",
        "loli aesthetic",
    ],
)
def test_contains_blocked_keyword_detects(text):
    assert contains_blocked_keyword(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        "adult woman, 25 years old, mature features",
        "young adult, fresh face, 22 years",
        "italian woman portrait",
        "",
        None,
    ],
)
def test_contains_blocked_keyword_clean(text):
    assert contains_blocked_keyword(text or "") is None


def test_is_lora_filename_safe():
    assert is_lora_filename_safe("aiinfluencer1_flux.safetensors") is True
    assert is_lora_filename_safe("loli_anime_v3.safetensors") is False
    assert is_lora_filename_safe("schoolgirl_outfit.safetensors") is False


def test_pediatric_keywords_non_empty():
    """Sanity: la lista no se vacía por accidente."""
    assert len(PEDIATRIC_KEYWORDS) > 20
    assert "child" in PEDIATRIC_KEYWORDS
    assert "loli" in PEDIATRIC_KEYWORDS
