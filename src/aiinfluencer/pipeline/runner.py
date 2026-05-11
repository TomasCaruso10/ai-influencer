"""Runner. Entry point que ejecuta el grafo para una pieza.

API:
    request = PieceRequest(prompt_seed="cafe scene", model_choice="flux+lora_a1")
    deps = WorkflowDeps.with_dummies()
    result = await run_piece(request, deps)
    # result es PieceApproved | PieceRejected | PausedAtReview
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

import logfire
from pydantic import BaseModel
from pydantic_graph import End
from pydantic_graph.persistence.in_mem import FullStatePersistence

from aiinfluencer.pipeline.deps import WorkflowDeps
from aiinfluencer.pipeline.graph import piece_graph
from aiinfluencer.pipeline.nodes import HumanReviewNode, PromptExpandNode
from aiinfluencer.pipeline.output import PieceApproved, PieceRejected
from aiinfluencer.pipeline.state import PieceRecord, WorkflowState


class PieceRequest(BaseModel):
    """Input para ejecutar el grafo sobre una pieza nueva."""

    prompt_seed: str
    model_choice: str = "flux+lora_aiinfluencer1"
    character_id: str = "aiinfluencer1"
    seed: int | None = None


class PausedAtReview(BaseModel):
    """Resultado intermedio cuando el grafo se pausa en HumanReviewNode."""

    status: Literal["paused_at_review"] = "paused_at_review"
    piece_id: str


def _make_record(request: PieceRequest) -> PieceRecord:
    return PieceRecord(
        piece_id=f"piece_{uuid.uuid4().hex[:12]}",
        prompt_seed=request.prompt_seed,
        model_choice=request.model_choice,
        character_id=request.character_id,
        seed=request.seed,
    )


async def run_piece(
    request: PieceRequest,
    deps: WorkflowDeps,
) -> PieceApproved | PieceRejected | PausedAtReview:
    """Ejecuta el grafo para una nueva pieza. Si llega a HumanReviewNode
    y `deps.auto_approve_in_review=False`, devuelve `PausedAtReview` y deja
    el state persistido para resume posterior.
    """
    record = _make_record(request)
    state = WorkflowState(record=record)

    persistence = FullStatePersistence()
    persistence.set_graph_types(piece_graph)

    logfire.info(
        "pipeline_start piece_id={piece_id} model={model}",
        piece_id=record.piece_id,
        model=record.model_choice,
    )

    async with piece_graph.iter(
        PromptExpandNode(),
        state=state,
        deps=deps,
        persistence=persistence,
    ) as run:
        while True:
            node = await run.next()

            # HITL pause point — interceptar ANTES de que el nodo corra
            # solo si auto_approve está OFF y todavía no hay decisión humana
            if (
                isinstance(node, HumanReviewNode)
                and not deps.auto_approve_in_review
                and state.record.human_approved is None
                and state.record.rejection_reason is None
            ):
                state.record.status = "waiting_review"
                await deps.mongo.save_record(state.record)
                logfire.info(
                    "pipeline_paused piece_id={piece_id} reason=human_review",
                    piece_id=record.piece_id,
                )
                return PausedAtReview(piece_id=record.piece_id)

            if isinstance(node, End):
                await deps.mongo.save_record(state.record)
                logfire.info(
                    "pipeline_complete piece_id={piece_id} result={result}",
                    piece_id=record.piece_id,
                    result=getattr(node.data, "result", "unknown"),
                )
                return node.data
