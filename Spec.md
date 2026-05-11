# Spec — AI Influencer Project

> Visión producto completa post-MVP. Reemplaza la spec inicial que solo cubría Fase 1.
>
> Última actualización: 2026-05-11 (post-MVP validación + audit state-of-the-art).

## Qué es

Negocio personal de **AI influencer**: una persona sintética fotorealista con identidad consistente que opera como creadora de contenido en Instagram + TikTok (SFW) y monetiza vía Fanvue + OnlyFans-style platforms (NSFW). Producto-negocio del usuario (Tomás Caruso) en Argentina, target Fanvue + brand deals.

## Para quién

Producto-negocio del usuario. Sin clientes externos. El objetivo es generar revenue propio escalable y sostenible.

## Validación del modelo (post-research)

**Datos reales del rubro 2026** (research forensic):
- Top 1% AI Fanvue: $50K+/mes (Ami BNW, Aya Petite)
- Tier "muy bueno" estable: $10-30K/mes (Emily Pellegrini-tier)
- Aitana López: $4-8K/mes consistente (NO los $30K que pintó la prensa — plateau followers desde 2024)
- Median creator decente: $500-5K/mes después 3-6 meses consistentes
- **Time to first significant revenue**: 6-12 meses con esfuerzo serio

**Time-to-value target**: $5-10K/mes en 12 meses calendar.

## Hipótesis de negocio

| # | Hipótesis | Status |
|---|---|---|
| H1 | Es viable generar contenido fotorealista NSFW con identidad consistente | ✅ **VALIDADA** (MVP, 2026-05-11) |
| H2 | Es viable construir pipeline production-grade que produzca 50-100 piezas/semana | 🔄 En camino (Fase 2 Foundation) |
| H3 | Funnel IG/TikTok → Fanvue convierte a ratio que justifica costo + time-to-market | ❓ A validar (Fase 3 Distribución) |
| H4 | Personaje específico (morocha italiana ojos verdes 19yo) convierte mejor que alternativa | ❓ A validar (Fase 3+) |
| H5 | Multi-personaje portfolio escala revenue linealmente | ❓ A validar (Fase 6) |

## Restricciones non-negociables

### Legal/Compliance
- **Mayoría de edad absoluta**: contenido únicamente de adultos. CSAM/AIG-CSAM = línea roja legal absoluta (felony US/EU/AR).
- **Likeness**: caras 100% sintéticas. Cero referencia a personas reales identificables. Violar = TAKE IT DOWN Act US (2 años cárcel).
- **Disclosure AI**: cumplir EU AI Act art. 50 (mandatorio desde 2 ago 2026). Multas hasta €15M o 3% facturación.
- **Plataformas**: cumplir ToS Fanvue (AI permitido con disclosure), TikTok (auto-label), Meta (auto-label C2PA).

### Operacional
- **NO chatbot LLM** respondiendo subs sin disclosure (riesgo class action "chatter scam" — caso N.Z. v. Fenix).
- **Audit trail mandatorio** EU AI Act: prompt + seed + modelo + LoRAs + safety scores + outcome + reviewer (retention 6 años).
- **Photoshop / post-processing manual** sobre outputs críticos (80% rejection rate de raw output es estándar industria).

## Persona objetivo del MVP

**aiinfluencer1** (canon lockeado, 2026-05-10):
- Adult woman, 19 years old, young adult features, fresh face
- Italian heritage, soft feminine sensual features
- Long jet black hair, perfectly straight and sleek, salon-finished glossy, mid-back length
- Soft hazel green eyes, almond-shaped, sultry bedroom eyes, alluring gaze
- Porcelain fair skin, smooth and luminous, natural healthy glow
- Soft heart-shaped face, defined cheekbones, balanced youthful features
- Defined dark eyebrows, full plump glossy lips, natural pink tone
- Hourglass body, natural feminine curves, well-toned, 168cm tall
- Small beauty mark above the left side of upper lip
- Subtle dimple on right cheek when smiling
- Soft natural makeup, glossy lips, light tan eyeliner, natural lashes
- Playful flirty confident expression, magnetic alluring presence
- Girl next door beauty with sex appeal, instagram influencer aesthetic
- Photorealistic candid photography, natural daylight or soft window light

Ver `prompts/identity_canon.txt` para versión completa.

## Decisiones técnicas (lockeadas post-MVP)

### Stack de generación (validado en MVP)
- **Cloud**: RunPod pod RTX 4090 ($0.34-0.69/h)
- **Engine**: ComfyUI native
- **SFW Instagram/TikTok**: FLUX.1-dev + LoRA aiinfluencer1_flux + PuLID-Flux II (pendiente fix)
- **NSFW softcore**: Chroma1-HD + LoRA aiinfluencer1_flux
- **NSFW hardcore**: bigASP v2.5 + LoRA aiinfluencer1_sdxl
- **Identidad**: LoRA dual (FLUX rank 32 + SDXL rank 16) entrenados sobre dataset canon de 54 imgs

### Stack de pipeline (Fase 2)
- **Orquestación**: pydantic-graph + Logfire (incremental); migrar a + Prefect 3 + Modal cuando volumen lo justifique
- **State persistence**: MongoDB Atlas free tier
- **Storage assets**: Cloudflare R2 ($0.015/GB/mes, egress $0)
- **Metadata + audit log**: MongoDB

### Stack de compliance (Fase 2)
- **C2PA signing**: `c2pa-python` SDK con clave en HSM/KMS
- **Age classifier**: `dima806/fairface_age_image_detection`
- **NSFW classifier**: `Falconsai/nsfw_image_detection` + Q16
- **Face QC**: InsightFace `buffalo_l`, cos > 0.45 vs canon mean
- **Disclosure**: bio + caption visible "AI" + watermark Fanvue

