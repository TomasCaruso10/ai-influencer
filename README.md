# ai-influencer

Proyecto personal — generación de contenido fotorealista con identidad consistente para distribución en redes sociales y plataformas de monetización.

Estado: **MVP de validación**. No es la pipeline final automatizada.

## Documentación

- `Spec.md` — qué es el proyecto y restricciones.
- `~/.claude/plans/ok-cloud-hoy-vamos-partitioned-river.md` — plan ejecutable del MVP.
- `docs/research/` — research consolidado del rubro (modelos, plataformas, infra, negocio).
- `docs/implementation/` — documentación descriptiva de cada módulo / fase implementada (se llena con el progreso).

## Safety policy

Este proyecto opera bajo restricciones no-negociables:

1. **Edad**: contenido únicamente de adultos. Salvaguardas técnicas:
   - Prompts positivos de identidad incluyen `"adult woman, 25 years old, mature features"`.
   - Negative prompt fixture (`prompts/safety_negative.txt`) contiene términos pediátricos prohibidos en TODA generación.
   - **MVP**: curación 100% manual via `scripts/curate.py` — el desarrollador aprueba cada imagen.
   - **Fase 2 (automatización)**: classifier de edad off-the-shelf (HuggingFace `dima806/age_image_classification_vit` o similar) como pre-filtro antes de la curación HITL.
   - Datasets de entrenamiento contienen solo imágenes de adultos verificados.
   - **CSAM y AIG-CSAM**: línea roja absoluta. Felony en US/EU/AR.
2. **Likeness**: caras 100% sintéticas. Cero referencia a personas reales o celebridades en prompts o datasets.
3. **Disclosure AI**: cumplir Meta/TikTok policies y EU AI Act art. 50 (mandatorio desde agosto 2026).

## Estructura

```
ai-influencer/
├── Spec.md
├── README.md
├── pyproject.toml
├── docs/
│   ├── research/
│   └── implementation/
├── prompts/
│   ├── identity_canon.txt
│   ├── safety_negative.txt
│   ├── sfw_lifestyle/
│   └── nsfw/
├── workflows/         # ComfyUI JSON
├── scripts/           # setup, generate, train, curate
└── outputs/           # gitignored
```

## Stack (MVP)

- **Cloud**: RunPod pod RTX 4090
- **Engine**: ComfyUI
- **Imagen NSFW**: bigASP v2 (SDXL) + Chroma (FLUX) — AB
- **Imagen SFW**: FLUX.1-dev
- **Identidad**: LoRAs duales SDXL+FLUX entrenados sobre dataset canon sintético
- **Video**: Wan 2.2 I2V + Kling 2.0 API (comparativa)
- **Lenguaje**: Python (uv-managed)
