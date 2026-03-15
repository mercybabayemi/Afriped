"""POST /api/v1/ingest/synthetic — trigger RAG vectorstore bootstrap."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from app.rag.vectorstore import get_document_count

router = APIRouter()

_ingestion_running = False


def _run_synthetic_ingest(board: str, subject: str, level: str) -> None:
    global _ingestion_running
    try:
        from app.rag.ingestion.ingest import ingest_synthetic
        count = ingest_synthetic(board=board, subject=subject, level=level)
        logger.info(f"Synthetic ingest complete: {count} chunks added")
    except Exception as exc:
        logger.error(f"Synthetic ingest failed: {exc}")
    finally:
        _ingestion_running = False


@router.post("/ingest/synthetic")
async def trigger_synthetic_ingest(
    background_tasks: BackgroundTasks,
    board: str = "NERDC",
    subject: str = "mathematics",
    level: str = "SSS1",
):
    """Bootstrap the vectorstore with synthetic curriculum content.

    Runs in the background — returns immediately. Check /api/v1/ingest/status
    to see how many documents are in the store.
    """
    global _ingestion_running
    if _ingestion_running:
        raise HTTPException(status_code=409, detail="Ingestion already running")

    _ingestion_running = True
    background_tasks.add_task(_run_synthetic_ingest, board, subject, level)
    return {
        "status": "started",
        "message": f"Synthetic ingestion started for {board} {subject} {level}. Check /ingest/status.",
    }


@router.get("/ingest/status")
async def ingest_status():
    """Return current vectorstore document count and ingestion state."""
    return {
        "document_count": get_document_count(),
        "ingestion_running": _ingestion_running,
    }
