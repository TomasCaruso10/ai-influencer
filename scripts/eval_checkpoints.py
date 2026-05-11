"""Eval batch de checkpoints LoRA.

Uso:
    python scripts/eval_checkpoints.py \\
        --checkpoints-dir /workspace/loras \\
        --pattern "aiinfluencer1_sdxl-step*.safetensors" \\
        --eval-prompts prompts/eval_prompts.txt \\
        --seeds 42,43,44 \\
        --canon-mean outputs/canon/_mean_embedding.npy \\
        --output-dir outputs/eval_v1 \\
        --base-url http://127.0.0.1:8188

Output:
    outputs/eval_v1/samples/   → todas las imgs generadas
    outputs/eval_v1/report.csv → raw data
    outputs/eval_v1/summary.json → aggregations
    outputs/eval_v1/report.html → grid visual
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from aiinfluencer.eval import (
    CheckpointEvaluator,
    DummyMetric,
    EvalConfig,
    FaceSimilarityMetric,
)
from aiinfluencer.eval.checkpoint_evaluator import DummyImageGenerator


def _load_prompts(path: Path) -> list[str]:
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


async def main_async(args: argparse.Namespace) -> int:
    checkpoints = sorted(args.checkpoints_dir.glob(args.pattern))
    if not checkpoints:
        print(f"ERROR: no checkpoints match {args.pattern} in {args.checkpoints_dir}", file=sys.stderr)
        return 1

    prompts = _load_prompts(args.eval_prompts) if args.eval_prompts else [
        "aiinfluencer1, portrait close-up, soft natural lighting",
        "aiinfluencer1, full body at a cafe, casual outfit",
        "aiinfluencer1, gym selfie, athletic wear",
        "aiinfluencer1, at the beach, summer outfit",
    ]
    seeds = [int(s) for s in args.seeds.split(",")]

    config = EvalConfig(
        checkpoints=checkpoints,
        eval_prompts=prompts,
        seeds=seeds,
        output_dir=args.output_dir,
    )

    metrics = []
    if args.canon_mean and args.canon_mean.exists():
        metrics.append(FaceSimilarityMetric(canon_mean_path=args.canon_mean))
    if not metrics:
        print("WARNING: no metrics enabled (canon-mean missing). Using dummy.", file=sys.stderr)
        metrics.append(DummyMetric())

    # Generator: DummyImageGenerator por default (validación del framework).
    # Para integración con ComfyUI real, hay que implementar un adapter aparte.
    generator = DummyImageGenerator()

    evaluator = CheckpointEvaluator(metrics=metrics, generator=generator)
    print(f"Evaluating {len(checkpoints)} checkpoints × {len(prompts)} prompts × {len(seeds)} seeds = {config.total_samples} samples")
    report = await evaluator.run(config)

    report.to_csv(args.output_dir / "report.csv")
    report.to_summary_json(args.output_dir / "summary.json")
    report.to_html_grid(args.output_dir / "report.html")

    print()
    print(f"=== Best per metric ===")
    for metric, (ckpt, score) in report.best_checkpoint_per_metric().items():
        print(f"  {metric}: {ckpt} ({score:.4f})")
    winner = report.weighted_overall_winner()
    if winner:
        print(f"\nWeighted winner: {winner[0]} ({winner[1]:.4f})")
    print(f"\nOutputs: {args.output_dir}")
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoints-dir", type=Path, required=True)
    ap.add_argument("--pattern", type=str, default="*.safetensors")
    ap.add_argument("--eval-prompts", type=Path, default=None)
    ap.add_argument("--seeds", type=str, default="42")
    ap.add_argument("--canon-mean", type=Path, default=Path("outputs/canon/_mean_embedding.npy"))
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/eval_v1"))
    ap.add_argument("--base-url", type=str, default="http://127.0.0.1:8188")
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
