# Research — Video + Lip-Sync Pipeline (2026)

> Para AI influencer con character LoRA. Generar Reels/TikToks 5-15s (9:16 vertical) manteniendo identidad. Asume LoRA FLUX + LoRA SDXL ya entrenados.

## 1. Wan 2.2 con Character LoRA

**Variantes y VRAM**:
- **TI2V-5B**: 8 GB VRAM mín. 5s @ 480p en ~4 min RTX 4090, 720p ~9 min. Para drafts.
- **I2V-A14B** (MoE 27B total, 14B activos): 16 GB mín, 24 GB recomendado. 720p 5s = ~9 min en 4090. **Es la versión a usar para calidad final**.
- **Animate-14B**: variante específica para character animation + lip-sync por pose driving.

**Arquitectura MoE**: dos expertos — high-noise (layout/motion, early timesteps) y low-noise (texturas/cara, late timesteps). **Esto es clave**: tu LoRA FLUX/SDXL **NO se usa directamente**. Necesitás entrenar **dos LoRAs Wan 2.2** (high-noise + low-noise) para mantener identidad. Reusar LoRA de imagen NO funciona.

**Repo a usar** (Wrapper Kijai estaba broken):
- **Native ComfyUI** soporta Wan 2.2 oficialmente desde julio 2025 (`Workflow → Browse Templates → Video → Wan2.2 14B I2V`). Más estable.
- Kijai `ComfyUI-WanVideoWrapper`: activo pero más bleeding-edge bugs.
- Low-VRAM: GGUF quantizations (`city96` repo) + **LightX2V LoRA** acelerador (3-4x mantiene calidad).

**Identity drift — cómo evitarlo**:
1. **Entrenar LoRA Wan 2.2 específico**. Stack: AI-Toolkit o Diffusion-Pipe. Dataset: 10-30 clips de 2-3s + 20-40 imágenes. ~3000-5000 steps, LR 0.0002, sigmoid timestep schedule, rank 16 (32 solo si muchos ángulos).
2. **Aplicar LoRA en ambos modelos** (high + low). Low-noise cuida la cara.
3. **Clip corto**: 5s @ 24fps sweet spot. 10s+ ya drift.
4. **Combo**: imagen inicial generada con LoRA FLUX → I2V Wan 2.2 con LoRA Wan del mismo personaje.

**Calidad vs Wan 2.1**: 2.2 entrenó con +83% más video. MoE da convergencia superior. En Wan-Bench 2.0 supera varios comerciales. Realismo humano notablemente mejor que 2.1.

## 2. HunyuanVideo 1.5 / I2V

- 8.3B params, lightweight. **14 GB VRAM** mín (con offload), cómodo en 24 GB.
- ~75s/clip 5s @ 480p en 4090 (step-distilled). 720p full: 3-5 min.
- ComfyUI native desde dic 2025. LoRA training scripts oficiales (Tencent) también dic 2025.
- **Más rápido que Wan 2.2-14B** pero motion humano más limitado. Wan 2.2 gana en realismo y motion complejo.
- Comunidad NSFW grande en Civitai (más permisiva que Wan).

## 3. APIs Comerciales

| Modelo | Precio 10s | Identity preservation | NSFW |
|---|---|---|---|
| **Kling 2.1/2.6** | ~$0.84 ($0.084/s) | 1-2 ref images, mejora pero débil | **NO** — moderación multinivel estricta |
| **Hailuo 02 Pro 1080p** | $0.49-$1.25 | Image ref decente | NO oficial |
| **Veo 3.1 Fast 720p** | $1.00 sin audio / $2.00 con audio | Excelente, **audio nativo** | NO (Google policy) |
| **Veo 3.1 4K** | hasta $3.00/10s | Best in class | NO |

**Conclusión APIs**: SFW → **Veo 3.1 audio nativo** resuelve TODO en una llamada. NSFW → APIs no sirven, vuelta a local (Wan 2.2/Hunyuan).

## 4. LivePortrait (open source, Kuaishou)

