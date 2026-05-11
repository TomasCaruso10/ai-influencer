"""SafetyFilterNode — corre classifiers post-gen: age, NSFW, Q16.

Placeholder Fase 2.0: usa DummySafetyClassifiers (siempre pasa). Implementación
real en Bloque 2.1 Compliance (HuggingFace models).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.output import RejectionReason
from aiinfluencer.pipeline.state import SafetyScores
from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.face_qc import FaceQCNode
    from aiinfluencer.pipeline.nodes.human_review import HumanReviewNode


@dataclass
class SafetyFilterNode(AppNode):
    """Edad >= 20, NSFW score OK por target, Q16 sin flags."""

    async def run(self, ctx: Context) -> "FaceQCNode | HumanReviewNode":
        from aiinfluencer.pipeline.nodes.face_qc import FaceQCNode

        image = ctx.state.require_raw_image()

        age_result = await ctx.deps.classifiers.age_classify(image)
        nsfw_score = await ctx.deps.classifiers.nsfw_classify(image)
        q16_inappropriate = await ctx.deps.classifiers.q16_classify(image)

        scores = SafetyScores(
            age_predicted_bucket=age_result.get("bucket"),
            age_is_adult=age_result.get("is_adult"),
            nsfw_score=nsfw_score,
            q16_inappropriate=q16_inappropriate,
        )
        ctx.state.safety_scores = scores

        logfire.info(
            "safety_check piece_id={piece_id} age_bucket={age} adult={adult} nsfw={nsfw} q16={q16}",
            piece_id=ctx.state.piece_id,
            age=scores.age_predicted_bucket,
            adult=scores.age_is_adult,
            nsfw=scores.nsfw_score,
            q16=scores.q16_inappropriate,
        )

        # Age check — línea roja, reject inmediato si no es adulto
        if scores.age_is_adult is False:
            ctx.state.set_safety_passed(False)
            return self.reject_with_review(
                ctx,
                RejectionReason.AGE_CLASSIFIER_FAILED,
                detail=f"age_bucket={scores.age_predicted_bucket}",
            )

        # Q16 — flag de inappropriate (violence/gore/etc)
        if scores.q16_inappropriate:
            ctx.state.set_safety_passed(False)
            return self.reject_with_review(
                ctx,
                RejectionReason.Q16_INAPPROPRIATE,
                detail="Q16 classifier flagged inappropriate content",
            )

        ctx.state.set_safety_passed(True)
        return FaceQCNode()
