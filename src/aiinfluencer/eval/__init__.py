"""Quality eval framework para LoRAs.

Quick reference:
    from aiinfluencer.eval import CheckpointEvaluator, EvalConfig, FaceSimilarityMetric

    metrics = [FaceSimilarityMetric(canon_mean_path="canon/_mean.npy")]
    evaluator = CheckpointEvaluator(metrics=metrics, generator=comfy_gen)
    config = EvalConfig(
        checkpoints=[Path("loras/v1_step_500.safetensors"), ...],
        eval_prompts=["aiinfluencer1 portrait", ...],
        seeds=[42, 43, 44],
        output_dir=Path("outputs/eval_v1"),
    )
    report = await evaluator.run(config)
    report.to_csv(config.output_dir / "report.csv")
"""

from aiinfluencer.eval.checkpoint_evaluator import CheckpointEvaluator, EvalConfig
from aiinfluencer.eval.metrics import (
    DummyMetric,
    FaceSimilarityMetric,
    Metric,
)
from aiinfluencer.eval.reports import EvalReport, ScoreRow

__all__ = [
    "CheckpointEvaluator",
    "EvalConfig",
    "EvalReport",
    "ScoreRow",
    "Metric",
    "DummyMetric",
    "FaceSimilarityMetric",
]
