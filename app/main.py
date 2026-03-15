"""FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes.health import router as health_router
from app.api.routes.skills import router as skills_router
from app.api.routes.curriculum import router as curriculum_router
from app.api.routes.content import router as content_router
from app.api.routes.assessment import router as assessment_router
from app.api.routes.insights import router as insights_router
from app.api.routes.ingest import router as ingest_router

RAW_DATA_DIR = Path("data/raw")
_REAL_FILE_SUFFIXES = {".pdf", ".docx", ".doc", ".txt"}


def _real_files_exist() -> bool:
    if not RAW_DATA_DIR.exists():
        return False
    return any(
        f.suffix.lower() in _REAL_FILE_SUFFIXES
        for f in RAW_DATA_DIR.rglob("*") if f.is_file()
    )


async def _bootstrap_rag() -> None:
    """Ingest real curriculum files from data/raw/ if vectorstore is empty.

    Runs as a background task after the server is already healthy.
    Does NOT generate synthetic content — that blocks startup for 10+ min on CPU.
    If no real files exist and vectorstore is empty, app starts without RAG context
    (generation still works, just without curriculum retrieval).
    """
    from app.rag.vectorstore import get_document_count

    try:
        count = get_document_count()
    except Exception as exc:
        logger.warning(f"Could not read vectorstore on startup: {exc}")
        return

    if count > 0:
        logger.info(f"Vectorstore ready — {count} chunks already loaded. Skipping bootstrap.")
        return

    if _real_files_exist():
        logger.info(f"Found curriculum files in {RAW_DATA_DIR} — ingesting in background.")
        try:
            from app.rag.ingestion.ingest import ingest_files
            await asyncio.to_thread(ingest_files, RAW_DATA_DIR)
            logger.info(f"Background ingest complete — {get_document_count()} chunks in vectorstore.")
        except Exception as exc:
            logger.error(f"Background ingest failed: {exc}")
    else:
        # Try the committed teacher corpus (works on Spaces and any clone)
        corpus_dir = Path("corpus/teacher_content")
        if corpus_dir.exists() and any(corpus_dir.glob("*.docx")):
            logger.info(f"Found teacher corpus at {corpus_dir} — ingesting {sum(1 for _ in corpus_dir.glob('*.docx'))} files in background.")
            try:
                from research.datasets.ingest_teacher_content import ingest_teacher_content
                await asyncio.to_thread(ingest_teacher_content)
                logger.info(f"Teacher corpus ingest complete — {get_document_count()} chunks in vectorstore.")
            except Exception as exc:
                logger.error(f"Teacher corpus ingest failed: {exc}")
        else:
            logger.info("Vectorstore empty — no corpus files found. App ready; generation works without RAG.")


async def _warmup_models() -> None:
    """Eagerly load both LLM pipelines so they're cached before any request."""
    from app.core.llm import get_phi_pipeline, get_judge_pipeline

    try:
        await asyncio.to_thread(get_phi_pipeline)
        logger.info("Primary model (Phi-3) warmed up.")
    except Exception as exc:
        logger.warning(f"Primary model warmup failed: {exc}")

    try:
        await asyncio.to_thread(get_judge_pipeline)
        logger.info("Judge model (TinyLlama) warmed up.")
    except Exception as exc:
        logger.warning(f"Judge model warmup failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load LLM pipelines, then start server. Bootstrap RAG in background.

    Startup order:
    1. Warmup models (Phi-3 + TinyLlama) — blocks until loaded, ~30s on warm cache
    2. yield — server becomes healthy and starts accepting requests
    3. Bootstrap RAG runs as background task (non-blocking)
    """
    await _warmup_models()
    asyncio.create_task(_bootstrap_rag())
    yield


app = FastAPI(
    title="AfriPed",
    description=(
        "African Pedagogical Evaluation Framework — AI-powered educational content generation "
        "for Nigerian and West African learners. Generates curriculum-aligned, culturally authentic "
        "content across four pillars: Curriculum, Content, Assessment, and Insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(health_router,     prefix=PREFIX, tags=["Health"])
app.include_router(skills_router,     prefix=PREFIX, tags=["Skill Library"])
app.include_router(curriculum_router, prefix=PREFIX, tags=["Curriculum"])
app.include_router(content_router,    prefix=PREFIX, tags=["Content"])
app.include_router(assessment_router, prefix=PREFIX, tags=["Assessment"])
app.include_router(insights_router,   prefix=PREFIX, tags=["Insights"])
app.include_router(ingest_router,     prefix=PREFIX, tags=["Ingestion"])
