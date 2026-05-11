# Research — Modelos de generación NSFW (estado del arte 2026)

> Compilado durante planning. Usado para tomar decisiones de stack en el plan del MVP.

## 1. Modelos base para NSFW

### Pony Diffusion (V6 XL, V7) — descartado como primario

- **V6 XL**: fine-tune de SDXL, dataset ~2.6M imágenes, sistema de tags propio con "score tags" (`score_9`, `score_8_up`, `score_7_up`) y `rating_explicit/questionable/safe`. Excelente para anatomía y NSFW de **estilo ilustración / anime / cartoon**. Para fotorealismo es flojo en piel y luz; convendría ir a derivados como CyberRealistic Pony, Real Pony, Pony Realism.
- **V7**: cambio de arquitectura — ya **no es SDXL**, está construido sobre **AuraFlow** (rama Flux-like) con dataset expandido a ~10M imágenes y nuevo sistema de "style grouping" (`anime_1`, `smooth_shading_48`, etc.). Mejor comprensión de prompts en lenguaje natural. Sigue dominando NSFW estilizado.
- **Veredicto**: si el target es **fotorealismo de OnlyFans-style**, Pony NO es la mejor opción base. Sí lo sería como secondary pipeline para variantes "estilizadas" o cartoon.

### SDXL + LoRAs NSFW (línea fotorealista) — primario para MVP

- **bigASP v2**: fine-tune de SDXL base sobre **6M+ fotos curadas (40M training samples)**. **El SDXL fotorealista NSFW de referencia 2026** junto con Lustify.
- **LUSTIFY v2.0**: merge de bigASP + Pyro's NSFW + dataset curado de ~2700 fotos extra. Muy buen rendering de piel y luz "fotográfica". Hay variantes Lightning para inferencia rápida.
- **Big Lust**: merge bigASP + Lustify, considerado por la comunidad uno de los mejores SDXL no-Pony para NSFW.
- **RealVisXL V5 / Juggernaut XL X**: SFW fotorealistas excelentes, NSFW limitado pero compatibles con LoRAs NSFW de Civitai.
- SDXL sigue siendo el caballo de batalla en 2026 por **ecosistema** (LoRAs, ControlNets, IP-Adapter, ADetailer maduros) y costo de inferencia bajo.

### FLUX y forks NSFW — secundario para MVP (AB)

- **FLUX.1-dev** (12B params, rectified flow transformer) y **FLUX.1-schnell** (4-step distilled): base extremadamente capaz en luz, manos y composición, pero el modelo "vanilla" es alineado (no genera nudity explícita).
- **Chroma**: el fork uncensored más serio sobre Flux. Compatible con LoRAs Flux existentes. VRAM mínima 12GB (RTX 3060), recomendado 16-24GB. La opción Flux más versátil para NSFW fotorealista.
- **Flux-uncensored (enhanceaiteam)**, **Fluxed Up** (Civitai 847101): checkpoints NSFW directos sobre Flux.
- **FLUX 2 Pro** (2026): permite LoRAs propios; aparecen guías de "character consistency LoRA training" específicas para FLUX 2.
- **Trade-off**: Flux/Chroma da mejor calidad de imagen única, pero más caro en VRAM e inferencia que SDXL, y el ecosistema de ControlNet/IP-Adapter es menos completo.

### Tabla de decisión por uso

| Uso | Modelo primario | Razón |
|---|---|---|
| Fotorealismo NSFW principal | **bigASP v2** o **LUSTIFY v2** (SDXL) | Mejor ratio calidad/costo, ecosistema maduro |
| Calidad máxima por imagen | **Chroma** (Flux uncensored) | Mejor luz/piel/manos |
| Variantes estilizadas | **Pony V7** o **CyberRealistic Pony V7** | Anatomía + LoRAs |
| SFW de Instagram/TikTok | **RealVisXL V5** o **FLUX.1-dev** | Limpio, sin sesgo NSFW |

SD 1.5 está **prácticamente fuera** para producción fotorealista de calidad alta en 2026.

## 2. Consistencia de personaje (lo crítico)

