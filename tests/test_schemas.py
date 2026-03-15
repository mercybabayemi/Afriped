"""Tests for all schema files."""
import pytest
from pydantic import ValidationError

from app.schemas.common import (
    BloomLevel, CurriculumBoard, EducationLevel, EnvironmentConstraint,
    Language, LearnerProfile, PedagogicalGoals, ProgramType, SkillDomain,
    SkillTag, Subject, ValidationReport, ValidationStatus,
)
from app.schemas.curriculum import CurriculumGenerationRequest, CurriculumOutputType
from app.schemas.content import ContentGenerationRequest, ContentType
from app.schemas.assessment import AssessmentGenerationRequest, AssessmentType, QuestionItem
from app.schemas.insights import InsightsRequest
from app.schemas.skills import SkillLibraryItem, SkillLibraryResponse


# ── Common schemas ─────────────────────────────────────────────────────────────

def test_skill_tag_valid():
    tag = SkillTag(skill_name="Critical Thinking", skill_domain=SkillDomain.COGNITIVE)
    assert tag.skill_name == "Critical Thinking"
    assert tag.parent_skill is None


def test_learner_profile_defaults():
    profile = LearnerProfile(education_level=EducationLevel.SSS1)
    assert profile.program_type == ProgramType.ACADEMIC
    assert profile.special_needs == []


def test_pedagogical_goals_defaults():
    goals = PedagogicalGoals(learning_objectives=["Explain photosynthesis"])
    assert goals.bloom_level == BloomLevel.UNDERSTAND
    assert goals.target_skills == []


def test_validation_report():
    report = ValidationReport(
        status=ValidationStatus.PASSED,
        rules_passed=["length_check", "bloom_verb_presence"],
        rules_failed=[],
    )
    assert report.revision_count == 0


def test_language_enum_values():
    assert Language.YORUBA.value == "yo"
    assert Language.MIXED_EN_YO.value == "en-yo"
    assert Language.PIDGIN_NG.value == "pcm"


# ── Curriculum schemas ─────────────────────────────────────────────────────────

def _make_learner(level="SSS1"):
    return LearnerProfile(education_level=level)


def _make_goals():
    return PedagogicalGoals(learning_objectives=["Explain the topic"])


def test_curriculum_request_defaults():
    req = CurriculumGenerationRequest(
        subject=Subject.MATHEMATICS,
        education_level=EducationLevel.SSS1,
        output_type=CurriculumOutputType.SCHEME_OF_WORK,
        learner_profile=_make_learner(),
        pedagogical_goals=_make_goals(),
    )
    assert req.curriculum_board == CurriculumBoard.NERDC
    assert req.num_terms == 3
    assert req.use_rag is True


def test_curriculum_request_max_tokens_bounds():
    with pytest.raises(ValidationError):
        CurriculumGenerationRequest(
            subject=Subject.MATHEMATICS,
            education_level=EducationLevel.SSS1,
            output_type=CurriculumOutputType.SCHEME_OF_WORK,
            learner_profile=_make_learner(),
            pedagogical_goals=_make_goals(),
            max_tokens=50,  # below minimum of 256
        )


# ── Content schemas ────────────────────────────────────────────────────────────

def test_content_request_topic_min_length():
    with pytest.raises(ValidationError):
        ContentGenerationRequest(
            subject=Subject.BIOLOGY,
            topic="ab",  # too short
            content_type=ContentType.LESSON_PLAN,
            learner_profile=_make_learner(),
            pedagogical_goals=_make_goals(),
        )


def test_content_request_valid():
    req = ContentGenerationRequest(
        subject=Subject.BIOLOGY,
        topic="Photosynthesis in Plants",
        content_type=ContentType.WORKSHEET,
        learner_profile=_make_learner("JSS3"),
        pedagogical_goals=_make_goals(),
        output_language=Language.YORUBA,
    )
    assert req.output_language == Language.YORUBA
    assert req.include_answer_key is True


# ── Assessment schemas ─────────────────────────────────────────────────────────

def test_assessment_request_defaults():
    req = AssessmentGenerationRequest(
        subject=Subject.CHEMISTRY,
        topic="Atomic Structure",
        assessment_type=AssessmentType.EXAM_QUESTIONS,
        learner_profile=_make_learner("SSS2"),
    )
    assert req.curriculum_board == CurriculumBoard.WAEC
    assert req.num_questions == 10


def test_question_item():
    q = QuestionItem(
        question_number=1,
        question_text="What is photosynthesis?",
        question_format="SHORT_ANSWER",
        bloom_level="UNDERSTAND",
        difficulty="EASY",
        topic_tags=["photosynthesis"],
        marks=2,
    )
    assert q.skill_tags == []
    assert q.marks == 2


# ── Insights schemas ───────────────────────────────────────────────────────────

def test_insights_request_valid():
    req = InsightsRequest(
        content="This lesson explains how to calculate the area of a circle using the formula A = πr².",
        content_type="LESSON_PLAN",
        expected_bloom_level=BloomLevel.APPLY,
    )
    assert req.run_readability is True
    assert req.run_bloom_analysis is True


def test_insights_request_too_short():
    with pytest.raises(ValidationError):
        InsightsRequest(content="short", content_type="x")


# ── Skills schemas ─────────────────────────────────────────────────────────────

def test_skill_library_response():
    item = SkillLibraryItem(
        skill_name="Critical Thinking",
        skill_domain=SkillDomain.COGNITIVE,
        parent_skill=None,
        description="Analysing information objectively",
    )
    resp = SkillLibraryResponse(
        total=1,
        domains={"cognitive": [item]},
        skills=[item],
    )
    assert resp.total == 1
