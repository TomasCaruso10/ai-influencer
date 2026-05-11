#!/usr/bin/env bash
# Entrenamiento de LoRA FLUX del personaje, vía AI-Toolkit (Ostris).
# Correr DENTRO del pod RunPod después de runpod_setup.sh.
#
# Pre-requisitos:
#   - ~30 imágenes canon curadas en $DATASET_DIR (mismas que LoRA SDXL).
#   - FLUX.1-dev en /workspace/ComfyUI/models/diffusion_models/flux1-dev.safetensors.
#   - AI-Toolkit instalado:
#       cd /workspace && git clone https://github.com/ostris/ai-toolkit
#       cd ai-toolkit && pip install -r requirements.txt
#
# AI-Toolkit usa archivos YAML de config (no CLI flags como kohya).
# Este script genera un YAML on-the-fly y lo ejecuta.
#
# Salida:
#   /workspace/loras/<CHARACTER_NAME>_flux.safetensors

set -euo pipefail

CHARACTER_NAME="${CHARACTER_NAME:-canon}"
DATASET_DIR="${DATASET_DIR:-/workspace/datasets/$CHARACTER_NAME}"
OUTPUT_DIR="${OUTPUT_DIR:-/workspace/loras}"
FLUX_PATH="${FLUX_PATH:-/workspace/ComfyUI/models/diffusion_models/flux1-dev.safetensors}"
AITK_DIR="${AITK_DIR:-/workspace/ai-toolkit}"

NETWORK_DIM=32
LR=1e-4
MAX_STEPS=2000
RESOLUTION=1024
TRIGGER_WORD="${TRIGGER_WORD:-${CHARACTER_NAME}}"  # token único para invocar a la persona

mkdir -p "$OUTPUT_DIR"

CONFIG_FILE="/tmp/${CHARACTER_NAME}_flux_config.yaml"
cat > "$CONFIG_FILE" <<EOF
job: extension
config:
  name: ${CHARACTER_NAME}_flux
  process:
    - type: sd_trainer
      training_folder: ${OUTPUT_DIR}
      device: cuda:0
      trigger_word: ${TRIGGER_WORD}
      network:
        type: lora
        linear: ${NETWORK_DIM}
        linear_alpha: ${NETWORK_DIM}
      save:
        dtype: bf16
        save_every: 250
        max_step_saves_to_keep: 4
      datasets:
        - folder_path: ${DATASET_DIR}
          caption_ext: txt
          caption_dropout_rate: 0.05
          shuffle_tokens: false
          cache_latents_to_disk: true
          resolution: [${RESOLUTION}]
      train:
        batch_size: 1
        steps: ${MAX_STEPS}
        gradient_accumulation_steps: 1
        train_unet: true
        train_text_encoder: false
        gradient_checkpointing: true
        noise_scheduler: flowmatch
        timestep_type: linear
        optimizer: adamw8bit
        lr: ${LR}
        ema_config:
          use_ema: true
          ema_decay: 0.99
        dtype: bf16
      model:
        name_or_path: ${FLUX_PATH}
        is_flux: true
        quantize: true
      sample:
        sampler: flowmatch
        sample_every: 250
        width: 1024
        height: 1024
        prompts:
          - "${TRIGGER_WORD} adult woman, 25 years old, portrait, soft natural lighting, photorealistic"
          - "${TRIGGER_WORD} adult woman, 25 years old, full body, casual outfit, outdoor"
        neg: ""
        seed: 42
        guidance_scale: 4
        sample_steps: 24
EOF

cd "$AITK_DIR"
python run.py "$CONFIG_FILE"

echo "==> Done. LoRA saved to $OUTPUT_DIR/${CHARACTER_NAME}_flux/${CHARACTER_NAME}_flux.safetensors"
