# State-of-the-Art Audit — AI Influencer Project (post-MVP)

> Auditoría honesta del proyecto post-MVP. Compara estado actual vs top tier industry 2026 (Aitana López, Milla Sofia, Emily Pellegrini, top Fanvue AI Creators).
>
> **Modo profesor + investigador**: cada gap explicado, con qué es, cómo lo usan los pros, complejidad (S/M/L/XL), costo aprox, dependencias.
>
> Última actualización: 2026-05-11. Research consolidado con 4 agents paralelos. Findings completos en:
> - [face-consistency-stack.md](research/face-consistency-stack.md)
> - [video-pipeline-2026.md](research/video-pipeline-2026.md)
> - [top-influencers-forensic.md](research/top-influencers-forensic.md)
> - [orchestration-compliance-2026.md](research/orchestration-compliance-2026.md)

## Resumen ejecutivo

**Estado actual del proyecto**: ~25% del top tier industry. Validamos lo crítico (identidad consistente cross-modelo, SFW+NSFW funcional) pero faltan TODAS las capas de production-grade (QA automatizado, video, voz, post-processing, orchestration, distribución).

**Top tier real (revisión del research)**:
- Aitana López: $4-8K/mes (NO los $30K que la prensa pintó — plateau followers desde 2024, ER mediocre 0.8%)
- Emily Pellegrini: $100K acumulado Fanvue (Italian-LA, creator anónimo 14-16h/día)
- Ami BNW, Aya Petite (AI puras): $50K+/mes consistente — **el verdadero top 1% AI**
- Tier "muy bueno" (estable, escalable): $10-30K/mes con 1-3K subs Fanvue

**Time to revenue realista**: 6-12 meses para $10K/mes, no 3 meses como suena en prensa.

## Gap 1 — Face Consistency cross-modelo

### Lo que tenemos
- LoRA FLUX rank 32 (`aiinfluencer1_flux_FINAL.safetensors`, 165 MB)
- LoRA SDXL rank 16 (`aiinfluencer1_sdxl_FINAL.safetensors`, 110 MB)
- Workflows base ComfyUI para FLUX, Chroma, SDXL+bigASP

### Lo que falta
- **IP-Adapter FaceID Plus v2** en SDXL workflow (refuerza identidad sobre LoRA)
- **PuLID-Flux II** en FLUX workflow (equivalente para FLUX, broken antes — re-instalar versión correcta)
- **FaceDetailer multi-pass** (denoise 0.45→0.25→0.15) usando mismo LoRA
- **ReActor + CodeFormer 0.5** para hero shots críticos (necesita fix torchao o usar venv aislado)
- **InsightFace ArcFace QC automático** (buffalo_l, threshold 0.45 cosine vs canon mean embedding)

### Stack ganador 2026 (de research)
```
[LoRA character] → base gen
   → [IPAdapter FaceID v2 (SDXL) o PuLID-Flux II (FLUX)] @ 0.7-0.85
   → [FaceDetailer + LoRA] denoise 0.45 → 0.25 → 0.15 (3 passes)
   → [ReActor + CodeFormer 0.5] (solo hero shots)
   → [InsightFace QC, cos > 0.45 vs canon mean → reject si no pasa]
```
Identity accuracy del stack: **~97%** (vs 80-90% solo con LoRA).

### Complejidad y costo
- **M** (medium): wiring ComfyUI + Python ~50 LOC InsightFace QC + workflow JSON edits.
- ~6-10h trabajo, $0 infra extra.
- **ROI: ALTÍSIMO** — resuelve la varianza cross-modelo que ya observamos.

## Gap 2 — Quality eval automatizado durante training

### Lo que descubrimos en el MVP
Entrenamos a ciegas:
- Loss curve baja pero no nos dice si la identidad pega
- Samples del trainer mienten (EMA dilution + walk_seed varianza)
- Decidimos "el sweet spot fue step 1000" recién con test post-training en ComfyUI
- **Perdimos ~1h de cómputo y 20 minutos tuyos** porque samples del trainer engañaron

### Lo que falta implementar

Pipeline de evaluation automático que se corra **DURANTE** y **DESPUÉS** del training:

1. **Validation set heldout**: 5-10 imgs del canon que NO entran al training. Cada checkpoint genera N samples con prompts test, comparamos contra heldout con métricas:
   - **InsightFace ArcFace similarity**: cosine similarity entre embedding de output vs canon. Target > 0.6.
   - **LAION aesthetic predictor v2.5**: score 0-10 de "qué tan buena foto" estética.
   - **CLIP prompt adherence**: similarity entre prompt y output, indica si el modelo obedece.
