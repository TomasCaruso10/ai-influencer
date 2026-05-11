"""Batch generation FLUX + LoRA v2 via ComfyUI HTTP API.

Iterates prompts × seeds, submits workflow, polls for completion,
downloads outputs to local dir. NO FaceDetailer en esta versión simple.

Uso (en pod):
    python scripts/generate_batch_v2.py \\
        --comfy-url http://127.0.0.1:18188 \\
        --workflow workflows/flux_with_lora_simple_v2.json \\
        --prompts /workspace/prompts_eval_v2.txt \\
        --seeds 42,123,777 \\
        --output /workspace/outputs/v2_batch
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


def submit_prompt(comfy_url: str, workflow: dict) -> str:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(f"{comfy_url}/prompt", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    return data["prompt_id"]


def wait_completion(comfy_url: str, prompt_id: str, timeout: int = 300) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{comfy_url}/history/{prompt_id}", timeout=15) as resp:
            history = json.load(resp)
        entry = history.get(prompt_id)
        if entry is not None:
            status = entry.get("status", {})
            if status.get("completed") is True or entry.get("outputs"):
                return entry
        time.sleep(2)
    raise TimeoutError(f"prompt_id={prompt_id} did not complete in {timeout}s")


def download_image(comfy_url: str, filename: str, subfolder: str, type_: str, dst: Path) -> None:
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": type_})
    with urllib.request.urlopen(f"{comfy_url}/view?{params}", timeout=60) as resp:
        dst.write_bytes(resp.read())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--comfy-url", default="http://127.0.0.1:18188")
    ap.add_argument("--workflow", type=Path, required=True)
    ap.add_argument("--prompts", type=Path, required=True)
    ap.add_argument("--seeds", default="42,123", help="comma-separated")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--prompt-node-id", default="15", help="ID of CLIPTextEncode positive node")
    ap.add_argument("--seed-node-id", default="19", help="ID of KSampler node")
    ap.add_argument("--save-node-id", default="21", help="ID of SaveImage node (or 40 for v2)")
    args = ap.parse_args()

    workflow_template = json.loads(args.workflow.read_text())
    prompts = [
        line.strip()
        for line in args.prompts.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    seeds = [int(s) for s in args.seeds.split(",")]

    args.output.mkdir(parents=True, exist_ok=True)

    total = len(prompts) * len(seeds)
    counter = 0
    for prompt_idx, prompt in enumerate(prompts):
        for seed in seeds:
            counter += 1
            workflow = json.loads(json.dumps(workflow_template))
            workflow[args.prompt_node_id]["inputs"]["text"] = prompt
            workflow[args.seed_node_id]["inputs"]["seed"] = seed
            # Override save prefix per pair for unique names
            workflow[args.save_node_id]["inputs"]["filename_prefix"] = f"v2_p{prompt_idx:02d}_s{seed}"

            print(f"[{counter}/{total}] prompt={prompt[:60]}... seed={seed}", flush=True)
            try:
                pid = submit_prompt(args.comfy_url, workflow)
                hist = wait_completion(args.comfy_url, pid, timeout=180)
                # Find output image
                outputs = hist.get("outputs", {}).get(args.save_node_id, {}).get("images", [])
                for img in outputs:
                    dst = args.output / f"v2_p{prompt_idx:02d}_s{seed}_{img['filename']}"
                    download_image(args.comfy_url, img["filename"], img.get("subfolder", ""), img.get("type", "output"), dst)
                    print(f"    saved {dst.name}", flush=True)
            except Exception as exc:
                print(f"    ERROR: {exc}", flush=True)

    print(f"\nDone. {counter} jobs submitted. Output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
