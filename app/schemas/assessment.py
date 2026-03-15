"""Schemas for Pillar 3 — Assessment & Question Bank."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import (
    BloomLevel,
    CulturalContext,
    CurriculumBoard,
    Language,
    LearnerProfile,
    RAGMetadata,
    SkillTag,
    Subject,
    ValidationReport,
)


class AssessmentType(str, Enum):
    QUIZ                 = "QUIZ"
    EXAM_QUESTIONS       = "EXAM_QUESTIONS"
    QUESTION_BANK        = "QUESTION_BANK"
    DIAGNOSTIC_TEST      = "DIAGNOSTIC_TEST"
    MARKING_SCHEME       = "MARKING_SCHEME"
    RUBRIC               = "RUBRIC"
    REMEDIATION_EXERCISE = "REMEDIATION_EXERCISE"


class DifficultyLevel(str, Enum):
    EASY   = "EASY"
    MEDIUM = "MEDIUM"
    HARD   = "HARD"
    MIXED  = "MIXED"


class QuestionFormat(str, Enum):
    MULTIPLE_CHOICE   = "MULTIPLE_CHOICE"
    TRUE_FALSE        = "TRUE_FALSE"
    SHORT_ANSWER      = "SHORT_ANSWER"
    FILL_IN_THE_BLANK = "FILL_IN_THE_BLANK"
    ESSAY             = "ESSAY"
    STRUCTURED        = "STRUCTURED"
    MIXED             = "MIXED"


class QuestionItem(BaseModel):
    question_number: int
    question_text: str
    question_format: str
    bloom_level: str
    difficulty: str
    skill_tags: List[SkillTag] = Field(default_factory=list)
    topic_tags: List[str] = Field(default_factory=list)
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    marks: Optional[int] = None


class AssessmentGenerationRequest(BaseModel):
    request_id: Optional[str] = None
    subject: Subject
    topic: str = Field(..., min_length=3, max_length=200)
    assessment_type: AssessmentType
    curriculum_board: CurriculumBoard = CurriculumBoard.WAEC
    learner_profile: LearnerProfile
    bloom_level: BloomLevel = BloomLevel.UNDERSTAND
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    question_format: QuestionFormat = QuestionFormat.MIXED
    num_questions: int = Field(10, ge=1, le=100)
    target_skills: List[str] = Field(
        default_factory=list,
        description="Filter questions to specific skills from the skill library",
    )
    output_language: Language = Language.ENGLISH
    cultural_context: CulturalContext = Field(default_factory=CulturalContext)
    include_answer_key: bool = True
    include_marking_guide: bool = True
    include_bloom_tags: bool = True
    include_difficulty_tags: bool = True
    include_topic_tags: bool = True
    use_rag: bool = True
    rag_top_k: int = Field(4, ge=1, le=10)
    max_tokens: int = Field(2048, ge=256, le=4096)


class AssessmentGenerationResponse(BaseModel):
    request_id: Optional[str] = None
    assessment_type: str
    subject: str
    topic: str
    curriculum_board: str
    questions: List[QuestionItem] = Field(default_factory=list)
    raw_output: str
    total_marks: Optional[int] = None
    estimated_duration_minutes: Optional[int] = None
    bloom_distribution: dict = Field(default_factory=dict)
    difficulty_distribution: dict = Field(default_factory=dict)
    skill_distribution: dict = Field(
        default_factory=dict,
        description="skill_name → question count",
    )
    validation: ValidationReport
    rag_metadata: Optional[RAGMetadata] = None
    model_used: str
    generation_time_seconds: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: List[str] = Field(default_factory=list)
