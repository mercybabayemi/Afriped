"""Rules validation node — runs 8 fast rule checks on generated content."""
from __future__ import annotations

from loguru import logger

from app.agents.state import AfriPedState
from app.schemas.common import ValidationReport, ValidationStatus
from app.validation.rules import run_all_rules, compute_bloom_accuracy_score


def rules_node(state: AfriPedState) -> AfriPedState:
    """Run all rule-based checks and write ValidationReport to state."""
    content = state.get("generated_content") or state.get("final_content") or ""
    request = state.get("request")

    if not content:
        report = ValidationReport(
            status=ValidationStatus.FAILED,
            rules_failed=["no_content"],
            notes=["No generated content to validate"],
        )
        return {**state, "validation_report": report}

    # Extract params from request
    max_tokens = getattr(request, "max_tokens", 1024) if request else 1024

    lang = "en"
    if request:
        lang_attr = getattr(request, "output_language", None)
        if lang_attr:
            lang = lang_attr.value if hasattr(lang_attr, "value") else str(lang_attr)

    bloom = "UNDERSTAND"
    if request:
        goals = getattr(request, "pedagogical_goals", None)
        if goals:
            bl = getattr(goals, "bloom_level", None)
            if bl:
                bloom = bl.value if hasattr(bl, "value") else str(bl)
        else:
            bl = getattr(request, "bloom_level", None)
            if bl:
                bloom = bl.value if hasattr(bl, "value") else str(bl)

    use_local_names = True
    if request:
        ctx = getattr(request, "cultural_context", None)
        if ctx:
            use_local_names = getattr(ctx, "use_local_names", True)

    content_type = "LESSON_PLAN"
    if request:
        ct = getattr(request, "content_type", None) or getattr(request, "output_type", None)
        if ct:
            content_type = ct.value if hasattr(ct, "value") else str(ct)

    board = "NERDC"
    if request:
        ba = getattr(request, "curriculum_board", None)
        if ba:
            board = ba.value if hasattr(ba, "value") else str(ba)

    num_questions = None
    if request:
        num_questions = getattr(request, "num_questions", None)

    rules_report = run_all_rules(
        content,
        max_tokens=max_tokens,
        expected_language=lang,
        bloom_level=bloom,
        use_local_names=use_local_names,
        content_type=content_type,
        curriculum_board=board,
        num_questions=num_questions,
    )

    prev_count = state.get("revision_count", 0)

    if rules_report.has_hard_fail:
        status = ValidationStatus.FAILED
    elif rules_report.all_passed:
        status = ValidationStatus.PASSED if prev_count == 0 else ValidationStatus.REVISED
    else:
        status = ValidationStatus.FLAGGED

    report = ValidationReport(
        status=status,
        rules_passed=rules_report.passed,
        rules_failed=rules_report.failed + rules_report.hard_failed,
        revision_count=prev_count,
        notes=rules_report.notes,
    )

    bloom_score = compute_bloom_accuracy_score(content, bloom)

    logger.info(
        f"[rules_node] Status={status} passed={len(rules_report.passed)} "
        f"failed={len(rules_report.failed)} bloom_score={bloom_score}"
    )
    return {**state, "validation_report": report, "bloom_accuracy_score": bloom_score}
