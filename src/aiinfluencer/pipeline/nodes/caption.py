"""CaptionNode — genera caption SFW/NSFW según target.

Placeholder Fase 2.0: caption fija. Implementación real podría usar LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.store import StoreNode


@dataclass
class CaptionNode(AppNode):
    """Genera caption para el target channel."""

    async def run(self, ctx: Context) -> "StoreNode":
        from aiinfluencer.pipeline.nodes.store import StoreNode

        # Placeholder: caption fija con disclosure
        ctx.state.caption = "✨ #AI #aigenerated"

        logfire.info(
            "caption_generated piece_id={piece_id} caption={caption}",
            piece_id=ctx.state.piece_id,
            caption=ctx.state.caption,
        )

        return StoreNode()
