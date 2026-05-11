"""Test Chroma + LoRA — hardcore límite del modelo."""
import json, os, sys, time, uuid
from pathlib import Path
import httpx

ROOT = Path(__file__).parent.parent
WORKFLOW = ROOT / "workflows" / "chroma_with_lora.json"
OUT = ROOT / "outputs" / "chroma_nsfw_v3_hardcore"
OUT.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:8188"

PHYSICAL = "italian woman, long jet black hair, hazel green eyes, fair porcelain skin"

PROMPTS = [
    ("01_doggystyle",  f"aiinfluencer1, {PHYSICAL}, on all fours doggystyle position, ass up in the air, exposed vulva and asshole visible from behind, detailed anatomy, photorealistic, nude, nsfw, explicit"),
    ("02_spread",      f"aiinfluencer1, {PHYSICAL}, lying on back legs spread wide open, fully exposed pussy, anatomically correct vulva detailed, photorealistic, nude, nsfw, explicit, gynecologic view"),
    ("03_ass_pussy",   f"aiinfluencer1, {PHYSICAL}, bent over showing ass and pussy from behind, hands on butt cheeks spreading, exposed asshole and vulva, photorealistic, nude, nsfw, explicit"),
    ("04_pov_blowjob", f"aiinfluencer1, {PHYSICAL}, kneeling on bed pov, mouth open tongue out looking up, suggestive blowjob position, naked body visible, photorealistic, nude, nsfw, explicit"),
]

wf = json.loads(WORKFLOW.read_text())
client_id = str(uuid.uuid4())

with httpx.Client(timeout=httpx.Timeout(120.0)) as cli:
    for ctx_name, prompt in PROMPTS:
        dest = OUT / f"{ctx_name}.png"
        if dest.exists():
            print(f"skip exists: {dest.name}", flush=True); continue

        wf2 = json.loads(json.dumps(wf))
        wf2["15"]["inputs"]["text"] = prompt
        wf2["21"]["inputs"]["noise_seed"] = 42
        wf2["24"]["inputs"]["filename_prefix"] = ctx_name

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
