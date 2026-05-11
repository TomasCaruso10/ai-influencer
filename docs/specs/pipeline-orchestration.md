# Spec — Pipeline Orchestration MVP (pydantic-graph)

> Esqueleto del pipeline production con pydantic-graph. Nodos como placeholders (raise NotImplementedError o pasthrough) que se irán implementando en bloques posteriores de Fase 2.
>
> Source: `docs/state-of-the-art-audit.md` Gap 6 + skill `pydantic-graph`.

## Objetivo

Tener el grafo + tipos + state + deps + runner funcionando con todos los nodos declarados aunque cada uno sea placeholder. Después, cada bloque siguiente de Fase 2 (Face Consistency, Quality Eval, Post-processing, Compliance) llena uno o varios nodos con lógica real.

## Flujo del grafo

```
[PromptExpandNode]      ← input: PieceRequest (seed prompt, contexto)
        ↓                  output: positive + negative + metadata
[GenerateNode]          ← Genera imagen con LoRA + modelo base elegido
        ↓                  output: raw_image_path
[SafetyFilterNode]      ← age + nsfw + Q16 classifiers
        ↓                  rechaza si falla → ReviewNode con flag
[FaceQCNode]            ← InsightFace cos similarity vs canon mean
        ↓                  rechaza si <threshold → ReviewNode con flag
[PostProcessNode]       ← FaceDetailer + upscale + grain + re-encode
        ↓                  output: processed_image_path
[C2PASignNode]          ← inyecta C2PA manifest + disclosure metadata
        ↓
[HumanReviewNode]       ← PAUSE point para approval HITL
        ↓                  resume con decision Approve | Reject
[CaptionNode]           ← genera caption SFW/NSFW según target
        ↓
[StoreNode]             ← persiste asset en R2 + metadata en Mongo
        ↓
[End[PieceOutput]]      ← Approved | Rejected
```

## Tipos (`src/aiinfluencer/pipeline/types.py`)

```python
from pydantic_graph import BaseNode, GraphRunContext

Context = GraphRunContext[WorkflowState, WorkflowDeps]

class AppNode(BaseNode[WorkflowState, WorkflowDeps, PieceOutput]):
    """Base para todos los nodos. Helpers compartidos."""
    def reject_with_review(self, ctx: Context, reason: RejectionReason, detail: str) -> "HumanReviewNode":
        ...
```

## State (`src/aiinfluencer/pipeline/state.py`)

`WorkflowState(BaseModel)`:
- `record: PieceRecord` — flat DB model (persiste a Mongo)
- `raw_image_path: Optional[Path]`
- `processed_image_path: Optional[Path]`
- `safety_scores: Optional[SafetyScores]`
- `face_qc_score: Optional[float]`
- `caption: Optional[str]`
- Proxy properties para `piece_id`, `status`, etc.

## Deps (`src/aiinfluencer/pipeline/deps.py`)

`WorkflowDeps(@dataclass)`:
- `comfy_client: ComfyClient` (HTTP client a ComfyUI)
- `mongo_client: MongoClient` (state persistence + audit log)
- `r2_client: R2Client` (asset storage)
- `c2pa_signer: C2PASigner` (firma metadata)
- `face_qc: FaceQC` (InsightFace embeddings)
- `classifiers: SafetyClassifiers` (age, NSFW, Q16)

## Output discriminated union (`src/aiinfluencer/pipeline/output.py`)

```python
class PieceApproved(BaseModel):
    result: Literal["approved"] = "approved"
    piece_id: str
    r2_key: str

class PieceRejected(BaseModel):
    result: Literal["rejected"] = "rejected"
    piece_id: str
    reason: RejectionReason
    detail: str

PieceOutput = Annotated[PieceApproved | PieceRejected, Field(discriminator="result")]
```

## Nodos (placeholders Fase 2)

Cada nodo en su propio módulo `src/aiinfluencer/pipeline/nodes/<nombre>.py`. Status inicial:

| Nodo | Status inicial | Implementación real en |
|---|---|---|
| `PromptExpandNode` | placeholder (passthrough) | Fase 2 (más adelante, opcional) |
| `GenerateNode` | placeholder (mock image) | Fase 2 (workflows actuales) |
| `SafetyFilterNode` | placeholder (always pass) | Bloque 2.1 Compliance |
| `FaceQCNode` | placeholder (always pass) | Bloque 2.2 Face Consistency |
| `PostProcessNode` | placeholder (passthrough) | Bloque 2.5 Post-processing |
| `C2PASignNode` | placeholder (no-op) | Bloque 2.1 Compliance |
| `HumanReviewNode` | placeholder (auto-approve) | Bloque 2.6 (parte HITL) |
| `CaptionNode` | placeholder (fixed text) | Más adelante |
| `StoreNode` | placeholder (local fs) | Fase 4 (R2 migration) |

## Runner (`src/aiinfluencer/pipeline/runner.py`)

```python
async def run_piece(request: PieceRequest, deps: WorkflowDeps) -> PieceOutput | dict:
    state = WorkflowState(record=PieceRecord.from_request(request))
    persistence = MongoDBStatePersistence(deps.mongo_client, ...)
    persistence.set_graph_types(piece_graph)

    async with piece_graph.iter(PromptExpandNode(), state=state, deps=deps, persistence=persistence) as run:
        while True:
            node = await run.next()

            if isinstance(node, HumanReviewNode):
                state.record.status = "waiting_review"
                await state.save_record(deps.mongo_client)
                return {"status": "paused", "piece_id": state.piece_id}

            if isinstance(node, End):
                await state.save_record(deps.mongo_client)
                return node.data
```

## Persistence (`src/aiinfluencer/pipeline/persistence.py`)

`MongoDBStatePersistence` custom implementation (basado en BaseStatePersistence) que:
- Guarda snapshots en colección `pipeline_snapshots`
- Audit log en colección `audit_events`
- Resume from latest snapshot por `piece_id`

## CLI (`scripts/pipeline.py`)

```bash
# Generar 1 pieza
python scripts/pipeline.py run --prompt "..." --model flux+lora_a1

# Resume pieza en pause
python scripts/pipeline.py resume --piece-id abc123 --approve

# Batch
python scripts/pipeline.py run --batch 10 --variations-file prompts/sfw_lifestyle/bootstrap_variations.txt
```

## Tests (`tests/pipeline/`)

- `test_state.py` — proxy properties, save/load
- `test_graph_smoke.py` — graph corre end-to-end con placeholders, llega a End
- `test_human_review_pause.py` — pause en HumanReviewNode, resume
- `test_rejection_paths.py` — safety filter falla → ReviewNode
- Mocks de comfy_client, mongo_client, r2_client

## Criterio "done" del esqueleto

- [ ] Estructura de directorios creada
- [ ] Tipos + state + deps + output definidos
- [ ] 9 nodos placeholders implementados
- [ ] Graph declarado a nivel módulo
- [ ] Runner async con pause/resume HITL
- [ ] CLI básico funcional (`pipeline.py run`)
- [ ] Tests smoke pasando

KPI: `python scripts/pipeline.py run --prompt "test"` corre end-to-end sin errores, output `{"result": "approved", "piece_id": "..."}` aunque cada nodo sea placeholder.
