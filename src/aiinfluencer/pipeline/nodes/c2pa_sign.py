"""C2PASignNode — firma manifest C2PA + disclosure metadata.

Placeholder Fase 2.0: no-op, marca el flag. Implementación real en Bloque 2.1
Compliance (`c2pa-python` SDK).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.human_review import HumanReviewNode


@dataclass
class C2PASignNode(AppNode):
    """Inyecta C2PA manifest + disclosure metadata en processed_image_path."""

    async def run(self, ctx: Context) -> "HumanReviewNode":
        from aiinfluencer.pipeline.nodes.human_review import HumanReviewNode

        processed = ctx.state.require_processed_image()

        manifest = {
            "claim_generator": "ai-influencer/0.2.0",
            "title": processed.name,
            "assertions": [
                {
                    "label": "c2pa.actions",
                    "data": {
                        "actions": [
                            {"action": "c2pa.created", "softwareAgent": ctx.state.model_choice}
                        ]
                    },
                },
                {
                    "label": "c2pa.training-mining",
                    "data": {
                        "entries": {
                            "c2pa.ai_generative_training": {"use": "notAllowed"}
                        }
                    },
                },
            ],
        }

        signed = await ctx.deps.c2pa.sign(processed, manifest)
        ctx.state.processed_image_path = signed
        ctx.state.set_c2pa_signed(True)

        logfire.info(
            "c2pa_signed piece_id={piece_id} path={path}",
            piece_id=ctx.state.piece_id,
            path=str(signed),
        )

        return HumanReviewNode()
