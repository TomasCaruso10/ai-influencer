# Research — Modelos SFW + video + voz + funnel a OF

> Compilado durante planning. Stack para Instagram/TikTok y conversión hacia plataformas de monetización.

## 1. Modelos de imagen para fotorealismo SFW

| Modelo | Calidad piel/cara | Anatomía/manos | Ecosistema LoRA/ControlNet | Costo | Veredicto |
|---|---|---|---|---|---|
| **FLUX.1-dev** | Excelente, pero piel a veces "oily/wax" | Muy bueno (manos correctas la mayoría) | Maduro (Civitai, ComfyUI, PuLID-Flux, ACE++) | Local 24GB VRAM o API (fal.ai/Replicate ~$0.025/img) | **Default 2026 para pipeline propia** |
| **FLUX.2 Pro / Flux1.1** | Mejor texturas y poros | Mejor coherencia | Más chico, LoRA scene en transición | API (BFL/fal) | Hero shots, no volumen |
| **SDXL + RealVisXL V5 / Juggernaut XL / epiCRealism** | Muy bueno con LoRA correcto, menos "oily" | Inferior a Flux | El **más maduro** del mercado | Local 12GB VRAM, 4x más rápido que Flux | **Vigente 2026 para volumen** |
| **SD 3.5 Large** | Aesthetic limpio | Decente | Ecosistema chico | Local 24GB VRAM | Niche, no recomendable principal |
| **Midjourney V7** | Top en estética "instagrameable" | Muy bueno | API oficial limitada | $30-60/mes | Mood boards, no pipeline (TOS gris) |
| **Imagen 4 Ultra (Google)** | El más fotorrealista en benchmarks | Excelente | Solo Vertex AI, sin LoRA | Enterprise | Caro, sin control identidad — descartar |
| **Ideogram 3.0** | Bueno, fuerte en text rendering | Decente | API | Pay per use | Útil para imágenes con texto |

**Recomendación**:
- **Stack principal SFW**: FLUX.1-dev local + LoRA propia entrenada con 30-50 fotos canon.
- **Stack secundario**: SDXL + RealVisXL V5 + LoRA equivalente para volumen.
- **Mismo modelo SFW e NSFW NO conviene**: Flux base está alineado, NSFW requiere checkpoints específicos. La identidad se sostiene con la misma LoRA + face embedding (PuLID/InstantID).

## 2. Identidad consistente cross-modelo

LoRA SDXL ≠ LoRA Flux (arquitecturas distintas). Hay que entrenar **dos LoRAs paralelas** del mismo dataset canon, o usar adapters de identidad por encima.

| Técnica | Funciona en | Calidad identidad | Velocidad | Notas |
|---|---|---|---|---|
| **LoRA dedicada** (kohya, ai-toolkit) | Por arquitectura | **Máxima** — captura cara, body, vibe, ropa | Entrenamiento 30-60min en 4090 | Gold standard |
| **PuLID-Flux** | Flux solo | Muy buena, zero-shot (1 foto ref) | Rápido, sin training | Buen complemento a LoRA |
| **InstantID** | SDXL | La más alta en benchmarks | Resource-heavy | Mejor para SDXL |
| **ACE++ / EcomID** | Flux | Buena outfits/escenas | Medio | Útil fashion/products |
| **HyperLoRA / IP-Adapter FaceID** | SDXL | Media | Rápido | Backup |
| **ReActor / face-swap final** | Cualquiera | "Pega" cara final | Fast | Truco clave: genera con lo que sea, swap final con foto canon |

**Workflow "una identidad, múltiples modelos"**:

1. Generar 30-50 caras canon con Flux + prompt fijo, curar las 20 mejores.
2. Entrenar LoRA-Flux y LoRA-SDXL en paralelo con el mismo dataset.
3. SFW IG/TikTok: Flux + LoRA-Flux + PuLID con foto canon.
4. NSFW OF: SDXL/Pony + LoRA-SDXL + InstantID + face-swap final con ReActor con foto canon.
5. **Foto canon única** = "ID card" reusada en todo: PuLID, InstantID, ReActor, IPAdapter.

## 3. Video corto vertical (Reels/TikTok 9:16, 5-15s)