2. **Batch eval por checkpoint**: en lugar de mirar samples del trainer (con EMA), generamos samples reales con cada checkpoint .safetensors → comparamos métricas → elegimos el sweet spot.
3. **Early stopping**: si las 3 métricas no mejoran 3 checkpoints seguidos, parar.
4. **TensorBoard / wandb dashboard**: visualizar loss + metrics + sample images en tiempo real.
5. **Hyperparam sweep** (más adelante): con Optuna corremos 3-4 configs en paralelo (rank 16/32/64, lr 5e-5/1e-4/2e-4) y elegimos el mejor por métricas, no por ojo.

**Tooling stack sugerido**:
- `insightface==0.7.3` (ya instalado, broken por torchao — fix en research)
- `aesthetic-predictor-v2-5` (HuggingFace, simple pipeline)
- `clip-anytorch` (ya en ai-toolkit deps)
- `tensorboard` (ya en sd-scripts deps)
- `optuna` (sweep tooling, simple agregar)

**Complejidad**: Medium. ~1 día de setup + integración con scripts/eval_checkpoints.py + dashboard.

**ROI**: ALTÍSIMO. Resuelve el dolor de cabeza #1 ("estoy entrenando a ciegas 3h sin saber si va a salir").

## Gap 3 — Video pipeline

### Lo que descubrimos
- ComfyUI-WanVideoWrapper: broken por incompat. NO probamos video.
- **Aitana publica 90% fotos**, video solo Stories/Reels cortos (lección importante).

### Lo que falta — stack ganador 2026
**LoRA dual de Wan 2.2** (NO reusa LoRA imagen — necesita training específico):
- 10-30 clips de 2-3s + 20-40 imágenes
- 3000-5000 steps, LR 7e-5 a 2e-4, sigmoid schedule, rank 16-32
- Entrenar **2 LoRAs** (high-noise + low-noise) por arquitectura MoE
- Costo: $5-15 cloud H100 o 6-10h en RTX 4090

**Pipeline ganador para 50 Reels/mes**:

| Pipeline | Uso | Costo | Tiempo |
|---|---|---|---|
| **A — Talking head** | Reels selfie hablando | $1.20/Reel (Hedra) | 20 min |
| **B — B-roll cinemático** | Sin lip-sync visible | Solo GPU + tiempo | 30-45 min |
| **C — Premium híbrido** | Wan 2.2 + Sync.so lipsync | $0.50-1/Reel | 45-60 min |
| **D — SFW max calidad** | Veo 3.1 con audio nativo | $2.50/Reel | poco |

**Tooling**:
- **Hedra Character-3** ($30/mo Creator plan, 3600 credits ~11min video) — talking head from foto
- **ComfyUI native** Wan 2.2 I2V-A14B (no el Kijai wrapper broken)
- **Sync.so lipsync-2-pro** ($0.10/s) para reemplazar boca en video Wan
- **LivePortrait** local para volumen
- **ElevenLabs Creator** ($22/mo) para voz

### Complejidad y costo
- **L** (large): training Wan LoRA + setup nodes + workflows + iteración.
- ~30-40h trabajo, $30-50 costo training + $70-100/mes operacional.
- **ROI: ALTO** — TikTok requiere video. Sin esto solo IG feed estático.

## Gap 4 — Voz + lip-sync

### Lo que falta
**Pipeline construir voz única del personaje**:
1. ElevenLabs v3 **Voice Design** → generar voz sintética desde descripción (~$22/mo Creator)
2. Generar 30 min audio con esa voz
3. Re-clonar en F5-TTS local o ElevenLabs Pro Voice Clone (lock voz fija)
4. **NUNCA clonar voces reales** — right of publicity legal

**Lip-sync pipeline**:
- **Hedra Character-3** para talking head from foto (default)
- **Sync.so lipsync-2-pro** para video existente

### Complejidad y costo
- **S-M**: setup ElevenLabs + workflow tts + lip-sync.
- ~5-8h trabajo, $30/mo Hedra + $22/mo ElevenLabs.
- **ROI: MEDIO** — necesario para Reels talking head pero no urgente.

## Gap 5 — Post-processing pipeline

### Lo que falta
Workflow ComfyUI completo de producción:

