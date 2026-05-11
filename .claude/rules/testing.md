# Testing — convenciones

> Source: convenciones AI-first del global CLAUDE.md + pyproject pytest config.

## Stack

- `pytest` con `pytest-asyncio` mode=auto (todos los `async def test_*` son detectados)
- Mocks via `unittest.mock` (stdlib)
- Coverage: no obligatorio, pero apuntar a >70% en core packages

## Criterio "qué testear"

"¿Claude Code puede verificar esto sin correr el pod / ComfyUI / GPU real?"
- SÍ → escribir test
- NO → manual QA con outputs locales (ej: humanization visual check)

### Testear (siempre)
- Lógica determinística: transformations, calculadora de scores, aggregations
- Pipelines de pydantic-graph: cada rama (happy path + rejections + HITL pause)
- Protocols: `test_X_implements_protocol` para asegurar API compatibility
- Block list pediátrico: false positives + false negatives
- State proxy properties + setters
- Caption file parsers
- Serialización CSV/JSON/HTML

### NO testear
- Llamadas reales a ComfyUI / InsightFace / HuggingFace / RunPod (mockear)
- GPU compute real (mockear o usar fixtures pre-computadas)
- Visuales (humanization rendering — visual eyeball)

## Mocking convencional

- **ComfyUI**: `DummyComfyClient` en `aiinfluencer.pipeline.deps` (devuelve fake PNG path)
- **Mongo**: `DummyMongoClient` (in-memory dict)
- **InsightFace**: `monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace(imread=...))` + `@patch("...face_qc.embeddings._get_face_analysis")`
- **Transformers/HuggingFace**: `MagicMock(return_value=[{"label": "...", "score": 0.x}])` + `@patch("..._ensure_X_loaded")`
- **c2pa-python**: lazy import en code, mockear `_signer` directamente en test

## Async tests

```python
async def test_my_async_thing():
    deps = WorkflowDeps.with_dummies()
    request = PieceRequest(prompt_seed="...")
    result = await run_piece(request, deps)
    assert isinstance(result, PieceApproved)
```

NO usar `@pytest.mark.asyncio` (mode=auto lo aplica solo).

## Fixtures comunes

- `tmp_path` (pytest builtin): para archivos temporales, paths
- Custom: `sample_image`, `canon_mean_path`, `classifiers` — definirlas locales al test file

## Directory mirror

```
src/aiinfluencer/<dominio>/    →    tests/<dominio>/
```

Cada test file: `test_<modulo>.py`. NO mezclar tests de varios módulos en un solo file.

## Tests "slow" (futuro)

Cuando agreguemos integration tests que necesitan modelos reales (insightface + canon mean reales):

```python
@pytest.mark.slow
async def test_real_face_qc_integration():
    ...
```

Y en CI: `pytest -m "not slow"` por default.

Pero por ahora: TODOS los tests deben correr en CI en <30s sin GPU.

## Smoke test del grafo

`tests/pipeline/test_graph_smoke.py` corre el grafo end-to-end con todos los dummies. Si esto se rompe, NADA del pipeline está funcionando.

## Patterns que ya quedaron en la base

- `WorkflowDeps.with_dummies()` para grafo smoke
- `_make_fake_face` helper en `tests/face_qc/test_embeddings.py`
- `_make_report()` helper en `tests/eval/test_reports.py`
- `fake_image` fixture con PIL real (no `b"\x89PNG..."` raw — eso PIL no lo lee)
