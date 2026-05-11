# Face QC — convenciones

> Identity verification automática vs canon mean embedding. Source: `docs/specs/face-consistency.md` + `docs/research/face-consistency-stack.md`.

## Stack lockeado

- **InsightFace `buffalo_l`** (no antelopev2): SCRFD-10GF detection + ResNet50 @ WebFace600K, ~326 MB
- **Embedding**: 512-dim, L2-normalized (cosine sim == dot product)
- **Threshold default**: 0.45 cosine vs canon mean
- **Reject score 0.0** si no se detecta cara (configurable via `FaceQC.no_face_score`)

## Workflow de uso

```python
# 1) Una vez por personaje: compute canon mean
from aiinfluencer.face_qc import compute_canon_mean
import numpy as np

mean = compute_canon_mean(Path("outputs/canon"))
np.save("outputs/canon/_mean_embedding.npy", mean)

# 2) Runtime: instanciar verifier
from aiinfluencer.face_qc import FaceQC
verifier = FaceQC(canon_mean_path="outputs/canon/_mean_embedding.npy")
similarity = await verifier.cosine_similarity(image_path)
```

## Reglas duras

1. **Lazy imports** de insightface + cv2 + onnxruntime — son optional deps `face-qc`. NUNCA importar en module top-level.
2. **Single FaceAnalysis instance** por proceso — `lru_cache` en `_get_face_analysis()`.
3. **Validar load_canon_mean**: shape == (512,) y L2-norm ≈ 1.0. Raise antes de uso.
4. **Skip imágenes sin cara en compute_canon_mean** (warn, no error) — algunas pueden ser body-only.
5. **`buffalo_l`**, no antelopev2 (research dice 0.687 threshold mítico es bullshit, real es 0.30-0.45).

## Cuándo usar canon mean vs single reference

- **Canon mean**: para QC general "es esta persona en general". Más robusto a una mala foto del canon.
- **Single reference** (foto canon "ID card"): para IPAdapter FaceID y ReActor face-swap en runtime. Una sola foto consistente para inyección.

Ambos pueden coexistir: `outputs/canon/_mean_embedding.npy` + `outputs/canon/_id_card.png`.

## Métricas concretas (medidas en el MVP)

- LoRA FLUX SFW: cos sim mean ~0.68 vs canon mean (10/10 pass)
- LoRA SDXL hardcore NSFW: NO_FACE en 8/8 (problema de framing — cara muy chica en poses extremas, NO problema del LoRA)

## Tests

Mockear `_get_face_analysis()` + `cv2.imread`. Stubear `cv2` en `sys.modules` con `monkeypatch.setitem` para evitar dependency en optional dep. Ver `tests/face_qc/test_embeddings.py` para el pattern.

## Cuándo NO usar canon mean

Si vas a entrenar **persona nueva** (multi-personaje, Fase 5), cada personaje tiene su propio `outputs/canon_<id>/_mean_embedding.npy`. El path se parametriza por `character_id` en `WorkflowDeps`.
