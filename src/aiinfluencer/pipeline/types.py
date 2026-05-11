"""Tipos compartidos: Context alias + AppNode base class.

Convención: TODOS los nodos heredan de `AppNode`. Esto permite agregar helpers
compartidos (ej `reject_with_review`) sin tocar cada nodo individualmente.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_graph import BaseNode, GraphRunContext

from aiinfluencer.pipeline.deps import WorkflowDeps
from aiinfluencer.pipeline.output import PieceOutput, RejectionReason
from aiinfluencer.pipeline.state import WorkflowState

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.human_review import HumanReviewNode


Context = GraphRunContext[WorkflowState, WorkflowDeps]
"""Alias del context que todos los nodos usan. Define una vez, importá everywhere."""


class AppNode(BaseNode[WorkflowState, WorkflowDeps, PieceOutput]):
    """Base class para todos los nodos del pipeline.

    Provee helpers compartidos para los patterns más comunes (rejection,
    safety failure, etc.) que todos los nodos pueden reusar.
    """

    def reject_with_review(
        self,
        ctx: Context,
        reason: RejectionReason,
        detail: str = "",
    ) -> "HumanReviewNode":
        """Marca la pieza con razón de rechazo y manda a HITL review.

        El reviewer humano puede confirmar el reject (→ End[PieceRejected])
        o overridear (→ Approve manualmente).
        """
        from aiinfluencer.pipeline.nodes.human_review import HumanReviewNode

        ctx.state.set_rejection(reason, detail)
        return HumanReviewNode()
