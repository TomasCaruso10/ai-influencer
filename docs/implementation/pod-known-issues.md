# Pod — known issues (Fase 1)

## ComfyUI custom nodes broken (no bloqueantes)

### ComfyUI-WanVideoWrapper

**Error**: `cannot import name 'get_key_weight' from 'comfy.model_patcher'`

**Causa**: el wrapper requiere features de ComfyUI muy recientes que no están en master HEAD actual.

**Impacto**: bloquea generación de video I2V. **No bloqueante para Fase 1** (imágenes); reaparece en Fase 3 (video).

**Workaround para Fase 3**:
- Pinear una versión de WanVideoWrapper compatible con la versión de ComfyUI que tengamos.
- O actualizar ComfyUI a HEAD-of-master cuando lleguemos a Fase 3.
- O migrar a `kijai/ComfyUI-HunyuanVideoWrapper` (HunyuanVideo I2V) como alternativa.

### ComfyUI-ReActor

**Error**: `infer_schema(func): Parameter input has unsupported type torch.Tensor` (torchao API mismatch).

**Causa**: ReActor usa una API de `torchao` que cambió tras update reciente de torch en el venv.

**Impacto**: bloquea face-swap post-hoc. **No bloqueante para Fase 1** (la consistencia de identidad la sostienen el LoRA + IPAdapter + FaceDetailer); reaparece en Fase 2 cuando queramos face-swap como refuerzo final NSFW.

**Workaround para Fase 2**:
- Pinear `torchao` a la versión que ReActor soporta (probable `torchao<0.10`).
- O usar `face-swap` alternativo (ej. `inswapper` directo via insightface) sin pasar por ReActor node.

## Notas sobre la imagen base

`ghcr.io/ai-dock/comfyui:latest-cuda` viene con ComfyUI **v0.2.2 pineada** (HEAD detached).
Hicimos `git reset --hard origin/master` para subirlo a v0.9.73 (commit `aa9d2fc7`). Este reset
debe repetirse cada vez que se cree un pod nuevo si la imagen ai-dock no actualiza su pin
(o se incorpora como step en `runpod_setup.sh`).

## Próxima vez que se cree un pod nuevo

El `runpod_setup.sh` actual asume ComfyUI ya cloneado en `/opt/ComfyUI` (lo trae ai-dock).
Pero NO actualiza ComfyUI ni instala las deps faltantes en el venv `/opt/environments/python/comfyui`.
Hay que actualizar el script antes del próximo `pod up`. TODO: agregar al script:

1. `git -C /opt/ComfyUI reset --hard origin/master`
2. Recreate symlinks `/opt/ComfyUI/{models,custom_nodes,input,output}` → `/workspace/...`
3. `/opt/environments/python/comfyui/bin/pip install piexif toml insightface segment-anything facexlib ftfy ultralytics mediapipe`
4. `/opt/environments/python/comfyui/bin/pip install -r /opt/ComfyUI/requirements.txt`
5. `supervisorctl restart comfyui`

(Esto ya quedó hecho a mano en el pod actual — sirve si destruimos y recreamos.)
