# Research — Face Consistency Stack (2026)

> Stack para mantener identidad perfecta cross-modelo (FLUX, SDXL, Chroma, bigASP) y cross-pose. Asume LoRA del personaje ya entrenado. Foco: implementación práctica.

## 1. IP-Adapter FaceID Plus v2 (SDXL)

**Cómo funciona**: combina embeddings de ArcFace (insightface) con CLIP image embeddings vía cross-attention. Requiere SIEMPRE un LoRA acompañante específico (`ip-adapter-faceid-plusv2_sdxl_lora.safetensors`).

**Settings pros (medibles)**:
- `weight`: 0.8 base, `v2 weight`: 2.0, `weight_faceidv2` cómodo 0.5–1.0
- `lora_weight` (LoRA FaceID propio): 0.6–0.7
- Layer overrides SDXL: `input_7: 1.12`, `output_3: 0.96`, `output_4: 0.96`
- Combinación de embeddings: `concat` para múltiples references, `average` para suavizar
- ArcFace metric: EUC < 0.27, COS < 0.015 (excelente)

**Combinación con LoRA del personaje**: coexisten compitiendo por capas. Character-LoRA en 0.7–0.85, FaceID LoRA-weight bajo a 0.5–0.6.

**Cuello de botella**:
- En **SDXL: maduro y estable**.
- En **FLUX: NO existe IPAdapter FaceID Plus v2 oficial**. Se usa **PuLID-Flux** como reemplazo.
- Identity recognition: 76–82% (lo más bajo del trío FaceID/InstantID/PuLID).
- ~25s @ SDXL 1024 / 4090, solo 7.8 GB VRAM (el más rápido).

**Cuándo usar**: alto volumen donde fidelidad no necesita ser pixel-perfect. Primer pase antes de FaceDetailer.

## 2. InstantID (SDXL)

**Componentes**: IP-Adapter especializado en ArcFace face embeddings + ControlNet de face landmarks 5-point.

**Identity accuracy**: 82–86% cosine similarity. Gana a FaceID, pierde a PuLID por 3–5 puntos.

**Casos donde GANA**:
- Caras anguladas / 3/4 / perfiles (landmarks anclan estructura)
- Lighting complejo (warm/golden)
- Un solo nodo "drop-in"

**Casos donde PIERDE**:
- Artefacto "squinty eyes"
- Prompt adherence inferior a HyperLoRA/PuLID
- Full-body: cara queda dominante por landmarks

**Workflow**: `InstantIDFaceAnalysis` → `InstantIDModelLoader` → `ApplyInstantID` + ControlNet (`controlnet_instantid_sdxl.safetensors`). Weights: IP-Adapter 0.75–0.85, ControlNet 0.4–0.7. >0.8 atrapa pose.

**VRAM**: 8.5 GB, 28s/img.

## 3. PuLID-Flux / PuLID Flux II

**Workflow ComfyUI exacto**:
1. `Load Diffusion Model` (Flux dev FP8) → `Apply PuLID Flux` (weight 0.8–0.95)
2. `PulidFluxModelLoader` (`pulid_flux_v0.9.1.safetensors`) + `PulidFluxInsightFaceLoader` (antelopev2)
3. `PulidFluxEvaClipLoader` (EVA02-CLIP-L-14-336)
4. Reference image → `Apply PuLID Flux` con `start_at=0.0`, `end_at=1.0`
5. `FluxGuidance` 2.5–3.5 (bajar si LoRA pierde fuerza)
6. `KSampler` 20–25 steps, euler/simple

**Weight ranges**:
- PuLID v0.9.0: 0.8–0.95 (>1.0 degrada)
- PuLID v0.9.1: 0.9–1.0
- `start_at=0.0, end_at=1.0` = máxima identidad
- `start_at=0.3, end_at=0.7` = más libertad artística

**Combinación con LoRA FLUX**: delicada. Si LoRA es full finetune → PuLID degrada. **Usar LoRA-style o merges, no finetunes**. Para Chroma (basado en flux-schnell): **NO oficialmente soportado**.

**Identity accuracy**: 88–93% (mejor del trío).

**Limitaciones**:
- Consistencia entre seeds: **menor que LoRA puro**. Mismo prompt+ref distinto seed → cara similar pero NO idéntica.
- VRAM: 10.2 GB, 35s/img (más lento y pesado).
- Sobre-adherencia a pose/expresión del reference.

## 4. ReActor Face-Swap Post-hoc

