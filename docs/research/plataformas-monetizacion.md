# Research — Plataformas de monetización (consolidado)

> Documento pedido explícitamente por el usuario. Compara Fanvue, OnlyFans, Passes, Loyalfans y Patreon (entre otras) para tomar la decisión final de plataforma destino del funnel.

## TL;DR

- **Fanvue** es la única plataforma con categoría oficial "AI Creator" y políticas explícitamente diseñadas para personas sintéticas. Es la **opción más segura para MVP**.
- **OnlyFans** sigue siendo la más grande, pero el overhaul de política 2026 exige que el AI **se parezca al humano real verificado**. Personajes 100% sintéticos = ban inmediato. Para usar OnlyFans necesitarías a) tu propia identidad como base del LoRA o b) una socia humana real cuyo KYC y likeness sostengan la cuenta.
- **Patreon** prohíbe AI fotorealista en tiers adultos. Descartado para nuestro caso.
- **Passes**: principalmente útil como **link aggregator** desde IG/TikTok (90/10 split), no como plataforma primaria de NSFW.
- **Loyalfans**: alternativa más permisiva pero con mucho menos tráfico orgánico — útil como diversificación, no como primary.
- **Recomendación de plan**: arrancar Fanvue, **luego** evaluar si vale extender a OnlyFans con anchor humano.

## Comparativa lado a lado

