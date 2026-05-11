"""Block list de keywords pediátricos. Aplica a:

- Filenames de LoRAs y embeddings al cargar
- Prompts antes de submit
- Captions auto-generadas

Match es case-insensitive sustring contra una lista fija de tokens del rubro.
Approach conservador: ante la duda, bloquea.
"""

from __future__ import annotations

PEDIATRIC_KEYWORDS: frozenset[str] = frozenset({
    "child", "children", "kid", "kids", "baby", "babies",
    "infant", "infants", "toddler", "preteen", "preteens",
    "teen", "teens", "teenage", "teenager", "teenagers", "teenaged",
    "minor", "minors", "underage", "young girl", "young boy",
    "schoolgirl", "schoolboy", "schoolkid",
    "loli", "lolita", "shota", "shotacon",
    "jailbait", "youngster", "juvenile", "adolescent",
    "small body child", "flat chest child", "childlike", "child-like",
    "immature features",
    "middle school", "elementary",
})
"""Keywords que NUNCA deben aparecer en prompts, captions ni nombres de LoRA.
La lista es exhaustiva intencionalmente — preferimos false positives que falsos
negativos en este eje específico (riesgo legal AIG-CSAM)."""


def contains_blocked_keyword(text: str) -> str | None:
    """Returns el primer keyword bloqueado encontrado, o None si está limpio.

    Match case-insensitive sustring.
    """
    if not text:
        return None
    lower = text.lower()
    for keyword in PEDIATRIC_KEYWORDS:
        if keyword in lower:
            return keyword
    return None


def is_lora_filename_safe(filename: str) -> bool:
    """True si el filename del LoRA NO contiene keywords pediátricos.

    Use case: filter antes de cargar LoRA en ComfyUI workflow.
    """
    return contains_blocked_keyword(filename) is None
