# Workflow — commits, tests, ramas

## Conventional Commits

Formato: `<type>(<scope>): <subject>`

### Scopes del proyecto
- `pipeline` — pydantic-graph nodos, runner, state
- `face-qc` — InsightFace stack
- `eval` — checkpoint evaluator
- `post-process` — humanization, resizing
- `compliance` — C2PA, classifiers, audit, block list
- `workflows` — ComfyUI JSONs
- `scripts` — CLIs en `scripts/`
- `infra` — pod, deps, build
- `docs` — README, spec, roadmap, research
- `tests` — solo tests, sin cambios productivos

### Reglas
- Commits **en inglés**.
- Subject imperativo, sin punto, max 72 chars.
- Body opcional para "por qué" (no "qué" — eso está en el diff).
- NUNCA `--no-verify` (pre-commit hooks deben pasar).
- NUNCA `--amend` salvo si el commit anterior NO está pusheado.

## Ciclo de feature
1. Spec: definir en `docs/specs/<feature>.md` ANTES de tocar código.
2. Implement: código + tests en mismo PR.
3. Actualizar docs si cambia la arquitectura:
   - `CLAUDE.md` si cambia stack o estructura
   - `.claude/rules/<dominio>.md` si cambia un patrón
   - `docs/implementation/<feature>.md` para describir cómo funciona
4. Run tests: `uv run pytest tests/` debe pasar 100%.
5. Commit con scope correcto.

## Tests obligatorios por dominio

Cada feature nueva incluye sus tests. Convención:
- `src/aiinfluencer/<dominio>/...` → `tests/<dominio>/test_<modulo>.py`
- Mockear deps externas (ComfyUI, Mongo, R2, HuggingFace, InsightFace)
- Para nodos del grafo: testear cada rama (happy path + rejections)
- Para Protocols: incluir test `test_<X>_implements_protocol`

## Pre-flight checklist antes de commit

1. `uv run pytest tests/` pasa todos
2. `uv run ruff check src/ tests/ scripts/` sin errores (cuando se setee)
3. Docs actualizadas si cambió pattern/stack
4. `.env` NO está en staging (`git status --short` no debe mostrarlo)
5. Archivos generados en `outputs/` NO están staged (gitignored)

## Branches y PRs

Solo branch `main` por ahora (proyecto solo dev). Cuando entren colaboradores:
- Feature branches `feat/<scope>-<desc>`
- PRs con descripción que linkea al spec o issue
- Squash merge a main

## Cuándo crear PR vs commit directo

Mientras solo trabaje el owner: commit directo a main. Cuando entre alguien más: PRs obligatorios.
