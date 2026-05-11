"""Compliance técnico: C2PA signing + classifiers + audit log + block list.

Stack:
- C2PA: `c2pa-python` SDK (optional dep `compliance`)
- Age classifier: HuggingFace `dima806/fairface_age_image_detection`
- NSFW classifier: `Falconsai/nsfw_image_detection`
- Q16 classifier: violence/blood/inappropriate flags
- Audit log: Logfire + MongoDB schema
- Block list: helpers para filtrar LoRAs/embeddings con keywords pediátricos

Para que el pipeline corra en environments sin las deps ML pesadas, los
imports son lazy. Tests usan mocks.
"""

from aiinfluencer.compliance.block_list import (
    PEDIATRIC_KEYWORDS,
    contains_blocked_keyword,
    is_lora_filename_safe,
)
from aiinfluencer.compliance.classifiers import (
    AgeClassifierResult,
    HuggingFaceSafetyClassifiers,
    NSFWClassifierResult,
)

__all__ = [
    "HuggingFaceSafetyClassifiers",
    "AgeClassifierResult",
    "NSFWClassifierResult",
    "PEDIATRIC_KEYWORDS",
    "contains_blocked_keyword",
    "is_lora_filename_safe",
]
