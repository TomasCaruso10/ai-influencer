# Roadmap — AI Influencer Project

> Fases priorizadas por ROI tras MVP. Cada fase con criterios "done", KPIs medibles, dependencias, complejidad y costo estimado.
>
> Source: state-of-the-art-audit.md + 4 research docs.
>
> Última actualización: 2026-05-11

## Visión

Producir contenido SFW (Instagram/TikTok) + NSFW (Fanvue/OnlyFans) de una persona sintética con identidad perfecta cross-modelo, escalable a 50-100 piezas/semana, compliant con EU AI Act + US TAKE IT DOWN Act, y monetizable a $10K+/mes en ~6-12 meses.

## Fase 1 — MVP de validación

**Estado: ✅ COMPLETO (2026-05-10/11)**

Done:
- LoRA dual entrenado (FLUX rank 32 + SDXL rank 16)
- Workflows ComfyUI base para FLUX, Chroma, SDXL+bigASP
- Pipeline manual reproducible (RunPod + ComfyUI + scripts)
- Validación end-to-end: SFW + NSFW soft + NSFW hardcore
- Repo en GitHub con todo el código

Costo: ~$8 totales.

## Fase 2 — Foundation Production (Quality + Compliance)

**Objetivo**: pasar de "MVP que funciona" a "producción que escala". Bloques fundacionales antes de tocar volumen/distribución.

**Estimación total**: ~60-90h trabajo, $5-10 infra, **3-4 semanas calendario** part-time.

### Bloque 2.1 — Compliance crítico (CRITICAL LEGAL)

**ROI: CRÍTICO LEGAL** — sin esto, riesgo €15M multa EU + 2 años cárcel TAKE IT DOWN Act US.

**Criterio done**: cada output publicable tiene watermark C2PA + age classifier OK + audit log + disclosure visible.

Subtasks:
- [ ] Integrar `c2pa-python` SDK con HSM/KMS para clave privada
- [ ] Pipeline post-gen mandatorio: age classifier (`dima806/fairface_age_image_detection`) + NSFW classifier (`Falconsai/nsfw_image_detection`) + Q16
- [ ] Audit log estructurado (Logfire) con prompt + seed + modelo + LoRAs + safety scores + outcome + reviewer (6 años retention)
- [ ] Block list LoRAs/embeddings con keywords pediátricos
- [ ] Disclosure template para bio + caption auto-injection
- [ ] AFIP setup (factura E, exportación servicios IVA 0%, CLAE audiovisual)
- [ ] Docs `docs/compliance/safety-policy.md` + `docs/compliance/audit-trail-spec.md`

**Complejidad**: M-L. **Tiempo**: 15-25h. **Costo**: $0.

**KPI**: 100% outputs publishables pasan classifiers + tienen C2PA + audit log.

### Bloque 2.2 — Face Consistency Stack (HIGH ROI)

**Objetivo**: identidad **97%** cross-modelo (vs 80-90% solo con LoRA hoy).

Subtasks:
- [ ] Integrar **FaceDetailer multi-pass** (denoise 0.45→0.25→0.15) en todos los workflows (FLUX, SDXL, Chroma)
- [ ] Integrar **IP-Adapter FaceID Plus v2** en workflow SDXL+bigASP (weight 0.6-0.8)
- [ ] Re-instalar **PuLID-Flux II** correctamente (versión compatible con ComfyUI actual)
- [ ] **ReActor + CodeFormer 0.5** en workflow opcional hero shots (fix torchao o venv aislado)
- [ ] **InsightFace ArcFace QC** automático: `buffalo_l`, cos similarity > 0.45 vs canon mean embedding
- [ ] Script `scripts/face_qc.py` que filtra outputs en batch

**Complejidad**: M. **Tiempo**: 6-10h. **Costo**: $0.

**KPI**: cosine similarity ArcFace ≥ 0.55 en 80%+ de outputs (vs canon mean embedding).

### Bloque 2.3 — Quality Eval Automatizado (HIGH ROI)

**Objetivo**: no entrenar LoRAs a ciegas. Saber qué checkpoint es el sweet spot SIN esperar 3h.

Subtasks:
- [ ] **Validation set heldout**: 5-10 imgs canon NO en training
- [ ] Script `scripts/eval_checkpoints.py`: carga cada `.safetensors`, genera N samples con prompts test, calcula:
  - InsightFace similarity vs canon mean
  - LAION aesthetic predictor v2.5 score
  - CLIP prompt adherence
