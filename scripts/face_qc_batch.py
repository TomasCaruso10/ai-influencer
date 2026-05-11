"""Batch face QC sobre un directorio de outputs.

Compara cada imagen vs canon mean, exporta CSV + summary.

Uso:
    python scripts/face_qc_batch.py \
        --canon-mean outputs/canon/_mean_embedding.npy \
        --inputs outputs/lora_final_test \
        --threshold 0.45 \
        --output-csv outputs/face_qc_report.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from aiinfluencer.face_qc import FaceQC, embedding_for_image, load_canon_mean
from aiinfluencer.face_qc.exceptions import NoFaceDetectedError
import numpy as np

IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canon-mean", type=Path, required=True)
    ap.add_argument("--inputs", type=Path, required=True, help="Dir con imágenes a evaluar")
    ap.add_argument("--threshold", type=float, default=0.45)
    ap.add_argument("--output-csv", type=Path, default=Path("outputs/face_qc_report.csv"))
    args = ap.parse_args()

    canon_mean = load_canon_mean(args.canon_mean)
    images = sorted(p for p in args.inputs.iterdir() if p.suffix.lower() in IMG_EXTS)

    if not images:
        print(f"ERROR: no images in {args.inputs}", file=sys.stderr)
        return 1

    rows: list[dict] = []
    passes = 0
    failures = 0
    no_face = 0
    for img in images:
        try:
            emb = embedding_for_image(img)
            sim = float(np.dot(emb, canon_mean))
            verdict = "PASS" if sim >= args.threshold else "FAIL"
            if verdict == "PASS":
                passes += 1
            else:
                failures += 1
        except NoFaceDetectedError:
            sim = 0.0
            verdict = "NO_FACE"
            no_face += 1
        rows.append({
            "filename": img.name,
            "cos_similarity": f"{sim:.4f}",
            "threshold": args.threshold,
            "verdict": verdict,
        })
        print(f"{verdict:8} {sim:.4f}  {img.name}")

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "cos_similarity", "threshold", "verdict"])
        writer.writeheader()
        writer.writerows(rows)

    total = len(images)
    pct = 100.0 * passes / total if total else 0.0
    print()
    print(f"=== Summary ===")
    print(f"Total:    {total}")
    print(f"Pass:     {passes} ({pct:.1f}%)")
    print(f"Fail:     {failures}")
    print(f"No face:  {no_face}")
    print(f"Report:   {args.output_csv}")
    return 0 if failures == 0 and no_face == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
