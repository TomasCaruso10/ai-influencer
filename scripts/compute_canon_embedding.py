"""Compute mean embedding del canon dataset.

Uso:
    python scripts/compute_canon_embedding.py \
        --canon-dir outputs/canon \
        --output outputs/canon/_mean_embedding.npy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from aiinfluencer.face_qc import compute_canon_mean


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon-dir", type=Path, default=Path("outputs/canon"))
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/canon/_mean_embedding.npy"),
    )
    args = ap.parse_args()

    if not args.canon_dir.exists():
        print(f"ERROR: canon dir does not exist: {args.canon_dir}", file=sys.stderr)
        return 1

    print(f"Computing canon mean from {args.canon_dir}...")
    mean = compute_canon_mean(args.canon_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.output, mean)
    norm = float(np.linalg.norm(mean))
    print(f"Saved {args.output} (shape={mean.shape}, norm={norm:.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
