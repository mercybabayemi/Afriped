"""LLM-as-Judge node — TinyLlama 1.1B; triggered only on rule failure."""
from __future__ import annotations

from loguru import logger

from app.agents.state import AfriPedState
from app.schemas.common import ValidationReport, ValidationStatus
from app.validation.judge import run_judge, judge_passes


def judge_node(state: AfriPedState) -> AfriPedState:
    """Evaluate content with TinyLlama 1.1B and update ValidationReport."""
    content = state.get("generated_content") or state.get("final_content") or ""
    request = state.get("request")

    if not content:
        return state

    # Extract context
    content_type = "content"
    subject = "general"
    education_level = "SSS1"
    curriculum_board = "WAEC"
    bloom_level = "UNDERSTAND"
    output_language = "en"

    if request:
        ct = getattr(request, "content_type", None) or getattr(request, "output_type", None)
        if ct:
            content_type = ct.value if hasattr(ct, "value") else str(ct)

        sa = getattr(request, "subject", None)
        if sa:
            subject = sa.value if hasattr(sa, "value") else str(sa)

        ba = getattr(request, "curriculum_board", None)
        if ba:
            curriculum_board = ba.value if hasattr(ba, "value") else str(ba)

        goals = getattr(request, "pedagogical_goals", None)
        if goals:
            bl = getattr(goals, "bloom_level", None)
            if bl:
                bloom_level = bl.value if hasattr(bl, "value") else str(bl)
        else:
            bl = getattr(request, "bloom_level", None)
            if bl:
                bloom_level = bl.value if hasattr(bl, "value") else str(bl)

        lang = getattr(request, "output_language", None)
        if lang:
            output_language = lang.value if hasattr(lang, "value") else str(lang)

        lp = getattr(request, "learner_profile", None)
        if lp:
            el = getattr(lp, "education_level", None)
            if el:
                education_level = el.value if hasattr(el, "value") else str(el)
        else:
            el = getattr(request, "education_level", None)
            if el:
                education_level = el.value if hasattr(el, "value") else str(el)

    prev_report = state.get("validation_report")
    failed_rules = prev_report.rules_failed if prev_report else []

    avg_score, dimension_scores, revision_instruction = run_judge(
        content,
        content_type=content_type,
        subject=subject,
        education_level=education_level,
        curriculum_board=curriculum_board,
        bloom_level=bloom_level,
        output_language=output_language,
        failed_rules=failed_rules,
    )

    passes = judge_passes(avg_score, dimension_scores)
    prev_count = state.get("revision_count", 0)

    if passes:
        status = ValidationStatus.FLAGGED  # rule-failed but judge approved
    else:
        status = ValidationStatus.FAILED

    report = ValidationReport(
        status=status,
        rules_passed=prev_report.rules_passed if prev_report else [],
        rules_failed=failed_rules,
        judge_score=avg_score,
        judge_dimensions=dimension_scores,
        revision_count=prev_count,
        notes=(prev_report.notes if prev_report else []),
    )

    logger.info(f"[judge_node] avg={avg_score:.2f} passes={passes} revision_instr={'yes' if revision_instruction else 'no'}")

    return {
        **state,
        "validation_report": report,
        "revision_instruction": revision_instruction if not passes else None,
    }
