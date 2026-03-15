"""Automated evaluation metrics for AfriPed outputs.

Run:
    python tests/eval/metrics.py --golden-dir tests/eval/golden_set
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Optional


# ── Bloom verb classifier ──────────────────────────────────────────────────────

BLOOM_VERBS = {
    "REMEMBER":   ["define", "list", "recall", "name", "identify", "state"],
    "UNDERSTAND": ["explain", "describe", "summarise", "paraphrase", "interpret", "classify"],
    "APPLY":      ["solve", "use", "demonstrate", "calculate", "apply", "carry out"],
    "ANALYZE":    ["analyse", "analyze", "compare", "contrast", "distinguish", "examine"],
    "EVALUATE":   ["evaluate", "justify", "assess", "critique", "judge", "argue"],
    "CREATE":     ["design", "create", "compose", "construct", "develop", "produce"],
}

LOCAL_NAMES = {
    "chukwuemeka", "adaeze", "aminu", "tunde", "kofi", "ama", "fatima",
    "emeka", "ngozi", "kwame", "abena", "bola", "sola", "kemi", "biodun",
    "chioma", "nkechi", "uchenna", "obiora", "chiamaka", "obinna", "chidi",
    "aisha", "musa", "ibrahim", "halima", "zainab",
}
WESTERN_NAMES = {
    "john", "james", "peter", "michael", "david", "william", "robert",
    "mary", "jennifer", "jessica", "emily", "sarah", "elizabeth", "lisa",
}


# ── Individual metric functions ────────────────────────────────────────────────

def bloom_accuracy(generated: str, expected_level: str) -> float:
    """Return 1.0 if the expected Bloom-level verbs are found, 0.0 otherwise."""
    verbs = BLOOM_VERBS.get(expected_level.upper(), [])
    if not verbs:
        return 0.0
    lower = generated.lower()
    found = sum(1 for v in verbs if v in lower)
    return min(1.0, found / max(1, len(verbs) // 2))


def cultural_name_ratio(generated: str) -> float:
    """Return ratio of local West African names to all detected names (higher = better)."""
    words = re.findall(r"\b[A-Z][a-z]+\b", generated)
    name_words = [w for w in words if w.lower() in LOCAL_NAMES or w.lower() in WESTERN_NAMES]
    if not name_words:
        return 1.0  # no names detected → neutral
    local = sum(1 for w in name_words if w.lower() in LOCAL_NAMES)
    return round(local / len(name_words), 2)


def language_accuracy(generated: str, expected_lang: str) -> float:
    """Detect output language and compare to expected."""
    try:
        from langdetect import detect  # type: ignore
        detected = detect(generated[:500])
        lang_map = {"en": "en", "yo": "yo", "ha": "ha", "ig": "ig", "pcm": "en"}
        expected_code = lang_map.get(expected_lang.split("-")[0], expected_lang)
        return 1.0 if detected == expected_code else 0.0
    except Exception:
        return 0.5  # unknown


def format_compliance(generated: str, content_type: str) -> float:
    """Return 0–1 structural compliance score."""
    ct = content_type.upper()
    if ct == "LESSON_PLAN":
        keywords = ["objective", "activity", "assessment"]
        found = sum(1 for kw in keywords if kw in generated.lower())
        return round(found / len(keywords), 2)
    elif ct in {"QUIZ", "EXAM_QUESTIONS"}:
        q_count = len(re.findall(r"Q?\d+[\.\)]\s", generated))
        return min(1.0, q_count / 5)
    elif ct in {"SCHEME_OF_WORK", "TERM_PLAN"}:
        has_week = bool(re.search(r"week\s*\d+", generated, re.IGNORECASE))
        return 1.0 if has_week else 0.0
    return 0.5  # neutral for unknown types


def rouge_l(hypothesis: str, reference: str) -> float:
    """ROUGE-L F1 score."""
    try:
        from rouge_score import rouge_scorer  # type: ignore
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        result = scorer.score(reference, hypothesis)
        return round(result["rougeL"].fmeasure, 4)
    except ImportError:
        # Fallback: token overlap
        hyp_tokens = set(hypothesis.lower().split())
        ref_tokens = set(reference.lower().split())
        if not ref_tokens:
            return 0.0
        overlap = hyp_tokens & ref_tokens
        precision = len(overlap) / max(1, len(hyp_tokens))
        recall = len(overlap) / max(1, len(ref_tokens))
        if precision + recall == 0:
            return 0.0
        return round(2 * precision * recall / (precision + recall), 4)


def skill_tag_precision(
    detected_skills: List[str],
    expected_skills: List[str],
) -> float:
    """Precision of skill tag predictions vs expected."""
    if not expected_skills:
        return 1.0
    detected_set = set(s.lower() for s in detected_skills)
    expected_set = set(s.lower() for s in expected_skills)
    hits = detected_set & expected_set
    return round(len(hits) / max(1, len(expected_set)), 2)


def readability_score(text: str) -> float:
    """Flesch Reading Ease (0-100; higher = easier)."""
    try:
        import textstat  # type: ignore
        return round(textstat.flesch_reading_ease(text), 1)
    except ImportError:
        return 50.0  # neutral default


# ── Golden set evaluation ──────────────────────────────────────────────────────

def evaluate_golden_set(golden_dir: Path) -> list[dict]:
    """Evaluate all JSON examples in the golden set directory.

    Each golden set file should be JSON with:
    {
        "generated": "...",
        "reference": "...",       # optional
        "content_type": "...",
        "expected_bloom": "...",
        "expected_language": "en",
        "expected_skills": [...]
    }
    """
    results = []
    for fp in sorted(golden_dir.glob("*.json")):
        try:
            example = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  Skip {fp.name}: {exc}")
            continue

        generated = example.get("generated", "")
        reference = example.get("reference", "")
        content_type = example.get("content_type", "LESSON_PLAN")
        expected_bloom = example.get("expected_bloom", "UNDERSTAND")
        expected_lang = example.get("expected_language", "en")
        expected_skills = example.get("expected_skills", [])
        detected_skills = example.get("detected_skills", [])

        metrics = {
            "file": fp.name,
            "bloom_accuracy": bloom_accuracy(generated, expected_bloom),
            "cultural_name_ratio": cultural_name_ratio(generated),
            "language_accuracy": language_accuracy(generated, expected_lang),
            "format_compliance": format_compliance(generated, content_type),
            "rouge_l": rouge_l(generated, reference) if reference else None,
            "skill_tag_precision": skill_tag_precision(detected_skills, expected_skills),
            "readability_ease": readability_score(generated),
        }
        results.append(metrics)
        print(f"  {fp.name}: bloom={metrics['bloom_accuracy']:.2f} "
              f"cultural={metrics['cultural_name_ratio']:.2f} "
              f"format={metrics['format_compliance']:.2f}")

    return results


def aggregate(results: list[dict]) -> dict:
    """Compute mean for each numeric metric across all golden examples."""
    if not results:
        return {}
    keys = [k for k in results[0] if k != "file" and results[0][k] is not None]
    agg = {}
    for key in keys:
        vals = [r[key] for r in results if r.get(key) is not None]
        agg[key] = round(sum(vals) / len(vals), 4) if vals else None
    return agg


def main():
    parser = argparse.ArgumentParser(description="AfriPed evaluation metrics")
    parser.add_argument(
        "--golden-dir",
        type=Path,
        default=Path("research/evaluation/golden_set"),
        help="Directory containing golden set JSON files",
    )
    parser.add_argument("--output", type=Path, default=None, help="Save results to JSON file")
    args = parser.parse_args()

    if not args.golden_dir.exists():
        print(f"Golden set directory not found: {args.golden_dir}")
        print("Create JSON files in tests/eval/golden_set/ to run evaluation.")
        return

    print(f"\nEvaluating golden set: {args.golden_dir}")
    print("-" * 60)
    results = evaluate_golden_set(args.golden_dir)

    if not results:
        print("No golden set files found.")
        return

    agg = aggregate(results)
    print("\n" + "=" * 60)
    print("AGGREGATE METRICS")
    print("=" * 60)
    for k, v in agg.items():
        print(f"  {k:<30} {v}")

    if args.output:
        out = {"results": results, "aggregate": agg}
        args.output.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
