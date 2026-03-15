"""Tests for after_rules routing — verifies the bloom accuracy gate."""
import pytest

from app.agents.routing import after_rules, BLOOM_ACCURACY_GATE
from app.schemas.common import ValidationReport, ValidationStatus


def _state(status: ValidationStatus, bloom_score=None, rules_failed=None):
    report = ValidationReport(
        status=status,
        rules_failed=rules_failed or [],
    )
    state = {"validation_report": report}
    if bloom_score is not None:
        state["bloom_accuracy_score"] = bloom_score
    return state


# ── PASSED status ──────────────────────────────────────────────────────────────

def test_passed_high_bloom_goes_to_end():
    """PASSED + bloom above gate → end."""
    state = _state(ValidationStatus.PASSED, bloom_score=BLOOM_ACCURACY_GATE)
    assert after_rules(state) == "end"


def test_passed_bloom_above_gate_goes_to_end():
    """PASSED + bloom well above gate → end."""
    state = _state(ValidationStatus.PASSED, bloom_score=1.0)
    assert after_rules(state) == "end"


def test_passed_bloom_below_gate_goes_to_judge():
    """PASSED + bloom below gate → judge (content too shallow)."""
    state = _state(ValidationStatus.PASSED, bloom_score=BLOOM_ACCURACY_GATE - 0.01)
    assert after_rules(state) == "judge"


def test_passed_no_bloom_score_goes_to_end():
    """PASSED + no bloom score in state → end (score unavailable, binary rules passed)."""
    state = _state(ValidationStatus.PASSED, bloom_score=None)
    assert after_rules(state) == "end"


# ── REVISED status ────────────────────────────────────────────────────────────

def test_revised_high_bloom_goes_to_end():
    state = _state(ValidationStatus.REVISED, bloom_score=0.80)
    assert after_rules(state) == "end"


def test_revised_low_bloom_goes_to_judge():
    state = _state(ValidationStatus.REVISED, bloom_score=0.20)
    assert after_rules(state) == "judge"


# ── FAILED status ─────────────────────────────────────────────────────────────

def test_failed_explicit_content_goes_to_end():
    """Hard fail (explicit content) → end without judge."""
    state = _state(ValidationStatus.FAILED, rules_failed=["explicit_content"])
    assert after_rules(state) == "end"


def test_failed_profanity_goes_to_end():
    """Hard fail (profanity) → end without judge."""
    state = _state(ValidationStatus.FAILED, rules_failed=["profanity_detected"])
    assert after_rules(state) == "end"


def test_failed_soft_goes_to_judge():
    """Soft fail (e.g. cultural flag) → judge for review."""
    state = _state(ValidationStatus.FAILED, rules_failed=["cultural_flag"])
    assert after_rules(state) == "judge"


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_no_report_goes_to_end():
    """No validation report → end (nothing to judge)."""
    assert after_rules({}) == "end"


def test_flagged_status_goes_to_judge():
    """FLAGGED status → judge."""
    state = _state(ValidationStatus.FLAGGED)
    assert after_rules(state) == "judge"
