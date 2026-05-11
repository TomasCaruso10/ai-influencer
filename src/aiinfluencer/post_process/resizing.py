"""Resize a aspect ratios target por canal de distribución.

Aspect ratios standard 2026:
- Instagram feed cuadrado: 1080x1080 (1:1)
- Instagram feed portrait: 1080x1350 (4:5) — máximo crop vertical IG
- Stories / Reels / TikTok: 1080x1920 (9:16)
- Twitter / X: 1200x675 (16:9)
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from PIL import Image


class Channel(StrEnum):
    IG_FEED_SQUARE = "ig_feed_square"
    IG_FEED_PORTRAIT = "ig_feed_portrait"
    REELS_TIKTOK = "reels_tiktok"
    TWITTER = "twitter"


_DIMENSIONS: dict[Channel, tuple[int, int]] = {
    Channel.IG_FEED_SQUARE: (1080, 1080),
    Channel.IG_FEED_PORTRAIT: (1080, 1350),
    Channel.REELS_TIKTOK: (1080, 1920),
    Channel.TWITTER: (1200, 675),
}


def resize_for_channel(
    input_path: Path,
    output_path: Path,
    channel: Channel,
    quality: int = 92,
) -> Path:
    """Resize + crop center a las dimensiones del canal target.

    Strategy: scale al menor de width/height match + center crop al exacto.
    Evita distortion y mantiene el sujeto centrado.
    """
    target_w, target_h = _DIMENSIONS[channel]

    img = Image.open(input_path).convert("RGB")
    src_w, src_h = img.size

    # Calcular escala para que tape el target
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Center crop al exacto
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "JPEG", quality=quality, optimize=True)
    return output_path
