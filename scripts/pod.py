"""Lifecycle del pod RunPod desde local. Infra-as-code minimal.

Comandos:
    up       crear pod (terminate-recreate idempotente), esperar ready, mostrar URLs
    down     terminar pod (libera GPU, network volume persiste)
    status   info del pod del proyecto (running, costo, URLs)
    ssh      imprimir comando SSH al pod activo
    session  up + esperar Ctrl+C + down automático (lifecycle interactivo)

Usa el SDK oficial `runpod`. Config en `.env` (ver `.env.example`).
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

import logfire
import runpod

PROJECT_TAG = "ai-influencer-mvp"
HTTP_PORTS = (8188, 8888)  # ComfyUI + Jupyter
SSH_PORT = 22


def load_dotenv(path: Path = Path(".env")) -> None:
    """Mini-parser de .env. Sin dependencia externa."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_config() -> dict[str, Any]:
    load_dotenv()
    required = ["RUNPOD_API_KEY", "RUNPOD_VOLUME_ID"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing env vars: {missing}. Copy .env.example to .env and fill them.")

    return {
        "api_key": os.environ["RUNPOD_API_KEY"],
        "volume_id": os.environ["RUNPOD_VOLUME_ID"],
        "gpu_type": os.environ.get("RUNPOD_GPU_TYPE", "NVIDIA GeForce RTX 4090"),
        "cloud_type": os.environ.get("RUNPOD_CLOUD_TYPE", "COMMUNITY").upper(),
        "image": os.environ.get("RUNPOD_IMAGE", "ghcr.io/ai-dock/comfyui:latest-cuda"),
        "container_disk_gb": int(os.environ.get("RUNPOD_CONTAINER_DISK_GB", "50")),
        "ssh_pubkey": os.environ.get("RUNPOD_SSH_PUBKEY", ""),
        "region": os.environ.get("RUNPOD_REGION", ""),
    }


def find_project_pod() -> dict[str, Any] | None:
    pods = runpod.get_pods() or []
    for pod in pods:
        if pod.get("name") == PROJECT_TAG:
            return pod
    return None


def fetch_pod(pod_id: str) -> dict[str, Any]:
    info = runpod.get_pod(pod_id)
    return info or {}


def print_pod_info(pod: dict[str, Any]) -> None:
    pod_id = pod.get("id", "?")
    runtime = pod.get("runtime") or {}
    ports = runtime.get("ports") or []

    print(f"\nPod:    {pod.get('name')} ({pod_id})")
    print(f"Status: {pod.get('desiredStatus')}")
    print(f"GPU:    {pod.get('machine', {}).get('gpuDisplayName', '?')}")
    cost_per_hr = pod.get("costPerHr")
    if cost_per_hr:
        print(f"Cost:   ${cost_per_hr}/h")
    uptime = runtime.get("uptimeInSeconds")
    if uptime:
        print(f"Uptime: {uptime // 60} min")

    if not ports:
        print("(no ports yet — pod still booting)")
        return

    for p in ports:
        priv = p.get("privatePort")
        pub = p.get("publicPort")
        ip = p.get("ip")
        proto = p.get("type", "tcp")
        if priv == SSH_PORT and ip and pub:
            print(f"SSH:    ssh root@{ip} -p {pub}")
        elif priv in HTTP_PORTS and proto == "http":
            label = "ComfyUI" if priv == 8188 else "Jupyter"
            print(f"{label:8} https://{pod_id}-{priv}.proxy.runpod.net")


def cmd_up(args: argparse.Namespace) -> None:
    cfg = get_config()
    runpod.api_key = cfg["api_key"]

    existing = find_project_pod()
    if existing:
        logfire.info("pod already exists id={pod_id}", pod_id=existing["id"])
        print_pod_info(fetch_pod(existing["id"]))
        return

    if not cfg["ssh_pubkey"]:
        logfire.warning("RUNPOD_SSH_PUBKEY empty — SSH won't work, only HTTP proxy")

    env_vars = {}
    if cfg["ssh_pubkey"]:
        env_vars["PUBLIC_KEY"] = cfg["ssh_pubkey"]

    logfire.info(
        "creating pod gpu={gpu} cloud={cloud} image={image}",
        gpu=cfg["gpu_type"],
        cloud=cfg["cloud_type"],
        image=cfg["image"],
    )

    base_kwargs = dict(
        name=PROJECT_TAG,
        image_name=cfg["image"],
        gpu_type_id=cfg["gpu_type"],
        container_disk_in_gb=cfg["container_disk_gb"],
        volume_in_gb=0,
        ports="8188/http,8888/http,22/tcp",
        network_volume_id=cfg["volume_id"],
        volume_mount_path="/workspace",
        env=env_vars,
    )
    if cfg["region"]:
        base_kwargs["data_center_id"] = cfg["region"]

    # Fallback chain: probar COMMUNITY primero (más barato), si no hay stock SECURE.
    primary = cfg["cloud_type"]
    fallback = "SECURE" if primary == "COMMUNITY" else "COMMUNITY"
    cloud_chain = [primary, fallback] if primary != fallback else [primary]

    pod = None
    for cloud in cloud_chain:
        try:
            logfire.info("trying create_pod cloud={cloud}", cloud=cloud)
            pod = runpod.create_pod(cloud_type=cloud, **base_kwargs)
            print(f"Pod created on {cloud} cloud.")
            break
        except Exception as e:
            msg = str(e).lower()
            if "no longer any instances" in msg or "unavailable" in msg or "no available" in msg:
                logfire.warning("no stock on cloud={cloud}, trying next", cloud=cloud)
                continue
            raise

    if pod is None:
        sys.exit(
            f"No available GPUs for {cfg['gpu_type']} on either {cloud_chain}. "
            "Try different RUNPOD_REGION or RUNPOD_GPU_TYPE."
        )

    pod_id = pod["id"]
    logfire.info("pod created id={pod_id}", pod_id=pod_id)

    print(f"Waiting for pod {pod_id} to be ready (typical ~60-90s)", end="", flush=True)
    deadline = time.time() + 300
    last_status = None
    while time.time() < deadline:
        info = fetch_pod(pod_id)
        status = info.get("desiredStatus")
        if status != last_status:
            print(f" [{status}]", end="", flush=True)
            last_status = status
        runtime = info.get("runtime") or {}
        if runtime.get("uptimeInSeconds", 0) > 0 and (runtime.get("ports") or []):
            print()
            print_pod_info(info)
            print(
                f"\nNote: ai-dock images take ~2-3 min after `uptime` reports >0 to fully load ComfyUI."
            )
            print(f"Test with: curl -sS https://{pod_id}-8188.proxy.runpod.net/system_stats")
            return
        time.sleep(5)
        print(".", end="", flush=True)

    sys.exit(f"\nPod {pod_id} did not become ready in 5 minutes. Check the RunPod console.")


def cmd_down(args: argparse.Namespace) -> None:
    cfg = get_config()
    runpod.api_key = cfg["api_key"]

    pod = find_project_pod()
    if not pod:
        print(f"No pod found for project {PROJECT_TAG}")
        return

    pod_id = pod["id"]
    if not args.yes:
        confirm = input(f"Terminate pod {pod_id}? Network volume keeps all data. [y/N] ")
        if confirm.lower() != "y":
            print("Cancelled.")
            return

    logfire.info("terminating pod id={pod_id}", pod_id=pod_id)
    runpod.terminate_pod(pod_id)
    print(f"Terminated {pod_id}. Network volume preserved.")


def cmd_status(args: argparse.Namespace) -> None:
    cfg = get_config()
    runpod.api_key = cfg["api_key"]

    pod = find_project_pod()
    if not pod:
        print(f"No pod for project {PROJECT_TAG}. Run `pod.py up` to create.")
        return
    print_pod_info(fetch_pod(pod["id"]))


def cmd_ssh(args: argparse.Namespace) -> None:
    cfg = get_config()
    runpod.api_key = cfg["api_key"]

    pod = find_project_pod()
    if not pod:
        sys.exit(f"No pod for project {PROJECT_TAG}")

    info = fetch_pod(pod["id"])
    runtime = info.get("runtime") or {}
    for p in runtime.get("ports") or []:
        if p.get("privatePort") == SSH_PORT and p.get("ip") and p.get("publicPort"):
            print(f"ssh root@{p['ip']} -p {p['publicPort']}")
            return
    sys.exit("SSH port not exposed yet (pod still booting?). Try again in ~30s.")


def cmd_session(args: argparse.Namespace) -> None:
    """`up` + esperar Ctrl+C + auto `down`. Lifecycle interactivo."""
    cmd_up(args)
    print("\n" + "=" * 70)
    print("  Pod running. Press Ctrl+C to TERMINATE the pod and exit.")
    print("  (Closing the terminal without Ctrl+C leaves the pod running!)")
    print("=" * 70)
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\nReceived interrupt. Terminating pod...")
        args.yes = True
        cmd_down(args)


def main() -> int:
    logfire.configure(send_to_logfire=False, console=False)

    ap = argparse.ArgumentParser(
        description="RunPod lifecycle for ai-influencer MVP", prog="pod.py"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("up", help="Create pod (idempotent: returns existing if any)")

    p_down = sub.add_parser("down", help="Terminate pod (volume persists)")
    p_down.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    sub.add_parser("status", help="Show pod info")
    sub.add_parser("ssh", help="Print SSH command")
    sub.add_parser("session", help="up + wait for Ctrl+C + auto down")

    args = ap.parse_args()

    handlers = {
        "up": cmd_up,
        "down": cmd_down,
        "status": cmd_status,
        "ssh": cmd_ssh,
        "session": cmd_session,
    }
    handlers[args.cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