| Modelo | Realismo humano | 9:16 nativo | Duración | Costo (10s) | API/local |
|---|---|---|---|---|---|
| **Kling 2.0 / 2.5** | Top tier | Sí | hasta 10s, extensible 2min | ~$0.70 | API (Kuaishou, fal) |
| **Hailuo 02 (MiniMax)** | Muy bueno, sigue prompts detallados | Sí | 6-10s | ~$0.50 | API |
| **Runway Gen-4 / Gen-4.5** | Excelente control | Sí | 10s | ~$1.20 | API |
| **Luma Ray2 / Dream Machine** | Bueno | Sí | 5-10s | ~$0.40 | API |
| **Veo 3.1 (Google)** | El más realista + audio nativo | Sí | hasta 8s | Premium | Vertex AI |
| **WAN 2.1 / 2.2** | Bueno, en mejora | Sí | 5s | **Gratis local** (24GB+ VRAM) | Open source |
| **HunyuanVideo** | Decente | Sí | 5s | Gratis local | Open source |

**Recomendación**: **Kling 2.0 / Hailuo 02** API para arrancar (mejor ratio costo/calidad para humanos en 9:16). **WAN 2.2 local** para escalar volumen sin sangrar API.

**Lip-sync (talking head)**:

| Tool | Mejor para | Costo | Veredicto |
|---|---|---|---|
| **Hedra Character-3** | Foto + voz → talking head | $30+/mes | **Top pick 2026** |
| **HeyGen Avatar IV** | Avatares pre-construidos | $30-90/mes | "Avatar-y", se nota |
| **LivePortrait** | Open source, drive con video | Gratis local | Bueno volumen |
| **Sonic** | Open source, audio-driven | Gratis local | Calidad menor a Hedra |
| **VEED Fabric 1.0** | Top en accuracy | API | Alternativa a Hedra |
| **Sync.so** | Lip sync de video existente | API | Para post-process |

**Recomendación**: Hedra Character-3 para clips talking head. LivePortrait local para volumen. Combinar: cuerpo en Kling (I2V), lip-sync con Sync.so si es necesario hablar.

## 4. Voz única para la influencer

| Tool | Calidad | Cloning data | Lic. comercial | Costo |
|---|---|---|---|---|
| **ElevenLabs v3** | Top tier prosodia | Instant 60s, Pro 30min | OK | $22-330/mes |
| **PlayHT 3.0** | Muy buena, baja latencia | Similar | OK | $31+/mes |
| **Resemble AI** | Buena, focus enterprise | 30min+ | OK + watermark | Enterprise |
| **F5-TTS** (open) | Compite con ElevenLabs zero-shot | 10s | OK (MIT-friendly) | Gratis local |
| **XTTS v2 / Coqui** (open) | Muy buena | 6s | **NO comercial** (Coqui PML) | Gratis local |
| **Voxtral TTS** (Mistral, mar 2026) | 62.8% lo prefirió sobre ElevenLabs Flash | 10s | Open | Gratis |
| **Chatterbox** (open, MIT) | Buena | 5-10s | OK comercial | Gratis |

**Cómo construir una voz única (no clonar persona real)**:

1. Sintetizar voz base con ElevenLabs **Voice Design** (genera voces sintéticas desde descripción).
2. Generar 30 minutos de audio leyendo guion variado.
3. Re-clonar esa voz sintética en F5-TTS o ElevenLabs Pro Voice Clone para fijarla.
4. **NUNCA clonar voces reales** (right of publicity).

**Recomendación**: ElevenLabs v3 + Voice Design (build) → F5-TTS o Chatterbox (clone for volume).

> **Nota MVP**: voz queda **fuera de alcance** de Fase 1 del MVP. Se prepara la decisión pero no se ejecuta hasta Fase 2.

## 5. Detección anti-IA en plataformas (mayo 2026)

**Lo que SÍ hacen Meta y TikTok**:

- **C2PA Content Credentials**: TikTok auto-detecta y label desde enero 2025 (1.3B videos labeled). Meta integró C2PA en IG/FB en 2024. Auto-label rate ~35-45%.
- **SynthID** (Google/DeepMind): watermark imperceptible en pixeles, presente en outputs Imagen/Veo. Sobrevive screenshots, recompresión, crops menores.
- **Detectores propios**: clasificadores propios sobre uploads. No perfectos pero mejoran cada quarter.
- **EU AI Act art. 50**: desde **agosto 2026** label obligatorio en plataformas grandes en UE.