- **No es difusión**, es retargeting facial framework. Casi real-time, liviano.
- Foto + **driving video** (cara hablando) o audio → transfiere expresión/movimiento. Animación cabeza+ojos+boca.
- ComfyUI: `kijai/ComfyUI-LivePortraitKJ` o `PowerHouseMan/ComfyUI-AdvancedLivePortrait`.
- **Use case**: animar foto fija. **Limitación: solo cabeza/hombros**, no cuerpo ni cambios plano. Reels "talking head" close-up: sí. Escenas con movimiento corporal: no.
- Aitana probablemente usa esto para "stories" cortas selfie hablando.

## 5. Hedra Character-3

- **Audio + foto → talking video**. Modelo omnimodal.
- **Precio**: Basic $10/mo (1000 credits), Creator $30/mo (3600 credits = ~11 min 720p), Pro $75/mo (11k credits). 30s @ 720p = 180 credits.
- **Live Avatars** (streaming): $0.05/min.
- Calidad: lip-sync **9/10**, mejor a nivel portrait según benchmarks. Mejor resolución que LivePortrait.
- **Estándar de facto** para "foto → talking head" sin driving video.
- Identity preservation buena pero no perfecta — pierde microdetalle vs source.
- NSFW: políticas restrictivas, no apto adulto.

## 6. Sync.so / VEED Fabric

**Sync.so** (lip-sync sobre video existente):
- `lipsync-2`: **$0.04/s** general
- `lipsync-2-pro`: ~$0.10/s premium
- `lipsync-1.9.0-beta`: $0.02-0.025/s fast
- Hobbyist $5/mo, Creator $19/mo.

**VEED Fabric 1.0**:
- $0.15/s output (avatar) o $0.40/min lip-sync sobre video existente.
- **El más rápido testeado** (68% más rápido que competidores), líder en accuracy + micro-expressions.

**Caso uso clave**: tenés video del personaje (Wan 2.2) y querés cambiar la boca para nuevo guión → Sync.so o Fabric. Calidad: Fabric > Sync.so > Hedra en naturalidad cara cuerpo completo.

## 7. Combinación Ganadora 2026 (50 Reels/mes top calidad)

**Pipeline A — Talking head close-up** (lo que más performa en Reels):
1. FLUX + LoRA → imagen 9:16 personaje, expresión neutra
2. ElevenLabs/OpenAI TTS → audio guión (~$0.30/min)
3. **Hedra Character-3** → talking head (180 credits/30s = ~$0.83 Creator plan)
4. Post: After Effects/CapCut → b-roll, text, CTA

Tiempo: 5-10 min gen + 10 min edición = ~20 min/Reel. Costo: ~$1.20/Reel.

**Pipeline B — B-roll cinemático + voiceover** (sin lip-sync visible):
1. FLUX + LoRA → keyframe
2. **Wan 2.2 I2V-A14B** local (4090) → 5s clip × 2-3 shots = 15s
3. ElevenLabs TTS → narración voice-over
4. Edición CapCut

Tiempo: 30-45 min/Reel en 4090. Costo: solo luz+tiempo.

**Pipeline C — Premium híbrido** (top quality NSFW-tolerant):
1. FLUX + LoRA → foto inicial
2. **Wan 2.2 I2V** con LoRA Wan dedicado → 5s body shot manteniendo identidad
3. **Sync.so lipsync-2-pro** → reemplaza boca con audio TTS ($0.10/s × 5s = $0.50)
4. Stitch shots en post

Tiempo: 45-60 min/Reel. Costo: ~$0.50-1.00/Reel + GPU.

**Pipeline D — SFW max calidad sin local**:
1. FLUX + LoRA → foto
2. **Veo 3.1 con audio nativo** → 10s con voz sincronizada ($2.00)
3. Post

Costo: ~$2.50/Reel. Top tier SFW, NSFW imposible.

## 8. Cómo lo hacen Aitana López y Milla Sofia

Info pública + inferencia técnica:
- **The Clueless** (Aitana) hace meetings semanales de "guión de vida". Generan **mayormente fotos** (90% feed estático). Videos/stories cortos, **talking head close-up** o b-roll pocos segundos.
- Stack inferido: Stable Diffusion / FLUX + LoRA → Photoshop → para video: LivePortrait o Hedra para selfies hablando.
- **Milla Sofia**: aún más estática. 95% fotos editoriales. Videos esporádicos muy cortos.
- **Clave de éxito**: la narrativa, no la complejidad técnica del video. "Slice of life" + storytelling. Pocos Reels, muchas fotos.

