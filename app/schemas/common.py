"""Shared enums and base models used across all pillars."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Skill domain ───────────────────────────────────────────────────────────────

class SkillDomain(str, Enum):
    TECHNICAL  = "technical"
    BEHAVIORAL = "behavioral"
    COGNITIVE  = "cognitive"
    LANGUAGE   = "language"


class SkillTag(BaseModel):
    skill_name: str = Field(..., description="Exact name from the Enum Skill Library")
    skill_domain: SkillDomain
    parent_skill: Optional[str] = Field(None, description="None if root skill")


# ── Curriculum boards ──────────────────────────────────────────────────────────

class CurriculumBoard(str, Enum):
    NERDC   = "NERDC"
    WAEC    = "WAEC"
    NECO    = "NECO"
    NABTEB  = "NABTEB"
    UBEC    = "UBEC"
    BECE_GH = "BECE_GH"
    WAEC_GH = "WAEC_GH"
    GES_GH  = "GES_GH"
    CUSTOM  = "CUSTOM"


# ── Education levels ───────────────────────────────────────────────────────────

class EducationLevel(str, Enum):
    PRIMARY_1_3         = "PRIMARY_1_3"
    PRIMARY_4_6         = "PRIMARY_4_6"
    JSS1                = "JSS1"
    JSS2                = "JSS2"
    JSS3                = "JSS3"
    SSS1                = "SSS1"
    SSS2                = "SSS2"
    SSS3                = "SSS3"
    TERTIARY            = "TERTIARY"
    VOCATIONAL_BASIC    = "VOCATIONAL_BASIC"
    VOCATIONAL_ADVANCED = "VOCATIONAL_ADVANCED"
    ADULT_LITERACY      = "ADULT_LITERACY"
    PROFESSIONAL_DEV    = "PROFESSIONAL_DEV"


# ── Programme types ────────────────────────────────────────────────────────────

class ProgramType(str, Enum):
    ACADEMIC            = "ACADEMIC"
    VOCATIONAL          = "VOCATIONAL"
    COMMUNITY           = "COMMUNITY"
    LIFE_SKILLS         = "LIFE_SKILLS"
    AGRICULTURAL        = "AGRICULTURAL"
    TEACHER_TRAINING    = "TEACHER_TRAINING"
    YOUTH_ENTERPRISE    = "YOUTH_ENTERPRISE"
    RELIGIOUS_EDUCATION = "RELIGIOUS_EDUCATION"


# ── Subjects ───────────────────────────────────────────────────────────────────

class Subject(str, Enum):
    # Core Academic
    MATHEMATICS          = "mathematics"
    ENGLISH_LANGUAGE     = "english_language"
    BIOLOGY              = "biology"
    CHEMISTRY            = "chemistry"
    PHYSICS              = "physics"
    FURTHER_MATHEMATICS  = "further_mathematics"
    ECONOMICS            = "economics"
    GOVERNMENT           = "government"
    GEOGRAPHY            = "geography"
    HISTORY              = "history"
    CIVIC_EDUCATION      = "civic_education"
    SOCIAL_STUDIES       = "social_studies"
    YORUBA_LANGUAGE      = "yoruba_language"
    IGBO_LANGUAGE        = "igbo_language"
    HAUSA_LANGUAGE       = "hausa_language"
    FRENCH               = "french"
    COMPUTER_SCIENCE     = "computer_science"
    BASIC_SCIENCE        = "basic_science"
    AGRICULTURAL_SCIENCE = "agricultural_science"
    HOME_ECONOMICS       = "home_economics"
    VISUAL_ART           = "visual_art"
    MUSIC                = "music"
    PHYSICAL_EDUCATION   = "physical_education"
    FINANCIAL_ACCOUNTING = "financial_accounting"
    COMMERCE             = "commerce"
    CRS                  = "crs"
    IRS                  = "irs"
    # Non-academic / vocational
    FINANCIAL_LITERACY   = "financial_literacy"
    HEALTH_EDUCATION     = "health_education"
    DIGITAL_LITERACY     = "digital_literacy"
    ENTREPRENEURSHIP     = "entrepreneurship"
    AGRICULTURE_EXTENSION = "agriculture_extension"
    TRADE_SKILL          = "trade_skill"
    CUSTOM_SUBJECT       = "custom_subject"


# ── Output languages ───────────────────────────────────────────────────────────

class Language(str, Enum):
    ENGLISH      = "en"
    YORUBA       = "yo"
    IGBO         = "ig"
    HAUSA        = "ha"
    IGALA        = "igl"
    PIDGIN_NG    = "pcm"
    TWI          = "tw"
    EWE          = "ee"
    MIXED_EN_YO  = "en-yo"
    MIXED_EN_HA  = "en-ha"
    MIXED_EN_IG  = "en-ig"


# ── Bloom's taxonomy ───────────────────────────────────────────────────────────

class BloomLevel(str, Enum):
    REMEMBER   = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY      = "APPLY"
    ANALYZE    = "ANALYZE"
    EVALUATE   = "EVALUATE"
    CREATE     = "CREATE"


# ── Environment constraints ────────────────────────────────────────────────────

class EnvironmentConstraint(str, Enum):
    STANDARD_DIGITAL  = "STANDARD_DIGITAL"
    LOW_BANDWIDTH     = "LOW_BANDWIDTH"
    PRINT_READY       = "PRINT_READY"
    OFFLINE_COMMUNITY = "OFFLINE_COMMUNITY"


# ── Validation ─────────────────────────────────────────────────────────────────

class ValidationStatus(str, Enum):
    PASSED  = "PASSED"
    FLAGGED = "FLAGGED"
    REVISED = "REVISED"
    FAILED  = "FAILED"


class ValidationReport(BaseModel):
    status: ValidationStatus
    rules_passed: List[str] = Field(default_factory=list)
    rules_failed: List[str] = Field(default_factory=list)
    judge_score: Optional[float] = None
    judge_dimensions: Optional[dict] = None
    bloom_accuracy_score: Optional[float] = None   # 0.0–1.0; set by rules_node
    revision_count: int = 0
    notes: List[str] = Field(default_factory=list)


# ── RAG metadata ───────────────────────────────────────────────────────────────

class RAGMetadata(BaseModel):
    chunks_used: int = 0
    sources: List[str] = Field(default_factory=list)
    similarity_scores: List[float] = Field(default_factory=list)
    synthetic_chunks: int = 0


# ── Learner profile ────────────────────────────────────────────────────────────

class LearnerProfile(BaseModel):
    age_range: Optional[str] = None
    education_level: EducationLevel
    program_type: ProgramType = ProgramType.ACADEMIC
    special_needs: List[str] = Field(default_factory=list)
    prior_knowledge: Optional[str] = None
    socioeconomic_context: Optional[str] = None
    class_size: Optional[int] = None


# ── Pedagogical goals ──────────────────────────────────────────────────────────

class PedagogicalGoals(BaseModel):
    bloom_level: BloomLevel = BloomLevel.UNDERSTAND
    learning_objectives: List[str] = Field(default_factory=list)
    target_skills: List[str] = Field(
        default_factory=list,
        description="Skill names from the Enum Skill Library",
    )
    skill_domain: Optional[SkillDomain] = Field(
        None, description="Domain filter used during skill auto-tagging"
    )
    duration_minutes: Optional[int] = None
    assessment_style: Optional[str] = None
    teaching_approach: Optional[str] = None


# ── Cultural context ───────────────────────────────────────────────────────────

class CulturalContext(BaseModel):
    region: Optional[str] = None
    use_local_examples: bool = True
    use_local_names: bool = True
    avoid_cultural_bias: bool = True
    festival_calendar_aware: bool = False
    custom_cultural_notes: Optional[str] = None
