"""BLIP-2 captioning para el dataset del LoRA.
Corre DENTRO del pod con el venv de ComfyUI.

Por cada imagen .png en DATASET_DIR genera un .txt con el caption.
El trigger word se prepende al inicio.
"""

import os
import sys
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
import torch

TRIGGER = "aiinfluencer1"
DATASET_DIR = "/workspace/datasets/aiinfluencer1"

print("Loading BLIP-2 (first time downloads ~2GB)...", flush=True)
processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-opt-2.7b", torch_dtype=torch.float16
).to("cuda")
print("Model loaded. Captioning...", flush=True)

files = sorted(f for f in os.listdir(DATASET_DIR) if f.endswith(".png"))
for i, fname in enumerate(files, 1):
    img_path = os.path.join(DATASET_DIR, fname)
    txt_path = img_path.replace(".png", ".txt")
    img = Image.open(img_path).convert("RGB")
    inputs = processor(img, return_tensors="pt").to("cuda", torch.float16)
    out = model.generate(**inputs, max_new_tokens=60)
    cap = processor.decode(out[0], skip_special_tokens=True).strip()
    final = TRIGGER + ", " + cap
    with open(txt_path, "w") as f:
        f.write(final)
    print("[" + str(i) + "/" + str(len(files)) + "] " + fname + ": " + final[:100], flush=True)

print("DONE", flush=True)