1. **Base generation** (FLUX/SDXL/Chroma + LoRA) → 1024x1024
2. **FaceDetailer** (Impact Pack) con mismo LoRA, denoise 0.35-0.5
3. **Hand detailer** (Impact Pack) si están rotas
4. **Upscale 2x** (4x-UltraSharp + tile, denoise 0.2-0.3) → 2048x2048
5. **Optional SUPIR** para hero shots
6. **Re-encode**: PNG → JPEG q92 → 1080x1350 IG / 1080x1920 Reels
7. **Camera grain pass**: ISO 400-800 + chromatic aberration + vignetting
8. **C2PA sign**: metadata firmada (NO strip — riesgo legal alto)
9. **InsightFace verification**: final QC

### Insight crítico del research
**Aitana y top operators hacen Photoshop manual 15-45 min por foto final**. Es el secreto que la prensa no cuenta: **80% rejection rate de outputs raw, post-processing pesado obligatorio**.

### Complejidad y costo
- **M**: workflow ComfyUI + Python post + opcional Photoshop manual.
- ~10-15h setup inicial, $0 infra.
- **ROI: ALTO** — diferencia entre "AI obvio" e "indistinguible" es 80% post-processing.

## Gap 6 — Pipeline orchestration

### Lo que tenemos
Scripts Python sueltos + comandos manuales. Sin scheduling, sin retries, sin dashboard, sin HITL formal.

### Stack ganador (de research)
**Híbrido**: pydantic-graph (FSM por pieza) + Prefect 3 (scheduling/retries/dashboard) + Modal (GPU bursts).

**Flujo**:
```
[prompt seed] → [LLM expand] → [generate] → [safety filter] →
[face consistency check] → [upscale + post-process] →
[HITL review] → [caption gen] → [store] → [schedule post]
```

Cada nodo con: retries, timeouts, logging Logfire, state persistence MongoDB, pause/resume HITL.

### Complejidad y costo
- **L** (large): integración pydantic-graph + Prefect + Modal + nodos de gen.
- ~40-60h trabajo, <$200/mes operacional (A10G Modal + Prefect Cloud opcional).
- **ROI: ALTO** — desbloquea escalar a 50-100 piezas/semana sin perder tu tiempo.

## Gap 7 — Distribución + scheduling + plataformas

### Lo que falta
1. **Apertura cuentas**:
   - Instagram (cuenta principal del personaje)
   - TikTok (cuenta principal)
   - Fanvue (KYC del owner real Tomás Caruso)
   - **Passes** como link aggregator (90/10 split, IG-friendly)
2. **Scheduler**:
   - **Metricool** o **Later** ($20-30/mo) — los más usados en el rubro
   - **Substy** ($50-100/mo) si vamos a Fanvue serio (chatter management nativo)
3. **Bio strategy**: 3 líneas (identidad + oferta + CTA link aggregator)
4. **KYC**: tu propio ID + selfie como AI Creator (personaje sintético OK en Fanvue)

### Insight crítico del research
**90% del revenue Fanvue/OnlyFans viene de CHATTERS**, no de subs base. Sin chatter strategy estás dejando 80-90% de la plata en la mesa.

**Opciones chatter**:
- Vos personalmente (escala limitada)
- Agencia humana (30-40% comm)
- AI OFM agency operadora (50-70% comm, manejan TODO end-to-end)

### Complejidad y costo
- **S-M**: crear cuentas + setup scheduler + bio.
- ~5-10h trabajo, $50-100/mes operacional + chatter fees variables.
- **ROI: CRÍTICO** — sin distribución no hay revenue.

## Gap 8 — Compliance moderno

### Lo que tenemos
- Safety negative fixture (pediátrico)
- Canon con "19 years old" + "young adult woman"
- Curación manual del owner

### Lo que falta
1. **EU AI Act Art. 50 compliance** (mandatorio 2 ago 2026): watermark machine-readable + disclosure visible. Multas hasta €15M o 3% facturación.
2. **C2PA signing** en cada output (Python SDK `c2pa-python`)
3. **SynthID-style watermark** invisible (opcional, complementario a C2PA)
4. **Age classifier post-gen** mandatorio:
   - `dima806/fairface_age_image_detection` o `nateraw/vit-age-classifier`
   - Reject "0-19" automático, cuarentena ambigüedad
5. **NSFW classifier multi-clase**: `Falconsai/nsfw_image_detection` + Q16 (violence, blood)
6. **Audit log estructurado**: prompt + seed + modelo + LoRAs + safety scores + outcome + reviewer (6 años retención mínimo)
7. **Block list LoRAs/embeddings** con keywords pediátricos
8. **Compromiso Thorn Safety by Design** documentado

### Argentina específico (ARCA/AFIP)
- Factura E exportación servicios IVA 0%
- Monotributo cat K hasta $82M anual
- Crypto payouts permitidos pero gravados Ganancias
- CLAE: "producción contenido audiovisual redes sociales"
- Documentar flujo: plataforma → wallet → exchange registrado → cuenta bancaria con factura E