- [ ] **Batch eval grid**: tabla checkpoint × prompt × score, exportable PNG/HTML
- [ ] **Early stopping**: si métricas no mejoran 3 checkpoints seguidos → notify, sugerir parar
- [ ] **TensorBoard / Logfire** dashboard durante training
- [ ] **Optuna sweep** (opcional v2): correr 3-4 configs en paralelo, elegir ganador automático

**Complejidad**: M-L. **Tiempo**: 10-15h. **Costo**: $0.

**KPI**: tiempo de decisión "qué checkpoint usar" baja de 3h ciegas a 5 min con tabla.

### Bloque 2.4 — Dataset v2 (HIGH ROI)

**Objetivo**: LoRA mejor con dataset más curado + variedad.

Subtasks:
- [ ] **Filtro InsightFace auto**: cos similarity entre fotos del dataset > 0.6 = misma persona. Descarta outliers
- [ ] Generar **10 fotos cuerpo completo** (faltaron en v1)
- [ ] Generar **10 fotos 3/4 view** para mejorar ángulos
- [ ] Re-curar a **25-30 imgs ultra consistentes** (sacar las "puede dar" del v1)
- [ ] Re-train LoRA v2 (FLUX + SDXL) con dataset v2 + eval automático del Bloque 2.3

**Complejidad**: M. **Tiempo**: 6-10h. **Costo**: $3-5.

**KPI**: cos similarity output vs canon mean sube ≥ 0.05 puntos vs v1.

### Bloque 2.5 — Post-Processing Pipeline (HIGH ROI)

**Objetivo**: outputs "indistinguibles de AI obvio". 80% del juego.

Subtasks:
- [ ] Workflow ComfyUI final: base → FaceDetailer → HandDetailer → 4x-UltraSharp upscale 2x → output
- [ ] (Opcional hero) SUPIR upscaler para hero shots
- [ ] Script Python post: PNG→JPEG q92 + resize aspect ratios IG/TikTok/Reel
- [ ] **Humanization pass** (Gap 9): grain ISO 400-800 + chromatic aberration sutil + vignetting
- [ ] Versionado outputs por canal (1080x1350 IG, 1080x1920 Reels, 1080x1080 cuadrado)
- [ ] Documentar `docs/specs/post-processing.md`

**Complejidad**: M. **Tiempo**: 10-15h. **Costo**: $0.

**KPI**: rejection rate post-processing baja de 80% (raw outputs) a 30% (después de pipeline).

### Bloque 2.6 — Pipeline Orchestration MVP (MEDIUM ROI)

**Objetivo**: scripts sueltos → orchestrated FSM con HITL y persistencia.

**Stack**: pydantic-graph (lo conocemos) + Logfire para observability.

Subtasks:
- [ ] Diseñar grafo: `prompt → expand → generate → safety_filter → face_qc → post_process → c2pa_sign → human_review → caption → store → schedule`
- [ ] Implementar nodos como `BaseNode` de pydantic-graph
- [ ] `MongoDBStatePersistence` para HITL pause/resume
- [ ] CLI runner: `python scripts/pipeline.py run --batch=10`
- [ ] HITL UI mínima (CLI o Gradio simple) para approval/reject

**Complejidad**: M-L. **Tiempo**: 20-30h (subset de Gap 6 full). **Costo**: $0 (MongoDB Atlas free tier).

**KPI**: producir 1 pieza end-to-end sin tocar terminal entre nodos.

## Fase 3 — Distribución + Revenue Streams

**Objetivo**: arrancar a generar tráfico real → conversion → ingreso.

### Bloque 3.1 — Plataformas + KYC

