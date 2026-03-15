"""Download, cache, and ingest Nigerian education datasets from HuggingFace.

Downloads to: data/raw/nigerian_education/<key>/<key>.parquet
Processed:    data/processed/nigerian_education/<key>/<key>_chunks.parquet
ChromaDB:     data/chroma/ (via app.rag.vectorstore)

Usage:
    # Download + save locally + ingest all datasets
    python research/datasets/download_hf_datasets.py --all

    # Download + save locally only (no ChromaDB ingest)
    python research/datasets/download_hf_datasets.py --all --save-only

    # Load from local cache + ingest (no re-download)
    python research/datasets/download_hf_datasets.py --all --from-cache

    # Specific datasets
    python research/datasets/download_hf_datasets.py --datasets online_exams learning_materials

    # Preview schema without any downloads
    python research/datasets/download_hf_datasets.py --preview --datasets vocational

    # List all available datasets
    python research/datasets/download_hf_datasets.py --list
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Ensure project root on path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use loguru if available (project env), fall back to stdlib logging
try:
    from loguru import logger  # type: ignore
except ImportError:
    import logging as _logging
    _logging.basicConfig(level=_logging.INFO, format="%(levelname)s | %(message)s")
    logger = _logging.getLogger("download_hf_datasets")  # type: ignore

# ── Storage paths ──────────────────────────────────────────────────────────────

RAW_DIR       = PROJECT_ROOT / "data" / "raw"       / "nigerian_education"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "nigerian_education"
CACHE_MANIFEST = RAW_DIR / "_manifest.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ── Dataset registry ───────────────────────────────────────────────────────────

REGISTRY: dict[str, dict] = {
    "vocational": {
        "hf_id": "electricsheepafrica/nigerian_education_vocational_technical",
        "board": "NABTEB",
        "subject": "trade_skill",
        "level": "VOCATIONAL_ADVANCED",
        "text_fields": ["content", "text", "passage", "description", "material"],
        "subject_field": "subject",
        "topic_fields": ["topic", "category", "subtopic"],
        "combine_qa": False,
    },
    "continuous_assessment": {
        "hf_id": "Ben-45/nigerian_education_continuous_assessment",
        "board": "NERDC",
        "subject": "general",
        "level": "SSS1",
        "text_fields": ["comment", "feedback", "description", "text", "remarks"],
        "combine_fields": ["subject", "score", "grade"],
        "subject_field": "subject",
        "topic_fields": ["topic", "assessment_type", "subject"],
        "combine_qa": False,
    },
    "digital_learning": {
        "hf_id": "electricsheepafrica/nigerian_education_digital_learning",
        "board": "NERDC",
        "subject": "digital_literacy",
        "level": "SSS1",
        "text_fields": ["content", "text", "passage", "material", "description"],
        "subject_field": "subject",
        "topic_fields": ["topic", "module", "unit"],
        "combine_qa": False,
    },
    "online_exams": {
        "hf_id": "electricsheepafrica/nigerian_education_online_exams",
        "board": "WAEC",
        "subject": "general",
        "level": "SSS2",
        "text_fields": ["question", "answer", "content", "text"],
        "subject_field": "subject",
        "topic_fields": ["topic", "chapter", "subject"],
        "combine_qa": True,
    },
    "learning_materials": {
        "hf_id": "electricsheepafrica/nigerian_education_learning_materials",
        "board": "NERDC",
        "subject": "general",
        "level": "JSS3",
        "text_fields": ["content", "material", "text", "passage", "description"],
        "subject_field": "subject",
        "topic_fields": ["topic", "title", "chapter", "unit"],
        "combine_qa": False,
    },
    "teacher_training": {
        "hf_id": "electricsheepafrica/nigerian_education_teacher_training",
        "board": "NERDC",
        "subject": "general",
        "level": "TEACHER_TRAINING",
        "text_fields": ["content", "text", "training_content", "description", "material"],
        "subject_field": "subject",
        "topic_fields": ["topic", "module", "skill", "competency"],
        "combine_qa": False,
    },
    "special_needs": {
        "hf_id": "electricsheepafrica/nigerian_education_special_needs",
        "board": "UBEC",
        "subject": "general",
        "level": "PRIMARY_4_6",
        "text_fields": ["content", "text", "description", "strategy", "material", "approach"],
        "subject_field": "subject",
        "topic_fields": ["topic", "disability_type", "category", "intervention"],
        "combine_qa": False,
    },
}


# ── Manifest (tracks what has been downloaded) ─────────────────────────────────

def _load_manifest() -> dict:
    if CACHE_MANIFEST.exists():
        return json.loads(CACHE_MANIFEST.read_text())
    return {}


def _save_manifest(manifest: dict) -> None:
    CACHE_MANIFEST.write_text(json.dumps(manifest, indent=2))


def is_cached(dataset_key: str) -> bool:
    """Return True if raw parquet is already on disk."""
    path = RAW_DIR / dataset_key / f"{dataset_key}.parquet"
    return path.exists()


# ── Text + metadata helpers ────────────────────────────────────────────────────

def _extract_text(example: dict, cfg: dict) -> str:
    if cfg.get("combine_qa"):
        q = str(example.get("question", "") or "")
        a = str(example.get("answer", "") or "")
        if q and a:
            return f"Question: {q}\nAnswer: {a}"
    for field in cfg["text_fields"]:
        val = example.get(field, "")
        if isinstance(val, str) and val.strip():
            return val.strip()
    if cfg.get("combine_fields"):
        parts = [f"{f}: {example[f]}" for f in cfg["combine_fields"] if example.get(f) is not None]
        if parts:
            return " | ".join(parts)
    values = [str(v) for v in example.values() if isinstance(v, str) and str(v).strip()]
    return " ".join(values[:3]) if values else ""


def _extract_metadata(example: dict, cfg: dict, dataset_key: str) -> dict:
    meta: dict = {
        "source": f"hf:{cfg['hf_id']}",
        "dataset_key": dataset_key,
        "board": cfg["board"],
        "level": cfg["level"],
        "synthetic": False,
    }
    subject_val = example.get(cfg.get("subject_field", "subject"), cfg["subject"])
    meta["subject"] = str(subject_val).lower().replace(" ", "_") if subject_val else cfg["subject"]
    for field in cfg.get("topic_fields", []):
        val = example.get(field)
        if val:
            meta["topic"] = str(val)
            break
    return meta


# ── Download and cache to disk ─────────────────────────────────────────────────

def download_and_cache(
    dataset_key: str,
    max_examples: int = 5000,
    force: bool = False,
) -> Path | None:
    """Download HF dataset and save as Parquet to data/raw/nigerian_education/<key>/."""
    try:
        import pandas as pd
        from datasets import load_dataset  # type: ignore
    except ImportError:
        logger.error("Run: pip install datasets pandas pyarrow")
        return None

    out_dir  = RAW_DIR / dataset_key
    out_path = out_dir / f"{dataset_key}.parquet"
    out_dir.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not force:
        logger.info(f"Cache hit: {dataset_key} → {out_path}")
        return out_path

    cfg = REGISTRY[dataset_key]
    logger.info(f"Downloading {dataset_key} from {cfg['hf_id']} (max {max_examples} rows)...")

    try:
        ds = load_dataset(cfg["hf_id"], split="train", streaming=True)
    except Exception as exc:
        logger.error(f"Failed to load {cfg['hf_id']}: {exc}")
        return None

    rows = []
    for i, example in enumerate(ds):
        if i >= max_examples:
            break
        text = _extract_text(example, cfg)
        if text and len(text) >= 20:
            meta = _extract_metadata(example, cfg, dataset_key)
            rows.append({"text": text, **meta, **{k: str(v) for k, v in example.items() if isinstance(v, (str, int, float))}})

    if not rows:
        logger.warning(f"No usable rows for {dataset_key}")
        return None

    df = pd.DataFrame(rows)
    df.to_parquet(out_path, index=False)

    # Save stats alongside
    stats = {
        "dataset_key": dataset_key,
        "hf_id": cfg["hf_id"],
        "rows_downloaded": len(rows),
        "columns": df.columns.tolist(),
        "text_len_mean": round(df["text"].str.len().mean(), 1),
        "text_len_median": round(df["text"].str.len().median(), 1),
        "downloaded_at": datetime.utcnow().isoformat() + "Z",
        "parquet_path": str(out_path),
    }
    (out_dir / "stats.json").write_text(json.dumps(stats, indent=2))

    manifest = _load_manifest()
    manifest[dataset_key] = stats
    _save_manifest(manifest)

    logger.success(f"Saved {len(rows):,} rows → {out_path} ({out_path.stat().st_size // 1024} KB)")
    return out_path


# ── Load from local cache ──────────────────────────────────────────────────────

def load_from_cache(dataset_key: str):
    """Load cached Parquet as a pandas DataFrame."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("Run: pip install pandas pyarrow")
        return None

    out_path = RAW_DIR / dataset_key / f"{dataset_key}.parquet"
    if not out_path.exists():
        logger.warning(f"No cache for {dataset_key} — run without --from-cache first")
        return None
    df = pd.read_parquet(out_path)
    logger.info(f"Loaded {dataset_key} from cache: {len(df):,} rows")
    return df


