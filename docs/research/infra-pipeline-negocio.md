# Research — Infraestructura, pipeline operacional y modelo de negocio

> Compilado durante planning. Stack para correr generación + pipeline + cobro desde Argentina.

## 1. GPU rental / cloud compute

### Tabla de precios actual (2026, on-demand, USD/hora)

| GPU | RunPod Community | RunPod Secure | Vast.ai (marketplace) | Notas |
|---|---|---|---|---|
| RTX 4090 (24GB) | ~$0.34/h | ~$0.59-0.69/h | ~$0.29-0.40/h | Caballo de batalla imagen + LoRA |
| RTX 5090 (32GB) | ~$0.69/h | ~$0.89/h | $0.50-0.80/h | 32GB ayuda con FLUX en fp16 sin offload |
| A100 80GB | ~$1.19-1.39/h spot | ~$1.89/h | ~$1.40/h | Overkill para inference, útil para training multi-LoRA |
| H100 80GB | ~$1.99-2.69/h | ~$2.99/h | ~$1.55-1.65/h | Solo si batch grande o video (Wan/Hunyuan) |

**Storage** (RunPod network volume): $0.07/GB/mes (<1TB), $0.05/GB/mes (>1TB). Egress $0. Para 200GB de checkpoints + LoRAs ≈ $14/mes. **Mantener el volume aunque el pod esté apagado** para no re-bajar 20GB de FLUX cada vez.

### Comparativa de plataformas

- **RunPod**: el default razonable. Templates ComfyUI listos, serverless workers, network volumes, UI clara. Levantar pod en ~60s.
- **Vast.ai**: 30-50% más barato pero marketplace (host variable, fiabilidad incierta). Buena opción cuando ya tenés workflow estable. Mal para empezar.
- **Modal**: serverless puro Python. Excelente para integrar con stack pydantic-graph, pero ToS más restrictivo. No ideal para NSFW.
- **Replicate**: pay-per-second sobre modelos pre-deployed. Útil para prototipar; AUP prohíbe contenido sexual explícito. Solo SFW.
- **fal.ai**: serverless con FLUX dev/pro/Kontext, LoRA hosting, $0.025/MP FLUX dev, $0.03/MP FLUX pro, ~$0.04 por imagen 1024². AUP no autoriza pornografía explícita. Útil **SFW**, no NSFW.
- **Lambda Labs / CoreWeave**: enterprise-tier, contratos. Innecesario para MVP.
- **Salad**: GPU residencial distribuido desde $0.02/h. Muy barato pero hosts son PCs gamers; latencia variable. ToS no autoriza adult.

### Política NSFW (lo importante)

- **RunPod**: ToS oficial prohíbe "graphic adult content" PERO en práctica hay tutoriales oficiales NSFW en su blog y comunidad Civitai con templates promocionados. Enforcement laxo. **Estándar de facto** del rubro. **El pod es tuyo**: lo que generes en tu volume queda ahí; no auditan output salvo abuso reportado. CSAM/deepfakes personas reales: ban inmediato + reporte NCMEC.
- **Vast.ai**: similar, ToS genérico, hosts individuales. NSFW lícito de adultos: pasa.
- **fal/Replicate/Modal**: serverless gestionado → no.

**Regla**: para NSFW, ComfyUI self-hosted en pod (RunPod o Vast.ai). Para SFW, fal.ai o Replicate ahorran ops.

### Serverless vs pod por hora — para MVP

- **MVP (no automatizado, vos curando)**: **pod por hora**. Levantás un pod RTX 4090 cuando vas a generar (1-2h por sesión), cerrás. Costo real: $0.50-1/h × 4-6h/semana ≈ $10-25/mes.
- **Post-MVP automatizado**: RunPod Serverless con `worker-comfyui` (repo `runpod-workers/worker-comfyui`). Endpoints `/runsync` y `/run` + `/status`. Solo pagás por segundo de inferencia.

### Estimación de costo del MVP

| Item | Tiempo | Costo |
|---|---|---|
| Generar 100 imágenes FLUX 1024² en RTX 4090 | ~12s/img × 100 ≈ 20min + setup | ~$0.50-1.00 |
| Entrenar 1 LoRA personaje (FLUX, 30 imgs, 2000 steps) | ~2-3h en RTX 4090 / ~45-60min en H100 | $1-3 (4090) / $2-3 (H100) |
| Storage 200GB persistente | mensual | ~$14/mes |
| **MVP mes 1 estimado** (12-15h pod + storage) | | **$25-50/mes** |