## 9. Wan 2.2 LoRA Training para video

**Sí, necesitás entrenar LoRA video específico**. NO reusa LoRA imagen.
- Dataset: 10-30 clips cortos (2-3s) + 20-40 imágenes. Más motion variety = mejor.
- 3000-5000 steps, LR 7e-5 a 2e-4, sigmoid schedule, rank 16-32.
- Entrenar **ambos**: high-noise LoRA + low-noise LoRA. Activar ambos en inference.
- Tools: **AI-Toolkit** (más maduro), **Diffusion-Pipe**, RunComfy trainer hosted.
- Costo training: ~$5-15 cloud (H100 2-4h) o 6-10h en RTX 4090.
- "Differential Output Preservation = person" ayuda a no perder identidad.

## Recomendación final (50 Reels/mes top calidad)

**Setup**:
1. RTX 4090 local o cloud (~$0.60/h)
2. ComfyUI native + Wan 2.2 I2V-A14B (fp8) + LightX2V LoRA acelerador
3. Entrenar Wan 2.2 LoRA dual (high + low) del personaje — one-time ~$10 cloud
4. Cuenta Hedra Creator ($30/mo)
5. Sync.so pay-as-you-go ($0.04-0.10/s)
6. ElevenLabs Creator ($22/mo)

**Mix mensual (50 Reels)**:
- 30 Reels Pipeline A (Hedra) → $25 credits
- 15 Reels Pipeline B/C (Wan 2.2) → $0-15 sync
- 5 Reels Pipeline D (Veo 3.1 hero) → $12

**Costo total**: ~$70-100/mes APIs + GPU + voces. **Tiempo**: ~20-25h/mes (~25 min/Reel promedio).

## Fuentes

- [Wan2.2 ComfyUI Native Workflow](https://docs.comfy.org/tutorials/video/wan/wan2_2)
- [Wan 2.2 Low-VRAM Workflow](https://github.com/Cordux/ComfyUI-Wan2.2-workflow)
- [Wan 2.2 VRAM Guide - Novita](https://blogs.novita.ai/wan-2-2-vram-find-the-best-gpu-setup-for-deployment/)
- [Wan-AI/Wan2.2-I2V-A14B HuggingFace](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B)
- [Wan-AI/Wan2.2-Animate-14B](https://huggingface.co/Wan-AI/Wan2.2-Animate-14B)
- [Wan 2.2 Character Consistency LoRA - RunComfy](https://www.runcomfy.com/trainer/ai-toolkit/wan-2-2-i2v-character-consistency-lora)
- [Identity-Preserving I2V (arxiv 2510.14255)](https://arxiv.org/html/2510.14255v1)
- [HunyuanVideo-1.5 GitHub](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5)
- [HunyuanVideo 1.5 Guide - Apatero](https://apatero.com/blog/hunyuanvideo-15-complete-guide-consumer-gpu-2025)
- [WAN 2.2 vs WAN 2.1 - fal.ai](https://blog.fal.ai/wan-2-2-vs-wan-2-1-whats-new-and-how-to-upgrade-your-video-pipeline/)
- [Cheapest AI Video API 2026 - Atlas Cloud](https://www.atlascloud.ai/blog/guides/cheapest-ai-video-generation-api-2026)
- [Kling AI NSFW Policy 2026](https://store.outrightcrm.com/blog/does-kling-ai-allow-nsfw-content/)
- [LivePortrait ComfyUI - RunComfy](https://www.runcomfy.com/comfyui-workflows/comfyui-liveportrait-workflow-animate-portraits)
- [Hedra Plans](https://www.hedra.com/plans)
- [LivePortrait vs Hedra](https://sdxlturbo.ai/blog-live-portrait-vs-hedra-ai-facial-animation-showdown-tutorial-50589)
- [Sync.so Pricing](https://sync.so/pricing)
- [Sync.so Lipsync Models](https://docs.sync.so/models/lipsync)
- [VEED Fabric 1.0 - fal.ai](https://fal.ai/models/veed/fabric-1.0)
- [Best Lip-Sync API 2026 - VEED](https://www.veed.io/learn/best-lipsync-api)
- [VEED Fabric for AI Influencers](https://www.eachlabs.ai/blog/veed-fabric-1-0-perfect-lip-sync-for-ai-influencers)
