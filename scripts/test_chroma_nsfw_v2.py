"""Test Chroma + LoRA NSFW v2 - prompts explícitos sin filtros restrictivos."""
import json, os, sys, time, uuid
from pathlib import Path
import httpx

ROOT = Path(__file__).parent.parent
WORKFLOW = ROOT / "workflows" / "chroma_with_lora.json"
OUT = ROOT / "outputs" / "chroma_nsfw_v2"
OUT.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:8188"

PHYSICAL = "italian woman, long jet black hair, hazel green eyes, fair porcelain skin"

PROMPTS = [
    ("01_topless",   f"aiinfluencer1, {PHYSICAL}, topless portrait, bare breasts visible, natural nipples, soft window light, photorealistic, nude, nsfw"),
    ("02_full_nude", f"aiinfluencer1, {PHYSICAL}, fully nude standing, anatomically detailed, natural body, soft studio lighting, full body view, photorealistic, nude, nsfw"),
    ("03_bedroom",   f"aiinfluencer1, {PHYSICAL}, lying nude on white bed sheets, breasts visible, sensual pose, soft morning light, photorealistic, nude, nsfw"),
    ("04_explicit",  f"aiinfluencer1, {PHYSICAL}, explicit nude pose, spread legs, anatomically correct vulva, intimate close, photorealistic, nude, nsfw, explicit"),
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
