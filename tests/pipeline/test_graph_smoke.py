"""Smoke tests del esqueleto. Corre el grafo end-to-end con placeholders."""

from __future__ import annotations

import pytest

from aiinfluencer.pipeline import PieceRequest, run_piece
from aiinfluencer.pipeline.deps import WorkflowDeps
from aiinfluencer.pipeline.output import PieceApproved, PieceRejected, RejectionReason
from aiinfluencer.pipeline.runner import PausedAtReview


async def test_happy_path_approves_with_dummies():
    """Con todos los dummies que pasan, el grafo termina en PieceApproved."""
    deps = WorkflowDeps.with_dummies()
    request = PieceRequest(prompt_seed="cafe portrait")

    result = await run_piece(request, deps)

    assert isinstance(result, PieceApproved)
    assert result.piece_id.startswith("piece_")
    assert result.r2_key is not None


async def test_hitl_pauses_at_review():
    """Con auto_approve_in_review=False, el grafo pausa en HumanReviewNode."""
    deps = WorkflowDeps.with_dummies()
    deps.auto_approve_in_review = False
    request = PieceRequest(prompt_seed="cafe portrait")

    result = await run_piece(request, deps)

    assert isinstance(result, PausedAtReview)
    assert result.status == "paused_at_review"


async def test_age_classifier_rejection_path():
    """Si age classifier reporta is_adult=False, llega a End[PieceRejected]
    con razón AGE_CLASSIFIER_FAILED."""

    class MinorAgeClassifier:
        async def age_classify(self, image_path):
            return {"bucket": "10-19", "is_adult": False, "confidence": 0.9}

        async def nsfw_classify(self, image_path):
            return 0.3

        async def q16_classify(self, image_path):
            return False

    deps = WorkflowDeps.with_dummies()
    deps.classifiers = MinorAgeClassifier()
    request = PieceRequest(prompt_seed="test")

    result = await run_piece(request, deps)

    assert isinstance(result, PieceRejected)
    assert result.reason == RejectionReason.AGE_CLASSIFIER_FAILED


async def test_face_qc_rejection_path():
    """Si face_qc devuelve <threshold, llega a End[PieceRejected] con razón
    FACE_QC_BELOW_THRESHOLD."""

    class FailingFaceQC:
        async def cosine_similarity(self, image_path):
            return 0.2  # < 0.45 threshold default

    deps = WorkflowDeps.with_dummies()
    deps.face_qc = FailingFaceQC()
    request = PieceRequest(prompt_seed="test")

    result = await run_piece(request, deps)

    assert isinstance(result, PieceRejected)
    assert result.reason == RejectionReason.FACE_QC_BELOW_THRESHOLD


async def test_q16_rejection_path():
    """Si Q16 flagea inappropriate, rechaza."""

    class Q16Flagging:
        async def age_classify(self, image_path):
            return {"bucket": "20-29", "is_adult": True, "confidence": 0.95}

        async def nsfw_classify(self, image_path):
            return 0.3

        async def q16_classify(self, image_path):
            return True

    deps = WorkflowDeps.with_dummies()
    deps.classifiers = Q16Flagging()
    request = PieceRequest(prompt_seed="test")

    result = await run_piece(request, deps)

    assert isinstance(result, PieceRejected)
    assert result.reason == RejectionReason.Q16_INAPPROPRIATE