Subtasks:
- [ ] Crear cuenta IG del personaje (handle decidir)
- [ ] Crear cuenta TikTok
- [ ] Crear cuenta **Fanvue** con KYC tuyo (Tomás Caruso, AI Creator)
- [ ] Crear cuenta **Passes** como link aggregator (IG-friendly)
- [ ] Bio strategy en cada (3 líneas: identidad + oferta + CTA Passes link)
- [ ] Disclosure compliance en bio (#AI o equivalent)

**Complejidad**: S. **Tiempo**: 3-5h.

### Bloque 3.2 — Content Calendar + Scheduling

Subtasks:
- [ ] Definir "bible del personaje": backstory, voz, valores, hobbies, mascota
- [ ] Calendar inicial: 3 posts/semana IG + Stories diarias + 2-3 TikToks/semana
- [ ] Tool: **Metricool** o **Later** ($20-30/mo)
- [ ] Mix de contenido inicial (semana 1-4): 60% lifestyle, 25% fitness, 15% BTS humanizing
- [ ] **NO Fanvue link directo** en IG bio (shadowban) — usar Passes

**Complejidad**: S-M. **Tiempo**: 5-10h setup + ongoing.

### Bloque 3.3 — Conversion Funnel + Chatter Strategy

Subtasks:
- [ ] Fanvue pricing tier: $9.99-14.99/mes base
- [ ] Bio Fanvue + CTA optimizado
- [ ] Welcome message automatizado nuevos subs
- [ ] **Chatter strategy**: arrancar vos mismo (escala limitada) → contratar 1 chatter humano cuando >100 subs activos
- [ ] DM templates + tone guide

**Complejidad**: M. **Tiempo**: 10-15h setup.

**KPI Fase 3 completa**: primer revenue de Fanvue en 3-6 meses, $500-2K/mes en 6 meses.

## Fase 4 — Video Pipeline

**Objetivo**: agregar Reels/TikToks de calidad. Requerido para TikTok presence real.

Subtasks:
- [ ] Entrenar **Wan 2.2 LoRA dual** (high-noise + low-noise) del personaje (~$10 cloud, 2-4h H100)
- [ ] Setup **ComfyUI native Wan 2.2 I2V-A14B** + LightX2V LoRA accel
- [ ] Cuenta **Hedra Creator** ($30/mo) para talking heads
- [ ] Cuenta **ElevenLabs Creator** ($22/mo) para voz
- [ ] Workflows ComfyUI video: Pipeline B (b-roll cinemático) + Pipeline C (premium híbrido)
- [ ] Sync.so pay-as-you-go ($0.04-0.10/s) para lip-sync over Wan
- [ ] Documentar `docs/specs/video-pipeline.md`

**Complejidad**: L. **Tiempo**: 30-40h. **Costo**: $30-50 training + $70-100/mo operacional.

**KPI**: producir 5 Reels/semana con identidad consistente.

## Fase 5 — Scale & Optimize

**Objetivo**: pasar de 10-20 piezas/semana a 50-100. Optimizar conversion.

Subtasks:
- [ ] **Prefect 3** orchestration (Cloud o self-host) para batches grandes
- [ ] **Modal** para GPU bursts on-demand
- [ ] Analytics dashboard: engagement IG/TikTok + conversion IG→Fanvue + retention Fanvue
- [ ] **A/B test prompts** automatizado (qué tipo de contenido convierte mejor)
- [ ] **Optuna sweep** LoRA v3 (rank + lr + steps optimal)
- [ ] **Hyper-niching exploration**: experimentar con vertical específico (fitness ultra, alt/edgy, cosplay)
- [ ] Agencia chatters humanos (30-40% comm) cuando >500 subs activos

**Complejidad**: L. **Tiempo**: 40-60h. **Costo**: <$200/mo ops.

**KPI**: $5-10K/mes Fanvue + 50K+ followers IG.

## Fase 6 — Multi-personaje (post-validación)

Si Fase 5 funciona y tenemos producto-mercado fit:
- Crear AI Influencer #2 (otra etnia, vibe, niche distinto)
- Reusar todo el pipeline + 5h training LoRAs nuevo personaje + $4
- Cross-promotion estratégica
- Scale a portfolio de 3-5 personajes en 12-18 meses

## KPIs Resumen por Fase

| Fase | KPI principal | Target |
|---|---|---|
| Fase 1 (MVP) | Identidad consistente cross-modelo | ✅ DONE |
| Fase 2 (Foundation) | Pipeline production-grade | 100% outputs publishables con compliance + face QC > 0.55 |
| Fase 3 (Distribución) | Primera revenue | $500-2K/mes Fanvue en 6 meses |
| Fase 4 (Video) | Reels production | 5/semana con identidad consistente |
| Fase 5 (Scale) | Revenue serio | $5-10K/mes + 50K followers |
| Fase 6 (Multi) | Portfolio diversificado | 3+ personajes activos |

## Tres reglas non-negociables

1. **Compliance ANTES de publicar**: cero output publicado sin C2PA + age QC + audit log. Riesgo legal real (€15M + cárcel).
2. **Disclosure SIEMPRE**: bio + caption visible "AI" o equivalente. EU AI Act art. 50 mandatory desde 2 ago 2026.
3. **NO chatbot LLM auto-respondiendo subs**: riesgo class action ("chatter scam"). Vos o humano contratado.