### Complejidad y costo
- **M-L**: integración C2PA + classifiers + audit log + documentación.
- ~15-25h trabajo, $0 infra (todos open-source classifiers).
- **ROI: CRÍTICO LEGAL** — sin esto, riesgo €15M multa + 2 años cárcel TAKE IT DOWN Act.

## Gap 9 — Humanization anti-AI-detection

### Insight del research
Plataformas detectan AI con: C2PA, SynthID, heurísticas visuales. Auto-label rate **25-30%** (no 100%).

**Lo que hacen los pros**: **NO ocultan AI** (riesgo legal + ban). Aceptan label + bajan engagement 10-25%. Pero **humanizan post-processing**:
- Grain ISO 400-800
- Chromatic aberration leve
- Imperfecciones humanas intercaladas (selfies "malas", motion blur)
- Mix con BTS "humanizing" (5% del feed)

### Complejidad y costo
- **S**: pasada Python con grain + filtros + variation.
- ~3-5h, $0.
- **ROI: ALTO** — la diferencia entre "AI obvio" y "AI creíble" es 50% post-processing.

## Gap 10 — Dataset re-curation v2 (mejora LoRA)

### Lo que descubrimos en el MVP
- 54 fotos curadas pero algunas "puede dar" (varianza mayor)
- **Faltaron fotos de cuerpo completo** (vos lo notaste explícito)
- **Faltó variedad de ángulos** (mucho retrato cerca, poco 3/4 y full body)

### Lo que falta
1. **Re-curar** las 54 → 25-30 ultra consistentes
2. **Generar +10 fotos cuerpo completo** con LoRA actual + variations específicas
3. **Generar +10 fotos 3/4 view** para mejorar ángulos
4. **Filtro auto con InsightFace** (cos similarity entre fotos del dataset > 0.6 = misma persona)
5. **Re-train LoRA v2** con dataset mejorado + eval automático (Gap 2)

### Complejidad y costo
- **M**: generación + curación + re-training.
- ~6-10h trabajo, $3-5 GPU.
- **ROI: ALTO** — todos los workflows mejoran con LoRA v2 más consistente.

## Ranking de Gaps por ROI (priority order)

| # | Gap | Complejidad | Costo $ | Costo tiempo | ROI | Bloquea |
|---|---|---|---|---|---|---|
| **1** | Compliance crítico (Gap 8) | M-L | $0 | 15-25h | CRÍTICO LEGAL | Todo published content |
| **2** | Face consistency stack (Gap 1) | M | $0 | 6-10h | ALTÍSIMO | Calidad output |
| **3** | Quality eval automático (Gap 2) | M-L | $0 | 10-15h | ALTÍSIMO | Iteración LoRAs |
| **4** | Dataset re-curation v2 (Gap 10) | M | $3-5 | 6-10h | ALTO | LoRAs v2 |
| **5** | Post-processing pipeline (Gap 5) | M | $0 | 10-15h | ALTO | Calidad "no parece AI" |
| **6** | Humanization (Gap 9) | S | $0 | 3-5h | ALTO | Anti-detection |
| **7** | Pipeline orchestration (Gap 6) | L | <$200/mo | 40-60h | ALTO | Escalar volumen |
| **8** | Distribución plataformas (Gap 7) | S-M | $50-100/mo | 5-10h | CRÍTICO REVENUE | Conversión $ |
| **9** | Video pipeline (Gap 3) | L | $30-50 + $70-100/mo | 30-40h | ALTO | TikTok / Reels |
| **10** | Voz + lip-sync (Gap 4) | S-M | $50/mo | 5-8h | MEDIO | Solo si videos talking |

## Próximas acciones

1. **Roadmap.md** — fases ordenadas por ROI con KPIs concretos (Fase 2 = Gaps 1, 2, 3, 4, 5, 6 — fundamentos)
2. **Spec.md v2** — visión producto completa
3. **Specs por feature** en `docs/specs/<gap>.md` cuando vamos a implementar cada uno

## Tres advertencias del research (importantes)

1. **NO copies Aitana literal** — stack 2023, plateau followers, ER mediocre. Saturado. Su revenue real es $4-8K/mes (no $30K que pintó la prensa).
2. **El cuello de botella REAL NO es generar imágenes** — es chatter ops + QC manual + post-processing. Top operators trabajan 8-14h/día en mensajería.
3. **Funnel realista**: 6-12 meses para $10K/mes con esfuerzo serio. **80% rejection rate** de outputs raw. NO es máquina que escupe plata sola.