**Integración al final del workflow**:
```
KSampler → VAE Decode → ReActorFaceSwap(source_image, swap_model=inswapper_128,
    face_restore=CodeFormer, codeformer_weight=0.5, face_restore_visibility=1.0)
```

**Ventajas**: cara 100% pegada. ArcFace cosine >0.85 vs source.

**Desventajas ("pegado look")**:
- Iluminación no matchea (cara frontal sobre body lateral)
- Texture mismatch
- Inswapper_128: solo 128×128 internamente — pérdida al hacer face >256 px
- Video: temporal jitter sin face tracking

**CodeFormer/GFPGAN refinement**:
- **CodeFormer**: weight 0.5 = balance. <0.5 favorece restauración, >0.7 favorece fidelity.
- **GFPGAN v1.4**: BROKEN en 2025-2026 (EOF errors, "humo blanco"). **Usar v1.3 o evitar**.
- **2026 recommendation**: CodeFormer 0.5 + ReActor. GFPGAN deprecating.

**Alternativas emergentes**:
- **ReSwapper** (built-in ReActor): mejora gradual, debajo de inswapper en similitud
- **HyperSwap 256** (Facefusion): 2x resolución, calidad superior, integración manual
- **GPEN-1024/2048** restore models: ya integrados en ReActor

## 5. InsightFace ArcFace Verification Automática

**Modelo recomendado**: `buffalo_l` (SCRFD-10GF detection + ResNet50@WebFace600K, 326MB). Outperforma a `antelopev2` por WebFace600K dataset mejor curado.

**Threshold real** (no el mito 0.6–0.7):
- Cosine similarity sobre `normed_embedding` (L2-normalizado)
- 1:1 verification @ FMR=1e-4: **threshold 0.30–0.45**
- QC LoRA: empezar en 0.4, ajustar
- Filtros pros: 0.4–0.6 wide match, 0.1–0.3 tight match

**Código Python**:
```python
import cv2, numpy as np
from insightface.app import FaceAnalysis

app = FaceAnalysis(name="buffalo_l",
                   providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

def get_face_embedding(image_path: str) -> np.ndarray | None:
    img = cv2.imread(image_path)
    faces = app.get(img)
    if not faces:
        return None
    face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
    return face.normed_embedding

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))

canon_embs = [get_face_embedding(p) for p in canon_dataset]
canon_mean = np.mean(canon_embs, axis=0)
canon_mean /= np.linalg.norm(canon_mean)

for generated_img in outputs:
    emb = get_face_embedding(generated_img)
    sim = cosine_sim(emb, canon_mean) if emb is not None else 0.0
    if sim < 0.45:
        ...
```

**Performance**: 30–80ms/img GPU (4090), 150–300ms CPU. Negligible vs gen (20–35s).

## 6. Combinación Ganadora 2026 — El Stack Standard

```
[Trained Character LoRA] → Base generation
        ↓
[IPAdapter FaceID Plus v2 (SDXL) o PuLID-Flux II (FLUX)] @ 0.7–0.85
        ↓
[FaceDetailer + same LoRA] denoise 0.35–0.45, feather 16–32, crop_factor 3.0
        ↓
[Multi-pass refinement: 0.45 → 0.25 → 0.15]
        ↓
[ReActor + CodeFormer 0.5] (solo hero shots críticos)
        ↓
[InsightFace QC automático, threshold cos > 0.45 vs canon mean embedding]
```

**Por qué NO "InstantID + face-swap final" puro**: face-swap mata variabilidad facial. Para influencer creíble necesitás variación natural — la da LoRA + FaceDetailer multipass.

**Identity accuracy del stack**: **~97%** (vs 88–93% PuLID solo, 84–91% sin LoRA).

**Hardware baseline**: 12 GB VRAM mín, 16–24 GB ideal.

## 7. ACE++ / EcomID

**ACE++**: zero-training character consistency via Flux Fill. Cargás LoRA ACE++ + reference. Ventaja: **outfit/escena consistency** (no solo cara). Cuándo conviene:
- Replicar outfit específico entre imágenes
- No querés entrenar LoRA por outfit
- Reference photo única

Limitación: pierde fidelidad facial vs PuLID/HyperLoRA en T2I libre.

**EcomID (SDXL)**: InstantID + PuLID + ControlNet propio. Foco e-commerce. Mejor consistencia semántica (rasgos invariantes al envejecimiento). Use case: **catálogo producto con misma modelo**.