## 2. Workflow de generación práctico

### ComfyUI como engine

- Self-host en pod: template "ComfyUI" oficial RunPod o Civitai (one-click SDXL/FLUX). Expone API en puerto 8188.
- **Invocación programática desde Python**:
  - `POST /prompt` con workflow JSON (exportado con "Save (API Format)")
  - WebSocket `/ws` para tracking de progreso por `prompt_id`
  - `GET /view` para descargar imagen
  - Cliente: `comfyui-api` (community) o `runpod-workers/worker-comfyui` para serverless
- **Templates**: workflows JSON versionados en repo. Variables expuestas: prompt, seed, LoRA weight, steps, CFG. Conviene parametrizar con `WorkflowBuilder` Python que toma template y reemplaza nodos.

### Self-host vs API gestionada

- **Self-host (recomendado)**: control total, NSFW posible, custom nodes (face detailer, upscalers, ControlNet), LoRAs propios. 1-2 días de setup la primera vez.
- **fal.ai endpoints**: `fal-ai/flux/dev`, `fal-ai/flux-lora`, `fal-ai/flux-pro/kontext`. $0.025-0.05 por imagen. SFW IG/TikTok y prototipar rápido. No NSFW.
- **Replicate**: similar, ~$0.003-0.05/img. Solo SFW.

### Recomendación práctica (split SFW/NSFW)

- **SFW (IG/TikTok)** post-MVP: fal.ai con LoRA hosteado. $0.04/img.
- **NSFW (OF/Fanvue)**: ComfyUI self-host en RunPod pod. FLUX/Chroma o SDXL bigASP + LoRA personaje + LoRA NSFW.

## 3. Pipeline architecture (pydantic-graph) — Fase 2

### Nodos sugeridos

```
prompt_seed (manual/template)
    -> prompt_expand (LLM: caption-style → SD-style con tokens del personaje)
    -> generate_image (ComfyUI HTTP/WS)
    -> safety_filter (CLIP age classifier + NSFW classifier para asegurar adult-only)
    -> face_consistency_check (ArcFace embedding vs ref del personaje, threshold cosine > 0.6)
    -> upscale (4x-UltraSharp / SUPIR)
    -> human_review (HITL: pause/resume con persistencia Mongo)
    -> caption_gen (LLM: caption IG en español/inglés según target)
    -> store (R2 + Mongo metadata)
    -> schedule (Buffer/Metricool API o manual)
```

### HITL en MVP

`pydantic-graph` tiene `MongoDBStatePersistence` (stack del usuario). El nodo `human_review` pausa la corrida, te muestra grid de candidatos, vos elegís 1 de 4 y resume. Crítico en MVP: la curación humana valida si los prompts/LoRA/seeds funcionan.

### Persistencia

- **Imágenes/videos**: Cloudflare R2. $0.015/GB/mes, **egress $0** (vs S3 $0.09/GB egress). 50GB de assets: $0.75/mes vs ~$5+ en S3 con tráfico.
- **Metadata**: MongoDB (stack del usuario). Schema mínimo:
  - `assets`: `{id, prompt, negative_prompt, seed, model, lora_weights, workflow_json_hash, r2_key, created_at, generation_id, parent_id, score_quality, score_face_consistency, used_in_post}`
  - `prompts`: prompts probados y métrica de éxito
  - `posts`: tracking de qué asset se publicó dónde y métricas
- **NO usar GridFS**: imágenes son archivos grandes, R2 es 10x más barato.

### Eval loop

Tabla `prompt_performance`: por cada `(prompt_template, lora_id, seed_range)` registrar:
- Quality score (manual o aesthetic predictor v2.5)
- Face consistency score
- Engagement post-publicación

## 4. Modelo de negocio AI influencer / OF

### Casos de éxito públicos

