"""ChromaDB vector store setup and persistence."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from loguru import logger

from app.core.config import settings
from app.rag.embeddings import get_embeddings

COLLECTION_NAME = "afriped_curriculum"


def _get_chroma_client() -> chromadb.PersistentClient:
    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(persist_dir),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    """Return a singleton Chroma vectorstore backed by distilgpt2 embeddings."""
    logger.info(f"Connecting to ChromaDB at {settings.chroma_persist_dir}")
    client = _get_chroma_client()
    vectorstore = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
    )
    count = vectorstore._collection.count()
    logger.info(f"ChromaDB collection '{COLLECTION_NAME}' has {count} documents")
    return vectorstore


def add_documents(
    texts: List[str],
    metadatas: List[dict],
    ids: Optional[List[str]] = None,
) -> None:
    """Add text chunks to the vector store."""
    vs = get_vectorstore()
    vs.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    logger.info(f"Added {len(texts)} chunks to ChromaDB")


def get_document_count() -> int:
    """Return total number of stored chunks."""
    try:
        vs = get_vectorstore()
        return vs._collection.count()
    except Exception:
        return 0