**Para Fase 2**: skip ambos. Implementar primero §6 stack.

## 8. HyperLoRA, FaceTailor, LayerDiffuse

**HyperLoRA** (ByteDance, CVPR 2025 Highlight): genera LoRA weights on-the-fly desde imagen reference. Descompone en Hyper ID-LoRA + Hyper Base-LoRA. Combinable con InstantID ControlNet.
- Production-ready para SDXL (HelloWorld XL 3.0, CyberRealistic XL, RealVisXL v4.0).
- NO para FLUX/Chroma.
- Setup medium-alto. ~2 GB extra.
- Mejor prompt adherence que PuLID/InstantID.
- **Para Fase 2**: vale experimentar si base es SDXL.

**FaceTailor**: nombre confuso. Lo real: **Impact Pack FaceDetailer**, **DZ-FaceDetailer**, **ComfyUI_FaceShaper**. Todos production-ready.

**LayerDiffuse**: transparent image gen (alpha channel). NO es face consistency. **Skip**.

## Recomendación para Fase 2

**Implementar en orden**:

1. **Pipeline base SDXL+LoRA+FaceDetailer multi-pass**: tenés LoRA, falta wiring FaceDetailer denoise 0.45→0.25→0.15.
2. **InsightFace QC automático**: script Python con `buffalo_l`, threshold 0.45, reject <threshold. ~50 LOC.
3. **PuLID-Flux II en FLUX path**: outputs alta-calidad cuando LoRA FLUX no alcance.
4. **ReActor + CodeFormer 0.5 opcional**: solo hero shots.
5. **HyperLoRA experimental**: evaluar contra stack actual.

**Skip**: EcomID (overkill), ACE++ (no prioritario), LayerDiffuse (N/A), GFPGAN v1.4 (broken).

**Métrica de éxito**: cosine ArcFace ≥ 0.45 (ideal 0.55+) vs canon mean embedding en todas las gens automáticas. Reject automático si no pasa.

## Fuentes

- [ComfyUI IPAdapter Plus Deep Dive - RunComfy](https://www.runcomfy.com/tutorials/comfyui-ipadapter-plus-deep-dive-tutorial)
- [IPAdapter FaceID Weight v2](https://www.comfyonline.app/blog/ipadapter-faceid-weight-v2)
- [PuLID Flux II ComfyUI - RunComfy](https://www.runcomfy.com/comfyui-workflows/pulid-flux-ii-in-comfyui-consistent-character-ai-generation)
- [ComfyUI-PuLID-Flux-Enhanced](https://github.com/sipie800/ComfyUI-PuLID-Flux-Enhanced)
- [PuLID vs InstantID vs FaceID - MyAIForce](https://myaiforce.com/pulid-vs-instantid-vs-faceid/)
- [InstantID vs PuLID vs FaceID 2025 - Apatero](https://apatero.com/blog/instantid-vs-pulid-vs-faceid-ultimate-face-swap-comparison-2025)
- [Flux PuLID vs InstantID vs EcomID - MyAIForce](https://myaiforce.com/flux-pulid-vs-ecomid-vs-instantid/)
- [ComfyUI-ReActor](https://github.com/Gourieff/ComfyUI-ReActor)
- [InsightFace Recognition Models](https://www.insightface.ai/guides/choose-face-recognition-model-and-evaluate)
- [FaceDetailer + LoRA Method 2025 - Apatero](https://apatero.com/blog/professional-face-swap-facedetailer-lora-method-comfyui-2025)
- [ACE++ Character Consistency - RunComfy](https://www.runcomfy.com/comfyui-workflows/ace-plus-plus-character-consistency)
- [SDXL_EcomID_ComfyUI](https://github.com/alimama-creative/SDXL_EcomID_ComfyUI)
- [ComfyUI-HyperLoRA - ByteDance](https://github.com/bytedance/ComfyUI-HyperLoRA)
- [HyperLoRA paper arxiv](https://arxiv.org/html/2503.16944v1)
- [4 Face Swap Techniques Compared - MyAIForce](https://myaiforce.com/hyperlora-vs-instantid-vs-pulid-vs-ace-plus/)
- [Consistent AI Influencers ComfyUI - Next Diffusion](https://www.nextdiffusion.ai/tutorials/create-consistent-ai-influencers-comfyui-earn-online-fanvue)
- [InsightFace para LoRA dataset filtering - FloYo](https://www.floyo.ai/workflows/insightface-for-filtering-character--qjjh5l9i6gjb)
