# Spec — Bloque 2.2 Face Consistency Stack

> Implementación del stack ganador 2026 para identidad cross-modelo. Target: ~97% identity accuracy.
>
> Source: `docs/research/face-consistency-stack.md` + `docs/state-of-the-art-audit.md` Gap 1.

## Objetivo

Tener QC automático de identidad funcionando + workflows ComfyUI con FaceDetailer multi-pass que mejoren las imágenes generadas antes del QC.

## Componentes

### 1. Python package `aiinfluencer.face_qc`

```
src/aiinfluencer/face_qc/
├── __init__.py
├── embeddings.py      # compute / load canon mean embedding
├── verifier.py        # FaceQC class implementing FaceQCProto
└── exceptions.py      # NoFaceDetected, AmbiguousFace
```

**API pública**:
```python
from aiinfluencer.face_qc import FaceQC, compute_canon_mean

# Setup one-time: compute mean embedding from canon dataset
mean_emb = compute_canon_mean(canon_dir=Path("outputs/canon"))
np.save("outputs/canon/_mean_embedding.npy", mean_emb)

# Runtime: instantiate verifier
verifier = FaceQC(canon_mean_path="outputs/canon/_mean_embedding.npy")
similarity = await verifier.cosine_similarity(image_path)  # 0-1
```

**Tooling**:
- `insightface==0.7.3` con `buffalo_l` model (~326 MB, auto-download)
- `onnxruntime` (CPU local, `onnxruntime-gpu` en pod)
- `opencv-python-headless` para img loading

**Algoritmo**:
1. Cargar imagen via cv2
2. Detectar caras con SCRFD-10GF (parte de buffalo_l)
3. Si hay 0 caras → raise `NoFaceDetected`
4. Si hay >1 cara → tomar la de bbox más grande (la principal)
5. Extraer `normed_embedding` (ResNet50 @ WebFace600K, L2-normalized)
6. Compute cosine similarity vs canon mean
7. Return float 0-1

**Threshold**: 0.45 default (de research). Configurable via `WorkflowDeps.face_qc_threshold`.

### 2. Script `scripts/compute_canon_embedding.py`

CLI para computar mean embedding del canon una sola vez:
```bash
python scripts/compute_canon_embedding.py \
    --canon-dir outputs/canon \
    --output outputs/canon/_mean_embedding.npy
```

Output: `.npy` con vector de 512-dim L2-normalized.

### 3. Script `scripts/face_qc_batch.py`

CLI para evaluar batch de outputs contra el canon mean:
```bash
python scripts/face_qc_batch.py \
    --canon-mean outputs/canon/_mean_embedding.npy \
    --inputs outputs/lora_final_test/ \
    --threshold 0.45 \
    --output-csv outputs/face_qc_report.csv
```

Útil para evaluar manualmente las 10 imgs del test final actual vs canon.

### 4. Replace dummy en `pipeline/nodes/face_qc.py`

El `FaceQCNode` ya está implementado correctamente — usa `ctx.deps.face_qc.cosine_similarity()`. Solo hay que cambiar la deps default de `DummyFaceQC` a `FaceQC` real cuando se quiere production mode.

`WorkflowDeps.with_production_face_qc(canon_mean_path)` builder agregamos.

### 5. Update workflows ComfyUI con FaceDetailer multi-pass

Tres workflows a modificar:
- `workflows/flux_with_lora.json`
- `workflows/chroma_with_lora.json`
- `workflows/sdxl_bigasp_nsfw.json`

Cada uno agrega después del KSampler:
- Nodo `FaceDetailer` (Impact Pack) con denoise 0.45
- Segundo `FaceDetailer` con denoise 0.25
- Tercer `FaceDetailer` con denoise 0.15
- LoRA aplicado en cada pass (mismo LoRA del personaje)

Para SDXL+bigASP también agregamos:
- `IPAdapterFaceID Plus v2` weight 0.7 sobre el model loader
- `LoRA` específica `ip-adapter-faceid-plusv2_sdxl_lora.safetensors` weight 0.65

(NOTA: estos workflows son JSONs que el pipeline carga y ejecuta en ComfyUI del pod. La validación real requiere correr ComfyUI con los custom nodes instalados; en local solo verificamos sintaxis JSON.)

### 6. Tests

`tests/face_qc/test_embeddings.py`:
- `compute_canon_mean` con dataset sintético devuelve vector L2-normalized
- Maneja imagen sin caras (raise)
- Maneja imagen con múltiples caras (toma la más grande)

`tests/face_qc/test_verifier.py`:
- `FaceQC.cosine_similarity()` con misma imagen del canon → ~1.0
- Con imagen de otra cara → <0.5
- Cumple Protocol `FaceQCProto`

`tests/pipeline/test_face_qc_integration.py`:
- `FaceQCNode` con `FaceQC` real (mockeando insightface) funciona end-to-end

## Criterio "done"

- [ ] Package `aiinfluencer.face_qc` implementado y tests pasan
- [ ] Scripts CLI funcionan
- [ ] `WorkflowDeps.with_production_face_qc()` builder agregado
- [ ] Workflows actualizados con FaceDetailer multi-pass
- [ ] Reporte CSV con face_qc score de las 10 imgs de `outputs/lora_final_test/` vs canon mean

## KPI

Reporte CSV de las 10 imgs del test final muestra cos similarity vs canon mean. Si ≥80% pasan threshold 0.45, el LoRA actual cumple. Si no, sabemos cuánto mejorar.
