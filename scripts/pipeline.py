"""CLI entry point del pipeline.

Uso:
    python scripts/pipeline.py run --prompt "cafe portrait" --model flux+lora_aiinfluencer1
    python scripts/pipeline.py run --batch 5
"""

from __future__ import annotations

import argparse
import asyncio
import sys

import logfire

from aiinfluencer.pipeline import PieceRequest, run_piece
from aiinfluencer.pipeline.deps import WorkflowDeps


async def _run_once(request: PieceRequest, deps: WorkflowDeps) -> int:
    result = await run_piece(request, deps)
    print(result.model_dump_json(indent=2))
    if getattr(result, "result", None) == "rejected":
        return 2
    return 0


async def _run_batch(prompts: list[str], model: str, deps: WorkflowDeps) -> int:
    failures = 0
    for prompt in prompts:
        request = PieceRequest(prompt_seed=prompt, model_choice=model)
        result = await run_piece(request, deps)
        result_kind = getattr(result, "result", getattr(result, "status", "unknown"))
        print(f"{result_kind}: {result.model_dump_json()}")
        if result_kind == "rejected":
            failures += 1
    return 2 if failures > 0 else 0


def main() -> int:
    logfire.configure(send_to_logfire=False, console=False)

    ap = argparse.ArgumentParser(prog="pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Ejecutar pipeline para una o varias piezas")
    p_run.add_argument("--prompt", type=str, help="Prompt seed (1 pieza)")
    p_run.add_argument("--batch", type=int, default=0, help="N piezas con prompts genéricos")
    p_run.add_argument(
        "--model",
        default="flux+lora_aiinfluencer1",
        help="model_choice: flux+lora_aiinfluencer1 | chroma+lora_aiinfluencer1 | sdxl_bigasp+lora_sdxl_aiinfluencer1",
    )
    p_run.add_argument("--hitl", action="store_true", help="Activar HITL (pausa en review)")

    args = ap.parse_args()

    deps = WorkflowDeps.with_dummies()
    deps.auto_approve_in_review = not args.hitl

    if args.cmd == "run":
        if args.batch > 0:
            prompts = [f"placeholder prompt #{i}" for i in range(args.batch)]
            return asyncio.run(_run_batch(prompts, args.model, deps))
        if args.prompt:
            return asyncio.run(_run_once(PieceRequest(prompt_seed=args.prompt, model_choice=args.model), deps))
        ap.error("--prompt or --batch required")

    return 1


if __name__ == "__main__":
    sys.exit(main())
