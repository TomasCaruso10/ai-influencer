# Face QC — implementation reference

> Cómo funciona la identity verification automática vs canon mean. Source: `src/aiinfluencer/face_qc/`.

## Resumen

Cada imagen generada se compara contra una **canon mean embedding** (el promedio L2-normalizado de los embeddings del dataset canon). Si la similitud coseno está por debajo de un threshold (default 0.45), la pieza se rechaza.

## Stack

| Pieza | Tecnología | Por qué |
|---|---|---|
| Detección + landmarks | InsightFace SCRFD-10GF | rápido, robusto a poses, viene con buffalo_l |
| Embedding | InsightFace `buffalo_l` (ResNet50 @ WebFace600K) | mainline 2025, 512-dim, ~326 MB descarga |
| Distancia | cosine (== dot product con L2-normed vectors) | rango [-1, 1], simple, calibración pública |
| Format storage | `outputs/canon/_mean_embedding.npy` | numpy save, 2KB, gitignored |

**NO** usamos antelopev2 — los thresholds míticos publicados (0.687) corresponden a datasets internos no replicables. Empíricamente con buffalo_l el threshold útil va 0.30-0.45.

## Archivos

| Archivo | Qué expone |
|---|---|
| `embeddings.py` | `embedding_for_image(path)`, `compute_canon_mean(dir)`, `load_canon_mean(path)` |
| `verifier.py` | `FaceQC(canon_mean_path)` dataclass impl de `FaceQCProto` con `async cosine_similarity(image_path)` |
| `exceptions.py` | `NoFaceDetectedError`, `MultipleFacesError` |

## Pipeline en runtime

```python
verifier = FaceQC(canon_mean_path="outputs/canon/_mean_embedding.npy",
                  no_face_score=0.0,
                  prefer_largest_face=True)

sim = await verifier.cosine_similarity(generated_image_path)
# sim ∈ [-1, 1]; >= 0.45 => OK
```

Internamente:
1. `cv2.imread` (lazy import — optional dep)
2. `app.get(img)` — SCRFD detect + ResNet50 embed
3. Si 0 caras → return `no_face_score` (default 0.0)
4. Si >1 cara → pick largest bbox area (`prefer_largest_face=True`)
5. `embedding = face.normed_embedding.astype(float32)` (ya L2-normed)
6. `sim = float(np.dot(embedding, canon_mean))`

## Compute canon mean

Una vez por personaje, con el dataset canon curado:

```python
from aiinfluencer.face_qc import compute_canon_mean
import numpy as np

mean = compute_canon_mean(Path("outputs/canon"))  # itera *.png, *.jpg
np.save("outputs/canon/_mean_embedding.npy", mean)
```

Skips imágenes sin cara (warn, no error). El resultado es un vector 512-dim L2-normed.

**Validación on load**: `load_canon_mean(path)` chequea shape == (512,) y `|norm-1.0| < 1e-3`. Raise antes de exponer el verifier al pipeline.

## Lazy imports

`insightface`, `cv2`, `onnxruntime` son optional deps `[face-qc]`. NO importarlos top-level del módulo. Patrón:

```python
def embedding_for_image(image_path: Path) -> np.ndarray:
    import cv2  # lazy
    img = cv2.imread(str(image_path))
    if img is None:
        raise NoFaceDetectedError(f"Cannot read image: {image_path}")
    app = _get_face_analysis()
    faces = app.get(img)
    ...
```

`_get_face_analysis()` es `@lru_cache(maxsize=1)` para tener una sola instancia FaceAnalysis por proceso (cargar el modelo cuesta ~2s + RAM/VRAM).

## Tests

Mockear `cv2.imread` con `monkeypatch.setitem(sys.modules, "cv2", SimpleNamespace(imread=lambda p: fake_array))` y `_get_face_analysis()` con `@patch`. Ver `tests/face_qc/test_embeddings.py` para el pattern completo (10 tests).

`tests/face_qc/test_verifier.py` ejercita la API async del verifier (4 tests).

## Métricas medidas en MVP

| Dataset | Resultado |
|---|---|
| LoRA FLUX SFW (10 generated images) | cos sim mean ~0.68, 10/10 PASS |
| LoRA SDXL hardcore NSFW (8 images) | 8/8 NO_FACE (problema framing — cara muy chica en poses extremas; NO es problema del LoRA) |

**Implicación práctica**: para piezas NSFW con framing extremo, el QC va a marcar NO_FACE. Solución (Fase 2.5): aumentar threshold de bbox area o agregar fallback con detección face crops más sensible. **TODO en spec.**

## Multi-personaje (Fase 5+)

Cada personaje tendrá su propio `outputs/canon_<character_id>/_mean_embedding.npy`. El path se va a parametrizar por `character_id` en `WorkflowDeps`. Por ahora hard-codeado a `outputs/canon/`.
