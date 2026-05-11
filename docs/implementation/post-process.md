# Post-process — implementation reference

> Humanización + resizing por canal. Source: `src/aiinfluencer/post_process/`.

## Resumen

Después de FaceDetailer + C2PA, las imágenes pasan por dos pipelines opcionales:

1. **Humanización** — agrega artefactos "humano-cámara" (grain, chromatic aberration, vignette) para reducir el look "AI-perfecto" que delata.
2. **Resizing por canal** — recorta + escala a las dimensiones target de cada plataforma (IG square, IG portrait, Reels/TikTok, Twitter).

## Archivos

| Archivo | Qué expone |
|---|---|
| `humanization.py` | `humanize(input, output, config)` + `HumanizationConfig` + helpers |
| `resizing.py` | `Channel` enum + `CHANNEL_DIMENSIONS` + `resize_for_channel(input, output, channel)` |

## Humanización

```python
from aiinfluencer.post_process import humanize, HumanizationConfig

config = HumanizationConfig(
    iso_grain=200,           # nivel de noise gaussiano (más alto = más grano)
    aberration_pixels=2,     # px de desplazamiento RGB channels
    vignette_strength=0.35,  # 0..1 darken corners
)
humanize(input_path, output_path, config)
```

### Etapas (orden importa)

1. **Chromatic aberration**: split en R/G/B, desplazar R y B en sentidos opuestos, recompose. Simula cromática de lentes baratas. `aberration_pixels=2` es sutil; >5 se vuelve obvio.

2. **Vignette**: máscara radial usando `numpy.ogrid` (más rápido que `np.fromfunction`):
   ```python
   y, x = np.ogrid[:h, :w]
   dist = np.sqrt((x - cx)**2 + (y - cy)**2)
   mask = 1.0 - (dist / max_dist) * strength
   mask = np.clip(mask, 0.0, 1.0)
   ```
   Multiplica cada pixel por mask (corners se oscurecen, centro no se toca). **Bug histórico**: la primera implementación tenía mask invertida (`distance / max_dist * strength` sumado), centro quedaba más oscuro que corners. Test `test_vignette_darkens_corners` lo cubre.

3. **Grain**: ruido gaussiano `np.random.normal(0, sigma, shape)` donde `sigma = iso_grain / 100`. Se suma a la imagen y se clamp a [0, 255]. Más realista que uniform noise (gaussiano se distribuye como sensor real).

## Resizing por canal

```python
from aiinfluencer.post_process import Channel, resize_for_channel

resize_for_channel(input_path, output_path, Channel.IG_FEED_PORTRAIT)
```

### Channel enum

| Enum | Dimensiones | Uso |
|---|---|---|
| `IG_FEED_SQUARE` | 1080 × 1080 | feed cuadrado clásico |
| `IG_FEED_PORTRAIT` | 1080 × 1350 | feed portrait (ratio 4:5) |
| `REELS_TIKTOK` | 1080 × 1920 | reels / tiktok / shorts (9:16) |
| `TWITTER` | 1200 × 675 | timeline X |

### Algoritmo

`center_crop_resize(img, target_w, target_h)`:
1. Compute aspect ratios source vs target
2. Si source más ancha → scale por height, crop width
3. Si source más alta → scale por width, crop height
4. Center crop al rectángulo target
5. Output exacto `target_w × target_h`

No upscale arriba de los píxeles reales — si la source es 1024×1024 y el target es 1080×1350, se hace upscale Lanczos (PIL `Image.LANCZOS`). Para piezas que requieren más resolución, hacer 4x-UltraSharp antes en ComfyUI.

## Cuándo aplicar humanización

- **SIEMPRE** en outputs para Instagram/TikTok (detectores AI están aprendiendo a marcar lo "demasiado limpio")
- **OPCIONAL** en Fanvue/OnlyFans (los usuarios prefieren foto limpia, no "filtrada")
- **NUNCA** en source images de LoRA training (queremos enseñar features faciales, no artefactos de cámara)

## Tests

- `tests/post_process/test_humanization.py` (8 tests) — grain agrega varianza, aberration cambia bordes, vignette oscurece corners, config defaults sanos
- `tests/post_process/test_resizing.py` (5 tests) — todas las dimensiones del Channel enum, center crop preserva contenido central

## Lo que NO está implementado todavía

- **Auto-disclosure caption** (`#AI`, `#AIGenerated`): planeado pero requiere config por canal + idioma del prompt
- **Watermark removal de C2PA**: ❌ NUNCA. Strip de C2PA es violación de EU AI Act Art. 50 (multa hasta €15M)
- **Color grading per channel** (ej. instagram look vs reels look): TODO Fase 2.6
