"""Test del LoRA FINAL con 10 prompts variados."""
import json, os, sys, time, uuid
from pathlib import Path
import httpx

ROOT = Path(__file__).parent.parent
WORKFLOW = ROOT / "workflows" / "flux_with_lora.json"
OUT = ROOT / "outputs" / "lora_final_test"
OUT.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:8188"
LORA_NAME = "aiinfluencer1_flux_FINAL.safetensors"

PHYSICAL = "italian woman, long jet black hair, hazel green eyes, fair porcelain skin"

PROMPTS = [
    ("01_portrait", f"aiinfluencer1, {PHYSICAL}, portrait close-up, soft natural lighting, looking at camera, photorealistic"),
    ("02_cafe",     f"aiinfluencer1, {PHYSICAL}, sitting at a cafe, holding coffee cup, casual outfit, candid moment, photorealistic"),
    ("03_gym",      f"aiinfluencer1, {PHYSICAL}, gym selfie, athletic sports bra and leggings, mirror reflection, photorealistic"),
    ("04_beach",    f"aiinfluencer1, {PHYSICAL}, at the beach, white bikini, ocean background, golden hour, photorealistic"),
    ("05_street",   f"aiinfluencer1, {PHYSICAL}, walking on a city street, denim jacket, urban background, instagram aesthetic, photorealistic"),
    ("06_kitchen",  f"aiinfluencer1, {PHYSICAL}, in a modern kitchen morning, cozy hoodie, soft daylight, photorealistic"),
    ("07_party",    f"aiinfluencer1, {PHYSICAL}, at a rooftop party night, elegant black dress, neon lights, smiling, photorealistic"),
    ("08_smile",    f"aiinfluencer1, {PHYSICAL}, smiling close-up portrait, soft beauty lighting, magazine quality, photorealistic"),
    ("09_yoga",     f"aiinfluencer1, {PHYSICAL}, yoga pose at sunrise terrace, athletic wear, peaceful expression, photorealistic"),
    ("10_studio",   f"aiinfluencer1, {PHYSICAL}, professional studio portrait, white background, fashion editorial, photorealistic"),
]

wf = json.loads(WORKFLOW.read_text())
client_id = str(uuid.uuid4())

with httpx.Client(timeout=httpx.Timeout(120.0)) as cli:
    for ctx_name, prompt in PROMPTS:
        dest = OUT / f"{ctx_name}.png"
        if dest.exists():
            print(f"skip exists: {dest.name}", flush=True); continue

        wf2 = json.loads(json.dumps(wf))
        wf2["13"]["inputs"]["lora_name"] = LORA_NAME
        wf2["13"]["inputs"]["strength_model"] = 1.0
        wf2["15"]["inputs"]["text"] = prompt
        wf2["19"]["inputs"]["seed"] = 42
        wf2["21"]["inputs"]["filename_prefix"] = ctx_name

        print(f"{ctx_name}: queueing...", flush=True)
        r = cli.post(f"{BASE_URL}/prompt", json={"prompt": wf2, "client_id": client_id})
        r.raise_for_status()
        pid = r.json()["prompt_id"]

        done = False
        errs = 0
        for _ in range(200):
            try:
                rh = cli.get(f"{BASE_URL}/history/{pid}", timeout=30)
                errs = 0
                if rh.status_code == 200 and pid in rh.json():
                    hist = rh.json()[pid]
                    for nid, out in (hist.get("outputs") or {}).items():
                        for img in out.get("images", []):
                            params = {"filename": img["filename"], "subfolder": img.get("subfolder",""), "type": img.get("type","output")}
                            rv = cli.get(f"{BASE_URL}/view", params=params, timeout=120)
                            dest.write_bytes(rv.content)
                            print(f"  saved {dest.name}", flush=True)
                    done = True; break
            except (httpx.ReadTimeout, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                errs += 1; print(f"  retry {errs}: {str(e)[:60]}", flush=True)
                if errs >= 8: break
                time.sleep(3); continue
            time.sleep(2)
        if not done: print(f"  FAILED {ctx_name} — continuing", flush=True)

print(f"\nDone. Files in {OUT}")
