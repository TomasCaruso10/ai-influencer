# Compliance — convenciones

> Stack técnico de compliance para EU AI Act + TAKE IT DOWN Act + AIG-CSAM safeguards. Source: `docs/research/orchestration-compliance-2026.md` + `docs/specs/face-consistency.md`.

## Reglas non-negociables del pipeline

1. **Nunca marcar `record.publishable = True` sin pasar** TODO:
   - Age classifier: `is_adult == True`
   - NSFW classifier: score conocido (puede ser >0.5 si es contenido NSFW intencional, eso es OK)
   - Q16 classifier: `inappropriate == False`
   - Face QC: cos similarity >= threshold (default 0.45)
   - C2PA signed
   - Audit log entry escrito

2. **Block list pediátrico** se aplica en 3 puntos:
   - Al cargar LoRA: `is_lora_filename_safe(filename)` → si False, raise
   - Antes de submit prompt: `contains_blocked_keyword(positive)` → si truthy, reject + audit
   - Antes de publicar caption: igual

3. **C2PA manifest** auto-inject — NUNCA strip de C2PA/SynthID/EXIF (riesgo legal DMCA + EU AI Act Art. 50).

4. **Audit log retention mínimo 6 años** (EU AI Act technical documentation requirement). MongoDB collection `audit_events` con TTL desactivado.

## API

```python
# Block list
from aiinfluencer.compliance import contains_blocked_keyword, is_lora_filename_safe

if not is_lora_filename_safe(lora_path.name):
    raise RuntimeError(f"LoRA filename matches pediatric block list: {lora_path}")

if contains_blocked_keyword(prompt):
    return self.reject_with_review(ctx, RejectionReason.AGE_CLASSIFIER_FAILED, ...)

# Classifiers
from aiinfluencer.compliance.classifiers import HuggingFaceSafetyClassifiers
classifiers = HuggingFaceSafetyClassifiers()  # lazy, no carga modelos hasta primer call
result = await classifiers.age_classify(image_path)  # {"bucket": "20-29", "is_adult": True, "confidence": 0.95}

# C2PA
from aiinfluencer.compliance.c2pa import C2PASigner
signer = C2PASigner(cert_pem_path=..., key_pem_path=...)
signed_path = await signer.sign(image_path)

# Audit
from aiinfluencer.compliance.audit import AuditEvent, emit
await emit(
    AuditEvent(
        piece_id=state.piece_id,
        node_name="SafetyFilterNode",
        action="age_check_passed",
        payload={"bucket": "20-29", "confidence": 0.95},
    ),
    mongo_client=ctx.deps.mongo,
)
```

## Models lockeados

- **Age**: `dima806/fairface_age_image_detection` (ViT, FairFace) — top descargas mensuales HF
- **NSFW**: `Falconsai/nsfw_image_detection` (binary safe/nsfw)
- **Q16**: TBD (CLIP-based para inappropriate concepts: violence, blood, self-harm) — placeholder hasta implementación

## Threshold defaults

- Age "20-29" bucket = adult OK
- Age "0-2", "3-9", "10-19" buckets = REJECT inmediato
- NSFW score: usado como info, no decision automatic (queremos NSFW intencional)
- Q16 inappropriate: True = reject

## EU AI Act Art. 50 disclosure

El pipeline DEBE producir output con:
- C2PA manifest firmado (machine-readable disclosure)
- (Future) caption auto-injection con `#AI` o equivalente para plataformas

Esto es **mandatorio desde 2 ago 2026** para usuarios EU. Multas hasta €15M o 3% facturación.

## TAKE IT DOWN Act (US, vigente 19 may 2026)

Aplica solo si el personaje sintético **se parece a persona real identificable**. Nuestro canon es 100% sintético → no aplica.

PERO: si en el futuro un LoRA se entrena con fotos de persona real sin consentimiento, cae bajo la ley. **Regla**: dataset training nunca incluye personas reales identificables.

## Argentina

Fuera de scope técnico del repo. Ver `docs/research/orchestration-compliance-2026.md` § 7 para referencia. Es responsabilidad del owner.
