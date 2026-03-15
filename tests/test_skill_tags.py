"""Tests for the Enum Skill Library and auto-tagging."""
import pytest

from app.skills.library import SkillLibrary, get_skill_library, LIBRARY_PATH


# ── Library loading ────────────────────────────────────────────────────────────

def test_library_loads():
    lib = SkillLibrary()
    assert lib.total > 0


def test_library_has_four_domains():
    lib = get_skill_library()
    assert set(lib.domains) == {"technical", "behavioral", "cognitive", "language"}


def test_library_total_skills():
    lib = get_skill_library()
    assert lib.total >= 80  # at minimum 80 skills


def test_get_by_domain_cognitive():
    lib = get_skill_library()
    cognitive = lib.get_by_domain("cognitive")
    assert len(cognitive) > 0
    assert all(s.skill_domain == "cognitive" for s in cognitive)


def test_get_by_domain_case_insensitive():
    lib = get_skill_library()
    assert len(lib.get_by_domain("TECHNICAL")) > 0


def test_get_by_name():
    lib = get_skill_library()
    item = lib.get_by_name("critical thinking")
    assert item is not None
    assert item.skill_domain == "cognitive"


def test_get_by_name_not_found():
    lib = get_skill_library()
    assert lib.get_by_name("nonexistent skill xyz") is None


def test_get_children():
    lib = get_skill_library()
    children = lib.get_children("Critical Thinking")
    names = [c.skill_name for c in children]
    assert "Logical Reasoning" in names
    assert "Deductive Reasoning" in names


# ── match_from_text ────────────────────────────────────────────────────────────

def test_match_from_text_basic():
    lib = get_skill_library()
    text = "Students will analyse data using statistical methods and create visualisations."
    tags = lib.match_from_text(text)
    assert len(tags) > 0


def test_match_from_text_critical_thinking():
    lib = get_skill_library()
    text = "This lesson develops critical thinking and logical reasoning skills."
    tags = lib.match_from_text(text)
    skill_names = {t.skill_name for t in tags}
    assert "Critical Thinking" in skill_names or "Logical Reasoning" in skill_names


def test_match_from_text_domain_filter():
    lib = get_skill_library()
    text = "Students will explain grammar, analyse data, and demonstrate leadership."
    tags_all = lib.match_from_text(text)
    tags_lang = lib.match_from_text(text, domain_filter="language")
    assert all(t.skill_domain == "language" for t in tags_lang)


def test_match_from_text_empty():
    lib = get_skill_library()
    assert lib.match_from_text("") == []


def test_match_from_targets():
    lib = get_skill_library()
    tags = lib.match_from_targets(["Critical Thinking", "Problem Solving", "Bogus Skill"])
    names = {t.skill_name for t in tags}
    assert "Critical Thinking" in names
    assert "Problem Solving" in names
    # Bogus skill silently skipped
    assert len(tags) == 2


def test_match_from_targets_empty():
    lib = get_skill_library()
    assert lib.match_from_targets([]) == []


# ── Skill library JSON integrity ───────────────────────────────────────────────

def test_skill_library_json_exists():
    assert LIBRARY_PATH.exists(), f"skill_library.json not found at {LIBRARY_PATH}"


def test_all_skills_have_domain():
    lib = get_skill_library()
    for item in lib.get_all():
        assert item.skill_domain in {"technical", "behavioral", "cognitive", "language"}


def test_child_skills_have_parent():
    lib = get_skill_library()
    all_names = {i.skill_name for i in lib.get_all()}
    for item in lib.get_all():
        if item.parent_skill is not None:
            assert item.parent_skill in all_names, (
                f"Parent '{item.parent_skill}' for '{item.skill_name}' not found in library"
            )


def test_singleton():
    lib1 = get_skill_library()
    lib2 = get_skill_library()
    assert lib1 is lib2
