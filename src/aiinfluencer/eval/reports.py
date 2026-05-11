"""Eval reports: agregación + serialización a CSV/HTML."""

from __future__ import annotations

import csv
import html
import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ScoreRow:
    """Una fila del eval report: (checkpoint, prompt, seed, metric) → score."""

    checkpoint: str  # nombre del checkpoint (sin path)
    prompt: str
    seed: int
    metric: str
    score: float
    image_path: str | None = None  # ref a la img generada (relative path)


@dataclass
class EvalReport:
    """Resultado del eval. Lista de scores + métodos de agregación."""

    rows: list[ScoreRow] = field(default_factory=list)

    def add(self, row: ScoreRow) -> None:
        self.rows.append(row)

    def add_many(self, rows: Iterable[ScoreRow]) -> None:
        self.rows.extend(rows)

    # ─── Aggregations ─────────────────────────────────────────────────────

    def mean_per_checkpoint_metric(self) -> dict[tuple[str, str], float]:
        """Returns dict (checkpoint, metric) → mean score."""
        bucket: dict[tuple[str, str], list[float]] = defaultdict(list)
        for r in self.rows:
            bucket[(r.checkpoint, r.metric)].append(r.score)
        return {key: statistics.mean(scores) for key, scores in bucket.items()}

    def best_checkpoint_per_metric(self) -> dict[str, tuple[str, float]]:
        """Returns dict metric → (best_checkpoint, score)."""
        means = self.mean_per_checkpoint_metric()
        per_metric: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for (ckpt, metric), score in means.items():
            per_metric[metric].append((ckpt, score))
        return {
            metric: max(items, key=lambda x: x[1]) for metric, items in per_metric.items()
        }

    def weighted_overall_winner(
        self, weights: dict[str, float] | None = None
    ) -> tuple[str, float] | None:
        """Combina métricas con pesos. Default: face_sim 0.5 + aesthetic 0.3 + clip 0.2.

        Returns (best_checkpoint, weighted_score) o None si no hay rows.
        """
        if not self.rows:
            return None
        weights = weights or {"face_similarity": 0.5, "aesthetic": 0.3, "clip_adherence": 0.2}
        means = self.mean_per_checkpoint_metric()
        per_ckpt: dict[str, float] = defaultdict(float)
        weight_sum: dict[str, float] = defaultdict(float)
        for (ckpt, metric), score in means.items():
            w = weights.get(metric, 0.0)
            if w <= 0.0:
                continue
            per_ckpt[ckpt] += score * w
            weight_sum[ckpt] += w
        if not per_ckpt:
            return None
        normalized = {ckpt: total / weight_sum[ckpt] for ckpt, total in per_ckpt.items()}
        winner = max(normalized.items(), key=lambda x: x[1])
        return winner

    # ─── Serialization ────────────────────────────────────────────────────

    def to_csv(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["checkpoint", "prompt", "seed", "metric", "score", "image"])
            for r in self.rows:
                writer.writerow([
                    r.checkpoint,
                    r.prompt,
                    r.seed,
                    r.metric,
                    f"{r.score:.4f}",
                    r.image_path or "",
                ])

    def to_summary_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        summary = {
            "total_rows": len(self.rows),
            "mean_per_checkpoint_metric": {
                f"{ckpt}|{metric}": round(score, 4)
                for (ckpt, metric), score in self.mean_per_checkpoint_metric().items()
            },
            "best_checkpoint_per_metric": {
                metric: {"checkpoint": ckpt, "score": round(score, 4)}
                for metric, (ckpt, score) in self.best_checkpoint_per_metric().items()
            },
        }
        winner = self.weighted_overall_winner()
        if winner is not None:
            summary["weighted_overall_winner"] = {
                "checkpoint": winner[0],
                "score": round(winner[1], 4),
            }
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def to_html_grid(self, path: Path, image_base_dir: Path | None = None) -> None:
        """HTML report con scores + thumbnails. `image_base_dir` para resolver paths."""
        path.parent.mkdir(parents=True, exist_ok=True)
        means = self.mean_per_checkpoint_metric()
        checkpoints = sorted({ckpt for (ckpt, _) in means.keys()})
        metrics = sorted({metric for (_, metric) in means.keys()})

        rows_html = []
        for ckpt in checkpoints:
            cells = [f"<td>{html.escape(ckpt)}</td>"]
            for m in metrics:
                score = means.get((ckpt, m))
                cell = f"{score:.3f}" if score is not None else "—"
                cells.append(f"<td>{cell}</td>")
            rows_html.append("<tr>" + "".join(cells) + "</tr>")

        winner = self.weighted_overall_winner()
        winner_text = (
            f"<p><strong>Weighted winner:</strong> {html.escape(winner[0])} ({winner[1]:.4f})</p>"
            if winner
            else ""
        )

        header_cells = "".join(f"<th>{html.escape(m)}</th>" for m in metrics)
        table = (
            "<table border='1' cellpadding='6' cellspacing='0'>"
            f"<thead><tr><th>checkpoint</th>{header_cells}</tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody>"
            "</table>"
        )
        document = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>Eval Report</title>"
            "<style>body{font-family:sans-serif;padding:1em} td,th{text-align:left}</style>"
            "</head><body>"
            f"<h1>Eval Report — {len(self.rows)} rows</h1>"
            f"{winner_text}{table}"
            "</body></html>"
        )
        path.write_text(document, encoding="utf-8")
