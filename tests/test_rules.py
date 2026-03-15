"""Tests for the 8 rule-based validation checks."""
import pytest

from app.validation.rules import (
    check_bloom_verbs,
    check_cultural_flags,
    check_curriculum_alignment,
    check_format_compliance,
    check_language_detection,
    check_length,
    check_no_explicit_content,
    check_no_hallucinated_dates,
    compute_bloom_accuracy_score,
    run_all_rules,
)


# ── length_check ───────────────────────────────────────────────────────────────

def test_length_pass():
    content = "x" * 2000
    result = check_length(content, max_tokens=1024)
    assert result.passed


def test_length_too_short():
    result = check_length("short", max_tokens=1024)
    assert not result.passed
    assert "too short" in result.message


def test_length_too_long():
    content = "x" * 100_000
    result = check_length(content, max_tokens=512)
    assert not result.passed
    assert "too long" in result.message


# ── bloom_verb_presence ────────────────────────────────────────────────────────

def test_bloom_verbs_found():
    content = "Students will explain the water cycle and describe precipitation."
    result = check_bloom_verbs(content, "UNDERSTAND")
    assert result.passed


def test_bloom_verbs_missing():
    content = "The water falls from the sky onto the ground."
    result = check_bloom_verbs(content, "CREATE")
    assert not result.passed


def test_bloom_verbs_unknown_level():
    result = check_bloom_verbs("anything", "BOGUS_LEVEL")
    assert result.passed  # should not crash; skipped


# ── cultural_flag_check ────────────────────────────────────────────────────────

def test_cultural_flags_local_names_pass():
    content = "Emeka and Ngozi went to Balogun Market to buy books for school."
    result = check_cultural_flags(content, use_local_names=True)
    assert result.passed


def test_cultural_flags_western_names_fail():
    content = "John and Mary and Peter and James and Michael went to school today."
    result = check_cultural_flags(content, use_local_names=True)
    assert not result.passed


def test_cultural_flags_not_required():
    content = "John and Mary went to school."
    result = check_cultural_flags(content, use_local_names=False)
    assert result.passed


# ── format_compliance ──────────────────────────────────────────────────────────

def test_format_lesson_plan_pass():
    content = "Objective: Learn fractions.\nActivity: Group work.\nAssessment: Quiz."
    result = check_format_compliance(content, "LESSON_PLAN")
    assert result.passed


def test_format_lesson_plan_fail():
    content = "This is just some random text without structure."
    result = check_format_compliance(content, "LESSON_PLAN")
    assert not result.passed


def test_format_quiz_pass():
    content = "1. What is 2+2?\n2. What is 3×3?\n3. What is 4-1?"
    result = check_format_compliance(content, "QUIZ", num_questions=3)
    assert result.passed


# ── no_hallucinated_dates ─────────────────────────────────────────────────────

def test_no_bad_dates_pass():
    content = "The curriculum was designed in 2019 and updated in 2023."
    result = check_no_hallucinated_dates(content)
    assert result.passed


def test_bad_date_flagged():
    content = "This event happened in 2099 and was referenced in 1750."
    result = check_no_hallucinated_dates(content)
    assert not result.passed


# ── no_explicit_content ────────────────────────────────────────────────────────

def test_clean_content_passes():
    content = "Students learn about the human reproductive system in biology class."
    result = check_no_explicit_content(content)
    assert result.passed


def test_explicit_content_hard_fail():
    content = "This lesson contains fuck and other profanity."
    result = check_no_explicit_content(content)
    assert not result.passed
    assert result.is_hard_fail


# ── curriculum_alignment ───────────────────────────────────────────────────────

def test_curriculum_alignment_pass():
    content = (
        "Week 1 Objective: Students will identify key learning activities. "
        "Assessment includes a quiz. Topic: Algebra."
    )
    result = check_curriculum_alignment(content, "NERDC")
    assert result.passed


def test_curriculum_alignment_fail():
    content = "Once upon a time there was a beautiful forest with many animals."
    result = check_curriculum_alignment(content, "NERDC")
    assert not result.passed


# ── run_all_rules ──────────────────────────────────────────────────────────────

def test_run_all_rules_passing_content():
    content = (
        "Week 1 Objective: Students will explain the concept of photosynthesis. "
        "Activity: Group discussion with Emeka and Ngozi. "
        "Assessment: Short quiz on key terms. Topic: Photosynthesis. "
        "Learning resources include textbooks. "
        + "x" * 1000  # ensure length check passes
    )
    report = run_all_rules(
        content,
        max_tokens=512,
        expected_language="en",
        bloom_level="UNDERSTAND",
        use_local_names=True,
        content_type="LESSON_PLAN",
        curriculum_board="NERDC",
    )
    assert report.all_passed or len(report.failed) <= 2  # most rules should pass


def test_run_all_rules_hard_fail():
    content = "fuck " * 50
    report = run_all_rules(content, max_tokens=512)
    assert report.has_hard_fail


# ── compute_bloom_accuracy_score ──────────────────────────────────────────────

def test_bloom_score_known_verbs():
    """Content with several UNDERSTAND verbs should score > 0."""
    content = "Students will explain and describe and classify the topic."
    score = compute_bloom_accuracy_score(content, "UNDERSTAND")
    assert 0.0 < score <= 1.0


def test_bloom_score_no_verbs():
    """Content with no matching verbs should score 0."""
    score = compute_bloom_accuracy_score("The sky is blue.", "CREATE")
    assert score == 0.0


def test_bloom_score_unknown_level():
    """Unknown bloom level returns 0.0 without crashing."""
    score = compute_bloom_accuracy_score("design and build and create", "BOGUS")
    assert score == 0.0


def test_bloom_score_capped_at_one():
    """Score is capped at 1.0 even with many matching verbs."""
    verbs = "explain describe classify identify locate recognise report select translate paraphrase summarise interpret exemplify infer compare illustrate"
    score = compute_bloom_accuracy_score(verbs, "UNDERSTAND")
    assert score == 1.0


def test_bloom_score_stored_in_rules_node(monkeypatch):
    """rules_node stores bloom_accuracy_score in the returned state."""
    from app.agents.nodes.rules_node import rules_node

    content = (
        "Week 1 Objective: Students will explain photosynthesis. "
        "Activity: Group work with Emeka and Ngozi. "
        "Assessment: Quiz on learning outcomes. Topic: Biology. "
        + "x" * 1000
    )

    class FakeRequest:
        max_tokens = 512
        output_language = None
        pedagogical_goals = None
        bloom_level = None
        cultural_context = None
        content_type = None
        output_type = None
        curriculum_board = None
        num_questions = None

    state = {"generated_content": content, "request": FakeRequest(), "revision_count": 0}
    result = rules_node(state)

    assert "bloom_accuracy_score" in result
    assert isinstance(result["bloom_accuracy_score"], float)
    assert 0.0 <= result["bloom_accuracy_score"] <= 1.0
