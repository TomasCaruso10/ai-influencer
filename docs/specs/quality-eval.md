# Spec — Bloque 2.3 Quality Eval Automatizado

> Eval framework para LoRAs: dado N checkpoints, genera samples con prompts fijos, calcula métricas y emite tabla comparativa. Resuelve "entrené 3h a ciegas".
>
> Source: `docs/state-of-the-art-audit.md` Gap 2.

## Objetivo

Reemplazar "ojo humano mirando samples del trainer" por métricas numéricas comparables checkpoint-vs-checkpoint. El sweet spot del LoRA queda determinado por la tabla, no por adivinanza.

## Componentes

### 1. Python package `aiinfluencer.eval`

```
src/aiinfluencer/eval/
├── __init__.py
├── metrics.py             # Protocols + helpers (sin deps ML pesadas)
├── checkpoint_evaluator.py # Core eval loop
└── reports.py             # CSV + HTML grid output
```

**API**:
```python
from aiinfluencer.eval import CheckpointEvaluator, EvalConfig

evaluator = CheckpointEvaluator(
    metrics=[face_qc, aesthetic, clip_adherence],  # implementations
    image_generator=comfy_generator,                # generates samples
)

config = EvalConfig(
    checkpoints=[Path("loras/v1_step_500.safetensors"), ...],
    eval_prompts=["aiinfluencer1 portrait", "aiinfluencer1 cafe", ...],
    seeds=[42, 43, 44],
)

report = await evaluator.run(config)
report.to_csv("eval_report.csv")
report.to_html_grid("eval_report.html")
```

### 2. Metrics (Protocol-based)

`Metric` Protocol:
```python
class Metric(Protocol):
    name: str  # ej "face_similarity", "aesthetic", "clip_adherence"

    async def score(self, image_path: Path, context: dict) -> float:
        """Returns score. Higher = better."""
```

Implementaciones provistas:
- **FaceSimilarityMetric**: wrappea `aiinfluencer.face_qc.FaceQC` (ya implementado)
- **AestheticMetric**: HuggingFace `shadowlilac/aesthetic-shadow-v2` o `cafeai/cafe_aesthetic` (optional dep face-qc, lazy import)
- **CLIPPromptAdherenceMetric**: `open_clip` similarity entre prompt y output (optional dep face-qc, lazy import)
- **DummyMetric**: returns constant, para tests

### 3. ImageGenerator Protocol

```python
class ImageGenerator(Protocol):
    async def generate(
        self, checkpoint: Path, prompt: str, seed: int
    ) -> Path:
        """Carga checkpoint, genera sample, devuelve path."""
```

Implementaciones:
- **ComfyUIGenerator**: invoca workflow via API (reusa `scripts/generate_batch.py` logic)
- **DummyGenerator**: returns fake path para tests

### 4. CheckpointEvaluator

Core loop:
```
for checkpoint in checkpoints:
    for prompt in eval_prompts:
        for seed in seeds:
            image = await generator.generate(checkpoint, prompt, seed)
            for metric in metrics:
                score = await metric.score(image, {"prompt": prompt, "seed": seed})
                report.add(checkpoint, prompt, seed, metric.name, score)

report.aggregate()  # mean por checkpoint × métrica
```

### 5. EvalReport

Estructura tabular:
```
checkpoint           | prompt           | seed | metric          | score
v1_step_500         | cafe portrait    | 42   | face_similarity | 0.62
v1_step_500         | cafe portrait    | 42   | aesthetic       | 5.8
v1_step_500         | cafe portrait    | 42   | clip_adherence  | 0.78
...
```

Aggregations:
- `mean_per_checkpoint_metric` → tabla checkpoint × metric con mean score
- `best_checkpoint_per_metric` → para cada métrica, qué checkpoint gana
- `weighted_overall_winner` → score combinado configurable (default: face_sim 0.5 + aesthetic 0.3 + clip 0.2)

Outputs:
- `report.to_csv(path)` → CSV raw
- `report.to_html_grid(path)` → HTML con thumbnails de samples + scores side-by-side

### 6. Script `scripts/eval_checkpoints.py`

```bash
python scripts/eval_checkpoints.py \
    --checkpoints-dir /workspace/loras \
    --checkpoint-pattern "aiinfluencer1_sdxl-step*.safetensors" \
    --eval-prompts prompts/eval_prompts.txt \
    --seeds 42,43,44 \
    --canon-mean outputs/canon/_mean_embedding.npy \
    --base-url http://127.0.0.1:8188 \
    --output-dir outputs/eval_v1/
```

Output:
- `outputs/eval_v1/samples/` — todas las imgs generadas
- `outputs/eval_v1/eval_report.csv` — raw data
- `outputs/eval_v1/eval_report.html` — grid visual
- `outputs/eval_v1/summary.json` — best checkpoint por metric + weighted winner

### 7. Tests

`tests/eval/`:
- `test_metrics.py` — Protocol compliance, scoring
- `test_checkpoint_evaluator.py` — orchestration con mocks (no llama ComfyUI real)
- `test_report.py` — aggregation logic + CSV/HTML output

## Criterio "done"

- [ ] Package `aiinfluencer.eval` con metrics + evaluator + report
- [ ] Tests unitarios pasando (mockean image gen + metrics ML pesadas)
- [ ] Script `scripts/eval_checkpoints.py` funcional con DummyGenerator
- [ ] Doc `docs/implementation/quality-eval.md` describiendo cómo usar

## KPI

Correr `eval_checkpoints.py` sobre los 8 checkpoints intermedios del LoRA SDXL actual (step_200 → step_2000), 4 prompts, 3 seeds = 96 samples evaluadas, tabla emitida en <5 min de tu tiempo (vs 3h ciegas anteriores).
