# Pipeline — pydantic-graph conventions

> Convenciones específicas para nodos del grafo de generación. Source: `Skill: pydantic-graph` + `docs/specs/pipeline-orchestration.md`.

## Pattern obligatorio para todo nodo nuevo

```python
# src/aiinfluencer/pipeline/nodes/my_node.py
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import logfire

from aiinfluencer.pipeline.types import AppNode, Context

if TYPE_CHECKING:
    from aiinfluencer.pipeline.nodes.next_node import NextNode


@dataclass
class MyNode(AppNode):
    """Descripción del nodo en una línea."""

    async def run(self, ctx: Context) -> "NextNode":
        from aiinfluencer.pipeline.nodes.next_node import NextNode  # local import

        # 1. Leer state via ctx.state (proxy properties al record)
        # 2. Llamar a deps via ctx.deps.xxx (typed Protocol)
        # 3. Actualizar state (set_xxx setters)
        # 4. Loggear con logfire template + kwargs
        # 5. Return next node O reject_with_review O End[Output]

        logfire.info("my_node_done piece_id={piece_id}", piece_id=ctx.state.piece_id)
        return NextNode()
```

## Reglas duras

1. **`@dataclass` SIEMPRE**. Nunca `BaseModel` para un nodo.
2. **Hereda de `AppNode`** (base class compartida con helpers como `reject_with_review`).
3. **TYPE_CHECKING para imports forward**: nodes del grafo se importan entre sí en circular. Usar string annotations + local imports en `run()`.
4. **Context alias**: usar `Context = GraphRunContext[WorkflowState, WorkflowDeps]` definido en `types.py`. NUNCA inline `GraphRunContext[...]`.
5. **Return type explícito**: union de classes del nodo siguiente, o `End[PieceApproved | PieceRejected]`.
6. **Logfire template strings**: nunca f-strings.
7. **State updates via proxy setters**: `ctx.state.set_safety_passed(True)`, no `ctx.state.record.safety_passed = True` (mantén encapsulación).
8. **Errores → reject_with_review**: si algo recuperable falla, marcar rejection_reason + ir a HumanReviewNode. Si es bug, dejar que el except propague.

## Registrar nodo en el grafo

`src/aiinfluencer/pipeline/graph.py`:
```python
piece_graph = Graph(
    nodes=[..., MyNode],  # agregar acá
    state_type=WorkflowState,
    run_end_type=PieceApproved | PieceRejected,
)
```

Y exportar en `src/aiinfluencer/pipeline/nodes/__init__.py`.

## HITL pause/resume

Si un nodo es punto de pausa para humano (default: `HumanReviewNode`), el RUNNER intercepta con `isinstance` ANTES de ejecutar `run()`:

```python
if isinstance(node, HumanReviewNode) and not deps.auto_approve_in_review:
    state.record.status = "waiting_review"
    await deps.mongo.save_record(state.record)
    return PausedAtReview(piece_id=record.piece_id)
```

Para resume: cargar state del Mongo, setear `state.record.human_approved = True/False`, re-iter desde snapshot. La decisión humana es state, no flag transient.

## State design

`WorkflowState(BaseModel)` wrappea `PieceRecord(BaseModel)` interno (lo que persiste a Mongo). Proxy properties: el state expone `piece_id`, `status`, etc. delegando al record. Esto mantiene una **única fuente de verdad persistible** sin que los nodos manipulen el record directo.

### Cuándo agregar campo nuevo al record vs al state
- **PieceRecord**: si va a persistir cross-snapshot (ej: nuevo flag, scores, paths a R2). Agregar proxy property + setter en WorkflowState.
- **WorkflowState (no record)**: in-memory only durante esta corrida (ej: embeddings temporales, intermediates).

## Tests de nodos

`tests/pipeline/test_<node>.py`:
- Mockear `WorkflowDeps` con dummies (ver `WorkflowDeps.with_dummies()`)
- Construir `WorkflowState` con `PieceRecord(...)` mínimo
- Llamar `await node.run(ctx)` directamente
- Assert: state cambios + return type
- Para rejection paths: assert que `ctx.state.record.rejection_reason` está seteado

## Cuándo NO crear un nodo

- Helper de transformación pura → función en módulo aparte (e.g., `humanization.py`)
- Cliente HTTP → `WorkflowDeps` field con Protocol typing
- Validación inline simple → método de `WorkflowState`

Los nodos son **steps semánticos del pipeline** (gen → safety → face_qc → post_process → ...). No son cajones para cualquier código.
