"""Hierarchical semantic chunker for West African curriculum documents."""
from __future__ import annotations

import re
from typing import List, Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger


# Headers that signal a new curriculum hierarchy level
CURRICULUM_HEADER_PATTERNS = [
    re.compile(r"^\s*(UNIT|TOPIC|WEEK|TERM|CHAPTER|SECTION|OBJECTIVE)\s*\d*[\s:\-]", re.IGNORECASE),
    re.compile(r"^\s*\d+\.\s+[A-Z]"),  # numbered headings
    re.compile(r"^[A-Z][A-Z\s]{4,}$"),  # ALL-CAPS headings
]

CHUNK_SIZE = 500       # target tokens (approx. 4 chars/token → ~2000 chars)
CHUNK_OVERLAP = 80     # overlap in tokens
CHARS_PER_TOKEN = 4


def _is_header(line: str) -> bool:
    return any(pat.match(line.strip()) for pat in CURRICULUM_HEADER_PATTERNS)


def _extract_hierarchy_header(text: str) -> Optional[str]:
    """Find the nearest curriculum header in the text block."""
    for line in text.splitlines():
        if _is_header(line):
            return line.strip()
    return None


def chunk_documents(
    docs: List[Document],
    *,
    metadata_overrides: Optional[dict] = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """Split documents into semantically coherent chunks.

    Strategy:
    1. Detect UNIT/TOPIC/WEEK/TERM headers to preserve hierarchy context.
    2. Prepend the nearest parent header to each chunk for retrieval context.
    3. Fall back to RecursiveCharacterTextSplitter for non-hierarchical text.
    """
    char_size = chunk_size * CHARS_PER_TOKEN
    char_overlap = chunk_overlap * CHARS_PER_TOKEN

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=char_size,
        chunk_overlap=char_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: List[Document] = []

    for doc in docs:
        text = doc.page_content
        base_meta = {**doc.metadata}
        if metadata_overrides:
            base_meta.update(metadata_overrides)

        # Attempt hierarchical split
        current_header: Optional[str] = None
        sections: List[tuple[Optional[str], str]] = []
        current_lines: List[str] = []

        for line in text.splitlines():
            if _is_header(line):
                if current_lines:
                    sections.append((current_header, "\n".join(current_lines)))
                current_header = line.strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_header, "\n".join(current_lines)))

        if not sections:
            # No hierarchy detected — plain split
            split_docs = splitter.split_documents([doc])
            for sd in split_docs:
                sd.metadata.update(base_meta)
            chunks.extend(split_docs)
            continue

        for header, section_text in sections:
            if not section_text.strip():
                continue
            # Prepend header context to each sub-chunk for retrieval
            prefix = f"[Context: {header}]\n" if header else ""
            prefixed = prefix + section_text

            sub_chunks = splitter.split_text(prefixed)
            for sub in sub_chunks:
                meta = {**base_meta}
                if header:
                    meta["section_header"] = header
                chunks.append(Document(page_content=sub, metadata=meta))

    logger.info(f"Chunked {len(docs)} documents → {len(chunks)} chunks")
    return chunks


def infer_metadata(doc: Document, source_file: str = "") -> dict:
    """Infer curriculum metadata (board, subject, level, topic) from text heuristics."""
    text = doc.page_content.lower()
    meta: dict = {"source_file": source_file or doc.metadata.get("source_file", "unknown")}

    # Board detection
    board_patterns = {
        "NERDC": ["nerdc", "national educational research"],
        "WAEC": ["waec", "west african examination"],
        "NECO": ["neco", "national examination council"],
        "NABTEB": ["nabteb"],
        "UBEC": ["ubec", "universal basic education"],
        "WAEC_GH": ["waec gh", "waec ghana"],
        "GES_GH": ["ges ghana", "ghana education service"],
        "BECE_GH": ["bece", "basic education certificate"],
    }
    for board, keywords in board_patterns.items():
        if any(kw in text for kw in keywords):
            meta["board"] = board
            break
    else:
        meta["board"] = "CUSTOM"

    # Level detection
    level_patterns = {
        "PRIMARY_1_3": ["primary 1", "primary 2", "primary 3"],
        "PRIMARY_4_6": ["primary 4", "primary 5", "primary 6"],
        "JSS1": ["jss1", "jss 1", "junior secondary 1"],
        "JSS2": ["jss2", "jss 2", "junior secondary 2"],
        "JSS3": ["jss3", "jss 3", "junior secondary 3"],
        "SSS1": ["sss1", "sss 1", "senior secondary 1", "ss1"],
        "SSS2": ["sss2", "sss 2", "senior secondary 2", "ss2"],
        "SSS3": ["sss3", "sss 3", "senior secondary 3", "ss3"],
        "TERTIARY": ["university", "polytechnic", "tertiary"],
    }
    for level, keywords in level_patterns.items():
        if any(kw in text for kw in keywords):
            meta["level"] = level
            break
    else:
        meta["level"] = "UNSPECIFIED"

    return meta