| Plataforma | Take rate creador | AI-friendly | KYC | Tráfico orgánico | Disclosure | Notas |
|---|---|---|---|---|---|---|
| **Fanvue** | 80% (mes 1: 85%) | **Sí, oficial — categoría AI Creator** | ID gov + selfie del owner real (no del personaje) | Medio-alto, en crecimiento desde 2024 | Watermark, caption o bio statement | Plataforma diseñada para AI desde el día uno. Reasonable Person's Test (3 mods evalúan disclosure) |
| **OnlyFans** | 80% | Permitido desde 2024, **endurecido 2026** | Liveness check del owner real **+** AI debe parecerse al humano real verificado | Alto (la #1 del rubro) | `#AI` o `#AIGenerated` visible obligatorio. Re-verificación cada 12 meses | Personaje 100% sintético = ban. Deepfakes = ban permanente |
| **Passes** | 90% (split 90/10, vs 80/20 OF) | Permitido | ID + selfie | Bajo en NSFW; alto como aggregator | Caso por caso | Lucy Guo, ex-Scale. Mejor IG-friendly aggregator 2026 |
| **Loyalfans** | 80% | Permitido | ID + selfie | Bajo | Soft | Más permisivo que OF en general; menos plata por sub |
| **Fansly** | 80% | Permitido con disclosure | ID + selfie | Medio | Tag obligatorio | Alternativa OF, más laxo. Ban a deepfakes. |
| **Patreon** | 88-90% | **Prohibido AI fotorealista en tiers adultos** | ID | Alto pero no NSFW-focus | N/A | Descartado para NSFW |
| **JustForFans** | 80% | Permitido | ID + liveness | Medio | Tag | Otra alternativa OF, comunidad más nicho |

## Detalle por plataforma

### Fanvue — recomendado primario

**Política AI** (oficial, mayo 2024 + actualizaciones 2026):
- Categoría oficial **"AI Creator"** durante onboarding.
- Acepta personajes 100% sintéticos (ej. Aitana López).
- Disclosure: al menos uno de
  - Watermark visible en cada imagen/video.
  - Caption con `#AI` o equivalente.
  - Bio statement permanente.
- Reasonable Person's Test: si 3 moderadores creen que un sub razonable confundiría el contenido con humano real → flag.
- KYC del **dueño** de la cuenta, no del personaje.

**Take rate**:
- Mes 1: 15% Fanvue / 85% creator (promo onboarding).
- Después: 20% / 80%.

**Cobro**:
- Bank transfer global.
- **Crypto (USDT/USDC)** — opción más limpia desde Argentina.
- Mínimo payout $20.

**Tráfico**:
- Crecimiento fuerte 2024-2026 a expensas de OF.
- Top earners $50k-$300k/mes. Bulk de creators $500-$5k/mes.

**Casos AI exitosos en Fanvue**:
- Aitana López: ~$30k/mes Fanvue + brand deals.
- Múltiples creators del rubro AI con 5-figure mensual.

**Por qué para MVP**: zero fricción legal, zero riesgo de ban por AI-only.

### OnlyFans — alta upside, alto requirement

**Política AI** (overhaul 2026):
- AI permitida solo si el creador está **verificado vía liveness** y el contenido **se parece al creador real verificado**.
- Personajes 100% sintéticos = **ban inmediato y permanente**.
- Deepfakes (cara de persona real generada por AI) = ban + reporte.
- Re-verificación cada 12 meses con nueva liveness.
- Etiquetado obligatorio: `#AI`, `#AIGenerated` visible en captions.

**Implicación para nosotros**:
- Para OF necesitamos un humano real verificado cuya likeness sea **la base del LoRA**. Las opciones son:
  - **Vos mismo** como base del LoRA (mainstreaming poco común, pero técnicamente posible).
  - **Una socia real** que pasa el KYC y cuyo rostro es la "semilla" del LoRA — el AI luego "expande" producción manteniendo similitud.
  - **Una creator humana real existente** con la que se hace partnership (ella aporta KYC + likeness, vos AI infrastructure).
- Sin anchor humano real, OF queda **bloqueado**.

**Take rate**: 20% OF / 80% creator.

**Tráfico**: la #1 del rubro. ~3M creators, 320M usuarios. Mayor pool de pagadores.

**Cobro**: bank transfer SWIFT (vía Payoneer intermediario desde AR es lo común) o e-wallet.

**Recomendación**: si Fanvue valida la hipótesis de viabilidad, evaluar luego cómo conseguir anchor humano para extender a OF.

### Passes — link aggregator, no primary NSFW

**Qué es**: aggregator/landing del estilo Linktree pero monetizable. Lucy Guo (ex-Scale AI) lanzó la plataforma con foco en creators 18+.

**Política AI**: permitida con disclosure caso por caso.

**Take rate**: 90% creator / 10% Passes — mejor que OF y Fanvue.

**Tráfico orgánico para NSFW**: bajo. La plataforma no tiene "feed" tipo OF.

**Uso recomendado**:
- **Como link aggregator desde IG/TikTok** (es la opción más amigable a Meta/TikTok en 2026 — IG no penaliza link a Passes como sí lo hace con linktree → OF directo).
- Vender access a Telegram/Discord privado de la influencer.
- **NO como primary plataforma de NSFW**.

### Loyalfans — diversificación

**Política AI**: permitida.

**Take rate**: 80% creator.

**Tráfico**: bajo en comparación con OF/Fanvue. Comunidad más leal (de ahí el nombre) pero menos pagadores.

**Uso**: mirror de Fanvue para diversificar revenue. Cross-postear contenido. No vale el esfuerzo en MVP.

### Fansly — alternativa OF

**Política AI**: permitida con disclosure. Ban a deepfakes de personas reales.

**Take rate**: 80%.

**Tráfico**: alternativa creciente a OF, comunidad más laxa. Algunos creators ban-hammered de OF migran acá.

**Uso**: posible mirror cuando se diversifica. No primary.

### JustForFans, AdmireMe, otros

- **JustForFans**: nicho LGBTQ-fuerte, comunidad chica.
- **AdmireMe**: UK-focus, similar OF.
- **MYM**: focus francés.

Ninguna relevante para MVP.

### Patreon — descartado

- Política 2026: **prohíbe AI fotorealista** en tiers adultos.
- El cambio fue motivado por el caso Jessica Foster y otros virals 2025.
- Para AI fotorealista NSFW, Patreon no es opción.

## Disclosure por plataforma

| Plataforma | Cómo declarar |
|---|---|
| Fanvue | Watermark visible **OR** caption `#AI` **OR** bio statement |
| OnlyFans | `#AI` visible obligatorio en TODAS las publicaciones |
| TikTok | Toggle "AI-generated" en upload (TikTok auto-detecta C2PA igualmente) |
| Instagram | Toggle "AI info" + bio statement |
| EU (todos) | Disclosure mandatorio desde 2 ago 2026 (EU AI Act art. 50) |

## Cobro desde Argentina

Cepo levantado sept 2025. Régimen BCRA permite freelancers cobrar sin límite.

| Plataforma | Métodos cobro AR | Recomendado |
|---|---|---|
| Fanvue | Bank transfer / crypto (USDT/USDC) | **Crypto + DolarApp/Wayex** |
| OnlyFans | Bank transfer SWIFT (vía Payoneer) o e-wallet | Payoneer → Wise → AR bank |
| Passes | Stripe directo | Stripe → bank or DolarApp |
| Loyalfans | Bank / crypto | Crypto |

**Setup óptimo desde AR**: Fanvue → payout USDC → wallet propia → DolarApp para liquidar. Sin retención banco AR, sin fricción.

## Recomendación de plan

1. **MVP completo (validar viabilidad técnica)**: sin necesidad de plataforma todavía. Solo se valida calidad de contenido.
2. **Post-MVP, fase de plataforma**: arrancar **Fanvue** (categoría AI Creator, zero riesgo ban, plataforma diseñada para esto).
3. **Si Fanvue valida** (~$1k+/mes en 6 meses): evaluar conseguir anchor humano real (vos mismo, socia, partnership) para extender a OF.
4. **Mirror eventual** en Fansly/Loyalfans si el contenido funciona.
5. **Passes**: usar **siempre** como link aggregator desde IG/TikTok (independiente de plataforma primaria).
6. **Patreon**: descartado.

## Fuentes

- [Fanvue AI Content Guidelines](https://help.fanvue.com/en/articles/9538738-is-ai-content-allowed-on-fanvue)
- [Fanvue KYC for AI creators](https://help.fanvue.com/en/articles/9539091-passing-kyc-and-creating-multiple-accounts-as-an-ai-creator)
- [OnlyFans 2026 AI/Deepfake Policy](https://list25.com/onlyfans-2026-policy-updates-ai-deepfake-ban-verification/)
- [OnlyFans AI Rules 2026 (Sozee)](https://sozee.ai/resources/onlyfans-ai-rules-2026/)
- [AI Adult Creator Guidelines 2026](https://sozee.ai/resources/2026-ai-adult-creator-guidelines/)
- [Passes overview](https://passes.com/about)
- [Best AI Influencer Platforms 2026 (Apatero)](https://apatero.ai/blog/best-platforms-for-ai-influencers-compared)
- [TAKE IT DOWN Act](https://blog.ericgoldman.org/archives/2025/12/onlyfans-defeats-chatter-scam-claim-n-z-v-fenix.htm)
- [Aitana López case study (Euronews)](https://www.euronews.com/next/2024/12/27/meet-the-first-spanish-ai-model-earning-up-to-10000-per-month)
- [Cepo / Régimen BCRA freelancers (Infobae)](https://www.infobae.com/economia/2025/09/23/fin-del-cepo-para-freelancers-como-cobrar-en-dolares-del-exterior-sin-limites-con-el-nuevo-regimen-del-bcra/)
