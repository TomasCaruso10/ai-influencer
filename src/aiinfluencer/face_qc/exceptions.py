"""Excepciones del módulo face_qc."""


class NoFaceDetectedError(Exception):
    """La imagen no contiene caras detectables."""


class AmbiguousFaceError(Exception):
    """Más de una cara y no se puede determinar cuál es la principal."""
