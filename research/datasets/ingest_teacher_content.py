"""Ingest real teacher lesson notes into AfriPed ChromaDB.

Source: ~/Downloads/Teachers Content/
Files:  77 DOCX lesson notes (JSS1-3, SS1-3 × ICT + Data Processing)
School: ENGREG HIGH SCHOOL, Pedro Shomolu, Lagos (2024/2025 session)

Usage:
    python research/datasets/ingest_teacher_content.py
    python research/datasets/ingest_teacher_content.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# ── project root on path ───────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from langchain_core.documents import Document
from loguru import logger

from app.rag.ingestion.chunker import chunk_documents
from app.rag.vectorstore import add_documents

# Repo-committed corpus (works on HuggingFace Spaces and any clone)
_REPO_CORPUS = ROOT / "corpus" / "teacher_content"
# Local dev fallback
_LOCAL_DOWNLOADS = Path.home() / "Downloads" / "Teachers Content"

TEACHER_CONTENT_DIR = _REPO_CORPUS if _REPO_CORPUS.exists() else _LOCAL_DOWNLOADS

# ── filename → metadata mapping ────────────────────────────────────────────────
# Filenames follow the pattern:  <LEVEL> WEEK <N> <SUBJECT>.docx
# e.g. "JSS1 WEEK 1 ICT.docx", "SS2 WEEK 3 DATA PROCESSING.docx"

LEVEL_MAP = {
    "JSS1": "JSS1",
    "JSS2": "JSS2",
    "JSS3": "JSS3",
    "SS1":  "SSS1",
    "SS2":  "SSS2",
    "SS3":  "SSS3",
    "SSS3": "SSS3",  # a few files use SSS3 directly
}

SUBJECT_MAP = {
    "ICT":             "computer_studies",
    "DATA PROCESSING": "data_processing",
}

FILENAME_RE = re.compile(
    r"^(JSS\d|SSS?\d)\s+WEEK\s+(\d+)\s+(ICT|DATA PROCESSING)\.(docx|txt)$",
    re.IGNORECASE,
)


def parse_filename(name: str) -> Optional[dict]:
    """Return metadata dict from filename, or None if not parseable."""
    m = FILENAME_RE.match(name)
    if not m:
        return None
    raw_level, week, raw_subject = m.group(1).upper(), m.group(2), m.group(3).upper()
    return {
        "level":   LEVEL_MAP.get(raw_level, raw_level),
        "week":    f"week_{week}",
        "subject": SUBJECT_MAP.get(raw_subject, raw_subject.lower()),
    }


# ── DOCX reader (no python-docx dependency needed — uses stdlib zipfile) ───────

_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def read_docx_text(path: Path) -> str:
    """Extract all text from a DOCX using stdlib (no python-docx required)."""
    try:
        with zipfile.ZipFile(path) as z:
            xml_bytes = z.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        paragraphs = root.findall(".//w:p", _NS)
        lines = []
        for para in paragraphs:
            runs = para.findall(".//w:t", _NS)
            line = "".join(r.text or "" for r in runs)
            if line.strip():
                lines.append(line.strip())
        return "\n".join(lines)
    except Exception as exc:
        logger.error(f"Failed to read {path.name}: {exc}")
        return ""


def _doc_id(text: str, meta: dict) -> str:
    key = text[:200] + meta.get("source_file", "") + meta.get("level", "")
    return hashlib.sha256(key.encode()).hexdigest()[:16]


# ── main ingestion ─────────────────────────────────────────────────────────────

def ingest_teacher_content(dry_run: bool = False) -> int:
    if not TEACHER_CONTENT_DIR.exists():
        logger.error(f"Directory not found: {TEACHER_CONTENT_DIR}")
        return 0

    # Prefer pre-extracted .txt files (no binary — works on HF Spaces);
    # fall back to .docx if only those are present (local dev with originals).
    txt_files  = sorted(TEACHER_CONTENT_DIR.glob("*.txt"))
    docx_files = sorted(TEACHER_CONTENT_DIR.glob("*.docx"))
    files = txt_files if txt_files else docx_files
    logger.info(f"Found {len(files)} {'TXT' if txt_files else 'DOCX'} files in {TEACHER_CONTENT_DIR}")

    total_chunks = 0
    skipped = []

    for path in files:
        meta_from_name = parse_filename(path.name)
        if not meta_from_name:
            logger.warning(f"Could not parse filename: {path.name} — skipping")
            skipped.append(path.name)
            continue

        if path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            text = read_docx_text(path)
        if not text.strip():
            logger.warning(f"Empty content: {path.name} — skipping")
            skipped.append(path.name)
            continue

        metadata = {
            "source_file":   path.name,
            "source":        "teacher_content_engreg_2024",
            "school":        "ENGREG HIGH SCHOOL",
            "location":      "Pedro Shomolu, Lagos",
            "session":       "2024/2025",
            "board":         "NERDC",
            "content_type":  "lesson_note",
            "real_teacher":  True,
            **meta_from_name,
        }

        doc = Document(page_content=text, metadata=metadata)
        chunks = chunk_documents([doc], metadata_overrides=metadata)

        logger.info(
            f"  {path.name} → {len(chunks)} chunks "
            f"[{metadata['level']} | {metadata['subject']} | {metadata['week']}]"
        )

        if not dry_run:
            texts = [c.page_content for c in chunks]
            metas = [{**c.metadata} for c in chunks]
            ids   = [_doc_id(c.page_content, c.metadata) for c in chunks]
            add_documents(texts=texts, metadatas=metas, ids=ids)

        total_chunks += len(chunks)

    logger.success(
        f"\n{'[DRY RUN] ' if dry_run else ''}Ingested {total_chunks} chunks "
        f"from {len(docx_files) - len(skipped)} files "
        f"({len(skipped)} skipped: {skipped or 'none'})"
    )
    return total_chunks


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Ingest ENGREG teacher lesson notes into AfriPed ChromaDB")
    p.add_argument("--dry-run", action="store_true", help="Parse and chunk without writing to ChromaDB")
    args = p.parse_args()
    ingest_teacher_content(dry_run=args.dry_run)