# ── ChromaDB ingest from DataFrame ────────────────────────────────────────────

def ingest_dataframe(df, dataset_key: str) -> int:
    """Ingest a pandas DataFrame into ChromaDB."""
    try:
        from app.rag.vectorstore import add_documents
        from app.rag.ingestion.chunker import chunk_documents
        from app.rag.ingestion.ingest import _doc_id
        from langchain_core.documents import Document
    except Exception as exc:
        logger.error(f"Cannot import app modules: {exc}")
        return 0

    cfg = REGISTRY[dataset_key]
    docs = [
        Document(
            page_content=row["text"],
            metadata={
                "source": row.get("source", f"hf:{cfg['hf_id']}"),
                "dataset_key": dataset_key,
                "board": row.get("board", cfg["board"]),
                "subject": row.get("subject", cfg["subject"]),
                "level": row.get("level", cfg["level"]),
                "topic": row.get("topic", ""),
                "synthetic": False,
            },
        )
        for _, row in df.iterrows()
        if isinstance(row.get("text"), str) and len(row["text"]) >= 20
    ]

    if not docs:
        logger.warning(f"No valid docs to ingest for {dataset_key}")
        return 0

    chunks = chunk_documents(docs)
    texts     = [c.page_content for c in chunks]
    metadatas = [{**c.metadata} for c in chunks]
    ids       = [_doc_id(c.page_content, c.metadata) for c in chunks]

    add_documents(texts=texts, metadatas=metadatas, ids=ids)
    logger.success(f"Ingested {len(chunks):,} chunks from {dataset_key}")
    return len(chunks)


