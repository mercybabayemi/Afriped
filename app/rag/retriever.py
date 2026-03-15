"""Metadata-filtered RAG retrieval."""
from __future__ import annotations

from typing import List, Optional, Tuple

from langchain_core.documents import Document
from loguru import logger

from app.rag.vectorstore import get_vectorstore
from app.schemas.common import RAGMetadata


def retrieve(
    query: str,
    *,
    board: Optional[str] = None,
    subject: Optional[str] = None,
    level: Optional[str] = None,
    top_k: int = 4,
) -> Tuple[str, RAGMetadata]:
    """Retrieve relevant curriculum chunks with optional metadata filtering.

    Args:
        query: The search query (e.g., topic or learning objective).
        board: Curriculum board filter (e.g., "NERDC", "WAEC").
        subject: Subject filter (e.g., "mathematics").
        level: Education level filter (e.g., "SSS1").
        top_k: Number of chunks to retrieve.

    Returns:
        Tuple of (concatenated context string, RAGMetadata).
    """
    vs = get_vectorstore()

    # Build metadata filter
    where_clauses = []
    if board:
        where_clauses.append({"board": board})
    if subject:
        where_clauses.append({"subject": subject})
    if level:
        where_clauses.append({"level": level})

    where: Optional[dict] = None
    if len(where_clauses) == 1:
        where = where_clauses[0]
    elif len(where_clauses) > 1:
        where = {"$and": where_clauses}

    try:
        if where:
            results: List[Tuple[Document, float]] = vs.similarity_search_with_score(
                query, k=top_k, filter=where
            )
        else:
            results = vs.similarity_search_with_score(query, k=top_k)
    except Exception as exc:
        logger.warning(f"RAG retrieval failed: {exc}; returning empty context")
        return "", RAGMetadata(chunks_used=0, sources=[], similarity_scores=[])

    if not results:
        logger.info("No RAG chunks found for query")
        return "", RAGMetadata(chunks_used=0, sources=[], similarity_scores=[])

    docs, scores = zip(*results)
    context_parts = []
    sources = []
    similarity_scores = []
    synthetic_count = 0

    for doc, score in zip(docs, scores):
        meta = doc.metadata or {}
        source = meta.get("source_file", "unknown")
        if meta.get("synthetic"):
            synthetic_count += 1

        header = f"[Source: {source} | Board: {meta.get('board','?')} | Subject: {meta.get('subject','?')} | Level: {meta.get('level','?')}]"
        context_parts.append(f"{header}\n{doc.page_content}")
        sources.append(source)
        similarity_scores.append(float(score))

    context = "\n\n".join(context_parts)
    rag_meta = RAGMetadata(
        chunks_used=len(docs),
        sources=list(set(sources)),
        similarity_scores=similarity_scores,
        synthetic_chunks=synthetic_count,
    )

    logger.info(f"Retrieved {len(docs)} chunks (synthetic: {synthetic_count})")
    return context, rag_meta
