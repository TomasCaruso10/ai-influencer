"""C2PA Content Credentials signing.

Wrappea `c2pa-python` SDK. Inyecta manifest firmado en el output con:
- claim_generator: identificador del pipeline
- actions: c2pa.created con softwareAgent (modelo)
- training-mining: declaración `ai_generative_training=notAllowed`

EU AI Act art. 50 compliance: el manifest sirve como disclosure
machine-readable para que Meta/TikTok auto-detecten + labelen.

Lazy import de c2pa (optional dep).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_DEFAULT_MANIFEST_TEMPLATE = {
    "claim_generator": "ai-influencer/0.2.0",
    "assertions": [
        {
            "label": "c2pa.actions",
            "data": {
                "actions": [
                    {"action": "c2pa.created", "softwareAgent": "REPLACE_ME"}
                ]
            },
        },
        {
            "label": "c2pa.training-mining",
            "data": {
                "entries": {
                    "c2pa.ai_generative_training": {"use": "notAllowed"}
                }
            },
        },
    ],
}


@dataclass
class C2PASigner:
    """Firma manifest C2PA en imagen. Implementa `C2PASignerProto` del pipeline.

    Args:
        cert_pem_path: path al cert público (PEM)
        key_pem_path: path a la private key (PEM). En prod usar HSM/KMS.
        timestamp_url: TSA URL para timestamp signing (default DigiCert).
    """

    cert_pem_path: Path | str | None = None
    key_pem_path: Path | str | None = None
    timestamp_url: str = "http://timestamp.digicert.com"
    claim_generator: str = "ai-influencer/0.2.0"

    def __post_init__(self) -> None:
        self._signer: Any = None
        self._certs: Any = None
        self._key: Any = None

    def _ensure_signer(self) -> None:
        if self._signer is not None:
            return
        if not self.cert_pem_path or not self.key_pem_path:
            raise RuntimeError(
                "C2PASigner requires cert_pem_path and key_pem_path. "
                "Use a test cert pair (cert.pem + key.pem) or skip C2PA in dev."
            )
        import c2pa  # lazy

        self._certs = Path(self.cert_pem_path).read_bytes()
        self._key = Path(self.key_pem_path).read_bytes()

        def _sign_callback(data: bytes) -> bytes:
            return c2pa.sign_with_private_key(self._key, c2pa.SigningAlg.PS256, data)

        self._signer = c2pa.create_signer(
            _sign_callback,
            c2pa.SigningAlg.PS256,
            self._certs,
            self.timestamp_url,
        )

    async def sign(self, image_path: Path, manifest: dict | None = None) -> Path:
        """Firma `image_path` con `manifest`, escribe output con sufijo `_signed`.

        Returns: path al archivo firmado.
        """
        import c2pa  # lazy

        self._ensure_signer()

        if manifest is None:
            manifest = self._build_default_manifest(image_path)

        output_path = image_path.with_name(f"{image_path.stem}_signed{image_path.suffix}")
        builder = c2pa.Builder(manifest)
        builder.sign_file(self._signer, str(image_path), str(output_path))
        return output_path

    def _build_default_manifest(self, image_path: Path) -> dict:
        import json

        manifest = json.loads(json.dumps(_DEFAULT_MANIFEST_TEMPLATE))  # deep copy
        manifest["claim_generator"] = self.claim_generator
        manifest["title"] = image_path.name
        return manifest