**Lo que NO hacen (todavía)**:

- Banear contenido AI por defecto. Política oficial es **labelear, no remover**, mientras no impersone a persona real ni engañe sobre hechos.
- AI influencers están permitidos en IG y TikTok si: (a) llevan label "AI-generated" cuando aplica, (b) no impersonan persona real, (c) no engañan en contexto factual.

**Estrategias de "humanización" (orden de impacto)**:

1. **Strip metadata C2PA/EXIF**: ExifTool, `remove-ai-watermarks`, `noai-watermark`. Trivial pero necesario.
2. **Remover SynthID** (si se usa Imagen/Veo): perturbaciones imperceptibles + resize. Tools: `remove-ai-watermarks`. **Importante**: Flux/SDXL/Kling NO tienen SynthID — saltar este paso si no usás Google.
3. **Re-encode pipeline**: PNG → JPEG q92 → resize a 1080x1350 (IG) o 1080x1920 (Reels). Rompe muchos watermarks invisibles.
4. **Pasada por camera grain**: ISO ~400-800, chromatic aberration leve, vignetting sutil.
5. **Imperfecciones humanas**: motion blur leve, recortes mal cuadrados ocasionales, "fotos malas" intercaladas (selfie en espejo desenfocado, pie con café).
6. **Foto del teléfono**: re-tomar imagen de pantalla con teléfono real o simular en Photoshop con perfil de lente. Muy efectivo, costoso de automatizar.
7. **No subir a 4K**: las plataformas comprimen igual. 1080p evita flags de detectores pixel-perfect.

**Importante legal**: remover SynthID/C2PA para hacer pasar contenido AI como humano puede violar **DMCA**, **EU AI Act art. 50** (multa hasta €15M o 3% facturación), y **COPIED Act** (US, propuesto). **Riesgo real, no teórico**.

**Casos exitosos conocidos (pipeline pública/inferida)**:

- **Aitana López** (The Clueless): Stable Diffusion + ComfyUI + LoRA propia + Photoshop manual heavy. ~€10-30k/mes (Fanvue + brand deals).
- **Milla Sofia**: similar, foco lifestyle finlandesa.
- **Jessica Foster** (viral 2026): IG + OnlyFans, persona "MAGA girl", probable Flux + LoRA.
- **Patrón común**: NO admiten ser IA en bio, label cuando IG lo fuerza, foco en lifestyle/fitness/cosplay, posteo 2-3x dia.

## 6. Estrategia de contenido del funnel SFW → OF

**Tipos de contenido SFW que más convierten (data agregada operadores 2026)**:

1. **Fitness / gym** (top conversion): bikini deportivo, gym selfies, ropa ajustada. Audiencia masculina 18-35 muy alta.
2. **Girl-next-door / lifestyle**: café, ropa casual, "día en mi vida", outfits OOTD. Construye parasocial.
3. **Cosplay light** (anime/gaming): nicho fuerte, alta lealtad.
4. **Travel / beach**: playa, viajes, bikini "natural". Excelente para summer.
5. **Modelaje / fashion**: lookbooks, try-on hauls (sin ser try-on de lencería).

**Frecuencia recomendada (operadores top)**:

- Instagram: **2-3 posts/dia** (1 feed + 1-2 stories) + **1-2 Reels/dia**.
- TikTok: **3-5 videos/dia** (volumen > calidad para feed algoritmo).
- Total: ~50-100 piezas/semana. **Imposible sin pipeline automatizada**.

**Storytelling y persona (criticísimo)**:

- **Backstory coherente**: nombre, edad, ciudad, profesión ficticia, hobbies, mascota. Documentar en una "bible" del personaje.
- **Voz consistente**: caption style, emoji habituales, slang.
- **Inconsistencia visual = death sentence**: según data de operadores, **inconsistencia de cara/cuerpo entre posts es la causa #1 de cancelación en primeros 30 días** en OF/Fanvue.
- **Arc narrativo**: episodios de la vida del personaje, no posts random. Genera retención.

