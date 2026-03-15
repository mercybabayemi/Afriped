"""Revision node — regenerates content guided by judge's revision_instruction."""
from __future__ import annotations

from loguru import logger

from app.agents.state import AfriPedState
from app.core.llm import generate_text
from app.core.prompts import build_revision_prompt, BASE_SYSTEM


def revise_node(state: AfriPedState) -> AfriPedState:
    """Rewrite content based on judge's revision instruction."""
    original = state.get("generated_content") or ""
    revision_instruction = state.get("revision_instruction") or "Improve quality and curriculum alignment."
    validation_report = state.get("validation_report")
    failed_rules = validation_report.rules_failed if validation_report else []
    request = state.get("request")

    if not original:
        return {**state, "error": "Nothing to revise"}

    # Build system context
    board = "NERDC"
    level = "SSS1"
    bloom = "UNDERSTAND"
    lang = "en"
    skills = "general"

    if request:
        ba = getattr(request, "curriculum_board", None)
        if ba:
            board = ba.value if hasattr(ba, "value") else str(ba)
        lp = getattr(request, "learner_profile", None)
        if lp:
            el = getattr(lp, "education_level", None)
            if el:
                level = el.value if hasattr(el, "value") else str(el)
        else:
            el = getattr(request, "education_level", None)
            if el:
                level = el.value if hasattr(el, "value") else str(el)
        goals = getattr(request, "pedagogical_goals", None)
        if goals:
            bl = getattr(goals, "bloom_level", None)
            if bl:
                bloom = bl.value if hasattr(bl, "value") else str(bl)
            skills = ", ".join(getattr(goals, "target_skills", []) or []) or "general"
        la = getattr(request, "output_language", None)
        if la:
            lang = la.value if hasattr(la, "value") else str(la)

    system_context = BASE_SYSTEM.format(
        curriculum_board=board,
        education_level=level,
        bloom_level=bloom,
        output_language=lang,
        language_instruction="",
        target_skills=skills,
        cultural_anchors="",
    )

    messages = build_revision_prompt(
        original_content=original,
        revision_instruction=revision_instruction,
        failed_rules=failed_rules,
        system_context=system_context,
    )

    try:
        max_tokens = getattr(request, "max_tokens", 1024) if request else 1024
        revised = generate_text(messages, max_new_tokens=max_tokens)
        prev_count = state.get("revision_count", 0)
        logger.info(f"[revise_node] Revision {prev_count + 1} complete ({len(revised)} chars)")
        return {
            **state,
            "generated_content": revised,
            "revision_count": prev_count + 1,
            "revision_instruction": None,
            "error": None,
        }
    except Exception as exc:
        logger.error(f"[revise_node] Revision failed: {exc}")
        return {**state, "error": str(exc)}
