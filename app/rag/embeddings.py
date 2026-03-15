"""Embedding wrapper: all-MiniLM-L6-v2 (lightweight, CPU-friendly sentence embeddings)."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a globally cached HuggingFaceEmbeddings instance.

    Loaded once per process; subsequent calls return the same object.
    """
    logger.info(f"Loading embedding model: {settings.embedding_model_id}")
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.embedding_model_id,
        model_kwargs={"device": "cuda" if _cuda_available() else "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("Embedding model loaded")
    return embeddings


def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    return get_embeddings().embed_query(text)


def embed_documents(texts: List[str]) -> List[List[float]]:
    """Embed a batch of document strings."""
    return get_embeddings().embed_documents(texts)


def _cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
