# Pod lifecycle — modelo mental + cheat sheet

## Modelo mental

```
┌─────────────────────────────┐         ┌────────────────────────────────┐
│  POD (efímero)              │         │  NETWORK VOLUME (persiste)     │
│  ─ GPU + container          │  monta  │  /workspace/                   │
│  ─ creado por scripts/pod.py│ ◄─────► │  ├── ComfyUI/                  │
│  ─ vive minutos a horas     │         │  ├── models/                   │
│  ─ se descarta libremente   │         │  ├── loras/                    │
│                             │         │  └── outputs/                  │
└─────────────────────────────┘         └────────────────────────────────┘
   GPU $0.34/h cuando RUNNING                $0.07/GB/mes (siempre)
   $0 cuando TERMINATED                       persiste cross-sesiones
```

**Idea clave**: el pod es **descartable**. Toda la state (modelos, LoRAs, outputs) vive en el Network Volume, separado del pod. Cada sesión: `pod up` (crea pod fresco, monta volume) → trabajamos → `pod down` (destruye el pod, volume queda intacto).

Esto es **terminate-recreate**, no stop/start. Razones:

- Stop/start del **mismo** pod no es confiable en Community Cloud — la GPU puede ser tomada por otro user mientras tu pod está stopped.
- Terminate-recreate es **idempotente**: el script de creación es la fuente de verdad, igual al primer día que al día 100.
- IP nueva cada vez, pero el script la maneja por vos.

## Estados y costos

| Estado | GPU | Container disk | Network Volume | Cobra |
|---|---|---|---|---|
| `RUNNING` | encendida | montado (50 GB ephemeral) | montado | **GPU + storage** |
| `TERMINATED` | destruida | borrado | persiste | **solo storage ($7/mes)** |

Estimado real:

| Uso | Costo mensual |
|---|---|
| 4 h/semana de trabajo (MVP típico) | **$5.85 GPU + $7 storage = $13** |
| Vacaciones (cero pods, volume parado) | **$7 storage** |
| Pod prendido toda la noche por accidente | $0.34 × 24 = **$8.16/día** |

## Cheat sheet de comandos

```bash
# Setup inicial (una sola vez)
cp .env.example .env
# Editar .env: pegar API key, volume id, SSH pubkey
ssh-keygen -t ed25519 -C "ai-influencer"   # si no tenés
cat ~/.ssh/id_ed25519.pub                   # pegar en RUNPOD_SSH_PUBKEY

uv sync                                     # o: pip install -e .

# Día a día
python scripts/pod.py up                    # crear pod (~60-90s)
python scripts/pod.py status                # ver pod activo
python scripts/pod.py ssh                   # imprime el comando SSH
python scripts/pod.py down                  # terminar pod

# Lifecycle interactivo (recomendado)
python scripts/pod.py session
# → crea pod, espera ready, imprime URLs
# → te quedás trabajando en otra terminal (SSH, browser de ComfyUI)
# → Ctrl+C en esta terminal cuando termines
# → script termina el pod automáticamente
```

## Lo que pasa después de `pod up`

1. Script llama `runpod.create_pod(...)` con la imagen `ghcr.io/ai-dock/comfyui:latest-cuda`.
2. RunPod aprovisiona la VM, monta el Network Volume en `/workspace`, levanta el container.
3. **ai-dock** arranca ComfyUI en `:8188`, sshd en `:22`, Jupyter en `:8888`.
4. Script hace polling hasta que `runtime.uptimeInSeconds > 0` y los puertos están publicados.
5. Te imprime:
   - `ComfyUI: https://<pod-id>-8188.proxy.runpod.net` — UI interactiva
   - `SSH:     ssh root@<ip> -p <port>` — terminal directa al pod
   - `Jupyter: https://<pod-id>-8888.proxy.runpod.net`

ai-dock tarda ~2-3 min adicionales después de uptime>0 para terminar de inicializar ComfyUI (descargar inits, instalar deps base). Test ready: `curl -sS https://<pod-id>-8188.proxy.runpod.net/system_stats`.

## Primera vez vs siguientes

**Primera vez** que levantás pod sobre un volume vacío:

1. `pod up`
2. SSH al pod
3. `bash scripts/setup_volume.sh` — instala custom nodes en /workspace, baja modelos al volume
4. (~15-30 min según ancho de banda y modelos elegidos)

**Siguientes** veces (todo ya bajado en el volume):

1. `pod up` — ai-dock detecta el volume, ComfyUI usa los modelos y custom nodes que ya están ahí (~2 min total)
2. Trabajamos
3. `pod down`

## Importante / gotchas

- **Cerrar la terminal NO termina el pod.** El pod corre en RunPod, independiente de tu PC. Siempre usá `pod down` o `Ctrl+C` en `pod session`.
- **`pod session` Ctrl+C es el flujo seguro** porque garantiza el `down`. Si arrancás con `pod up` solo y te olvidás, el pod se queda corriendo y consumiendo $0.34/h.
- **Verificar diariamente** mientras te acostumbrás: `python scripts/pod.py status` o entrar a runpod.io/console/pods. Si ves un pod que no esperabas → `pod down`.
- **Pricing actualizado**: a veces RunPod cambia precios o disponibilidad. La 4090 Community a $0.34 es lo común; si en tu región solo aparece Secure ($0.69), probá `RUNPOD_REGION=EU-RO-1` o equivalente.
- **El Network Volume NO se borra automáticamente** si terminás el pod. Para borrarlo: RunPod console → Storage → Delete. Solo hacelo cuando termines el proyecto.

## Salvaguarda manual sugerida

Cuando termines un día de trabajo:

```bash
python scripts/pod.py status   # verificar
python scripts/pod.py down     # terminar
python scripts/pod.py status   # confirmar "No pod found"
```

Si querés un recordatorio externo, agendá un cron en tu PC que mande notificación si el pod lleva > 4 h running. Implementación queda fuera del MVP por simplicidad (decisión del usuario).

## Referencias

- [RunPod Python SDK](https://github.com/runpod/runpod-python)
- [RunPod GraphQL API](https://docs.runpod.io/api-reference/pods/create-on-demand)
- [ai-dock/comfyui](https://github.com/ai-dock/comfyui)
- [ai-dock environment variables](https://github.com/ai-dock/comfyui#environment-variables)
