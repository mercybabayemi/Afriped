"""Edge-condition functions for the LangGraph StateGraph.

Kept in a separate module so unit tests can import routing logic without
pulling in the full langgraph dependency.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.agents.state import AfriPedState

# ── Gate thresholds ────────────────────────────────────────────────────────────
# Empirically derived via research/evaluation/threshold_ablation.py
# (bloom_accuracy_ablation sweep against the golden set).
# Interpretation (Anderson & Krathwohl 2001): content must contain ≥ 70% of
# the expected Bloom-level verb set to pass without judge review.
# Update this value from threshold_ablation results["recommended_bloom_accuracy_gate"]
# after each golden-set refresh.
BLOOM_ACCURACY_GATE: float = 0.70


def after_rules(state: "AfriPedState") -> Literal["end", "judge"]:
    report = state.get("validation_report")
    if report is None:
        return "end"
    from app.schemas.common import ValidationStatus

    if report.status == ValidationStatus.FAILED:
        # Hard fail (e.g. explicit content) — no judge needed
        if any("explicit" in r or "profanity" in r for r in report.rules_failed):
            return "end"
        return "judge"

    if report.status in (ValidationStatus.PASSED, ValidationStatus.REVISED):
        # All binary rules passed — apply the bloom accuracy gate.
        # Content that passes rule checks but lacks sufficient cognitive-level
        # verb coverage is sent to the judge for deeper evaluation rather than
        # silently accepted.  Threshold is empirically selected via
        # research/evaluation/threshold_ablation.py (bloom_accuracy_ablation).
        bloom_score = state.get("bloom_accuracy_score")
        if bloom_score is not None and bloom_score < BLOOM_ACCURACY_GATE:
            return "judge"
        return "end"

    return "judge"


def after_judge(state: "AfriPedState") -> Literal["end", "revise"]:
    from app.schemas.common import ValidationStatus
    report = state.get("validation_report")
    revision_count = state.get("revision_count", 0)

    if report and report.status == ValidationStatus.FLAGGED:
        return "end"  # judge approved despite rule failure

    if revision_count >= 2:
        return "end"  # max retries reached

    revision_instr = state.get("revision_instruction")
    if revision_instr:
        return "revise"

    return "end"
