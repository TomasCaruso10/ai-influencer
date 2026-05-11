"""CheckpointEvaluator — orquesta la eval de N checkpoints × M prompts × K seeds."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from aiinfluencer.eval.metrics import Metric
from aiinfluencer.eval.reports import EvalReport, ScoreRow

logger = logging.getLogger(__name__)


@runtime_checkable
class ImageGenerator(Protocol):
    """Genera una imagen dado un checkpoint + prompt + seed."""

    async def generate(self, checkpoint: Path, prompt: str, seed: int, output_dir: Path) -> Path:
        """Returns path local a la imagen generada."""
        ...


@dataclass
class DummyImageGenerator:
    """Genera archivos vacíos para tests."""

    async def generate(self, checkpoint: Path, prompt: str, seed: int, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{checkpoint.stem}_seed{seed}_{abs(hash(prompt)) % 10000}.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        return path


@dataclass
class EvalConfig:
    """Configuración de una corrida de eval."""

    checkpoints: list[Path]
    eval_prompts: list[str]
    seeds: list[int]
    output_dir: Path
    samples_subdir: str = "samples"

    def __post_init__(self) -> None:
        if not self.checkpoints:
            raise ValueError("checkpoints must not be empty")
        if not self.eval_prompts:
            raise ValueError("eval_prompts must not be empty")
        if not self.seeds:
            raise ValueError("seeds must not be empty")

    @property
    def samples_dir(self) -> Path:
        return self.output_dir / self.samples_subdir

    @property
    def total_samples(self) -> int:
        return len(self.checkpoints) * len(self.eval_prompts) * len(self.seeds)


@dataclass
class CheckpointEvaluator:
    """Evalúa checkpoints × prompts × seeds con un set de métricas.

    Args:
        metrics: lista de Metric implementations. Cada una se aplica a cada
                 imagen generada y produce un ScoreRow en el report.
        generator: ImageGenerator implementation.
        skip_existing: si True, no regenera samples cuyo output ya existe.
    """

    metrics: list[Metric]
    generator: ImageGenerator
    skip_existing: bool = True

    async def run(self, config: EvalConfig) -> EvalReport:
        report = EvalReport()
        config.samples_dir.mkdir(parents=True, exist_ok=True)

        total = config.total_samples
        processed = 0

        for checkpoint in config.checkpoints:
            for prompt in config.eval_prompts:
                for seed in config.seeds:
                    processed += 1
                    image_path = await self.generator.generate(
                        checkpoint=checkpoint,
                        prompt=prompt,
                        seed=seed,
                        output_dir=config.samples_dir,
                    )
                    logger.info(
                        "[%d/%d] %s seed=%d prompt=%s",
                        processed,
                        total,
                        checkpoint.stem,
                        seed,
                        prompt[:60],
                    )

                    context = {"prompt": prompt, "seed": seed, "checkpoint": str(checkpoint)}
                    for metric in self.metrics:
                        try:
                            score = await metric.score(image_path, context)
                        except Exception:
                            logger.exception("metric %s failed", metric.name)
                            score = float("nan")
                        report.add(
                            ScoreRow(
                                checkpoint=checkpoint.stem,
                                prompt=prompt,
                                seed=seed,
                                metric=metric.name,
                                score=score,
                                image_path=str(image_path.relative_to(config.output_dir))
                                if image_path.is_relative_to(config.output_dir)
                                else str(image_path),
                            )
                        )

        return report
