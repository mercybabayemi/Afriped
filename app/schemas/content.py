"""Schemas for Pillar 2 — Content Generation."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import (
    CulturalContext,
    CurriculumBoard,
    EnvironmentConstraint,
    Language,
    LearnerProfile,
    PedagogicalGoals,
    RAGMetadata,
    SkillTag,
    Subject,
    ValidationReport,
)


class ContentType(str, Enum):
    # Instructional
    LESSON_PLAN    = "LESSON_PLAN"
    UNIT_NOTES     = "UNIT_NOTES"
    LECTURE_NOTES  = "LECTURE_NOTES"
    STUDY_GUIDE    = "STUDY_GUIDE"
    WORKSHEET      = "WORKSHEET"
    WORKED_EXAMPLE = "WORKED_EXAMPLE"
    FLASHCARDS     = "FLASHCARDS"
    GLOSSARY       = "GLOSSARY"
    SUMMARY        = "SUMMARY"
    # Narrative / cultural
    STORY          = "STORY"
    DIALOGUE       = "DIALOGUE"
    CASE_STUDY     = "CASE_STUDY"
    # Non-academic
    VOCATIONAL_GUIDE      = "VOCATIONAL_GUIDE"
    COMMUNITY_AWARENESS   = "COMMUNITY_AWARENESS"
    EXTENSION_BULLETIN    = "EXTENSION_BULLETIN"


class ContentGenerationRequest(BaseModel):
    request_id: Optional[str] = None
    subject: Subject
    topic: str = Field(..., min_length=3, max_length=200)
    content_type: ContentType
    curriculum_board: CurriculumBoard = CurriculumBoard.NERDC
    learner_profile: LearnerProfile
    pedagogical_goals: PedagogicalGoals
    output_language: Language = Language.ENGLISH
    cultural_context: CulturalContext = Field(default_factory=CulturalContext)
    environment: EnvironmentConstraint = EnvironmentConstraint.STANDARD_DIGITAL
    max_tokens: int = Field(1024, ge=128, le=4096)
    include_teacher_notes: bool = False
    include_answer_key: bool = True
    use_rag: bool = True
    rag_top_k: int = Field(4, ge=1, le=10)


class ContentGenerationResponse(BaseModel):
    request_id: Optional[str] = None
    content: str
    content_type: str
    subject: str
    topic: str
    output_language: str
    curriculum_board: str
    bloom_level: str
    skill_tags: List[SkillTag] = Field(default_factory=list)
    validation: ValidationReport
    rag_metadata: Optional[RAGMetadata] = None
    model_used: str
    generation_time_seconds: float
    token_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: List[str] = Field(default_factory=list)
