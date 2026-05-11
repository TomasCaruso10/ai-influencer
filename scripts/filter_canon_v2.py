"""Filtra dataset canon usando InsightFace para detectar outliers.

Algoritmo:
1. Compute embedding per imagen
2. Compute centroid (media de embeddings)
3. Compute cos similarity de cada imagen vs centroid
4. Sortear por similarity descending
5. Keep top N (default 30)
6. Output: copia los kept a `output_dir`

Para correr en pod después de bajar el dataset original. Local Windows no
sirve por insightface dep.

Uso:
    python scripts/filter_canon_v2.py \\
        --input /workspace/datasets/aiinfluencer1 \\
        --output /workspace/datasets/aiinfluencer1_v2 \\
        --keep 30
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--keep", type=int, default=30)
    args = ap.parse_args()

    from aiinfluencer.face_qc import embedding_for_image
    from aiinfluencer.face_qc.exceptions import NoFaceDetectedError

    images = sorted(p for p in args.input.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if not images:
        print(f"ERROR: no images in {args.input}", file=sys.stderr)
        return 1

    print(f"Computing embeddings for {len(images)} images...")
    embs: dict[Path, np.ndarray] = {}
    for img in images:
        try:
            embs[img] = embedding_for_image(img)
        except NoFaceDetectedError as exc:
            print(f"  skip (no face): {img.name}: {exc}")

    if not embs:
        print("ERROR: no embeddings extracted", file=sys.stderr)
        return 2

    # Centroid normalized
    stack = np.stack(list(embs.values()))
    centroid = stack.mean(axis=0)
    centroid /= np.linalg.norm(centroid)

    # Score per image vs centroid
    scored: list[tuple[Path, float]] = []
    for path, emb in embs.items():
        scored.append((path, float(np.dot(emb, centroid))))
    scored.sort(key=lambda x: x[1], reverse=True)

    keep = scored[: args.keep]
    args.output.mkdir(parents=True, exist_ok=True)

    print(f"\nKept top {len(keep)}/{len(embs)} (sim vs centroid):")
    for path, score in keep:
        dst = args.output / path.name
        shutil.copy2(path, dst)
        # Copy caption .txt si existe
        caption = path.with_suffix(".txt")
        if caption.exists():
            shutil.copy2(caption, args.output / caption.name)
        print(f"  {score:.4f}  {path.name}")

    if len(scored) > len(keep):
        print(f"\nDiscarded {len(scored) - len(keep)} below cutoff:")
        for path, score in scored[len(keep) :][:5]:
            print(f"  {score:.4f}  {path.name}")
        if len(scored) > len(keep) + 5:
            print(f"  ... and {len(scored) - len(keep) - 5} more")

    print(f"\nWrote canon v2 to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
