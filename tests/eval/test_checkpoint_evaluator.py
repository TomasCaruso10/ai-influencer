"""Tests de CheckpointEvaluator. Mockean generador + métricas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from aiinfluencer.eval import CheckpointEvaluator, DummyMetric, EvalConfig
from aiinfluencer.eval.checkpoint_evaluator import (
    DummyImageGenerator,
    ImageGenerator,
)
from aiinfluencer.eval.reports import EvalReport


@dataclass
class _CountingGenerator:
    """Genera path único + cuenta llamadas."""

    call_count: int = 0

    async def generate(self, checkpoint: Path, prompt: str, seed: int, output_dir: Path) -> Path:
        self.call_count += 1
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{checkpoint.stem}_{seed}_{self.call_count}.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        return path


def test_eval_config_total_samples():
    config = EvalConfig(
        checkpoints=[Path("a.safetensors"), Path("b.safetensors")],
        eval_prompts=["p1", "p2"],
        seeds=[42, 43, 44],
        output_dir=Path("/tmp/eval"),
    )
    assert config.total_samples == 2 * 2 * 3


def test_eval_config_empty_inputs_raise():
    with pytest.raises(ValueError):
        EvalConfig(
            checkpoints=[],
            eval_prompts=["p"],
            seeds=[1],
            output_dir=Path("/tmp"),
        )
    with pytest.raises(ValueError):
        EvalConfig(
            checkpoints=[Path("a")],
            eval_prompts=[],
            seeds=[1],
            output_dir=Path("/tmp"),
        )
    with pytest.raises(ValueError):
        EvalConfig(
            checkpoints=[Path("a")],
            eval_prompts=["p"],
            seeds=[],
            output_dir=Path("/tmp"),
        )


async def test_evaluator_iterates_full_grid(tmp_path):
    """4 checkpoints × 2 prompts × 3 seeds × 1 metric = 24 rows."""
    config = EvalConfig(
        checkpoints=[tmp_path / f"ckpt_{i}.safetensors" for i in range(4)],
        eval_prompts=["prompt1", "prompt2"],
        seeds=[42, 43, 44],
        output_dir=tmp_path / "eval_out",
    )
    generator = _CountingGenerator()
    metrics = [DummyMetric(constant_score=0.5)]

    evaluator = CheckpointEvaluator(metrics=metrics, generator=generator)
    report = await evaluator.run(config)

    assert generator.call_count == 24
    assert len(report.rows) == 24
    assert all(r.score == 0.5 for r in report.rows)


async def test_evaluator_multiple_metrics_per_image(tmp_path):
    """2 métricas × 2 ckpt × 1 prompt × 1 seed = 4 rows (1 imagen × 2 metrics × 2 ckpts)."""
    config = EvalConfig(
        checkpoints=[tmp_path / "a.safetensors", tmp_path / "b.safetensors"],
        eval_prompts=["only_prompt"],
        seeds=[42],
        output_dir=tmp_path / "eval_out",
    )
    metrics = [
        DummyMetric(name="m1", constant_score=0.7),
        DummyMetric(name="m2", constant_score=0.4),
    ]

    evaluator = CheckpointEvaluator(metrics=metrics, generator=DummyImageGenerator())
    report = await evaluator.run(config)

    assert len(report.rows) == 4
    score_by_metric = {r.metric for r in report.rows}
    assert score_by_metric == {"m1", "m2"}


async def test_evaluator_failing_metric_records_nan(tmp_path):
    """Si una metric tira, se loggea NaN y sigue."""

    @dataclass
    class FailingMetric:
        name: str = "failing"

        async def score(self, image_path: Path, context: dict) -> float:
            raise RuntimeError("boom")

    config = EvalConfig(
        checkpoints=[tmp_path / "a.safetensors"],
        eval_prompts=["p"],
        seeds=[42],
        output_dir=tmp_path / "eval",
    )
    evaluator = CheckpointEvaluator(metrics=[FailingMetric()], generator=DummyImageGenerator())
    report = await evaluator.run(config)

    import math
    assert len(report.rows) == 1
    assert math.isnan(report.rows[0].score)


def test_dummy_image_generator_implements_protocol():
    gen = DummyImageGenerator()
    assert isinstance(gen, ImageGenerator)
