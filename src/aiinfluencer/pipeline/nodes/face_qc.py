"""FaceQCNode — InsightFace cos similarity vs canon mean embedding.

Placeholder Fase 2.0: usa DummyFaceQC (siempre devuelve 0.8). Implementación
real en Bloque 2.2 Face Consistency Stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.output import RejectionReason
from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.human_review import HumanReviewNode
    from aiinfluencer.pipeline.nodes.post_process import PostProcessNode


@dataclass
class FaceQCNode(AppNode):
    """Calcula similarity vs canon, rechaza si < threshold."""

    async def run(self, ctx: Context) -> "PostProcessNode | HumanReviewNode":
        from aiinfluencer.pipeline.nodes.post_process import PostProcessNode

        image = ctx.state.require_raw_image()
        threshold = ctx.deps.face_qc_threshold

        similarity = await ctx.deps.face_qc.cosine_similarity(image)
        ctx.state.face_qc_score = similarity

        logfire.info(
            "face_qc piece_id={piece_id} similarity={sim} threshold={th}",
            piece_id=ctx.state.piece_id,
            sim=similarity,
            th=threshold,
        )

        if similarity < threshold:
            ctx.state.set_face_qc_passed(False)
            return self.reject_with_review(
                ctx,
                RejectionReason.FACE_QC_BELOW_THRESHOLD,
                detail=f"cos_similarity={similarity:.3f} < threshold={threshold:.3f}",
            )

        ctx.state.set_face_qc_passed(True)
        return PostProcessNode()
