# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versionado [SemVer](https://semver.org/).

## [Unreleased]

### Added — Phase 2 Foundation

- **Pipeline orchestration** (`src/aiinfluencer/pipeline/`)
  - pydantic-graph FSM con 9 nodos: PromptExpand → Generate → SafetyFilter → FaceQC → PostProcess → C2PASign → HumanReview → Caption → Store
  - `WorkflowState(BaseModel)` + `PieceRecord(BaseModel)` con proxy properties
  - `WorkflowDeps(@dataclass)` con `@runtime_checkable` Protocols
  - HITL pause/resume con MongoDB snapshot persistence
  - `PieceOutput` discriminated union (`PieceApproved | PieceRejected`)
- **Face QC** (`src/aiinfluencer/face_qc/`)
  - InsightFace `buffalo_l` embeddings (512-dim L2-normed)
  - Canon mean + cosine similarity verifier (threshold 0.45 default)
  - `compute_canon_mean()` + `load_canon_mean()` con validación shape/norm
- **Checkpoint evaluator** (`src/aiinfluencer/eval/`)
  - N checkpoints × M prompts × K seeds loop
  - 4 métricas: FaceSimilarityMetric, AestheticMetric, CLIPPromptAdherenceMetric, DummyMetric
  - `EvalReport` con weighted overall winner + CSV/JSON/HTML export
- **Post-processing** (`src/aiinfluencer/post_process/`)
  - Humanización: grain (gaussian noise por ISO), chromatic aberration, vignette (numpy ogrid radial)
  - Channel enum + resize por canal (IG square/portrait, Reels/TikTok, Twitter)
- **Compliance stack** (`src/aiinfluencer/compliance/`)
  - Block list pediátrico (~30 keywords) — aplicado en LoRA load + pre-submit + pre-caption
  - HuggingFace classifiers: age (`dima806/fairface_age_image_detection`), NSFW (`Falconsai/nsfw_image_detection`), Q16 placeholder
  - C2PA signing (lazy import c2pa-python) — EU AI Act Art. 50 disclosure
  - Audit log a Mongo (retention 6 años por compliance)
- **ComfyUI workflows v2** (`workflows/`)
  - `flux_with_lora_v2.json` — FLUX + LoRA + FaceDetailer 3-pass (denoise 0.45 → 0.25 → 0.15)
  - `sdxl_bigasp_nsfw_v2.json` — bigASP + LoRA SDXL + IPAdapter FaceID Plus v2 + FaceDetailer 3-pass
- **Scripts operativos** (`scripts/`)
  - `compute_canon_embedding.py`, `face_qc_batch.py`, `filter_canon_v2.py`, `eval_checkpoints.py`, `pipeline.py`
- **Documentación**
  - `docs/state-of-the-art-audit.md` — 10 gaps vs industry top, ranked by ROI
  - `docs/roadmap.md` — 6 fases con KPIs
  - `docs/specs/{pipeline-orchestration,face-consistency,quality-eval}.md`
  - `docs/research/{face-consistency-stack,orchestration-compliance-2026,top-influencers-forensic,video-pipeline-2026}.md`
  - `docs/implementation/{pipeline,face-qc,eval,post-process,compliance}.md` — referencia de cómo funciona cada módulo
  - `docs/operations/dataset-v2-runbook.md` — pasos concretos para Bloque 2.4
  - `CLAUDE.md` + `.claude/rules/{pipeline,face-qc,compliance,workflow,testing}.md`
- **Testing**: 70 tests baseline (pipeline smoke, face_qc, eval, post_process, compliance) — corren en <2s sin GPU

### Infra

- Optional deps `[face-qc]`, `[compliance]`, `[dev]` para mantener install local en Windows sin MSVC funcional
- Lazy imports en módulos con deps ML pesadas (insightface, transformers, c2pa-python)
- Logfire structured logging (template strings + kwargs, NO f-strings)

## [0.1.0] — 2026-05-XX (Pre-Phase 2)

### Added — MVP Phase 1

- Initial repo skeleton + bootstrap manual con ComfyUI en pod RunPod RTX 4090
- LoRA training validation: FLUX rank 32 (ai-toolkit) + SDXL rank 16 (kohya)
- Dataset canon v1: 54 imágenes curadas manualmente
- Face QC validation: LoRA FLUX SFW 10/10 PASS (cos sim ~0.68 vs canon mean)
- NSFW hardcore validation con bigASP v2.5 + LoRA SDXL: detectó issue de framing (cara muy chica en poses extremas → NO_FACE en QC, NO problema del LoRA)
- Workflows v1 sin FaceDetailer (`flux_with_lora.json`, `sdxl_bigasp_nsfw.json`)
- Specs y research consolidados (plataformas-monetizacion, modelos NSFW/SFW/video)
