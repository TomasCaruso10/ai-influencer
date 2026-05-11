"""Humanization pass — hace que el output AI parezca más foto real.

Aplica:
- Grain ISO 400-800 (simula sensor noise)
- Chromatic aberration sutil (color fringing en bordes)
- Vignetting sutil (oscurece esquinas)
- Variación aleatoria de JPEG quality para evitar fingerprint per-pieza

Decisión del audit: NO strippamos C2PA. Solo agregamos imperfecciones humanas
sobre el output para que estéticamente parezca foto real, manteniendo el
disclosure metadata intacto.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
import numpy as np


@dataclass
class HumanizationConfig:
    """Parámetros del pipeline de humanization.

    Valores default son punto medio razonable de la literatura. Ajustar
    individualmente para A/B testing del feed.
    """

    grain_iso: int = 600
    """Intensidad del grain. 400-800 normal, 1200+ obvio."""

    chromatic_aberration_px: float = 0.6
    """Offset RGB en pixels para fringing. 0.5-1.5 sutil, >2 obvio."""

    vignette_strength: float = 0.18
    """0-1, oscurecimiento esquinas. 0.15-0.25 sutil."""

    jpeg_quality_min: int = 88
    jpeg_quality_max: int = 94
    """Variación aleatoria del JPEG quality para variar fingerprint per-pieza."""

    seed: int | None = None
    """Si None, random verdadero. Si set, reproducible."""


def _add_grain(img: Image.Image, iso: int, rng: random.Random) -> Image.Image:
    """Agrega Gaussian noise simulando sensor grain."""
    arr = np.asarray(img, dtype=np.int16)
    # ISO 100 → sigma ~3, ISO 800 → sigma ~12 (rough mapping)
    sigma = max(2.0, iso / 65.0)
    np_rng = np.random.default_rng(rng.getrandbits(64))
    noise = np_rng.normal(0, sigma, arr.shape).astype(np.int16)
    out = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def _add_chromatic_aberration(img: Image.Image, offset_px: float) -> Image.Image:
    """Shift los canales R y B levemente en direcciones opuestas."""
    if offset_px <= 0:
        return img
    rgb = img.convert("RGB").split()
    r, g, b = rgb
    o = int(round(offset_px))
    if o == 0:
        return img
    # Desplazar R hacia derecha, B hacia izquierda
    r_shifted = Image.new("L", img.size, 0)
    r_shifted.paste(r, (o, 0))
    b_shifted = Image.new("L", img.size, 0)
    b_shifted.paste(b, (-o, 0))
    return Image.merge("RGB", (r_shifted, g, b_shifted))


def _add_vignette(img: Image.Image, strength: float) -> Image.Image:
    """Oscurece esquinas con un radial gradient (centro claro → bordes oscuros)."""
    if strength <= 0:
        return img
    w, h = img.size
    cx, cy = w / 2.0, h / 2.0
    max_dist = float(np.sqrt(cx**2 + cy**2))

    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    # mask: 1.0 en centro, (1 - strength) en esquinas
    mask = 1.0 - (dist / max_dist) * strength
    mask = np.clip(mask, 0.0, 1.0).astype(np.float32)

    rgb = img.convert("RGB")
    arr = np.asarray(rgb, dtype=np.float32)
    out = (arr * mask[..., None]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out)


def humanize(
    input_path: Path,
    output_path: Path,
    config: HumanizationConfig | None = None,
) -> Path:
    """Aplica humanization pass sobre `input_path`, escribe a `output_path`.

    Returns: output_path. Output siempre JPEG con quality variable.
    """
    cfg = config or HumanizationConfig()
    rng = random.Random(cfg.seed)

    img = Image.open(input_path).convert("RGB")
    img = _add_grain(img, cfg.grain_iso, rng)
    img = _add_chromatic_aberration(img, cfg.chromatic_aberration_px)
    img = _add_vignette(img, cfg.vignette_strength)

    quality = rng.randint(cfg.jpeg_quality_min, cfg.jpeg_quality_max)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "JPEG", quality=quality, optimize=True)
    return output_path
