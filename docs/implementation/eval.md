# Eval — implementation reference

> Cómo funciona el checkpoint evaluator. Source: `src/aiinfluencer/eval/`.

## Resumen

Dado N checkpoints (de un LoRA en distintos epochs), M prompts, K seeds, evalúa **N×M×K imágenes** con un set de métricas configurables y produce un ranking de mejor checkpoint según score ponderado.

Sirve para responder: "después de entrenar mi LoRA, ¿qué epoch me quedo?".

## Archivos

| Archivo | Qué expone |
|---|---|
| `metrics.py` | `EvalMetric` Protocol + 4 impls: `FaceSimilarityMetric`, `AestheticMetric`, `CLIPPromptAdherenceMetric`, `DummyMetric` |
| `checkpoint_evaluator.py` | `CheckpointEvaluator`, `EvalConfig`, `EvalResult` |
| `reports.py` | `EvalReport` con aggregaciones + CSV/JSON/HTML export |

## EvalConfig

```python
@dataclass
class EvalConfig:
    checkpoints: list[Path]
    prompts: list[str]
    seeds: list[int]
    metric_weights: dict[str, float] = field(default_factory=lambda: {
        "face_similarity": 0.5,
        "aesthetic": 0.3,
        "clip_adherence": 0.2,
    })
```

Default weights: identity 50%, aesthetic 30%, prompt adherence 20%. Ajustable per-corrida.

## Loop principal

```python
evaluator = CheckpointEvaluator(
    image_generator=image_gen,  # ImageGenerator Protocol
    metrics=[face_sim, aesthetic, clip],
)
result = await evaluator.run(config)
```

Internamente:
```python
for checkpoint in checkpoints:
    image_gen.load_checkpoint(checkpoint)
    for prompt in prompts:
        for seed in seeds:
            img = await image_gen.generate(prompt, seed)
            for metric in metrics:
                score = await metric.score(img, prompt=prompt)
                result.add_score(checkpoint, prompt, seed, metric.name, score)
```

## EvalReport

`EvalReport` agrupa N×M×K resultados por checkpoint × metric:

- `mean_per_checkpoint_metric()` → `dict[Path, dict[str, float]]`
- `best_checkpoint_per_metric()` → `dict[str, Path]`
- `weighted_overall_winner(weights)` → `(checkpoint, score)`

**Tie-breaking**: si dos checkpoints empatan en weighted score, gana el de mayor face_similarity (regla de negocio: identity > aesthetic).

## Export

- `report.to_csv(path)` — 1 fila por (checkpoint, prompt, seed, metric)
- `report.to_json(path)` — full result + aggregations
- `report.to_html(path)` — tabla con grid de samples + scores (útil para review visual)

## Métricas implementadas

### FaceSimilarityMetric
Wrappea `FaceQC.cosine_similarity()`. Llama directo al verifier de `face_qc/`. NO_FACE → score 0.0.

### AestheticMetric
Lazy import HuggingFace pipeline `cafeai/cafe_aesthetic` (binary aesthetic/anti_aesthetic). Score ∈ [0, 1] del label "aesthetic". Placeholder por ahora — research dice que MLP-based predictor (ej. LAION aesthetic predictor v2.5) puede dar mejor calibración. **TODO en spec.**

### CLIPPromptAdherenceMetric
Lazy import CLIP, calcula cosine entre text embedding (prompt) y image embedding (generated). Normalizado a [0, 1] via `(sim + 1) / 2`.

### DummyMetric
Score determinístico desde hash(prompt + seed). Solo para tests.

## Protocol obligatorio

Todo nuevo metric tiene que implementar:
```python
class EvalMetric(Protocol):
    @property
    def name(self) -> str: ...
    async def score(self, image_path: Path, *, prompt: str = "") -> float: ...
```

Score ∈ [0, 1] convención. Si tu metric devuelve algo fuera de rango, el weighted overall winner se vuelve no comparable.

## Tests

- `tests/eval/test_metrics.py` (3 tests) — protocol compliance, hash determinism, score range
- `tests/eval/test_checkpoint_evaluator.py` (6 tests) — loop completo + edge cases (empty checkpoints, empty prompts, single seed, all-zero metric)
- `tests/eval/test_reports.py` (8 tests) — aggregations + tie-breaking + CSV/JSON/HTML serialization

## CLI: `scripts/eval_checkpoints.py`

```powershell
uv run python scripts/eval_checkpoints.py `
    --checkpoints-dir outputs/lora_test/checkpoints `
    --prompts prompts/eval_prompts.txt `
    --seeds 42,123,777 `
    --output outputs/eval/run_001
```

Produce CSV + HTML report en `outputs/eval/run_001/`.
