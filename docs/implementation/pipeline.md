# Pipeline — implementation reference

> Cómo funciona el orquestador `pydantic-graph` del repo. Source code en `src/aiinfluencer/pipeline/`.

## Big picture

El pipeline transforma un `PieceRequest` (prompt seed + ChannelHint) en un `PieceOutput` final (`PieceApproved` o `PieceRejected`) pasando por una **FSM determinística** de 9 nodos. La FSM persiste state cross-run en MongoDB, soporta **pause/resume HITL** (human review), y todos los efectos externos (ComfyUI, R2, classifiers, C2PA, audit) van por **Protocols** inyectables (mockeables en tests).

```
┌─────────────┐
│PromptExpand │── ChannelHint + canon → prompt final
└──────┬──────┘
       ▼
┌─────────────┐
│  Generate   │── ComfyUI submit + poll → raw image path
└──────┬──────┘
       ▼
┌─────────────┐
│SafetyFilter │── age + nsfw + Q16 + block list
└──────┬──────┘
       ▼ pass
┌─────────────┐                    fail
│   FaceQC    │─── cos sim vs canon mean ──── reject_with_review
└──────┬──────┘
       ▼ pass
┌─────────────┐
│ PostProcess │── humanize + resize per channel
└──────┬──────┘
       ▼
┌─────────────┐
│  C2PASign   │── manifest + sign
└──────┬──────┘
       ▼
┌─────────────┐
│ HumanReview │── runner PAUSE point (HITL gate)
└──────┬──────┘
       ▼ approved
┌─────────────┐
│   Caption   │── caption with #AI disclosure
└──────┬──────┘
       ▼
┌─────────────┐
│    Store    │── upload R2 + save record + emit
└──────┬──────┘
       ▼
  End[PieceApproved | PieceRejected]
```

## Archivos y responsabilidad

| Archivo | Qué hace |
|---|---|
| `types.py` | `Context = GraphRunContext[WorkflowState, WorkflowDeps]` alias + `AppNode` base con `reject_with_review()` helper |
| `state.py` | `WorkflowState(BaseModel)` wrapper + `PieceRecord(BaseModel)` interno (lo que persiste a Mongo) |
| `deps.py` | `WorkflowDeps(@dataclass)` con Protocol-typed fields + `DummyComfyClient`, `DummyMongoClient`, etc. para tests |
| `output.py` | Discriminated union `PieceApproved | PieceRejected` con `Literal` discriminator |
| `graph.py` | `piece_graph = Graph(nodes=[...], state_type=..., run_end_type=...)` module-level |
| `runner.py` | `run_piece(request, deps)` con intercepción HITL antes de `HumanReviewNode.run()` |
| `nodes/*.py` | 9 nodos (uno por archivo), pattern `@dataclass class XxxNode(AppNode)` |

## State design

**Dos niveles**:
- `WorkflowState(BaseModel)` — root del state runtime (in-memory + proxies a record)
- `PieceRecord(BaseModel)` interno — lo persistible a Mongo (`piece.state` collection)

```python
class WorkflowState(BaseModel):
    record: PieceRecord                       # persiste
    raw_image_path: Optional[Path] = None     # in-memory
    processed_image_path: Optional[Path] = None
    intermediate_embeddings: dict = {}

    @property
    def piece_id(self) -> str:
        return self.record.piece_id

    def set_safety_passed(self, v: bool) -> None:
        self.record.safety_passed = v
```

**Por qué proxies**: los nodos jamás tocan `state.record.*` directo. Pasa todo por setter/getter del state. Esto permite cambiar el shape del record sin que los nodos se enteren.

## HITL pause/resume

El runner intercepta `HumanReviewNode` ANTES de ejecutar `run()`:

```python
if (isinstance(node, HumanReviewNode)
    and not deps.auto_approve_in_review
    and state.record.human_approved is None
    and state.record.rejection_reason is None):
    state.record.status = "waiting_review"
    await deps.mongo.save_record(state.record)
    return PausedAtReview(piece_id=record.piece_id)
```

**Resume**: cargar record de Mongo, setear `record.human_approved = True/False`, re-iter desde snapshot. La decisión humana es **state** (persistido), no flag transient.

**Auto-approve mode**: `deps.auto_approve_in_review=True` salta el pause (usado en tests + dev local).

## Output discriminated union

```python
class PieceApproved(BaseModel):
    result: Literal["approved"] = "approved"
    piece_id: str
    r2_url: str
    metadata: dict

class PieceRejected(BaseModel):
    result: Literal["rejected"] = "rejected"
    piece_id: str
    reason: RejectionReason
    detail: str

PieceOutput = Annotated[PieceApproved | PieceRejected, Field(discriminator="result")]
```

Pydantic puede deserializar el output a la clase correcta solo mirando `result`. Crítico para resume y para el RPC futuro entre pod y orchestrator.

## Protocols vs concrete impls

`WorkflowDeps` campos:
- `comfy: ComfyClient` — Protocol con `async submit(workflow_json, prompt) -> Path`
- `mongo: MongoLikeClient` — Protocol con `async save_record(record)`, `async get_record(id)`
- `r2: ObjectStorageClient` — Protocol con `async upload(path, key) -> str`
- `face_qc: FaceQCProto` — Protocol con `async cosine_similarity(image) -> float`
- `classifiers: SafetyClassifiers` — Protocol con `async age_classify`, `nsfw_classify`, `q16_classify`
- `c2pa: C2PASignerProto` — Protocol con `async sign(image, manifest) -> Path`

Cada Protocol tiene `@runtime_checkable` para que tests verifiquen API compatibility con `isinstance(impl, Proto)`.

**Builder shortcuts**:
- `WorkflowDeps.with_dummies()` — todos los Protocols stubeados → smoke test
- `WorkflowDeps.with_production_face_qc(canon_mean_path)` — Face QC real, resto dummy

## Logfire convention

Todos los nodos loggean con template strings:
```python
logfire.info("face_qc piece_id={piece_id} cos_sim={sim:.4f} passed={ok}",
             piece_id=ctx.state.piece_id, sim=score, ok=score >= threshold)
```
Nunca f-strings (rompe structured indexing en logfire UI).

## Cómo agregar un nodo nuevo

1. Archivo `src/aiinfluencer/pipeline/nodes/my_node.py` con pattern del `.claude/rules/pipeline.md`
2. Registrarlo en `graph.py` lista `nodes=[..., MyNode]`
3. Exportarlo en `nodes/__init__.py`
4. Test en `tests/pipeline/test_my_node.py` mockeando deps

Si el nodo es punto de pausa nuevo, también agregar isinstance check en `runner.py`.

## Tests

`tests/pipeline/test_graph_smoke.py` ejercita el grafo end-to-end con todos dummies. Si esto rompe, nada del pipeline anda.

Tests por nodo individual: construir state mínimo + `await node.run(ctx)` directo, asserts sobre state changes + return type.
