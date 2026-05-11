"""PromptExpandNode — expande el prompt seed a positive + negative finales.

Placeholder Fase 2.0: pasa por defecto sin transformación, solo concatena
canon + safety_negative. Implementación LLM-expanded queda para más adelante.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.generate import GenerateNode


CANON_PATH = Path("prompts/identity_canon.txt")
NEGATIVE_PATH = Path("prompts/safety_negative.txt")


def _load_prompt_file(path: Path) -> str:
    if not path.exists():
        return ""
    parts: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts.append(line.rstrip(","))
    return ", ".join(parts)


@dataclass
class PromptExpandNode(AppNode):
    """Combina prompt seed + canon + safety_negative en positive/negative finales."""

    async def run(self, ctx: Context) -> "GenerateNode":
        from aiinfluencer.pipeline.nodes.generate import GenerateNode

        canon = _load_prompt_file(CANON_PATH)
        negative = _load_prompt_file(NEGATIVE_PATH)
        seed_prompt = ctx.state.record.prompt_seed

        # Placeholder: simple concat. Implementación real podría:
        # - usar LLM para reescribir variations naturales
        # - inyectar trigger word
        # - parametrizar tokens por modelo target
        positive = f"{canon}, {seed_prompt}" if seed_prompt else canon

        ctx.state.expanded_prompt_positive = positive
        ctx.state.expanded_prompt_negative = negative

        logfire.info(
            "prompt_expanded piece_id={piece_id} canon_len={canon_len} seed_len={seed_len}",
            piece_id=ctx.state.piece_id,
            canon_len=len(canon),
            seed_len=len(seed_prompt),
        )

        return GenerateNode()
