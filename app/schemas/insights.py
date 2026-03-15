"""Schemas for Pillar 4 — Insight & Diagnostics."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import (
    BloomLevel,
    CulturalContext,
    CurriculumBoard,
    EducationLevel,
    Language,
    SkillTag,
    Subject,
)


class InsightsRequest(BaseModel):
    request_id: Optional[str] = None
    content: str = Field(..., min_length=10)
    content_type: str
    subject: Optional[Subject] = None
    education_level: Optional[EducationLevel] = None
    curriculum_board: Optional[CurriculumBoard] = None
    expected_bloom_level: Optional[BloomLevel] = None
    expected_language: Optional[Language] = None
    expected_skills: Optional[List[str]] = Field(
        None,
        description="Skills the content is expected to cover",
    )
    expected_cultural_context: Optional[CulturalContext] = None
    run_rag_coverage_check: bool = True
    run_readability: bool = True
    run_bloom_analysis: bool = True
    run_cultural_analysis: bool = True
    run_skill_gap_analysis: bool = True
    run_curriculum_gap_analysis: bool = False


class InsightsResponse(BaseModel):
    request_id: Optional[str] = None
    readability: dict = Field(
        default_factory=dict,
        description="Flesch-Kincaid grade, complexity band",
    )
    bloom_analysis: dict = Field(
        default_factory=dict,
        description="Detected Bloom level, verbs found",
    )
    cultural_analysis: dict = Field(
        default_factory=dict,
        description="Name ratio, local example count, flags",
    )
    skill_tags_detected: List[SkillTag] = Field(default_factory=list)
    skill_gap_analysis: Optional[dict] = Field(
        None,
        description="Expected vs detected skills delta",
    )
    curriculum_coverage: Optional[dict] = Field(
        None,
        description="Percentage overlap with RAG corpus",
    )
    gap_analysis: Optional[dict] = Field(
        None,
        description="Curriculum topics not covered",
    )
    overall_quality_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Composite quality score"
    )
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