# ── Full pipeline: download → cache → ingest ───────────────────────────────────

def pipeline(
    dataset_key: str,
    max_examples: int = 5000,
    save_only: bool = False,
    from_cache: bool = False,
    force: bool = False,
) -> dict:
    """Full pipeline for one dataset. Returns a status dict."""
    result = {"key": dataset_key, "rows": 0, "chunks": 0, "cached": False, "ingested": False}

    if from_cache:
        df = load_from_cache(dataset_key)
        if df is None:
            result["error"] = "cache miss"
            return result
        result["cached"] = True
    else:
        path = download_and_cache(dataset_key, max_examples=max_examples, force=force)
        if path is None:
            result["error"] = "download failed"
            return result
        result["cached"] = True
        import pandas as pd
        df = pd.read_parquet(path)

    result["rows"] = len(df)

    if not save_only:
        n = ingest_dataframe(df, dataset_key)
        result["chunks"] = n
        result["ingested"] = n > 0

    return result


# ── Preview ────────────────────────────────────────────────────────────────────

def preview_dataset(dataset_key: str, n: int = 3) -> None:
    """Print schema + sample rows. Works from cache or live."""
    if is_cached(dataset_key):
        df = load_from_cache(dataset_key)
        if df is not None:
            print(f"\n{'='*60}\n{dataset_key} (from cache — {len(df):,} rows)\n{'='*60}")
            print(f"Columns: {df.columns.tolist()}")
            print(df.head(n).to_string())
            return

    # Live preview without full download
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        logger.error("Run: pip install datasets")
        return

    cfg = REGISTRY[dataset_key]
    logger.info(f"Streaming preview of {cfg['hf_id']}")
    try:
        ds = load_dataset(cfg["hf_id"], split="train", streaming=True)
    except Exception as exc:
        logger.error(f"{exc}")
        return

    print(f"\n{'='*60}\n{dataset_key} — {cfg['hf_id']}\n{'='*60}")
    for i, row in enumerate(ds):
        if i >= n:
            break
        print(f"\n--- Row {i+1} ---")
        print(f"  Columns : {list(row.keys())}")
        text = _extract_text(row, cfg)
        print(f"  Text    : {text[:200]!r}")
        print(f"  Metadata: {_extract_metadata(row, cfg, dataset_key)}")