### LoRA training (la solución real)

- **Dataset**: 15-30 imágenes de referencia de la "persona". Si la persona no existe → bootstrap sintético: generar 100-300 imágenes con el mismo prompt + seed-rotation, curar manualmente las 20-30 más coherentes (mismos rasgos faciales), entrenar LoRA.
- **Resolución**: 1024x1024 para SDXL; bucketing variable.
- **Parámetros sweet spot SDXL**: dim 32, alpha 16, lr 1e-4, scheduler cosine, **1500-2500 steps**, optimizer AdamW8bit o Prodigy.
- **FLUX/Chroma**: dim 16-32, lr 1e-4, **1800-2000 steps**, timestep_type linear, fuerza inferencia 1.3-1.5.
- **Tools**:
  - **kohya_ss**: gold standard, configurable. Mejor para SDXL.
  - **AI-Toolkit (Ostris)**: presets afinados para character LoRAs. Mejor "out-of-the-box" para Flux/Chroma.
  - **OneTrainer**: rápido, mejor likeness facial.
- **Costo**: 1-3h en RTX 4090 / A100. RunPod: ~USD 1-3 por LoRA. Archivo final 50-150 MB.

### Adapters de cara (complemento, NO reemplazo)

| Tool | Likeness | Flexibilidad expresión | VRAM | Madurez NSFW |
|---|---|---|---|---|
| **InstantID** | ~82-86% similitud | Media | Alta | Buena (SDXL) |
| **IP-Adapter FaceID Plus v2** | Muy buena | Alta | Baja | Excelente, simple |
| **PuLID** | Variable, peor consistencia entre imágenes | Baja | Media | Existe versión Flux |
| **ReActor** | Face-swap post-hoc | N/A (swap) | Baja | OK pero "pegado" |

**Estrategia ganadora 2026**: LoRA propio del personaje + IP-Adapter FaceID Plus v2 como refuerzo + ADetailer/FaceDetailer con el mismo LoRA en denoise 0.4-0.5. ReActor sólo para emergencias o videos.

## 3. Pipeline de producción

- **UI**: **ComfyUI** es el estándar de producción 2026 (control total, soporta Flux/Chroma/Wan/Hunyuan, batch automatización vía API). Forge alternativa form-based. **A1111 está deprecado**.
- **Workflow típico NSFW fotorealista**:
  1. Txt2img base (bigASP/Lustify) 1024x1024, sampler DPM++ 2M Karras o DPM++ SDE, 25-35 steps, CFG 4-7, **LoRA del personaje en 0.7-0.9**.
  2. **FaceDetailer / ADetailer** con el mismo LoRA, denoise 0.35-0.5.
  3. **Hand Detailer** opcional.
  4. **Upscale 2x** (4x-UltraSharp + tile upscale, denoise 0.2-0.3) → output 2048x2048.
- **Generación de "sets"**: fijar seed + prompt template + variar ángulo/pose/ropa con wildcards o ControlNet OpenPose. Para mantener escenario, regional prompter o IPAdapter de la primera imagen.

## 4. Video NSFW (estado real)

- **Wan 2.2** (Alibaba, MoE 14B): líder open-source 2026. I2V calidad alta. ~9 min para 5s @ 720p en RTX 4090 sin optimización; ~4 min @ 480p. Requiere 16GB VRAM mínimo (5B), 24GB recomendado, 80GB para A14B full. **LoRAs de personaje compatibles** → permite reusar el LoRA del influencer para video.
- **HunyuanVideo / HunyuanVideo-1.5 / I2V**: comparable a Wan. Comunidad activa de workflows NSFW (ej. "HunYuan_I2V_NFSW_Workflow" en Civitai).
- **LTX-Video / LTX-2**: más rápido, calidad menor.
- **Costo cloud**: 10s @ 1080p ~USD 1.50+ vía API; en RunPod H100 (~USD 2-3/h) un clip de 5s sale ~USD 0.30-0.60 con Wan 2.2 optimizado.
- **Veredicto**: video NSFW fotorealista de **3-6 segundos es viable hoy** con Wan 2.2 + LoRA del personaje. Más de 8s = artefactos. Estrategia: muchos clips cortos editados.

