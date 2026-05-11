#!/usr/bin/env bash
# Setup del Network Volume — correr DENTRO del pod la PRIMERA VEZ que arrancás un pod
# sobre un volume vacío. Idempotente: re-correrlo no hace daño.
#
# Asume: imagen `ghcr.io/ai-dock/comfyui:latest-cuda` (ai-dock viene con ComfyUI listo
# en /opt/ComfyUI; nosotros relocamos models y custom_nodes al volume persistente).
#
# Uso (vía SSH al pod):
#   cd /workspace
#   git clone <este-repo> ai-influencer
#   bash ai-influencer/scripts/runpod_setup.sh
#
# Lo que hace:
#   1. Crea la estructura de directorios en /workspace.
#   2. Symlinkea /opt/ComfyUI/models y /opt/ComfyUI/custom_nodes al volume.
#   3. Clona los custom nodes que necesitamos.
#   4. (Opcional, comentado) Baja modelos.

set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
COMFY_DIR="${COMFY_DIR:-/opt/ComfyUI}"

if [ ! -d "$COMFY_DIR" ]; then
  echo "ERROR: ComfyUI no encontrado en $COMFY_DIR. ¿Estás usando la imagen ai-dock/comfyui?"
  exit 1
fi

echo "==> Preparando estructura en $WORKSPACE"
mkdir -p "$WORKSPACE/models"/{checkpoints,loras,vae,clip,clip_vision,controlnet,upscale_models,insightface,ultralytics/bbox,ultralytics/segm,diffusion_models,pulid}
mkdir -p "$WORKSPACE/custom_nodes" "$WORKSPACE/output" "$WORKSPACE/input" "$WORKSPACE/datasets"

# ---------- Symlinks: ComfyUI usa /workspace para state persistente ----------
link_to_volume() {
  local target="$1"   # path original en /opt/ComfyUI
  local source="$2"   # path en /workspace
  if [ -L "$target" ]; then
    return  # ya symlinkeado
  fi
  if [ -d "$target" ] && [ "$(ls -A "$target" 2>/dev/null)" ]; then
    echo "==> Migrando contenido de $target a $source"
    cp -rn "$target/." "$source/" || true
  fi
  rm -rf "$target"
  ln -s "$source" "$target"
  echo "==> Symlinked $target -> $source"
}

link_to_volume "$COMFY_DIR/models" "$WORKSPACE/models"
link_to_volume "$COMFY_DIR/custom_nodes" "$WORKSPACE/custom_nodes"
link_to_volume "$COMFY_DIR/output" "$WORKSPACE/output"
link_to_volume "$COMFY_DIR/input" "$WORKSPACE/input"

# ---------- Custom nodes ----------
clone_or_pull() {
  local url="$1"
  local dir
  dir="$WORKSPACE/custom_nodes/$(basename "$url" .git)"
  if [ ! -d "$dir" ]; then
    git clone "$url" "$dir"
  else
    git -C "$dir" pull --ff-only || true
  fi
  if [ -f "$dir/requirements.txt" ]; then
    pip install -r "$dir/requirements.txt" || true
  fi
}

echo "==> Instalando custom nodes en $WORKSPACE/custom_nodes"
clone_or_pull https://github.com/ltdrdata/ComfyUI-Manager.git
clone_or_pull https://github.com/ltdrdata/ComfyUI-Impact-Pack.git           # FaceDetailer / ADetailer
clone_or_pull https://github.com/cubiq/ComfyUI_IPAdapter_plus.git           # IP-Adapter FaceID
clone_or_pull https://github.com/Gourieff/ComfyUI-ReActor.git               # face-swap
clone_or_pull https://github.com/cubiq/PuLID_ComfyUI.git                    # PuLID-Flux
clone_or_pull https://github.com/Fannovel16/comfyui_controlnet_aux.git
clone_or_pull https://github.com/kijai/ComfyUI-WanVideoWrapper.git          # Wan 2.2 I2V
clone_or_pull https://github.com/rgthree/rgthree-comfy.git

# ---------- Aux Python deps ----------
echo "==> Instalando deps aux"
pip install --quiet \
  insightface==0.7.3 \
  onnxruntime-gpu \
  || true

# ---------- Tools de training (LoRA) ----------
if [ ! -d "$WORKSPACE/kohya_ss" ]; then
  echo "==> Cloning kohya_ss"
  git clone https://github.com/bmaltais/kohya_ss "$WORKSPACE/kohya_ss"
fi
if [ ! -d "$WORKSPACE/ai-toolkit" ]; then
  echo "==> Cloning ai-toolkit (Ostris)"
  git clone https://github.com/ostris/ai-toolkit "$WORKSPACE/ai-toolkit"
  pip install -r "$WORKSPACE/ai-toolkit/requirements.txt" || true
fi

# ---------- Model downloads (comentado — descomentar lo que necesites) ----------
# Necesitás `HF_TOKEN` exportado (gated repos como FLUX.1-dev requieren auth).
#
# echo "==> Downloading FLUX.1-dev (24GB)"
# huggingface-cli download black-forest-labs/FLUX.1-dev flux1-dev.safetensors \
#   --local-dir "$WORKSPACE/models/diffusion_models" --local-dir-use-symlinks False
#
# echo "==> Downloading bigASP v2 (~7GB)"
# wget -O "$WORKSPACE/models/checkpoints/bigaspv2.safetensors" \
#   https://huggingface.co/fancyfeast/bigASP/resolve/main/bigaspv2.safetensors
#
# echo "==> Downloading 4x-UltraSharp upscaler"
# wget -O "$WORKSPACE/models/upscale_models/4x-UltraSharp.pth" \
#   https://huggingface.co/Kim2091/UltraSharp/resolve/main/4x-UltraSharp.pth

echo ""
echo "==> Setup complete."
echo "    Restart ComfyUI to pick up new custom nodes:"
echo "      supervisorctl restart comfyui     # ai-dock manages ComfyUI via supervisor"
echo "    Or kill & restart manually:"
echo "      pkill -f 'python.*main.py' && cd $COMFY_DIR && python main.py --listen 0.0.0.0 --port 8188 &"
