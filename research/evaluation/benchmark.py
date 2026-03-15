"""RAQ vs Baseline Benchmark for Adaptive LLM research.

Compares two conditions on the golden set:
  - full_raq   : generation with RAG + RAQ validation (production system)
  - baseline   : generation results stored without RAQ filtering

Also runs automated metrics (Bloom, cultural, format, ROUGE-L, skill precision)
to produce the comparison table for the paper.

Usage:
    # Evaluate golden set only (no live API calls needed)
    python research/evaluation/benchmark.py

    # With live API comparison (requires running FastAPI server)
    python research/evaluation/benchmark.py --live --api-url http://localhost:8000

    # Save results
    python research/evaluation/benchmark.py \
      --golden-dir research/evaluation/golden_set \
      --output research/evaluation/results/benchmark_results.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ── Import metrics ─────────────────────────────────────────────────────────────

from tests.eval.metrics import (
    bloom_accuracy,
    cultural_name_ratio,
    format_compliance,
    language_accuracy,
    readability_score,
    rouge_l,
    skill_tag_precision,
)


# ── Golden set evaluation ──────────────────────────────────────────────────────

def evaluate_example(example: dict) -> dict:
    """Compute all metrics for a single golden set example."""
    generated = example.get("generated", "")
    reference = example.get("reference", "")
    content_type = example.get("content_type", "LESSON_PLAN")
    expected_bloom = example.get("expected_bloom", "UNDERSTAND")
    expected_lang = example.get("expected_language", "en")
    expected_skills = example.get("expected_skills", [])
    detected_skills = example.get("detected_skills", [])
    validation = example.get("validation", {})

    metrics: dict = {
        # Core pedagogical metrics (RAQ contribution — beyond BLEU/ROUGE)
        "bloom_accuracy":       bloom_accuracy(generated, expected_bloom),
        "cultural_name_ratio":  cultural_name_ratio(generated),
        "format_compliance":    format_compliance(generated, content_type),
        "skill_tag_precision":  skill_tag_precision(detected_skills, expected_skills),
        # Readability
        "readability_ease":     readability_score(generated),
        # Standard NLP metric (baseline comparison)
        "rouge_l":              rouge_l(generated, reference) if reference else None,
        # Language accuracy
        "language_accuracy":    language_accuracy(generated, expected_lang),
        # RAQ validation report (if present)
        "raq_status":           validation.get("status"),
        "raq_judge_score":      validation.get("judge_score"),
        "raq_rules_failed":     len(validation.get("rules_failed", [])),
        "raq_revision_count":   validation.get("revision_count", 0),
    }

    # RAQ pass/fail binary (1 = PASSED or FLAGGED, 0 = REVISED or FAILED)
    if metrics["raq_status"] in ("PASSED", "FLAGGED"):
        metrics["raq_pass"] = 1
    elif metrics["raq_status"] in ("REVISED", "FAILED"):
        metrics["raq_pass"] = 0
    else:
        metrics["raq_pass"] = None

    return metrics


def evaluate_golden_set(golden_dir: Path) -> list[dict]:
    """Evaluate all golden set JSON files."""
    results = []
    for fp in sorted(golden_dir.glob("*.json")):
        try:
            example = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  Skip {fp.name}: {exc}")
            continue

        metrics = evaluate_example(example)
        metrics["file"] = fp.name
        metrics["content_type"] = example.get("content_type", "UNKNOWN")
        metrics["expected_bloom"] = example.get("expected_bloom", "UNKNOWN")
        results.append(metrics)

        # Per-file summary line
        raq_info = f" raq={metrics['raq_judge_score']:.2f}" if metrics.get("raq_judge_score") else ""
        print(
            f"  {fp.name:<35} "
            f"bloom={metrics['bloom_accuracy']:.2f}  "
            f"cultural={metrics['cultural_name_ratio']:.2f}  "
            f"format={metrics['format_compliance']:.2f}  "
            f"rouge_l={metrics['rouge_l'] or 'N/A'}"
            f"{raq_info}"
        )

    return results


# ── Aggregate ──────────────────────────────────────────────────────────────────

def aggregate(results: list[dict]) -> dict:
    """Compute mean ± std for each numeric metric."""
    if not results:
        return {}
    numeric_keys = [
        k for k in results[0]
        if k not in ("file", "content_type", "expected_bloom", "raq_status", "raq_rules_failed")
        and isinstance(results[0][k], (int, float, type(None)))
    ]
    agg: dict = {}
    for key in numeric_keys:
        vals = [r[key] for r in results if r.get(key) is not None]
        if not vals:
            agg[key] = {"mean": None, "std": None, "n": 0}
            continue
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / max(1, len(vals) - 1)
        std = variance ** 0.5
        agg[key] = {"mean": round(mean, 4), "std": round(std, 4), "n": len(vals)}
    return agg


# ── Live API comparison ────────────────────────────────────────────────────────

def run_live_comparison(
    golden_dir: Path,
    api_url: str = "http://localhost:8000",
) -> list[dict]:
    """Call the live API for each golden set example and record outputs.

    Saves raw API responses alongside golden set files as
    golden_set/<name>_live_response.json for later offline analysis.

    Requires: httpx, running FastAPI server at api_url
    """
    try:
        import httpx
    except ImportError:
        print("Install httpx: pip install httpx")
        return []

    results = []
    for fp in sorted(golden_dir.glob("*.json")):
        if "_live_response" in fp.name:
            continue
        try:
            example = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Build a content generation request from the golden example
        content_type = example.get("content_type", "LESSON_PLAN")
        request_body: dict = {}

        if content_type in ("LESSON_PLAN", "WORKSHEET", "STUDY_GUIDE"):
            endpoint = f"{api_url}/api/v1/content/generate"
            request_body = {
                "subject": example.get("subject", "mathematics"),
                "topic": example.get("topic", example.get("reference", "General Topic")[:50]),
                "content_type": content_type,
                "curriculum_board": example.get("curriculum_board", "NERDC"),
                "learner_profile": {
                    "education_level": example.get("education_level", "SSS1"),
                    "program_type": "ACADEMIC",
                },
                "pedagogical_goals": {
                    "bloom_level": example.get("expected_bloom", "UNDERSTAND"),
                    "learning_objectives": [],
                    "target_skills": example.get("expected_skills", []),
                },
                "output_language": example.get("expected_language", "en"),
                "cultural_context": {"use_local_names": True, "use_local_examples": True},
                "use_rag": True,
            }
        elif content_type in ("EXAM_QUESTIONS", "QUIZ"):
            endpoint = f"{api_url}/api/v1/assessment/generate"
            request_body = {
                "subject": example.get("subject", "mathematics"),
                "topic": example.get("topic", "General"),
                "assessment_type": "EXAM_QUESTIONS",
                "curriculum_board": example.get("curriculum_board", "WAEC"),
                "learner_profile": {
                    "education_level": example.get("education_level", "SSS2"),
                    "program_type": "ACADEMIC",
                },
                "bloom_level": example.get("expected_bloom", "ANALYZE"),
                "num_questions": 5,
                "use_rag": True,
            }
        else:
            print(f"  Skipping {fp.name} — no live endpoint for {content_type}")
            continue

        try:
            print(f"  Calling API for {fp.name}...")
            resp = httpx.post(endpoint, json=request_body, timeout=1200)
            resp.raise_for_status()
            api_response = resp.json()
            out_path = fp.parent / fp.name.replace(".json", "_live_response.json")
            out_path.write_text(json.dumps(api_response, indent=2, ensure_ascii=False))
            print(f"    Saved to {out_path.name}")
            results.append({"file": fp.name, "status": "ok", "response": api_response})
        except Exception as exc:
            print(f"    Error: {exc}")
            results.append({"file": fp.name, "status": "error", "error": str(exc)})

    return results


# ── Paper table formatter ──────────────────────────────────────────────────────

def format_paper_table(agg: dict) -> str:
    """Format aggregate metrics as a LaTeX-style table row for the paper."""
    metrics_order = [
        ("bloom_accuracy",      "Bloom Accuracy"),
        ("cultural_name_ratio", "Cultural Name Ratio"),
        ("format_compliance",   "Format Compliance"),
        ("skill_tag_precision", "Skill Tag Precision"),
        ("readability_ease",    "Readability Ease"),
        ("rouge_l",             "ROUGE-L"),
        ("raq_judge_score",     "RAQ Judge Score"),
        ("raq_pass",            "RAQ Pass Rate"),
    ]
    lines = [
        "Metric                    Mean    Std     N",
        "-" * 50,
    ]
    for key, label in metrics_order:
        if key in agg and agg[key]["mean"] is not None:
            m = agg[key]
            lines.append(f"{label:<26} {m['mean']:.4f}  {m['std']:.4f}  {m['n']}")
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RAQ benchmark — evaluate golden set")
    p.add_argument(
        "--golden-dir", type=Path,
        default=Path("research/evaluation/golden_set"),
        help="Golden set directory (default: research/evaluation/golden_set)",
    )
    p.add_argument(
        "--output", type=Path, default=None,
        help="Save results JSON to this path",
    )
    p.add_argument(
        "--live", action="store_true",
        help="Call live API to generate new outputs for comparison",
    )
    p.add_argument(
        "--api-url", default="http://localhost:8000",
        help="FastAPI server URL for live comparison (default: http://localhost:8000)",
    )
    p.add_argument(
        "--paper-table", action="store_true",
        help="Print a paper-ready metrics table",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if not args.golden_dir.exists():
        print(f"Golden set not found: {args.golden_dir}")
        print("Add JSON examples to research/evaluation/golden_set/")
        sys.exit(1)

    if args.live:
        print(f"\nRunning live API comparison against {args.api_url} ...")
        run_live_comparison(args.golden_dir, args.api_url)
        print("Live responses saved. Re-run without --live to evaluate them.")

    print(f"\nEvaluating golden set: {args.golden_dir}")
    print("-" * 70)
    results = evaluate_golden_set(args.golden_dir)

    if not results:
        print("No golden set files found.")
        sys.exit(1)

    agg = aggregate(results)

    print("\n" + "=" * 70)
    print("AGGREGATE METRICS")
    print("=" * 70)
    for key, vals in agg.items():
        if vals["mean"] is not None:
            print(f"  {key:<30} mean={vals['mean']:.4f}  std={vals['std']:.4f}  n={vals['n']}")

    if args.paper_table:
        print("\n" + "=" * 70)
        print("PAPER TABLE FORMAT")
        print("=" * 70)
        print(format_paper_table(agg))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        out = {
            "run_at": datetime.utcnow().isoformat() + "Z",
            "golden_dir": str(args.golden_dir),
            "n_examples": len(results),
            "results": results,
            "aggregate": agg,
        }
        args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False))
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
