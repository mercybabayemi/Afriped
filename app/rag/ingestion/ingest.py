"""CLI ingestion pipeline: python -m app.rag.ingestion.ingest

Usage:
    python -m app.rag.ingestion.ingest --input-dir data/raw --board NERDC --subject mathematics --level SSS1
    python -m app.rag.ingestion.ingest --synthetic --board NERDC --subject mathematics --level SSS1
    python -m app.rag.ingestion.ingest --hf-dataset --dataset castorini/mr-tydi --language english
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document
from loguru import logger

# Ensure project root is on path when run as __main__
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


from app.rag.ingestion.chunker import chunk_documents, infer_metadata
from app.rag.ingestion.loader import load_directory, load_file
from app.rag.vectorstore import add_documents, get_vectorstore


def _doc_id(text: str, meta: dict) -> str:
    """Deterministic ID from content + source so re-ingestion is idempotent."""
    key = text[:200] + meta.get("source_file", "") + meta.get("board", "")
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def ingest_files(
    input_dir: Optional[Path] = None,
    *,
    board: str = "NERDC",
    subject: str = "general",
    level: str = "SSS1",
    file_path: Optional[Path] = None,
) -> int:
    """Load, chunk, and store curriculum documents.

    Returns the number of chunks added.
    """
    docs: List[Document] = []
    if file_path:
        docs = load_file(file_path)
    elif input_dir:
        docs = load_directory(input_dir)
    else:
        raise ValueError("Provide either input_dir or file_path")

    if not docs:
        logger.warning("No documents loaded; nothing to ingest")
        return 0

    metadata_overrides = {"board": board, "subject": subject, "level": level}
    chunks = chunk_documents(docs, metadata_overrides=metadata_overrides)

    texts = [c.page_content for c in chunks]
    metadatas = []
    ids = []

    for chunk in chunks:
        meta = {**chunk.metadata}
        # Infer any missing fields
        inferred = infer_metadata(chunk)
        for k, v in inferred.items():
            meta.setdefault(k, v)
        metadatas.append(meta)
        ids.append(_doc_id(chunk.page_content, meta))

    add_documents(texts=texts, metadatas=metadatas, ids=ids)
    logger.success(f"Ingested {len(chunks)} chunks [{board} | {subject} | {level}]")
    return len(chunks)


def ingest_synthetic(
    board: str = "NERDC",
    subject: str = "mathematics",
    level: str = "SSS1",
) -> int:
    """Bootstrap vector store with synthetic Phi-3-generated curriculum outlines."""
    logger.info(f"Generating synthetic bootstrap data for {board} {subject} {level}")

    try:
        from app.core.llm import generate_text
    except Exception as exc:
        logger.error(f"Cannot load LLM for synthetic generation: {exc}")
        return 0

    prompt = [
        {"role": "system", "content": "You are a Nigerian curriculum expert."},
        {"role": "user", "content": (
            f"Generate a detailed NERDC scheme of work for {subject} at {level} level. "
            "Include topics, sub-topics, learning objectives, and week numbers for a 13-week term."
        )},
    ]

    text = generate_text(prompt, max_new_tokens=1024)
    if not text.strip():
        logger.warning("Synthetic generation returned empty text")
        return 0

    doc = Document(
        page_content=text,
        metadata={"source_file": f"synthetic_{board}_{subject}_{level}.txt"},
    )
    meta_overrides = {"board": board, "subject": subject, "level": level, "synthetic": True}
    chunks = chunk_documents([doc], metadata_overrides=meta_overrides)

    texts = [c.page_content for c in chunks]
    metadatas = [{**c.metadata} for c in chunks]
    ids = [_doc_id(c.page_content, c.metadata) for c in chunks]

    add_documents(texts=texts, metadatas=metadatas, ids=ids)
    logger.success(f"Synthetic bootstrap: {len(chunks)} chunks added")
    return len(chunks)


def ingest_hf_dataset(
    dataset_name: str = "castorini/mr-tydi",
    language: str = "english",
    max_examples: int = 500,
) -> int:
    """Ingest passages from a HuggingFace dataset."""
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        logger.error("datasets library not installed. Run: pip install datasets")
        return 0

    logger.info(f"Loading HF dataset {dataset_name} ({language})")
    try:
        ds = load_dataset(dataset_name, language, split="train", streaming=True)
    except Exception as exc:
        logger.error(f"Failed to load dataset {dataset_name}: {exc}")
        return 0

    docs: List[Document] = []
    for i, example in enumerate(ds):
        if i >= max_examples:
            break
        text = example.get("passage", "") or example.get("text", "") or ""
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={"source_file": f"hf:{dataset_name}", "synthetic": False},
            ))

    if not docs:
        logger.warning("No usable texts from HF dataset")
        return 0

    chunks = chunk_documents(docs)
    texts = [c.page_content for c in chunks]
    metadatas = [{**c.metadata} for c in chunks]
    ids = [_doc_id(c.page_content, c.metadata) for c in chunks]
    add_documents(texts=texts, metadatas=metadatas, ids=ids)
    logger.success(f"HF dataset: {len(chunks)} chunks added")
    return len(chunks)


# ── Nigerian education datasets (from local Parquet cache) ─────────────────────

_NIGERIAN_CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "nigerian_education"

_NIGERIAN_REGISTRY: dict[str, dict] = {
    "vocational":            {"board": "NABTEB", "subject": "trade_skill",     "level": "VOCATIONAL_ADVANCED"},
    "continuous_assessment": {"board": "NERDC",  "subject": "general",         "level": "SSS1"},
    "digital_learning":      {"board": "NERDC",  "subject": "digital_literacy", "level": "SSS1"},
    "online_exams":          {"board": "WAEC",   "subject": "general",         "level": "SSS2"},
    "learning_materials":    {"board": "NERDC",  "subject": "general",         "level": "JSS3"},
    "teacher_training":      {"board": "NERDC",  "subject": "general",         "level": "TEACHER_TRAINING"},
    "special_needs":         {"board": "UBEC",   "subject": "general",         "level": "PRIMARY_4_6"},
}


def ingest_nigerian_education(
    dataset_keys: Optional[List[str]] = None,
) -> int:
    """Ingest cached Nigerian education Parquet files into ChromaDB.

    Downloads must have been run first via:
        python research/datasets/download_hf_datasets.py --all --save-only

    Args:
        dataset_keys: list of keys from _NIGERIAN_REGISTRY, or None for all.

    Returns:
        Total number of chunks ingested.
    """
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        logger.error("Run: pip install pandas pyarrow")
        return 0

    keys = dataset_keys or list(_NIGERIAN_REGISTRY.keys())
    total = 0

    for key in keys:
        parquet_path = _NIGERIAN_CACHE_DIR / key / f"{key}.parquet"
        if not parquet_path.exists():
            logger.warning(f"Cache miss: {key} — run download_hf_datasets.py first")
            continue

        cfg = _NIGERIAN_REGISTRY[key]
        df = pd.read_parquet(parquet_path)
        logger.info(f"Ingesting {key} ({len(df):,} rows) from cache...")

        docs: List[Document] = []
        for _, row in df.iterrows():
            text = str(row.get("text", ""))
            if len(text) < 20:
                continue
            meta = {
                "source": f"nigerian_education:{key}",
                "board": str(row.get("board", cfg["board"])),
                "subject": str(row.get("subject", cfg["subject"])),
                "level": str(row.get("level", cfg["level"])),
                "topic": str(row.get("topic", "")),
                "dataset_key": key,
                "synthetic": False,
            }
            docs.append(Document(page_content=text, metadata=meta))

        if not docs:
            logger.warning(f"No valid docs for {key}")
            continue

        chunks = chunk_documents(docs)
        texts     = [c.page_content for c in chunks]
        metadatas = [{**c.metadata} for c in chunks]
        ids       = [_doc_id(c.page_content, c.metadata) for c in chunks]

        add_documents(texts=texts, metadatas=metadatas, ids=ids)
        logger.success(f"Ingested {len(chunks):,} chunks from {key}")
        total += len(chunks)

    return total


# ── CLI ────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AfriPed RAG ingestion pipeline")
    p.add_argument("--input-dir", type=Path, help="Directory of PDF/DOCX curriculum files")
    p.add_argument("--file", type=Path, help="Single file to ingest")
    p.add_argument("--board", default="NERDC", help="Curriculum board tag")
    p.add_argument("--subject", default="general", help="Subject tag")
    p.add_argument("--level", default="SSS1", help="Education level tag")
    p.add_argument("--synthetic", action="store_true", help="Generate synthetic bootstrap data")
    p.add_argument("--hf-dataset", action="store_true", help="Ingest from a HuggingFace dataset")
    p.add_argument("--dataset", default="castorini/mr-tydi", help="HF dataset name")
    p.add_argument("--language", default="english", help="HF dataset language subset")
    p.add_argument("--max-examples", type=int, default=500, help="Max HF examples to ingest")
    p.add_argument("--nigerian-education", action="store_true",
                   help="Ingest cached Nigerian education datasets (run download_hf_datasets.py first)")
    p.add_argument("--nigerian-datasets", nargs="+", choices=list(_NIGERIAN_REGISTRY.keys()),
                   help="Specific Nigerian dataset keys to ingest (default: all cached)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    total = 0

    if args.synthetic:
        total += ingest_synthetic(board=args.board, subject=args.subject, level=args.level)
    elif args.nigerian_education:
        total += ingest_nigerian_education(dataset_keys=args.nigerian_datasets)
    elif args.hf_dataset:
        total += ingest_hf_dataset(args.dataset, args.language, args.max_examples)
    elif args.file:
        total += ingest_files(file_path=args.file, board=args.board, subject=args.subject, level=args.level)
    elif args.input_dir:
        total += ingest_files(args.input_dir, board=args.board, subject=args.subject, level=args.level)
    else:
        print("No action specified. Use --help for usage.")
        sys.exit(1)

    print(f"\n✓ Total chunks ingested: {total}")