### Stack de distribución (Fase 3)
- **Plataformas primarias**: Fanvue (NSFW), Instagram (SFW funnel), TikTok (SFW funnel)
- **Link aggregator**: Passes (90/10 split, IG-friendly)
- **Scheduling**: Metricool o Later ($20-30/mo)
- **Chatter management**: Substy si Fanvue serio
- **Cobro AR**: Fanvue → USDC payout → DolarApp/Wayex
- **Facturación**: Factura E exportación servicios IVA 0%, monotributo cat K

### Stack de video (Fase 4)
- **Wan 2.2 I2V-A14B** local + LoRA Wan dual entrenado del personaje
- **Hedra Character-3** ($30/mo) para talking head
- **Sync.so lipsync-2-pro** ($0.04-0.10/s) para lip-sync sobre video Wan
- **ElevenLabs Creator** ($22/mo) para voz
- **LivePortrait** local para volumen secundario

## Fases del producto

Ver `docs/roadmap.md` para detalle completo. Resumen:

| Fase | Objetivo | Status | Estimación |
|---|---|---|---|
| **1 — MVP** | Validar identidad consistente cross-modelo SFW+NSFW | ✅ DONE | $8 totales |
| **2 — Foundation** | Production-grade: compliance + face QC + eval + dataset v2 + post-processing + orchestration MVP | 🔄 Next | 60-90h, $5-10 infra |
| **3 — Distribución** | Cuentas + content calendar + chatter strategy + primer revenue | ⏳ Después | 20-30h + $50-100/mo ops |
| **4 — Video** | Wan 2.2 LoRA + workflows Reels/TikTok | ⏳ Después | 30-40h, $30-50 train + $70-100/mo |
| **5 — Scale** | 50-100 piezas/semana + analytics + agencia chatters | ⏳ Después | 40-60h + <$200/mo |
| **6 — Multi-personaje** | Portfolio 3-5 personajes | ⏳ Eventual | 5h + $4 por personaje nuevo |

## Entregables principales

### Repo permanentes
- `Spec.md` (este documento) — visión producto
- `docs/roadmap.md` — fases y prioridades
- `docs/state-of-the-art-audit.md` — gaps vs industry top
- `docs/research/` — research consolidado por área (4 docs)
- `docs/implementation/` — descripción de cada módulo implementado
- `docs/compliance/` — safety policy + audit trail spec (Fase 2)
- `docs/specs/<feature>.md` — specs específicos por feature (cuando se implementan)

### Activos del personaje (post-Fase 2)
- LoRAs (FLUX + SDXL + Wan dual) en model registry
- Dataset canon v2 (25-30 imgs ultra consistentes)
- Foto canon "ID card" única para IPAdapter
- Voz fija (ElevenLabs cloned + F5-TTS local)
- Persona bible (backstory, voz, valores)

### Infraestructura
- RunPod pod ephemeral (manejado por `scripts/pod.py`)
- Network volume persistente 100 GB
- ComfyUI workflows versionados
- Pipeline orchestration (pydantic-graph)
- MongoDB Atlas para state + metadata + audit log
- Cloudflare R2 para assets

## Métricas de éxito

### Técnicas (Fase 2 done)
- Cosine similarity ArcFace ≥ 0.55 en 80%+ outputs vs canon mean
- 100% outputs publishables con C2PA + age QC + audit log
- Time to decide checkpoint sweet spot: 5 min (vs 3h ciegas)
- Post-processing rejection rate: 30% (vs 80% raw)

### Negocio (Fase 3-5)
- First revenue Fanvue: $500-2K/mes en 6 meses
- Followers IG: 10K en 3 meses, 50K en 12 meses
- Fanvue subs activos: 100 en 6 meses, 1K en 12 meses
- Revenue target: $5-10K/mes a 12 meses

## Riesgos identificados

### Legales/regulatorios
- EU AI Act Art. 50 (mandatorio 2 ago 2026): mitigado con C2PA + disclosure (Fase 2 Bloque 2.1)
- TAKE IT DOWN Act US: aplica solo si parecido a persona real — caras 100% sintéticas mitigan
- AIG-CSAM: línea roja absoluta, mitigada con age classifier + edad explícita prompts + canon adult

### Plataforma
- Meta/IG: shadowban si link directo a Fanvue → mitigado con Passes aggregator
- TikTok: stricter que IG con suggestive → mitigado con bikini OK, lencería NO
- OnlyFans 2026: requiere humano verificado real → vamos por **Fanvue** que sí permite AI

### Producto-mercado
- Mercado AI influencer saturado en 2026 (varios casos virales y plateaus) → mitigado con hyper-niching potencial y multi-personaje en Fase 6
- Chatter ops es el cuello de botella real (90% revenue) → planificado: vos personal → 1 chatter → agencia cuando >500 subs

### Operacionales
- Top operators trabajan 8-14h/día en mensajería + 80% rejection rate de outputs → set expectations realistas (no es máquina pasiva de plata)

## Lo que NO es este proyecto

- No es un wrapper de APIs comerciales (Midjourney, Runway, etc.) — necesitamos NSFW + control fino → modelos locales open
- No es un SaaS para terceros — producto-negocio personal
- No es chatbot LLM general purpose — riesgo legal alto
- No es un experimento de UI / frontend en esta fase — todo es backend + ComfyUI hasta Fase 5+