# ── Status report ──────────────────────────────────────────────────────────────

def print_status() -> None:
    """Print download status of all datasets."""
    manifest = _load_manifest()
    print(f"\n{'='*65}")
    print(f"{'Dataset':<25} {'Cached':<8} {'Rows':>8} {'Size':>8}  {'Downloaded'}")
    print(f"{'-'*65}")
    for key in REGISTRY:
        path = RAW_DIR / key / f"{key}.parquet"
        if path.exists():
            size = f"{path.stat().st_size // 1024} KB"
            m = manifest.get(key, {})
            rows = m.get("rows_downloaded", "?")
            ts   = m.get("downloaded_at", "?")[:10]
            print(f"  {key:<23} {'✓':<8} {str(rows):>8} {size:>8}  {ts}")
        else:
            print(f"  {key:<23} {'✗':<8} {'—':>8} {'—':>8}  not downloaded")
    print(f"{'='*65}")
    print(f"Raw cache dir: {RAW_DIR}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download, cache, and ingest Nigerian education HF datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python research/datasets/download_hf_datasets.py --all
  python research/datasets/download_hf_datasets.py --all --save-only
  python research/datasets/download_hf_datasets.py --all --from-cache
  python research/datasets/download_hf_datasets.py --datasets online_exams --force
  python research/datasets/download_hf_datasets.py --preview --datasets vocational
  python research/datasets/download_hf_datasets.py --status
        """,
    )
    p.add_argument("--all", action="store_true", help="Process all 7 datasets")
    p.add_argument("--datasets", nargs="+", choices=list(REGISTRY), help="Specific dataset keys")
    p.add_argument("--max-examples", type=int, default=5000, help="Max rows per dataset (default: 5000)")
    p.add_argument("--save-only", action="store_true", help="Download + cache only; skip ChromaDB ingest")
    p.add_argument("--from-cache", action="store_true", help="Load from local cache; skip HF download")
    p.add_argument("--force", action="store_true", help="Re-download even if cache exists")
    p.add_argument("--preview", action="store_true", help="Preview schema + samples")
    p.add_argument("--status", action="store_true", help="Show download status of all datasets")
    p.add_argument("--list", action="store_true", help="List all available datasets")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if args.list:
        print("\nAvailable datasets:")
        for key, cfg in REGISTRY.items():
            cached = "✓ cached" if is_cached(key) else "  not cached"
            print(f"  {key:<25} {cached}  {cfg['hf_id']}")
        return

    if args.status:
        print_status()
        return

    keys: list[str] = []
    if args.all:
        keys = list(REGISTRY.keys())
    elif args.datasets:
        keys = args.datasets
    else:
        print("Specify --all or --datasets <key...>. Use --list to see options.")
        sys.exit(1)

    if args.preview:
        for key in keys:
            preview_dataset(key)
        return

    print(f"\nProcessing {len(keys)} dataset(s) | max_examples={args.max_examples} | "
          f"save_only={args.save_only} | from_cache={args.from_cache}\n")

    total_rows   = 0
    total_chunks = 0
    results: list[dict] = []

    for key in keys:
        r = pipeline(
            key,
            max_examples=args.max_examples,
            save_only=args.save_only,
            from_cache=args.from_cache,
            force=args.force,
        )
        results.append(r)
        total_rows   += r.get("rows", 0)
        total_chunks += r.get("chunks", 0)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "✓" if r.get("cached") else "✗"
        ingest = f"  {r['chunks']:,} chunks ingested" if r.get("ingested") else "  (not ingested)"
        error  = f"  ERROR: {r['error']}" if r.get("error") else ""
        print(f"  {status} {r['key']:<25} {r.get('rows', 0):>6} rows{ingest}{error}")

    print(f"\n  Total rows cached  : {total_rows:,}")
    if not args.save_only:
        print(f"  Total chunks → DB  : {total_chunks:,}")
    print(f"\n  Cache directory    : {RAW_DIR}")


if __name__ == "__main__":
    main()
