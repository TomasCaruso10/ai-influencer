#!/usr/bin/env bash
# Entrenamiento de LoRA SDXL del personaje, vía kohya_ss.
# Correr DENTRO del pod RunPod después de runpod_setup.sh.
#
# Pre-requisitos:
#   - ~30 imágenes canon curadas en $DATASET_DIR (1024x1024 idealmente, bucketing OK).
#   - SDXL base checkpoint en /workspace/ComfyUI/models/checkpoints/.
#   - kohya_ss instalado:
#       cd /workspace && git clone https://github.com/bmaltais/kohya_ss
#       cd kohya_ss && bash setup.sh
#
# Salida:
#   /workspace/loras/<CHARACTER_NAME>_sdxl.safetensors

set -euo pipefail

CHARACTER_NAME="${CHARACTER_NAME:-canon}"
DATASET_DIR="${DATASET_DIR:-/workspace/datasets/$CHARACTER_NAME}"
OUTPUT_DIR="${OUTPUT_DIR:-/workspace/loras}"
SDXL_CKPT="${SDXL_CKPT:-/workspace/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors}"
KOHYA_DIR="${KOHYA_DIR:-/workspace/kohya_ss}"

# Sweet-spot params (ver docs/research/modelos-nsfw.md §2)
NETWORK_DIM=32
NETWORK_ALPHA=16
LR=1e-4
MAX_STEPS=2000

mkdir -p "$OUTPUT_DIR"

cd "$KOHYA_DIR"
source venv/bin/activate

accelerate launch --num_cpu_threads_per_process=2 \
  sdxl_train_network.py \
  --pretrained_model_name_or_path="$SDXL_CKPT" \
  --train_data_dir="$DATASET_DIR" \
  --output_dir="$OUTPUT_DIR" \
  --output_name="${CHARACTER_NAME}_sdxl" \
  --resolution="1024,1024" \
  --network_module=networks.lora \
  --network_dim=$NETWORK_DIM \
  --network_alpha=$NETWORK_ALPHA \
  --learning_rate=$LR \
  --lr_scheduler=cosine \
  --optimizer_type=AdamW8bit \
  --max_train_steps=$MAX_STEPS \
  --train_batch_size=1 \
  --gradient_accumulation_steps=4 \
  --mixed_precision=bf16 \
  --save_precision=bf16 \
  --save_model_as=safetensors \
  --enable_bucket \
  --bucket_reso_steps=64 \
  --bucket_no_upscale \
  --gradient_checkpointing \
  --xformers \
  --cache_latents \
  --max_data_loader_n_workers=2 \
  --seed=42

echo "==> Done. LoRA saved to $OUTPUT_DIR/${CHARACTER_NAME}_sdxl.safetensors"
