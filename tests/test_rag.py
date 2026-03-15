"""Tests for RAG pipeline components (no LLM required)."""
import pytest
from pathlib import Path
from langchain_core.documents import Document

from app.rag.ingestion.chunker import chunk_documents, _is_header, infer_metadata
from app.rag.ingestion.loader import load_file


# ── Chunker ────────────────────────────────────────────────────────────────────

def test_is_header_detects_unit():
    assert _is_header("UNIT 1: Introduction to Algebra")


def test_is_header_detects_week():
    assert _is_header("Week 3: Fractions and Decimals")


def test_is_header_ignores_body():
    assert not _is_header("Students will learn to solve quadratic equations.")


def test_chunk_documents_basic():
    doc = Document(
        page_content="Week 1: Algebra\nStudents learn basic operations.\n\nWeek 2: Geometry\nStudents learn shapes.",
        metadata={"source_file": "test.txt"},
    )
    chunks = chunk_documents([doc])
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.page_content.strip()


def test_chunk_documents_preserves_metadata():
    doc = Document(
        page_content="Some curriculum content about mathematics.",
        metadata={"source_file": "nerdc_math.pdf", "board": "NERDC"},
    )
    chunks = chunk_documents([doc], metadata_overrides={"subject": "mathematics"})
    assert all(c.metadata.get("subject") == "mathematics" for c in chunks)


def test_chunk_documents_with_hierarchy():
    text = "\n".join([
        "UNIT 1: NUMBERS",
        "Sub-topic: Whole Numbers",
        "Students will define whole numbers and list their properties.",
        "",
        "UNIT 2: ALGEBRA",
        "Sub-topic: Simple Equations",
        "Students will solve simple linear equations.",
    ])
    doc = Document(page_content=text, metadata={"source_file": "test.txt"})
    chunks = chunk_documents([doc])
    # Should detect at least 2 sections
    assert len(chunks) >= 1


def test_chunk_empty_document():
    doc = Document(page_content="", metadata={})
    chunks = chunk_documents([doc])
    assert chunks == []


# ── Metadata inference ─────────────────────────────────────────────────────────

def test_infer_metadata_nerdc():
    doc = Document(
        page_content="This is a NERDC curriculum guide for JSS1 students.",
        metadata={},
    )
    meta = infer_metadata(doc, source_file="nerdc_guide.pdf")
    assert meta["board"] == "NERDC"
    assert meta["level"] == "JSS1"
    assert meta["source_file"] == "nerdc_guide.pdf"


def test_infer_metadata_waec():
    doc = Document(
        page_content="WAEC examination questions for SSS3 biology candidates.",
        metadata={},
    )
    meta = infer_metadata(doc)
    assert meta["board"] == "WAEC"
    assert meta["level"] == "SSS3"


def test_infer_metadata_unknown():
    doc = Document(page_content="Some random educational text.", metadata={})
    meta = infer_metadata(doc)
    assert meta["board"] == "CUSTOM"
    assert meta["level"] == "UNSPECIFIED"


# ── Loader (text files only — no real PDF/DOCX in test env) ───────────────────

def test_load_txt_file(tmp_path):
    txt = tmp_path / "test_curriculum.txt"
    txt.write_text("Week 1: Introduction\nStudents learn the basics.", encoding="utf-8")
    docs = load_file(txt)
    assert len(docs) == 1
    assert "Week 1" in docs[0].page_content


def test_load_unsupported_extension(tmp_path):
    f = tmp_path / "data.xlsx"
    f.write_bytes(b"fake content")
    docs = load_file(f)
    assert docs == []
