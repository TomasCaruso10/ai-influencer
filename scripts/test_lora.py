"""Test del LoRA en ComfyUI con varias strengths.
Genera 4 prompts × 2 strengths = 8 imágenes para ver si la cara aprendida pega.
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
WORKFLOW = ROOT / "workflows" / "flux_with_lora.json"
OUT = ROOT / "outputs" / "lora_test"
OUT.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:8188"

PROMPTS = [
    ("portrait", "aiinfluencer1, italian woman, long jet black hair, hazel green eyes, fair porcelain skin, portrait close-up, soft natural lighting, looking at camera, photorealistic"),
    ("cafe",     "aiinfluencer1, italian woman, long jet black hair, hazel green eyes, fair porcelain skin, full body shot at a cafe, casual outfit, instagram aesthetic, photorealistic"),
    ("gym",      "aiinfluencer1, italian woman, long jet black hair, hazel green eyes, fair porcelain skin, gym selfie, athletic wear, mirror reflection, photorealistic"),
    ("beach",    "aiinfluencer1, italian woman, long jet black hair, hazel green eyes, fair porcelain skin, at the beach, summer outfit, golden hour, photorealistic"),
]

STRENGTHS = [1.0, 1.5]

wf = json.loads(WORKFLOW.read_text())
client_id = str(uuid.uuid4())

with httpx.Client(timeout=httpx.Timeout(120.0)) as cli:
    for strength in STRENGTHS:
        for ctx_name, prompt in PROMPTS:
            dest = OUT / f"s{strength}_{ctx_name}.png"
            if dest.exists():
                print(f"skip exists: {dest.name}", flush=True)
                continue

            wf2 = json.loads(json.dumps(wf))
            wf2["13"]["inputs"]["strength_model"] = strength
            wf2["15"]["inputs"]["text"] = prompt
            wf2["19"]["inputs"]["seed"] = 42
            wf2["21"]["inputs"]["filename_prefix"] = f"s{strength}_{ctx_name}"

            print(f"strength={strength} {ctx_name}: queueing...", flush=True)
            r = cli.post(f"{BASE_URL}/prompt", json={"prompt": wf2, "client_id": client_id})
            r.raise_for_status()
            pid = r.json()["prompt_id"]

            done = False
            errors = 0
            for _ in range(200):
                try:
                    rh = cli.get(f"{BASE_URL}/history/{pid}", timeout=30)
                    errors = 0
                    if rh.status_code == 200 and pid in rh.json():
                        hist = rh.json()[pid]
                        for node_id, out in (hist.get("outputs") or {}).items():
                            for img in out.get("images", []):
                                params = {"filename": img["filename"], "subfolder": img.get("subfolder",""), "type": img.get("type","output")}
                                rv = cli.get(f"{BASE_URL}/view", params=params, timeout=120)
                                dest.write_bytes(rv.content)
                                print(f"  saved {dest.name}", flush=True)
                        done = True
                        break
                except (httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                    errors += 1
                    print(f"  retry {errors}: {e}", flush=True)
                    if errors >= 8:
                        break
                    time.sleep(3)
                    continue
                time.sleep(2)
            if not done:
                print(f"  FAILED {ctx_name} — continuing", flush=True)

print(f"\nDone. Files in {OUT}")
