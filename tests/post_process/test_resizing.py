"""Tests del módulo post_process.resizing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from aiinfluencer.post_process.resizing import Channel, resize_for_channel


@pytest.fixture
def square_2k(tmp_path) -> Path:
    arr = np.zeros((2048, 2048, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    path = tmp_path / "src.png"
    img.save(path)
    return path


@pytest.mark.parametrize(
    "channel,expected",
    [
        (Channel.IG_FEED_SQUARE, (1080, 1080)),
        (Channel.IG_FEED_PORTRAIT, (1080, 1350)),
        (Channel.REELS_TIKTOK, (1080, 1920)),
        (Channel.TWITTER, (1200, 675)),
    ],
)
def test_resize_target_dimensions(square_2k, tmp_path, channel, expected):
    out = tmp_path / f"{channel}.jpg"
    resize_for_channel(square_2k, out, channel)
    img = Image.open(out)
    assert img.size == expected


def test_resize_writes_jpeg(square_2k, tmp_path):
    out = tmp_path / "out.jpg"
    resize_for_channel(square_2k, out, Channel.IG_FEED_SQUARE)
    assert out.exists()
    img = Image.open(out)
    assert img.format == "JPEG"
