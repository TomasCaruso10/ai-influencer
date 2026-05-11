"""Graph definition. Declarado a nivel de módulo (no dentro de función)."""

from __future__ import annotations

from pydantic_graph import Graph

from aiinfluencer.pipeline.deps import WorkflowDeps
from aiinfluencer.pipeline.nodes import (
    C2PASignNode,
    CaptionNode,
    FaceQCNode,
    GenerateNode,
    HumanReviewNode,
    PostProcessNode,
    PromptExpandNode,
    SafetyFilterNode,
    StoreNode,
)
from aiinfluencer.pipeline.output import PieceApproved, PieceRejected
from aiinfluencer.pipeline.state import WorkflowState

piece_graph: Graph[WorkflowState, WorkflowDeps, PieceApproved | PieceRejected] = Graph(
    nodes=[
        PromptExpandNode,
        GenerateNode,
        SafetyFilterNode,
        FaceQCNode,
        PostProcessNode,
        C2PASignNode,
        HumanReviewNode,
        CaptionNode,
        StoreNode,
    ],
    state_type=WorkflowState,
    run_end_type=PieceApproved | PieceRejected,
)
"""Grafo del pipeline. Cada pieza es una corrida independiente."""