- **Aitana López** (The Clueless, España): 370k followers IG, ~$10k/mes Fanvue al inicio (2023), reportes 2026 hablan de $30k/mes Fanvue + sponsorships (Victoria's Secret, Olaplex, Zara). Total estimado $800k-$1M acumulado.
- **Jessica Foster**: 1M followers IG en ~3 meses con persona AI militar pro-Trump → embudo a OF foot fetish. Growth ultra-rápido vía nicho político.
- **Top Fanvue earners**: $300k/mes los top 7 (mix humanos + AI).

### Métricas de funnel

- **Conversión IG → paid sub**: 1-3% en niches comerciales. 50k followers ≈ 500-1500 subs.
- **Pricing sub**: $9.99-$24.99/mes
- **Earning band**: $3k-$30k/mes con 1k-5k subs activos. Top tier $50k-$200k/mes.
- **Tiempo a primera conversión**: 3-12 meses típico. Casos virales (nicho fuerte): 1-3 meses. **MVP realista**: 6 meses para primera revenue significativa.

### Plataformas (comparación AI-friendly)

| Plataforma | Take rate | AI-friendly | KYC |
|---|---|---|---|
| **Fanvue** | 15% (mes 1), 20% después | **Explícito y bienvenido**. Categoría "AI Creator" oficial. | ID gov + selfie del owner real. |
| **OnlyFans** | 20% | Permitido con disclosure obligatorio + tag #AI. Deepfakes prohibidos (ban permanente desde 2026). Liveness check al onboarding. | Liveness detection del owner real. |
| **Passes / Loyalfans** | varía | Permitido pero menos tráfico orgánico. | ID + selfie. |

> Detalle completo de plataformas en `plataformas-monetizacion.md`.

### Disclosure requerido

- **OnlyFans**: tag #AI o #AIGenerated visible. Mandatorio desde 2026.
- **Fanvue**: watermark, caption O bio statement.
- **TikTok**: label "AI-generated" obligatorio. C2PA Content Credentials desde enero 2025 (auto-detect).
- **Instagram/Meta**: "AI info" label, soft enforcement, igual debe declararse.
- **EU AI Act**: desde 2 agosto 2026, mandatorio en toda la UE.

### Chatters (chat con subs)

- **No automatizar con LLM en MVP.** Caso *N.Z. v. Fenix* (federal, 2025) se desestimó pero sigue activo el riesgo de class action por "chatter scam" si subs descubren que no es la "modelo".
- **Práctica del rubro**: 80% de OF top earners delegan a agencias de chatters humanos (NEO Agency = ~70 creators, mix humano+AI tipo FlirtFlow). Cobran 30-50% de tips/PPV.
- **MVP**: vos chateás (o un chatter contratado). LLM-assisted en background (sugerencia de respuesta) está OK; LLM auto-respondiendo sin disclosure → riesgo legal y baja retención.

### KYC sin persona real

- Fanvue/OF requieren ID gov del **dueño de la cuenta**. Vos verificás como "Tomás Caruso, AI Creator". El personaje del LoRA no necesita verificación porque legalmente es ficticio.
- Si más adelante involucrás socio/socia (modelo de voz/manos para videos), esa persona también necesita pasar KYC.

## 5. Aspectos legales/éticos críticos

### Edad (línea roja absoluta)

- AIG-CSAM = mismo penalty que CSAM real en US, EU, AR. Federal felony en US.
- **Salvaguardas obligatorias**:
  1. **Dataset training del LoRA**: solo imágenes adultos verificados (≥25 años visualmente). NUNCA caras menores ni imágenes ambiguas.
  2. **Prompts positivos**: siempre `"adult woman, 25 years old, mature features"`.
  3. **Negative prompts**: `"child, teen, young, minor, underage, kid, schoolgirl, loli"` (estándar industria).
  4. **Filter post-gen**: clasificador de edad (ej. `nateraw/age-classifier` o CLIP-based) en el pipeline. Cualquier output "minor" → descartar y loggear.
  5. **Documentación**: README del repo con safety policy explícita. Si hay auditoría, evidencia de due diligence.

### Likeness rights

- **Nunca** cara de persona real en LoRA. Caras 100% sintéticas (composite de varias generaciones random).
- TAKE IT DOWN Act (US, mayo 2025): publicar deepfakes íntimos no consentidos = hasta 2 años cárcel. Plataformas obligadas a takedown en 48h desde mayo 2026.
- OnlyFans 2026: ban inmediato por deepfake/face-swap.

### Disclosure como AI

- Reduce engagement ~10-25% en IG vs cuentas que ocultan AI, pero ocultar es violación ToS y riesgo de ban masivo (Meta detecta C2PA + visual classifiers). **Cumplir**.

### Jurisdicción Argentina

- No hay restricción específica a generación de contenido adulto AI en AR (mayores de edad).
- AFIP: ingresos como exportación de servicios. Monotributo según ingresos o RI.

### Cobro desde Argentina (2026)

Buenas noticias: **cepo levantado en sept 2025**.

- Régimen BCRA septiembre 2025: freelancers cobran sin límite, no hay obligación de liquidar a pesos.
- Cupo USD 36k/año exento de liquidación oficial subsiste como floor garantizado.
- **Métodos prácticos**:
  - **Payoneer / Wise**: clásico, USD a cuenta global, retiro a banco AR o tarjeta.
  - **Deel**: USDC/USD/cripto. Útil si plataforma destino paga via SWIFT directo.
  - **DolarApp / Wayex**: stablecoins (USDC) directo. Sin pasar por banco AR.
  - **Fanvue payouts**: bank transfer global O **crypto** (USDT/USDC) — **la opción más limpia desde AR**.
  - **OnlyFans**: bank transfer SWIFT vía banco AR (Payoneer intermediario común) o e-wallet.
- **Recomendación**: Fanvue + payout en crypto (USDC) → wallet propia → P2P o DolarApp. Cero fricción.

## 6. Stack adoptado para MVP (decisión)

```
Generación SFW (IG/TikTok):  fal.ai (FLUX dev + LoRA hosted)            $0.04/img    [post-MVP]
Generación NSFW (OF/Fanvue): RunPod pod RTX 4090 + ComfyUI self-host    $0.34/h
Training LoRA personaje:     RunPod RTX 4090, ai-toolkit o kohya        $1-3 por LoRA
Storage assets:              Cloudflare R2                              $0.015/GB/mes [post-MVP]
Storage modelos/checkpoints: RunPod Network Volume                      $0.07/GB/mes
Metadata:                    MongoDB Atlas free tier (M0)               [Fase 2]
Pipeline:                    pydantic-graph + MongoDB persistence       [Fase 2]
Curación:                    HITL (vos en MVP)
Safety:                      age classifier + NSFW classifier post-gen + negative prompts
Plataforma monetización:     Por decidir (ver plataformas-monetizacion.md)
Cobro:                       Fanvue → USDC payout → DolarApp/Wayex
Tracking:                    Mongo collection prompts/assets/posts con score_*    [Fase 2]
Costo total MVP:             ~$25-50 USD
```

## Fuentes principales

- [RunPod Pricing](https://www.runpod.io/pricing)
- [Vast.ai Pricing](https://vast.ai/pricing)
- [RunPod ComfyUI Serverless](https://docs.runpod.io/tutorials/serverless/comfyui)
- [worker-comfyui](https://github.com/runpod-workers/worker-comfyui)
- [fal.ai pricing](https://fal.ai/pricing)
- [Fanvue AI Content Guidelines](https://help.fanvue.com/en/articles/9538738-is-ai-content-allowed-on-fanvue)
- [Fanvue KYC for AI creators](https://help.fanvue.com/en/articles/9539091-passing-kyc-and-creating-multiple-accounts-as-an-ai-creator)
- [OnlyFans 2026 AI/Deepfake Policy](https://list25.com/onlyfans-2026-policy-updates-ai-deepfake-ban-verification/)
- [TAKE IT DOWN Act](https://blog.ericgoldman.org/archives/2025/12/onlyfans-defeats-chatter-scam-claim-n-z-v-fenix.htm)
- [Aitana López case study](https://www.euronews.com/next/2024/12/27/meet-the-first-spanish-ai-model-earning-up-to-10000-per-month)
- [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/)
- [Cepo / Régimen BCRA freelancers (Infobae)](https://www.infobae.com/economia/2025/09/23/fin-del-cepo-para-freelancers-como-cobrar-en-dolares-del-exterior-sin-limites-con-el-nuevo-regimen-del-bcra/)
- [Thorn — Safety by Design for Generative AI](https://info.thorn.org/hubfs/thorn-safety-by-design-for-generative-AI.pdf)
- [ComfyUI FLUX LoRA character consistency 2026](https://www.apatero.com/blog/comfyui-lora-training-character-consistency-guide-2026)
