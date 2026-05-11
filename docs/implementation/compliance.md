# Compliance — implementation reference

> Stack técnico de compliance EU AI Act + TAKE IT DOWN Act + AIG-CSAM safeguards. Source: `src/aiinfluencer/compliance/`.

## Resumen

4 piezas, todas non-negociables:

| Pieza | Qué hace | Cuándo se activa |
|---|---|---|
| `block_list.py` | block list pediátrico keyword/filename | LoRA load + pre-submit + pre-caption |
| `classifiers.py` | age + NSFW + Q16 (HuggingFace) | post-generación, en `SafetyFilterNode` |
| `c2pa.py` | C2PA Content Credentials sign | `C2PASignNode`, antes de `publishable=True` |
| `audit.py` | audit log a Mongo | después de cada decisión crítica |

## block_list.py

```python
from aiinfluencer.compliance import contains_blocked_keyword, is_lora_filename_safe

PEDIATRIC_KEYWORDS = frozenset({
    "child", "children", "kid", "kids", "teen", "teens", "teenager",
    "minor", "underage", "young girl", "young boy", "schoolgirl",
    "loli", "lolita", "shota", "preteen", "tween", "infant",
    # ... ~30 keywords
})

contains_blocked_keyword(prompt: str) -> str | None
    # Devuelve el keyword matched (truthy) o None

is_lora_filename_safe(filename: str) -> bool
    # False si el filename contiene cualquier pediatric keyword
```

**Aplicado en 3 puntos del pipeline**:
1. `WorkflowDeps.with_lora(path)` → raise si `not is_lora_filename_safe(path.name)`
2. `PromptExpandNode.run()` → reject + audit si `contains_blocked_keyword(prompt_final)`
3. `CaptionNode.run()` → reject + audit si `contains_blocked_keyword(caption)`

**False positive policy**: si el matched keyword es válido en otro contexto (ej. "kid gloves"), el reject va a HITL. El humano puede aprobar override y el record queda con `human_approved_override=True`.

## classifiers.py

```python
from aiinfluencer.compliance.classifiers import HuggingFaceSafetyClassifiers

classifiers = HuggingFaceSafetyClassifiers()  # no carga modelos hasta primer call

age = await classifiers.age_classify(image_path)
# {"bucket": "20-29", "is_adult": True, "confidence": 0.95}

nsfw = await classifiers.nsfw_classify(image_path)
# {"score": 0.87, "label": "nsfw"}

q16 = await classifiers.q16_classify(image_path)
# {"inappropriate": False, "concept": None}
```

### Models lockeados

| Tarea | Model HF | Output |
|---|---|---|
| Age | `dima806/fairface_age_image_detection` | bucket categórico (0-2, 3-9, 10-19, 20-29, ...) |
| NSFW | `Falconsai/nsfw_image_detection` | binary safe/nsfw + score |
| Q16 | TBD (CLIP-based for inappropriate concepts) | inappropriate bool |

**Lazy load**: `_ensure_age_loaded()` carga el pipeline en primer call, cachea instance. Costo arranque: ~5s. Costo per-image: ~150-300ms.

### Thresholds en `SafetyFilterNode`

```python
if age["bucket"] in {"0-2", "3-9", "10-19"}:
    return self.reject_with_review(ctx, RejectionReason.AGE_CLASSIFIER_FAILED, ...)

if not age["is_adult"]:
    return self.reject_with_review(ctx, ...)

# NSFW: NO bloqueamos por score >0.5 (queremos NSFW intencional)
# pero logueamos para audit

if q16["inappropriate"]:
    return self.reject_with_review(ctx, RejectionReason.Q16_FAILED, ...)
```

## c2pa.py

```python
from aiinfluencer.compliance.c2pa import C2PASigner

signer = C2PASigner(
    cert_pem_path=Path("certs/signing.cert.pem"),
    key_pem_path=Path("certs/signing.key.pem"),
)
signed_path = await signer.sign(
    image_path,
    manifest={
        "claim_generator": "ai-influencer/1.0",
        "title": "Generated content",
        "ai_generated": True,
        "model_used": "FLUX.1-dev + LoRA aiinfluencer1",
    },
)
```

Internamente lazy-importa `c2pa-python` y firma in-place (el output_path es típicamente el mismo path con metadata embebida en JUMBF box del PNG).

**EU AI Act Art. 50 disclosure**: el manifest C2PA cuenta como "machine-readable disclosure" (mandatorio desde 2 ago 2026 para usuarios EU, multa hasta €15M).

**NUNCA strip de C2PA/SynthID/EXIF** post-sign. Si necesitas re-process la imagen (resize, watermark, etc.), hacelo ANTES del C2PA sign, no después.

## audit.py

```python
from aiinfluencer.compliance.audit import AuditEvent, emit

await emit(
    AuditEvent(
        piece_id=state.piece_id,
        node_name="SafetyFilterNode",
        action="age_check_passed",
        payload={"bucket": "20-29", "confidence": 0.95, "model": "fairface"},
        timestamp=datetime.now(UTC),
    ),
    mongo_client=ctx.deps.mongo,
)
```

`AuditEvent` es BaseModel persisten a Mongo collection `audit_events`. **Retention mínimo 6 años** (EU AI Act technical documentation requirement) — collection con TTL DESACTIVADO.

Logfire también recibe el event como `logfire.info("audit_event node={node_name} action={action} ...", **payload)` para indexing en runtime, además del backup persistente en Mongo.

## Tests

- `tests/compliance/test_block_list.py` (13 tests) — false positives, false negatives, filename variants, edge cases (empty, all whitespace, unicode)
- `tests/compliance/test_classifiers.py` (4 tests) — protocol compliance, mocked HF pipeline returns, lazy load behavior
- `tests/compliance/test_audit.py` — AuditEvent serialization + emit roundtrip a DummyMongo

## Lo que NO está implementado

- **Q16 model real**: actualmente placeholder que devuelve `inappropriate=False`. Spec en `docs/specs/face-consistency.md` § Compliance. **TODO Fase 2.6**.
- **C2PA cert provisioning**: el cert/key real hay que generarlos (probablemente self-signed para el MVP, luego CA si va a producción). **TODO Fase 3**.
- **SynthID watermarking**: complementario a C2PA, no es esencial todavía. Google SynthID-Image SDK no es público.

## EU AI Act timeline

| Fecha | Requerimiento | Compliance estado |
|---|---|---|
| 2 ago 2025 | Transparency obligations apply | ✅ pipeline ya inyecta C2PA |
| 2 ago 2026 | GPAI obligations + sanctions | ⚠️ falta cert real C2PA + caption AI disclosure |
| 2 ago 2027 | Full enforcement | TBD |

## TAKE IT DOWN Act (US, 19 may 2026)

Aplica solo si el personaje sintético se parece a persona real identificable. **Nuestro canon es 100% sintético → no aplica.** Pero si en el futuro un LoRA se entrena con fotos de persona real sin consentimiento, cae bajo la ley.

**Regla repo**: dataset training NUNCA incluye personas reales identificables. Esto es lockeado en `Spec.md` § Compliance.
