"""Aplica humanization (grain + chromatic aberration + vignette) a un directorio de imágenes.

Uso:
    python scripts/humanize_batch.py \\
        --input outputs/v2_quality \\
        --output outputs/v2_quality_human \\
        --iso-grain 200 --aberration 2 --vignette 0.35
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aiinfluencer.post_process.humanization import HumanizationConfig, humanize


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--iso-grain", type=int, default=200, help="0=off, 100-800 range")
    ap.add_argument("--aberration", type=int, default=2, help="px shift, 0=off")
    ap.add_argument("--vignette", type=float, default=0.35, help="0..1, 0=off")
    args = ap.parse_args()

    config = HumanizationConfig(
        grain_iso=args.iso_grain,
        chromatic_aberration_px=float(args.aberration),
        vignette_strength=args.vignette,
    )

    args.output.mkdir(parents=True, exist_ok=True)
    images = sorted(p for p in args.input.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})

    if not images:
        print(f"ERROR: no images in {args.input}", file=sys.stderr)
        return 1

    print(f"Humanizing {len(images)} images: grain={args.iso_grain} aberration={args.aberration}px vignette={args.vignette}")
    for img in images:
        dst = args.output / img.name
        humanize(img, dst, config)
        print(f"  {img.name}")

    print(f"\nWrote {len(images)} humanized images to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
