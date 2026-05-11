"""HumanReviewNode — punto de pausa para approval/reject HITL.

El runner detecta este nodo con `isinstance` y serializa el snapshot al
MongoDB. Una segunda invocación (resume) inyecta la decisión humana via
`ctx.state.record.human_approved = True/False` antes de re-correr.

Placeholder Fase 2.0: si `deps.auto_approve_in_review=True` (dev), aprueba
auto. Si False (prod), el runner debe interceptar este nodo ANTES de que
corra `run()` y pausar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire
from pydantic_graph import End

from aiinfluencer.pipeline.output import (
    PieceApproved,
    PieceRejected,
    RejectionReason,
)
from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.caption import CaptionNode


@dataclass
class HumanReviewNode(AppNode):
    """Pause point. Si auto_approve_in_review, aprueba o respeta rejection_reason."""

    async def run(self, ctx: Context) -> "CaptionNode | End[PieceApproved | PieceRejected]":
        from aiinfluencer.pipeline.nodes.caption import CaptionNode

        # Si ya hay rejection_reason seteada (vino de un reject_with_review), respetar.
        if ctx.state.record.rejection_reason is not None:
            logfire.info(
                "review piece_id={piece_id} confirmed_reject reason={reason}",
                piece_id=ctx.state.piece_id,
                reason=ctx.state.record.rejection_reason.value,
            )
            return End(
                PieceRejected(
                    piece_id=ctx.state.piece_id,
                    reason=ctx.state.record.rejection_reason,
                    detail=ctx.state.record.rejection_detail,
                )
            )

        # Si human_approved ya está seteado (resume con decisión), respetar.
        approved = ctx.state.record.human_approved
        if approved is None:
            # No vino decisión humana. En dev auto-aprobamos; en prod el runner
            # debe pausar antes de llegar acá (intercepta con isinstance).
            if ctx.deps.auto_approve_in_review:
                approved = True
            else:
                # En prod no debería pasar — el runner pausa antes. Si pasa, reject.
                logfire.warning(
                    "human_review reached without decision piece_id={piece_id}",
                    piece_id=ctx.state.piece_id,
                )
                return End(
                    PieceRejected(
                        piece_id=ctx.state.piece_id,
                        reason=RejectionReason.HUMAN_REJECTED,
                        detail="No human decision provided",
                    )
                )

        ctx.state.set_human_approved(approved)

        if not approved:
            ctx.state.set_rejection(RejectionReason.HUMAN_REJECTED, "Human reviewer rejected")
            return End(
                PieceRejected(
                    piece_id=ctx.state.piece_id,
                    reason=RejectionReason.HUMAN_REJECTED,
                    detail="Human reviewer rejected",
                )
            )

        logfire.info(
            "review piece_id={piece_id} approved=True",
            piece_id=ctx.state.piece_id,
        )
        return CaptionNode()
