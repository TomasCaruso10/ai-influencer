"""Tests de EvalReport: agregación + serialización."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from aiinfluencer.eval.reports import EvalReport, ScoreRow


def _make_report() -> EvalReport:
    r = EvalReport()
    # ckpt_a: face_sim mean 0.6, aesthetic mean 5.0
    r.add(ScoreRow("ckpt_a", "prompt1", 42, "face_similarity", 0.5))
    r.add(ScoreRow("ckpt_a", "prompt1", 43, "face_similarity", 0.7))
    r.add(ScoreRow("ckpt_a", "prompt1", 42, "aesthetic", 4.0))
    r.add(ScoreRow("ckpt_a", "prompt1", 43, "aesthetic", 6.0))
    # ckpt_b: face_sim mean 0.8, aesthetic mean 4.0
    r.add(ScoreRow("ckpt_b", "prompt1", 42, "face_similarity", 0.8))
    r.add(ScoreRow("ckpt_b", "prompt1", 43, "face_similarity", 0.8))
    r.add(ScoreRow("ckpt_b", "prompt1", 42, "aesthetic", 4.0))
    r.add(ScoreRow("ckpt_b", "prompt1", 43, "aesthetic", 4.0))
    return r


def test_mean_per_checkpoint_metric():
    report = _make_report()
    means = report.mean_per_checkpoint_metric()
    assert means[("ckpt_a", "face_similarity")] == 0.6
    assert means[("ckpt_a", "aesthetic")] == 5.0
    assert means[("ckpt_b", "face_similarity")] == 0.8
    assert means[("ckpt_b", "aesthetic")] == 4.0


def test_best_checkpoint_per_metric():
    report = _make_report()
    best = report.best_checkpoint_per_metric()
    assert best["face_similarity"] == ("ckpt_b", 0.8)
    assert best["aesthetic"] == ("ckpt_a", 5.0)


def test_weighted_overall_winner_default_weights():
    report = _make_report()
    # default: face_sim 0.5 + aesthetic 0.3 + clip 0.2
    # ckpt_a: (0.6*0.5 + 5.0*0.3) / 0.8 = (0.3 + 1.5) / 0.8 = 2.25
    # ckpt_b: (0.8*0.5 + 4.0*0.3) / 0.8 = (0.4 + 1.2) / 0.8 = 2.0
    # → ckpt_a gana
    winner = report.weighted_overall_winner()
    assert winner is not None
    ckpt, score = winner
    assert ckpt == "ckpt_a"


def test_weighted_overall_winner_custom_weights():
    report = _make_report()
    winner = report.weighted_overall_winner(weights={"face_similarity": 1.0})
    assert winner is not None
    ckpt, _ = winner
    assert ckpt == "ckpt_b"  # solo face_sim → ckpt_b gana (0.8 > 0.6)


def test_to_csv_writes_all_rows(tmp_path):
    report = _make_report()
    path = tmp_path / "report.csv"
    report.to_csv(path)

    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    assert rows[0] == ["checkpoint", "prompt", "seed", "metric", "score", "image"]
    assert len(rows) == 1 + len(report.rows)  # header + rows


def test_to_summary_json_contains_aggregations(tmp_path):
    report = _make_report()
    path = tmp_path / "summary.json"
    report.to_summary_json(path)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["total_rows"] == 8
    assert "mean_per_checkpoint_metric" in data
    assert "best_checkpoint_per_metric" in data
    assert data["best_checkpoint_per_metric"]["face_similarity"]["checkpoint"] == "ckpt_b"


def test_to_html_grid_writes_file(tmp_path):
    report = _make_report()
    path = tmp_path / "report.html"
    report.to_html_grid(path)

    content = path.read_text(encoding="utf-8")
    assert "<table" in content
    assert "ckpt_a" in content
    assert "ckpt_b" in content
    assert "face_similarity" in content


def test_empty_report_winner_returns_none():
    report = EvalReport()
    assert report.weighted_overall_winner() is None
