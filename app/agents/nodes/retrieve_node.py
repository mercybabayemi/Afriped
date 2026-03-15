"""RAG retrieval node — runs before each generation pillar (1-3)."""
from __future__ import annotations

from loguru import logger

from app.agents.state import AfriPedState
from app.rag.retriever import retrieve


def retrieve_node(state: AfriPedState) -> AfriPedState:
    """Retrieve relevant curriculum chunks and store in state."""
    request = state.get("request")
    if request is None:
        return {**state, "rag_context": None, "rag_metadata": None}

    # Build query from topic / subject / objectives
    pillar = state.get("pillar", "content")
    if pillar == "curriculum":
        topic = getattr(request, "subject", {})
        topic_str = topic.value if hasattr(topic, "value") else str(topic)
        query = f"{topic_str} curriculum scheme of work {getattr(request, 'education_level', '')}"
    elif pillar == "assessment":
        query = f"{getattr(request, 'topic', '')} {getattr(request, 'subject', '')} assessment questions"
    else:
        query = f"{getattr(request, 'topic', '')} {getattr(request, 'subject', '')}"

    board = None
    subject = None
    level = None

    board_attr = getattr(request, "curriculum_board", None)
    if board_attr:
        board = board_attr.value if hasattr(board_attr, "value") else str(board_attr)

    subject_attr = getattr(request, "subject", None)
    if subject_attr:
        subject = subject_attr.value if hasattr(subject_attr, "value") else str(subject_attr)

    level_attr = None
    if hasattr(request, "education_level"):
        level_attr = request.education_level
    elif hasattr(request, "learner_profile") and request.learner_profile:
        level_attr = request.learner_profile.education_level
    if level_attr:
        level = level_attr.value if hasattr(level_attr, "value") else str(level_attr)

    top_k = getattr(request, "rag_top_k", 4)

    try:
        context, rag_meta = retrieve(
            query,
            board=board,
            subject=subject,
            level=level,
            top_k=top_k,
        )
        logger.info(f"[retrieve_node] Retrieved {rag_meta.chunks_used} chunks")
        return {**state, "rag_context": context or None, "rag_metadata": rag_meta}
    except Exception as exc:
        logger.warning(f"[retrieve_node] RAG failed: {exc}")
        return {**state, "rag_context": None, "rag_metadata": None}
