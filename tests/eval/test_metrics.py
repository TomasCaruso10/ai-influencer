"""Tests del módulo eval.metrics."""

from __future__ import annotations

from pathlib import Path

import pytest

from aiinfluencer.eval.metrics import DummyMetric, Metric


async def test_dummy_metric_returns_constant():
    metric = DummyMetric(constant_score=0.42)
    score = await metric.score(Path("/fake.png"), {})
    assert score == 0.42


def test_dummy_metric_implements_protocol():
    metric = DummyMetric()
    assert isinstance(metric, Metric)
    assert metric.name == "dummy"


def test_metric_name_unique_per_implementation(tmp_path):
    """Convención: name único para evitar colisiones en aggregations."""
    from aiinfluencer.eval.metrics import (
        AestheticMetric,
        CLIPPromptAdherenceMetric,
        FaceSimilarityMetric,
    )
    import numpy as np

    mean_path = tmp_path / "_mean.npy"
    mean = np.zeros(512, dtype=np.float32)
    mean[0] = 1.0
    np.save(mean_path, mean)

    face_metric = FaceSimilarityMetric(canon_mean_path=mean_path)
    aest = AestheticMetric()
    clip = CLIPPromptAdherenceMetric()
    names = {face_metric.name, aest.name, clip.name}
    assert len(names) == 3
