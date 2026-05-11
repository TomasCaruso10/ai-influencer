# Spec — AI Influencer

## Qué es

Negocio personal de "AI influencer": una persona sintética coherente que opera como creadora de contenido en redes sociales (Instagram + TikTok con contenido SFW) y monetiza vía plataformas de contenido para adultos (OnlyFans, Fanvue u otras según research).

## Para quién

Producto-negocio del usuario (Tomás). No tiene clientes externos. El objetivo es generar revenue propio para liberarse de trabajo de consultoría/cliente.

## Hipótesis de negocio (a validar)

1. Es técnicamente viable generar contenido fotorealista NSFW de calidad comercial con identidad consistente entre piezas.
2. Es operativamente viable construir una pipeline automatizada que produzca el volumen requerido (~50-100 piezas/semana entre IG y TikTok).
3. El funnel SFW → plataforma paga convierte a un ratio que justifica el costo de producción y el time-to-market (~6 meses estimados).

Esta spec **no decide** las hipótesis 2 y 3. Las atacamos solo después de validar la 1.

## Restricciones no-negociables

- **Mayoría de edad absoluta**: contenido únicamente de adultos. Dataset de entrenamiento, prompts y outputs verificados con classifier post-generación. CSAM/AIG-CSAM = línea roja.
- **Likeness**: caras 100% sintéticas. Cero referencia a personas reales, celebridades o identidades reconocibles.
- **Disclosure AI**: cumplir requisitos de plataforma (#AI en captions, watermark, bio statement según corresponda) y EU AI Act art. 50 (mandatorio desde agosto 2026).

## Alcance del MVP (esta fase)

Validación de la hipótesis 1: generar manualmente, sin pipeline automatizada, un set representativo de assets (imágenes NSFW + SFW + 2-3 clips video) con la misma identidad sintética y calidad ≥ baseline de AI influencers exitosas (Aitana López, Milla Sofia).

Ver detalle en `~/.claude/plans/ok-cloud-hoy-vamos-partitioned-river.md`.

## Fuera de alcance del MVP

- Automatización con `pydantic-graph` (Fase 2).
- Generación de voz, lip-sync, talking head video (Fase 2).
- Apertura de cuentas en plataformas de monetización (Fase 3).
- Posting / scheduling automatizado (Fase 3).
- Chatters / customer interaction (Fase 4).

## Decisiones técnicas tomadas

Ver tabla en el plan. Resumen:

- **Cloud**: RunPod pod RTX 4090.
- **Engine**: ComfyUI self-host.
- **Imagen NSFW**: AB entre bigASP v2 (SDXL) y Chroma (FLUX uncensored).
- **Imagen SFW**: FLUX.1-dev.
- **Identidad**: bootstrap sintético (200 candidatos → curar 20-30 → LoRAs duales SDXL+FLUX), reforzada con IP-Adapter FaceID + ADetailer + face-swap final si necesario.
- **Video**: Wan 2.2 I2V (con LoRA) + comparativa Kling 2.0.
- **Plataforma de monetización**: por decidir tras research consolidado.

## Entregables MVP

1. Set de ~60 imágenes (40 NSFW AB + 20 SFW) curadas, upscaladas, con identidad consistente.
2. 2-3 clips de video corto vertical (3-6s, 9:16).
3. Decisión documentada SDXL vs FLUX/Chroma para NSFW (rúbrica AB).
4. Reporte `docs/implementation/mvp-results.md` con costo real, problemas encontrados, y veredicto de viabilidad.
5. LoRAs entrenados versionados en network volume.
6. Workflows ComfyUI exportados como JSON versionados en repo.
