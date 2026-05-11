"""Cliente Python para invocar ComfyUI en batch — bootstrap de candidatos.

Uso típico:
    python scripts/generate_batch.py \
        --workflow workflows/bootstrap_candidates.json \
        --canon prompts/identity_canon.txt \
        --negative prompts/safety_negative.txt \
        --variations prompts/sfw_lifestyle/bootstrap_variations.txt \
        --count 200 \
        --seed-start 1 \
        --output-dir outputs/candidates \
        --base-url https://wq7e7d1nirvjxi-8188.proxy.runpod.net

Cada iteración:
    seed = seed-start + i
    variation = variations[i % len(variations)]   # rotación
    positive = canon + ", " + variation
    negative = safety_negative

El workflow JSON debe tener nodos con _meta.title que contengan:
    - "POSITIVE"  → text se reemplaza con positive
    - "NEGATIVE"  → text se reemplaza con negative
    - cualquier KSampler  → seed se reemplaza
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx
import logfire
from tqdm import tqdm


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_prompt_file(path: Path) -> str:
    """Carga un archivo de prompt: ignora líneas vacías y comentarios `#`,
    concatena el resto en una línea separada por comas.
    """
    if not path.exists():
        return ""
    parts = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts.append(line.rstrip(","))
    return ", ".join(parts)


def load_variations_file(path: Path) -> list[str]:
    """Carga variations: una línea por variation, ignora vacías y `#`."""
    if not path.exists():
        return [""]
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out or [""]


def load_workflow(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def apply_inputs(workflow: dict, *, positive: str, negative: str, seed: int) -> dict:
    """Reemplaza positive/negative/seed en el workflow.
    Convención: nodos con title que contenga POSITIVE / NEGATIVE / KSampler.
    """
    wf = json.loads(json.dumps(workflow))  # deep copy
    for node in wf.values():
        title = (node.get("_meta") or {}).get("title", "").upper()
        ctype = node.get("class_type", "")
        inputs = node.get("inputs", {})
        if "POSITIVE" in title and "text" in inputs:
            inputs["text"] = positive
        elif "NEGATIVE" in title and "text" in inputs:
            inputs["text"] = negative
        elif ctype == "KSampler" and "seed" in inputs:
            inputs["seed"] = seed
    return wf


def queue_prompt(client: httpx.Client, base_url: str, workflow: dict, client_id: str) -> str:
    resp = client.post(
        f"{base_url}/prompt",
        json={"prompt": workflow, "client_id": client_id},
        timeout=30,
    )
    if resp.status_code >= 400:
        logfire.error(
            "queue_prompt failed status={status} body={body}",
            status=resp.status_code,
            body=resp.text[:500],
        )
        resp.raise_for_status()
    return resp.json()["prompt_id"]


def wait_history(client: httpx.Client, base_url: str, prompt_id: str, timeout: float = 600) -> dict:
    """Poll /history with resilient retries — el SSH tunnel puede tener hiccups
    durante descargas concurrentes en el pod."""
    deadline = time.time() + timeout
    consecutive_errors = 0
    while time.time() < deadline:
        try:
            r = client.get(f"{base_url}/history/{prompt_id}", timeout=60)
            consecutive_errors = 0
            if r.status_code == 200:
                data = r.json()
                if prompt_id in data:
                    return data[prompt_id]
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
            consecutive_errors += 1
            logfire.warning(
                "transient http error polling history (n={n}): {err}",
                n=consecutive_errors,
                err=str(e)[:120],
            )
            if consecutive_errors >= 5:
                raise
            time.sleep(min(2 ** consecutive_errors, 10))
            continue
        time.sleep(1.5)
    raise TimeoutError(f"prompt {prompt_id} not finished within {timeout}s")


def download_outputs(
    client: httpx.Client,
    base_url: str,
    history: dict,
    output_dir: Path,
    prefix: str,
) -> list[Path]:
    saved: list[Path] = []
    outputs = history.get("outputs", {})
    for node_id, node_out in outputs.items():
        for img in node_out.get("images", []):
            params = {
                "filename": img["filename"],
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output"),
            }
            r = client.get(f"{base_url}/view", params=params, timeout=120)
            r.raise_for_status()
            ext = Path(img["filename"]).suffix or ".png"
            dest = output_dir / f"{prefix}{ext}"
            dest.write_bytes(r.content)
            saved.append(dest)
    return saved


def main() -> int:
    ap = argparse.ArgumentParser(description="ComfyUI batch generator")
    ap.add_argument("--workflow", type=Path, required=True)
    ap.add_argument("--canon", type=Path, required=True, help="prompts/identity_canon.txt")
    ap.add_argument("--negative", type=Path, required=True, help="prompts/safety_negative.txt")
    ap.add_argument(
        "--variations",
        type=Path,
        default=None,
        help="prompts/.../bootstrap_variations.txt (opcional)",
    )
    ap.add_argument("--count", type=int, default=200)
    ap.add_argument("--seed-start", type=int, default=1)
    ap.add_argument("--output-dir", type=Path, default=Path("outputs/candidates"))
    ap.add_argument(
        "--base-url",
        default=None,
        help="ComfyUI URL. Default: COMFY_URL env var",
    )
    args = ap.parse_args()

    load_dotenv()
    base_url = (args.base_url or os.environ.get("COMFY_URL", "")).rstrip("/")
    if not base_url:
        sys.exit("Missing --base-url or COMFY_URL env var")

    logfire.configure(send_to_logfire=False, console=False)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    canon = load_prompt_file(args.canon)
    negative = load_prompt_file(args.negative)
    variations = load_variations_file(args.variations) if args.variations else [""]
    workflow_template = load_workflow(args.workflow)

    if not canon:
        sys.exit(f"Canon empty: {args.canon}")
    if not negative:
        sys.exit(f"Negative empty: {args.negative}")

    print(f"Canon ({len(canon)} chars): {canon[:120]}...")
    print(f"Variations: {len(variations)}")
    print(f"Generating {args.count} candidates -> {args.output_dir}")
    print(f"ComfyUI: {base_url}")

    client_id = str(uuid.uuid4())
    failures = 0
    with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        for i in tqdm(range(args.count), desc="generations"):
            seed = args.seed_start + i
            variation = variations[i % len(variations)]
            positive = f"{canon}, {variation}" if variation else canon

            try:
                wf = apply_inputs(workflow_template, positive=positive, negative=negative, seed=seed)
                prompt_id = queue_prompt(client, base_url, wf, client_id)
                history = wait_history(client, base_url, prompt_id, timeout=300)
                saved = download_outputs(
                    client,
                    base_url,
                    history,
                    args.output_dir,
                    prefix=f"seed{seed:06d}",
                )
                logfire.info(
                    "generated seed={seed} variation_idx={vi} files={n}",
                    seed=seed,
                    vi=i % len(variations),
                    n=len(saved),
                )
            except Exception as e:
                failures += 1
                logfire.warning(
                    "skipping seed={seed} due to error (failures={f}): {err}",
                    seed=seed,
                    f=failures,
                    err=str(e)[:200],
                )
                if failures >= 10:
                    print(f"\nABORT: too many failures ({failures}). Check pod / tunnel.")
                    return 2
                time.sleep(3)
                continue
    print(f"\nDone. {args.count - failures}/{args.count} succeeded. Output in {args.output_dir}")

    print(f"\nDone. Output in {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