**Restricciones IG/Meta para evitar shadowban / takedown**:

- Nada explícito: no genitales, no nipples, no posiciones sexuales, no sexual solicitation textual.
- **Bio**: usar **link aggregator** (Linktree, Beacons, Passes) — **NUNCA link directo a OnlyFans** (Meta lo penaliza). **Passes** (Lucy Guo, 90/10 split) es el aggregator más amigable a IG/TikTok en 2026.
- **Captions**: evitar palabras trigger ("subscribe", "premium content", "spicy", "exclusive 18+"). Código: "more of me elsewhere", "link in bio for the rest", "VIP".
- **No DM solicitation**: Meta detecta solicitation en DMs (2x más detection en 2026).
- **AI label**: cuando IG/TikTok auto-labelee, aceptar y seguir.

**Restricciones TikTok adicionales**:

- TikTok más estricto que IG con suggestive. Bikini OK, lencería NO.
- "For You Page" penaliza accounts que linkean a sites adult-skewed. Usar SFW aggregator.
- Lives: NO hacer (riesgo de exposed AI face mid-stream).

## Decisión adoptada en el plan MVP

| Capa | Pick principal | Pick alternativo |
|---|---|---|
| **Imagen SFW** | FLUX.1-dev + LoRA propia + PuLID-Flux | SDXL + RealVisXL V5 + InstantID |
| **Imagen NSFW** | bigASP / Lustify + LoRA-SDXL + ReActor | Chroma (Flux uncensored) — AB |
| **Identidad** | LoRA dual (Flux + SDXL) + foto canon única | — |
| **Video** | Kling 2.0 / Hailuo 02 (API) | WAN 2.2 local |
| **Lip-sync** (Fase 2) | Hedra Character-3 | LivePortrait local |
| **Voz** (Fase 2) | ElevenLabs v3 → F5-TTS local | Chatterbox |
| **Humanización** | ExifTool + JPEG re-encode + grain pass | Pillow/OpenCV custom |
| **Funnel link** | Passes (90/10) o Beacons | Linktree |

## Riesgos legales a considerar

1. EU AI Act art. 50 (label obligatorio agosto 2026).
2. Strip de SynthID/C2PA puede ser ilegal (DMCA/COPIED).
3. Meta puede banear cuenta sin warning si detectan AI no labelado + adult solicitation patterns.
4. Right of publicity: nunca usar voz/cara basada en persona real.

## Fuentes

- [Flux vs SDXL 2026](https://pxz.ai/blog/flux-vs-sdxl)
- [Comparing 4 Face Swap Techniques](https://myaiforce.com/hyperlora-vs-instantid-vs-pulid-vs-ace-plus/)
- [How to create AI influencer like Aitana López](https://www.theinfluencer.ai/blog/how-to-create-an-ai-influencer-like-aitana-lopez)
- [AI Video Generation Showdown 2026](https://www.aimagicx.com/blog/ai-video-generation-showdown-2026)
- [Best Lip Sync AI Tools 2026](https://gaga.art/blog/lip-sync-ai/)
- [HeyGen vs Hedra](https://lipsync.com/compare/heygen-vs-hedra)
- [ElevenLabs vs PlayHT vs Resemble 2026](https://www.index.dev/skill-vs-skill/ai-elevenlabs-vs-playht-vs-resemble)
- [Best Open-Source TTS 2026](https://findskill.ai/blog/best-open-source-tts-2026/)
- [TikTok AI Content Labeling 2026](https://www.auditsocials.com/blog/tiktok-ai-content-disclosure-rules-2026)
- [AI Disclosure Rules by Platform](https://influencermarketinghub.com/ai-disclosure-rules/)
- [Meta Adult Sexual Solicitation Policy](https://transparency.meta.com/policies/community-standards/sexual-solicitation/)
- [Instagram Rules for OnlyFans Creators 2026](https://www.inro.social/blog/avoid-instagram-bans-onlyfans)
- [How to Build SFW to NSFW Pipeline](https://sozee.ai/resources/build-sfw-to-nsfw-pipeline/)
- [remove-ai-watermarks (GitHub)](https://github.com/wiltodelta/remove-ai-watermarks)