## 5. Compliance y restricciones

- **OnlyFans 2026** (overhaul): AI permitida solo si el creador está verificado y el contenido se parece al creador real verificado. Deepfakes y personas sintéticas puras → ban inmediato. Re-verificación cada 12 meses. Etiquetado obligatorio `#AI`.
- **Patreon 2026**: prohíbe AI fotorealista en tiers adultos.
- **Mayoría de edad**: regla de oro técnica — prompts y LoRAs sólo de adultos, prohibir hard términos pediátricos en prompts/datasets. Civitai exige age-gating en uploads NSFW.
- **Cloud GPU**:
  - **RunPod permite NSFW** (community templates explícitos, posts oficiales).
  - **Vast.ai** permite NSFW en hosts comunitarios (depende del host).
  - **Replicate** y **Modal**: mucho más restrictivos. Evitar para NSFW.
  - **Civitai**: permite NSFW con flags. **HuggingFace**: restringe NSFW explícito.

## Decisión adoptada en el plan MVP

1. Cloud: RunPod pod RTX 4090.
2. UI: ComfyUI + workflow FaceDetailer + Upscale.
3. Modelo NSFW: AB entre **bigASP v2 (SDXL)** y **Chroma (FLUX)**.
4. Consistencia: LoRAs duales SDXL+FLUX entrenados sobre dataset canon sintético + IP-Adapter FaceID Plus v2 + ADetailer.
5. Video: Wan 2.2 I2V con LoRA, clips 3-6s.

## Fuentes

- [Pony Diffusion V6 XL (Civitai)](https://civitai.com/models/257749/pony-diffusion-v6-xl)
- [Towards Pony Diffusion V7](https://civitai.com/articles/5069/towards-pony-diffusion-v7)
- [Best Stable Diffusion Models 2026 (Aiarty)](https://www.aiarty.com/stable-diffusion-guide/best-stable-diffusion-models.htm)
- [bigASP v2 (Civitai)](https://civitai.com/models/502468/bigasp)
- [LUSTIFY v2.0 (HuggingFace)](https://huggingface.co/TheImposterImposters/LUSTIFY-v2.0)
- [Big Lust (Civitai)](https://civitai.com/models/575395/big-lust)
- [How to Run Flux Uncensored / Chroma 2026](https://offlinecreator.com/blog/how-to-run-flux-uncensored-locally-2026)
- [Fluxed Up Review](https://offlinecreator.com/blog/fluxed-up-flux-nsfw-checkpoint-review-2026)
- [FLUX 2 Pro LoRA Training Character Consistency 2026](https://apatero.com/blog/flux-2-pro-lora-training-character-consistency-2026)
- [AI Toolkit vs OneTrainer 2026](https://neurocanvas.net/blog/ai-toolkit-vs-onetrainer-zimage-guide/)
- [PuLID vs InstantID vs FaceID](https://myaiforce.com/pulid-vs-instantid-vs-faceid/)
- [ComfyUI vs A1111 vs Forge NSFW 2026](https://offlinecreator.com/blog/comfyui-vs-automatic1111-vs-forge)
- [Wan2.2 GitHub](https://github.com/Wan-Video/Wan2.2)
- [Wan 2.2 in <60s on H100 (Baseten)](https://www.baseten.co/blog/wan-2-2-video-generation-in-less-than-60-seconds/)
- [HunyuanVideo-1.5 (HuggingFace)](https://huggingface.co/tencent/HunyuanVideo-1.5)
- [RunPod ComfyUI NSFW template (Civitai)](https://civitai.com/articles/11447/runpod-template-one-click-comfyui-with-sdxl-for-effortless-sfwnsfw-image-generation)
- [Wan2.2 i2v fp8 NSFW on RunPod (GitHub)](https://github.com/bitsofintelligence101-lab/runpod-wan22-i2v-fp8-nsfw)
- [OnlyFans 2026 Policy Overhaul](https://list25.com/onlyfans-2026-policy-updates-ai-deepfake-ban-verification/)
