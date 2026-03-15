"""AfriPedState — shared TypedDict passed through the LangGraph StateGraph."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict

from app.schemas.common import RAGMetadata, SkillTag, ValidationReport
from app.schemas.curriculum import CurriculumGenerationRequest
from app.schemas.content import ContentGenerationRequest
from app.schemas.assessment import AssessmentGenerationRequest
from app.schemas.insights import InsightsRequest


class AfriPedState(TypedDict, total=False):
    # ── Routing ────────────────────────────────────────────────────────────────
    pillar: str                          # "curriculum" | "content" | "assessment" | "insights"

    # ── Request ────────────────────────────────────────────────────────────────
    request: Union[
        CurriculumGenerationRequest,
        ContentGenerationRequest,
        AssessmentGenerationRequest,
        InsightsRequest,
    ]

    # ── RAG ───────────────────────────────────────────────────────────────────
    rag_context: Optional[str]
    rag_metadata: Optional[RAGMetadata]

    # ── Generation ────────────────────────────────────────────────────────────
    generated_content: Optional[str]
    structured_output: Optional[Dict[str, Any]]   # parsed questions[] for assessment

    # ── Skill tagging ─────────────────────────────────────────────────────────
    skill_tags: List[SkillTag]

    # ── Validation ────────────────────────────────────────────────────────────
    validation_report: Optional[ValidationReport]
    bloom_accuracy_score: Optional[float]        # 0.0–1.0; set by rules_node
    revision_instruction: Optional[str]
    revision_count: int                  # incremented by revise_node; max 2

    # ── Output ────────────────────────────────────────────────────────────────
    final_content: Optional[str]

    # ── Error ─────────────────────────────────────────────────────────────────
    error: Optional[str]
