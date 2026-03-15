"""Pillar 2 — Content generation node (lessons, worksheets, stories, etc.)."""
from __future__ import annotations

from loguru import logger

from app.agents.state import AfriPedState
from app.core.llm import generate_text
from app.core.prompts import build_content_prompt


def generate_node(state: AfriPedState) -> AfriPedState:
    """Generate educational content for Pillar 2."""
    request = state.get("request")
    if request is None:
        return {**state, "error": "No request in state", "generated_content": None}

    rag_context = state.get("rag_context")
    max_tokens = getattr(request, "max_tokens", 256)

    try:
        messages = build_content_prompt(request, rag_context=rag_context)
        content = generate_text(messages, max_new_tokens=max_tokens)
        logger.info(f"[generate_node] Generated {len(content)} chars")
        return {**state, "generated_content": content, "error": None}
    except Exception as exc:
        logger.error(f"[generate_node] Generation failed: {exc}")
        return {**state, "generated_content": None, "error": str(exc)}
