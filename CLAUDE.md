# ai-influencer — Claude Code Project Index

> Proyecto personal de pipeline de generación AI con identidad consistente. Lee este archivo primero para entender la arquitectura, el stack y las convenciones.

## Qué es el proyecto

Pipeline de software (no SaaS, no API wrapper) para generar contenido visual (imagen + video) con una persona sintética fotorealista. Mantiene **identidad consistente cross-modelo** (FLUX, SDXL, Chroma, bigASP, Wan 2.2) usando LoRAs entrenados + face consistency stack.

**Estado**: post-MVP (Fase 1 validada). En Fase 2 — Foundation Production.

**Documentación principal**:
- [`Spec.md`](Spec.md) — visión producto + decisiones técnicas lockeadas
- [`docs/roadmap.md`](docs/roadmap.md) — fases priorizadas con KPIs
- [`docs/state-of-the-art-audit.md`](docs/state-of-the-art-audit.md) — gaps vs industry top
- [`docs/specs/`](docs/specs/) — specs por feature al implementar
- [`docs/research/`](docs/research/) — research consolidado (modelos, plataformas, compliance, etc.)
- [`docs/implementation/`](docs/implementation/) — descripción de módulos implementados

## Stack técnico

- **Lenguaje**: Python 3.11+ (uv-managed)
- **Package**: `aiinfluencer` (instalado editable con `uv sync`)
- **Orquestación pipeline**: `pydantic-graph` (FSM + HITL + state persistence)
- **Observability**: `logfire` (template strings, NO f-strings)
- **State persistence**: MongoDB Atlas (free tier) — schema en `pipeline.state`
- **Storage assets**: Cloudflare R2 (post-MVP)
- **GPU compute**: RunPod pod RTX 4090 ephemeral (`scripts/pod.py`)
- **Image generation**: ComfyUI self-host en pod
- **Face QC**: InsightFace `buffalo_l` (cosine similarity vs canon mean)
- **Compliance**: c2pa-python + HuggingFace classifiers
- **Tests**: pytest + pytest-asyncio (mode=auto)

## Estructura del repo

```
ai-influencer/
├── src/aiinfluencer/          # Python package
│   ├── pipeline/              # pydantic-graph orchestration
│   │   ├── nodes/             # 9 nodos del grafo
│   │   ├── graph.py           # piece_graph (module-level)
│   │   ├── runner.py          # run_piece + HITL pause/resume
│   │   ├── state.py           # WorkflowState (BaseModel) + PieceRecord
│   │   ├── deps.py            # WorkflowDeps (@dataclass) + Protocols
│   │   ├── output.py          # PieceOutput discriminated union
│   │   └── types.py           # Context alias + AppNode base
│   ├── face_qc/               # InsightFace ArcFace similarity
│   ├── eval/                  # Checkpoint evaluator + metrics + reports
│   ├── post_process/          # Humanization + resizing
│   └── compliance/            # C2PA + classifiers + audit + block list
├── scripts/                   # CLIs operativos
│   ├── pod.py                 # RunPod lifecycle
│   ├── pipeline.py            # Pipeline CLI entry
│   ├── compute_canon_embedding.py
│   ├── face_qc_batch.py
│   ├── filter_canon_v2.py     # dataset re-curation
│   ├── eval_checkpoints.py
│   ├── generate_batch.py      # ComfyUI batch invocation
│   └── ...
├── workflows/                 # ComfyUI workflow JSONs
├── prompts/                   # canon + variations + safety_negative
├── tests/                     # pytest, mirror de src/ structure
├── outputs/                   # gitignored: assets generados, LoRAs, samples
├── docs/                      # spec, roadmap, audit, research, implementation
└── .claude/rules/             # convenciones por dominio
```

## Convenciones críticas

### Pipeline (pydantic-graph)
Ver [`.claude/rules/pipeline.md`](.claude/rules/pipeline.md).
- Nodos: `@dataclass`, base `AppNode`
- State: `BaseModel` con proxy properties al `PieceRecord` interno
- Deps: `@dataclass` con `Protocol`-typed fields
- Output: discriminated union con `Literal` (`PieceApproved` | `PieceRejected`)
- Imports circulares: `TYPE_CHECKING` + local imports en `run()`

### Face QC (face_qc package)
Ver [`.claude/rules/face-qc.md`](.claude/rules/face-qc.md).
- Embeddings L2-normalized via InsightFace `buffalo_l`
- Canon mean en `outputs/canon/_mean_embedding.npy`
- Threshold default cosine 0.45

### Compliance (compliance package)
Ver [`.claude/rules/compliance.md`](.claude/rules/compliance.md).
- C2PA signing mandatorio antes de `publishable=true`
- Age + NSFW + Q16 classifiers post-gen
- Block list pediátrico en filenames + prompts + captions

### Optional deps ML pesadas
Stack ML (insightface, transformers, c2pa-python, etc.) en `[project.optional-dependencies]` para no romper instalación local en Windows sin MSVC. Lazy imports en módulos que las usan. Tests usan mocks → corren sin deps ML.

### Testing
Ver [`.claude/rules/testing.md`](.claude/rules/testing.md).
- pytest mode=auto async
- Tests por dominio: `tests/pipeline/`, `tests/face_qc/`, `tests/eval/`, `tests/post_process/`, `tests/compliance/`
- Mockear deps externas (ComfyUI, Mongo, R2, InsightFace, transformers)
- ~70 tests baseline. Cada feature nueva incluye sus tests.

### Logfire (no logging stdlib)
```python
import logfire
logfire.info("processed piece_id={piece_id} status={status}",
             piece_id=record.piece_id, status=record.status)
```
NUNCA f-strings — destruye structured indexing.

### Commits
Ver [`.claude/rules/workflow.md`](.claude/rules/workflow.md). Conventional Commits en inglés.

## Comandos frecuentes

```powershell
# Install deps
uv sync                              # base
uv sync --extra dev                  # + pytest/ruff
uv sync --extra dev --extra face-qc  # + insightface (Linux/pod only)
uv sync --extra dev --extra compliance # + c2pa + transformers

# Tests
uv run pytest tests/                 # todos
uv run pytest tests/pipeline/ -v     # un módulo

# Pipeline
uv run python scripts/pipeline.py run --prompt "..."

# Pod lifecycle
uv run python scripts/pod.py up
uv run python scripts/pod.py status
uv run python scripts/pod.py down
```

## Lo que NO está en este repo (scope)

- Marketing, distribución, content calendar, posting strategy
- Gestión de cuentas IG/TikTok/Fanvue
- Contabilidad (AFIP, monotributo, factura E)
- KYC personal del owner
- Chatter ops (responder DMs de subs)

Eso es responsabilidad operacional del usuario. El repo es 100% pipeline técnico.
