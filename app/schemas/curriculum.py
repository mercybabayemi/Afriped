"""Schemas for Pillar 1 — Curriculum Auto-Generation."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import (
    CulturalContext,
    CurriculumBoard,
    EducationLevel,
    EnvironmentConstraint,
    Language,
    LearnerProfile,
    PedagogicalGoals,
    RAGMetadata,
    SkillTag,
    Subject,
    ValidationReport,
)


class CurriculumOutputType(str, Enum):
    SCHEME_OF_WORK    = "SCHEME_OF_WORK"
    TERM_PLAN         = "TERM_PLAN"
    UNIT_PLAN         = "UNIT_PLAN"
    SCOPE_AND_SEQUENCE = "SCOPE_AND_SEQUENCE"
    LEARNING_OUTCOMES = "LEARNING_OUTCOMES"


class CurriculumGenerationRequest(BaseModel):
    request_id: Optional[str] = None
    subject: Subject
    education_level: EducationLevel
    curriculum_board: CurriculumBoard = CurriculumBoard.NERDC
    output_type: CurriculumOutputType
    num_terms: int = Field(3, ge=1, le=4)
    num_weeks_per_term: int = Field(13, ge=1, le=20)
    topics: Optional[List[str]] = Field(default_factory=list)
    learner_profile: LearnerProfile
    pedagogical_goals: PedagogicalGoals
    output_language: Language = Language.ENGLISH
    cultural_context: CulturalContext = Field(default_factory=CulturalContext)
    environment: EnvironmentConstraint = EnvironmentConstraint.STANDARD_DIGITAL
    include_resources: bool = True
    include_assessment_schedule: bool = True
    use_rag: bool = True
    max_tokens: int = Field(2048, ge=256, le=4096)


class CurriculumGenerationResponse(BaseModel):
    request_id: Optional[str] = None
    curriculum_output: str
    output_type: str
    subject: str
    education_level: str
    curriculum_board: str
    num_topics_generated: int = 0
    skill_tags: List[SkillTag] = Field(default_factory=list)
    validation: ValidationReport
    rag_metadata: Optional[RAGMetadata] = None
    model_used: str
    generation_time_seconds: float
    token_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: List[str] = Field(default_factory=list)
