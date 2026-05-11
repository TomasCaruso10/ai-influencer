# Dataset v2 — Runbook operativo

> Pasos concretos para correr Bloque 2.4 (re-curación dataset canon + re-train LoRA v2). Requiere pod RunPod arriba.

## Pre-flight (local, sin pod)

1. **Dataset v1 fuente**: `outputs/canon/` debe tener 50+ PNGs + `_mean_embedding.npy`.
2. **Espacio disco**: tener ~10GB libres en pod para LoRA training + samples.
3. **Credenciales**: `.env` con `RUNPOD_API_KEY` válido.

## Paso 1 — Levantar el pod

```powershell
uv run python scripts/pod.py up
```

Esto crea un pod RTX 4090 Community (~$0.34/h) con ComfyUI + ai-toolkit + sd-scripts instalados sobre el Network Volume persistente. Espera ~2-3 min hasta "ready" + imprime URLs (ComfyUI HTTP, SSH).

Verifica:
```powershell
uv run python scripts/pod.py status
```

## Paso 2 — Subir dataset v1 al pod

Desde local:
```powershell
$POD_IP = uv run python scripts/pod.py ssh | Select-String -Pattern "@(.+):" | ForEach-Object { $_.Matches.Groups[1].Value }
scp -P 22 outputs/canon/*.png root@${POD_IP}:/workspace/datasets/aiinfluencer1/
scp -P 22 outputs/canon/*.txt root@${POD_IP}:/workspace/datasets/aiinfluencer1/  # captions si las hay
```

(O `rsync -avz` si está disponible.)

## Paso 3 — Correr filter_canon_v2 en pod

SSH al pod:
```powershell
uv run python scripts/pod.py ssh
# o copia/pega el comando ssh que imprime
```

En el pod:
```bash
cd /workspace/ai-influencer
git pull
uv sync --extra face-qc

uv run python scripts/filter_canon_v2.py \
    --input /workspace/datasets/aiinfluencer1 \
    --output /workspace/datasets/aiinfluencer1_v2 \
    --keep 30
```

Output esperado: imprime score per image (sim vs centroid), copia top 30 a `aiinfluencer1_v2/`. Mantén también los `.txt` captions paired.

## Paso 4 — Re-train LoRA v2

### FLUX (ai-toolkit)
```bash
cd /workspace/ai-toolkit

# Editar config para apuntar a aiinfluencer1_v2 y subir rank si querés
# config/aiinfluencer1_flux_v2.yaml: dataset_path: /workspace/datasets/aiinfluencer1_v2

uv run python run.py config/aiinfluencer1_flux_v2.yaml
```

Tiempo estimado: 1-3h depende epochs (default 25 epochs × 30 imgs ≈ 1.5h).

Sale el LoRA en `/workspace/loras/aiinfluencer1_flux_v2.safetensors` + samples en `/workspace/loras/sample/`.

### SDXL (kohya)
```bash
cd /workspace/sd-scripts
# editar config: dataset path = aiinfluencer1_v2, rank 16
bash train_lora_sdxl_v2.sh
```

## Paso 5 — Evaluar checkpoints v2

```bash
cd /workspace/ai-influencer

uv run python scripts/eval_checkpoints.py \
    --checkpoints-dir /workspace/loras/aiinfluencer1_flux_v2_checkpoints \
    --prompts prompts/eval_prompts.txt \
    --seeds 42,123,777 \
    --output /workspace/outputs/eval_v2_$(date +%Y%m%d_%H%M)
```

Mira el HTML report → eligir mejor epoch.

## Paso 6 — Smoke test con workflow v2

Con el LoRA v2 ganador, generar 20 imgs con `workflows/flux_with_lora_v2.json` (FaceDetailer multi-pass):

```bash
uv run python scripts/generate_batch.py \
    --workflow workflows/flux_with_lora_v2.json \
    --lora /workspace/loras/aiinfluencer1_flux_v2_FINAL.safetensors \
    --prompts prompts/canon_variations.txt \
    --output /workspace/outputs/v2_smoke_$(date +%Y%m%d_%H%M) \
    --count 20
```

## Paso 7 — Face QC batch sobre output v2

```bash
uv run python scripts/face_qc_batch.py \
    --input /workspace/outputs/v2_smoke_<TIMESTAMP> \
    --canon-mean /workspace/datasets/aiinfluencer1_v2/_mean_embedding.npy \
    --output /workspace/outputs/v2_smoke_<TIMESTAMP>/face_qc_report.csv \
    --threshold 0.45
```

**Criterio de éxito**: ≥ 18/20 (90%) PASS. Si < 80%, revisar prompts (framing de cara muy chica → NO_FACE).

## Paso 8 — Bajar resultados a local

```powershell
# Desde local:
scp -P 22 -r root@${POD_IP}:/workspace/loras/aiinfluencer1_flux_v2_FINAL.safetensors outputs/loras/
scp -P 22 -r root@${POD_IP}:/workspace/outputs/v2_smoke_<TIMESTAMP> outputs/
scp -P 22 -r root@${POD_IP}:/workspace/outputs/eval_v2_<TIMESTAMP> outputs/eval/
```

## Paso 9 — Bajar el pod

```powershell
uv run python scripts/pod.py down
```

Esto **termina el pod** (deja de cobrar GPU) pero **conserva el Network Volume** ($0.07/GB/mes, ~$7/mes para 100GB). Los modelos, LoRAs y datasets ahí persisten para la próxima sesión.

## Checklist post-corrida

- [ ] LoRA v2 final commited a outputs/loras/ (gitignored, está OK local)
- [ ] CSV face QC report en outputs/v2_smoke_<TIMESTAMP>/
- [ ] HTML eval report en outputs/eval/v2_<TIMESTAMP>/
- [ ] Actualizar `docs/implementation/face-qc.md` con métricas v2 medidas
- [ ] Actualizar `CHANGELOG.md` con "Bloque 2.4 cerrado: LoRA v2 entrenado, X/20 PASS"
- [ ] Commit cualquier prompt/script tweak nuevo

## Costo estimado

| Item | Costo |
|---|---|
| Pod 4090 Community × 4h (filter + train + smoke + eval) | $1.40 |
| Network Volume share (1 mes/12 corridas) | $0.60 |
| **Total runbook completo** | **~$2 USD** |

## Troubleshooting

**"insightface install fails on Windows"** → no se puede correr `filter_canon_v2.py` local. Subí dataset al pod y corré ahí (este runbook asume eso).

**"face_yolov8m.pt no encontrado"** → el workflow v2 lo necesita para FaceDetailer. Descargarlo desde HF al pod:
```bash
cd /workspace/ComfyUI/models/ultralytics/bbox
wget https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8m.pt
```

**"IPAdapter FaceID model no encontrado"** → bajar al pod:
```bash
cd /workspace/ComfyUI/models/ipadapter
wget https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/ip-adapter-faceid-plusv2_sdxl.bin
cd /workspace/ComfyUI/models/loras
wget https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main/ip-adapter-faceid-plusv2_sdxl_lora.safetensors
```

**LoRA v2 cos sim peor que v1** → significa que el filtro fue demasiado agresivo o keep=30 quitó variabilidad útil. Re-correr con `--keep 40` o revisar las imágenes descartadas (puede que el centroid esté sesgado a un subset).
