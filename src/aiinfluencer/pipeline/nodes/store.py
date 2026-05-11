"""StoreNode — sube asset a storage + persiste record en Mongo. Final node.

Placeholder Fase 2.0: DummyStorage (local) + DummyMongo (in-memory).
Implementación real: R2 + MongoDB Atlas.
"""

from __future__ import annotations

from dataclasses import dataclass

import logfire
from pydantic_graph import End

from aiinfluencer.pipeline.output import PieceApproved
from aiinfluencer.pipeline.types import AppNode, Context


@dataclass
class StoreNode(AppNode):
    """Sube imagen + guarda record. Termina el grafo con PieceApproved."""

    async def run(self, ctx: Context) -> End[PieceApproved]:
        processed = ctx.state.require_processed_image()
        key = f"{ctx.state.record.character_id}/{ctx.state.piece_id}.png"

        url = await ctx.deps.storage.upload(processed, key)
        ctx.state.record.processed_image_key = url
        ctx.state.record.status = "approved"
        ctx.state.set_publishable(True)

        await ctx.deps.mongo.save_record(ctx.state.record)

        logfire.info(
            "stored piece_id={piece_id} url={url}",
            piece_id=ctx.state.piece_id,
            url=url,
        )

        return End(
            PieceApproved(piece_id=ctx.state.piece_id, r2_key=url)
        )
