"""PostProcessNode — FaceDetailer + upscale + grain + re-encode.

Placeholder Fase 2.0: passthrough. Copia raw_image_path → processed_image_path.
Implementación real en Bloque 2.5 Post-Processing Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.c2pa_sign import C2PASignNode


@dataclass
class PostProcessNode(AppNode):
    """FaceDetailer + HandDetailer + upscale + humanization grain + JPEG re-encode."""

    async def run(self, ctx: Context) -> "C2PASignNode":
        from aiinfluencer.pipeline.nodes.c2pa_sign import C2PASignNode

        raw = ctx.state.require_raw_image()

        # Placeholder: passthrough sin transformación. En real:
        # 1. submit FaceDetailer workflow (multi-pass denoise 0.45 → 0.25 → 0.15)
        # 2. HandDetailer si manos rotas
        # 3. 4x-UltraSharp upscale 2x
        # 4. grain ISO 400-800 + chromatic aberration + vignetting
        # 5. PNG → JPEG q92 + resize por aspect ratio target
        processed = raw  # placeholder: same path
        ctx.state.processed_image_path = processed

        logfire.info(
            "post_processed piece_id={piece_id} path={path}",
            piece_id=ctx.state.piece_id,
            path=str(processed),
        )

        return C2PASignNode()
