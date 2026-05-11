"""GenerateNode — invoca ComfyUI con el workflow apropiado al model_choice.

Placeholder Fase 2.0: usa DummyComfyClient que crea archivo vacío. En Fase 2.x
se conecta a ComfyClient real (ya tenemos `scripts/generate_batch.py` como base).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.output import RejectionReason
from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.human_review import HumanReviewNode
    from aiinfluencer.pipeline.nodes.safety_filter import SafetyFilterNode


@dataclass
class GenerateNode(AppNode):
    """Invoca ComfyUI y guarda raw_image_path en state."""

    async def run(self, ctx: Context) -> "SafetyFilterNode | HumanReviewNode":
        from aiinfluencer.pipeline.nodes.safety_filter import SafetyFilterNode

        seed = ctx.state.seed if ctx.state.seed is not None else random.randint(1, 10**9)
        ctx.state.record.seed = seed
        ctx.state.record.status = "generating"

        positive = ctx.state.expanded_prompt_positive or ""
        negative = ctx.state.expanded_prompt_negative or ""

        try:
            # Workflow selection por model_choice — placeholder: dict vacío.
            # En implementación real: cargar JSON del workflow apropiado.
            workflow: dict = {}

            raw_path = await ctx.deps.comfy.submit_workflow(
                workflow=workflow,
                prompt=positive,
                negative=negative,
                seed=seed,
            )
            ctx.state.raw_image_path = raw_path
            logfire.info(
                "generated piece_id={piece_id} seed={seed} path={path}",
                piece_id=ctx.state.piece_id,
                seed=seed,
                path=str(raw_path),
            )
        except Exception as exc:
            logfire.exception("generation failed for piece_id={piece_id}", piece_id=ctx.state.piece_id)
            return self.reject_with_review(
                ctx,
                RejectionReason.GENERATION_FAILED,
                detail=str(exc)[:200],
            )

        return SafetyFilterNode()
