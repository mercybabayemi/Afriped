"""Pillar 1 — Curriculum generation node."""
from __future__ import annotations

from loguru import logger

from app.agents.state import AfriPedState
from app.core.llm import generate_text
from app.core.prompts import build_curriculum_prompt


def curriculum_node(state: AfriPedState) -> AfriPedState:
    """Generate curriculum content (scheme of work / term plan / scope & sequence)."""
    request = state.get("request")
    if request is None:
        return {**state, "error": "No request in state", "generated_content": None}

    rag_context = state.get("rag_context")
    max_tokens = getattr(request, "max_tokens", 256)

    try:
        messages = build_curriculum_prompt(request, rag_context=rag_context)
        content = generate_text(messages, max_new_tokens=max_tokens)
        logger.info(f"[curriculum_node] Generated {len(content)} chars")
        return {**state, "generated_content": content, "error": None}
    except Exception as exc:
        logger.error(f"[curriculum_node] Generation failed: {exc}")
        return {**state, "generated_content": None, "error": str(exc)}
