"""
Threshold ablation for AfriPed gate parameters.

Sweeps three dimensions against the golden set:
  1. Cultural flag (western name ratio) — 40%–80%
  2. Bloom accuracy score — 0.30–0.80
  3. ROUGE-L × bloom_accuracy grid — for examples with a reference

Also audits Bloom verb lists against Anderson & Krathwohl (2001) revised
taxonomy and reports any additions or gaps.

Run:
    python research/evaluation/threshold_ablation.py
    python research/evaluation/threshold_ablation.py --golden-dir research/evaluation/golden_set_v2
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Anderson & Krathwohl (2001) canonical verb lists ──────────────────────────
# Source: Anderson, L.W. & Krathwohl, D.R. (2001). A Taxonomy for Learning,
#         Teaching and Assessing. Longman.

AK_VERBS: dict[str, list[str]] = {
    "REMEMBER": [
        "define", "duplicate", "list", "memorise", "memorize", "recall",
        "repeat", "reproduce", "state", "recognise", "recognize",
        "identify", "name", "label", "match", "select", "locate",
    ],
    "UNDERSTAND": [
        "classify", "describe", "discuss", "explain", "identify",
        "locate", "recognise", "recognize", "report", "select",
        "translate", "paraphrase", "summarise", "summarize",
        "interpret", "exemplify", "instantiate", "infer",
        "compare", "explain", "give examples", "illustrate",
    ],
    "APPLY": [
        "choose", "demonstrate", "dramatise", "dramatize",
        "employ", "illustrate", "interpret", "operate",
        "schedule", "sketch", "solve", "use", "write",
        "carry out", "execute", "implement", "apply",
        "calculate", "complete", "show", "practise", "practice", "perform",
    ],
    "ANALYZE": [
        "appraise", "compare", "contrast", "criticise", "criticize",
        "differentiate", "discriminate", "distinguish", "examine",
        "experiment", "question", "test", "analyse", "analyze",
        "break down", "categorise", "categorize", "separate",
        "order", "attribute", "organise", "organize", "deconstruct",
        "investigate", "relate", "select", "infer",
    ],
    "EVALUATE": [
        "appraise", "argue", "defend", "judge", "select",
        "support", "value", "evaluate", "critique", "assess",
        "justify", "recommend", "rate", "rank", "measure",
        "decide", "review", "weigh", "conclude", "prioritise", "prioritize",
    ],
    "CREATE": [
        "assemble", "construct", "create", "design", "develop",
        "formulate", "write", "plan", "produce", "generate",
        "invent", "make", "build", "compose", "hypothesise",
        "hypothesize", "propose", "combine", "compile", "devise",
    ],
}

# ── Current production verb lists (from rules.py) ────────────────────────────

PRODUCTION_VERBS: dict[str, list[str]] = {
    "REMEMBER":   ["define", "list", "recall", "name", "identify", "state", "memorise", "memorize",
                   "know", "recognise", "recognize", "repeat", "match", "label", "select"],
    "UNDERSTAND": ["explain", "describe", "summarise", "summarize", "paraphrase", "interpret", "classify", "give examples",
                   "understand", "discuss", "express", "locate", "report", "review", "tell"],
    "APPLY":      ["solve", "use", "demonstrate", "calculate", "apply", "carry out", "execute", "implement",
                   "practise", "practice", "show", "complete", "model", "perform", "present"],
    "ANALYZE":    ["analyse", "analyze", "compare", "contrast", "distinguish", "examine", "break down", "differentiate",
                   "investigate", "question", "test", "categorise", "categorize", "separate", "order"],
    "EVALUATE":   ["evaluate", "justify", "assess", "critique", "judge", "argue", "defend",
                   "review", "measure", "recommend", "rank", "select", "decide", "rate"],
    "CREATE":     ["design", "create", "compose", "construct", "develop", "produce", "plan",
                   "write", "make", "build", "generate", "formulate", "invent", "propose"],
}

# ── Name sets (mirror of rules.py) ───────────────────────────────────────────

WESTERN_NAMES = {
    "john", "james", "peter", "michael", "david", "william", "robert", "richard",
    "thomas", "charles", "george", "edward", "henry", "joseph", "paul",
    "mary", "jennifer", "jessica", "emily", "sarah", "elizabeth", "lisa",
    "susan", "karen", "nancy", "betty", "helen", "sandra", "donna",
    "matthew", "andrew", "daniel", "christopher", "mark", "joshua", "ryan",
    "kevin", "brian", "gary", "timothy", "jason", "jeff", "frank",
}

LOCAL_NAMES = {
    "chukwuemeka", "adaeze", "aminu", "tunde", "kofi", "ama", "fatima",
    "emeka", "ngozi", "kwame", "abena", "bola", "sola", "kemi", "biodun",
    "seun", "yetunde", "taiwo", "kehinde", "femi", "toyin", "chioma",
    "nkechi", "uchenna", "obiora", "chiamaka", "obinna", "chidi", "aisha",
    "musa", "ibrahim", "halima", "zainab", "binta", "garba", "yusuf",
    "efua", "akosua", "adjoa", "esi", "yaw", "kojo", "akua",
    "nana", "afia", "ekua", "mensah", "asante", "owusu", "boateng",
    "okonkwo", "ezinne", "ifeanyi", "oluwaseun", "olumide", "adebayo",
}


def _western_ratio(text: str) -> Optional[float]:
    words = re.findall(r"\b[A-Z][a-z]+\b", text)
    names = [w for w in words if w.lower() in WESTERN_NAMES or w.lower() in LOCAL_NAMES]
    if not names:
        return None
    western = sum(1 for n in names if n.lower() in WESTERN_NAMES)
    return western / len(names)


def _bloom_match(text: str, expected_level: str) -> bool:
    verbs = PRODUCTION_VERBS.get(expected_level.upper(), [])
    lower = text.lower()
    return any(v in lower for v in verbs)


def load_golden(golden_dir: Path) -> list[dict]:
    examples = []
    for f in sorted(golden_dir.glob("*.json")):
        with open(f) as fh:
            ex = json.load(fh)
        # Support both old golden set schema and new v2 schema
        content = (ex.get("generated")
                   or ex.get("content")
                   or ex.get("text", ""))
        bloom   = (ex.get("expected_bloom")
                   or ex.get("expected", {}).get("bloom_level")
                   or ex.get("bloom_level")
                   or ex.get("metadata", {}).get("bloom_level", ""))
        reference = ex.get("reference") or ex.get("ref", "")
        if content and bloom:
            examples.append({
                "content": content,
                "bloom_level": bloom.upper(),
                "reference": reference,
                "file": f.name,
            })
    return examples


# ── Threshold ablation ────────────────────────────────────────────────────────

def run_threshold_ablation(examples: list[dict]) -> dict:
    thresholds = [0.40, 0.50, 0.60, 0.70, 0.80]
    results = {}

    for thresh in thresholds:
        pass_count = 0
        applicable = 0
        for ex in examples:
            ratio = _western_ratio(ex["content"])
            if ratio is None:
                continue  # no names detected, skip
            applicable += 1
            if ratio <= thresh:
                pass_count += 1

        pct = pass_count / applicable * 100 if applicable else 0
        results[thresh] = {
            "threshold":   thresh,
            "pass_count":  pass_count,
            "applicable":  applicable,
            "pass_rate":   round(pct, 1),
        }

    return results


# ── Bloom accuracy score (mirrors rules.py:compute_bloom_accuracy_score) ──────

def _bloom_accuracy_score(content: str, bloom_level: str) -> float:
    """Fraction of the production verb list found; capped at 1.0.

    Denominator is half the verb list — mirrors the production gate formula so
    ablation thresholds translate directly to after_rules thresholds.
    """
    verbs = PRODUCTION_VERBS.get(bloom_level.upper(), [])
    if not verbs:
        return 0.0
    lower = content.lower()
    found = sum(1 for v in verbs if v in lower)
    return round(min(1.0, found / max(1, len(verbs) // 2)), 4)


# ── ROUGE-L (mirrors tests/eval/metrics.py) ───────────────────────────────────

def _rouge_l(hypothesis: str, reference: str) -> float:
    """ROUGE-L F1 with rouge_score library; falls back to token-overlap F1."""
    if not reference:
        return 0.0
    try:
        from rouge_score import rouge_scorer  # type: ignore
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        result = scorer.score(reference, hypothesis)
        return round(result["rougeL"].fmeasure, 4)
    except ImportError:
        hyp_tokens = set(hypothesis.lower().split())
        ref_tokens = set(reference.lower().split())
        if not ref_tokens:
            return 0.0
        overlap = hyp_tokens & ref_tokens
        p = len(overlap) / max(1, len(hyp_tokens))
        r = len(overlap) / max(1, len(ref_tokens))
        if p + r == 0:
            return 0.0
        return round(2 * p * r / (p + r), 4)


# ── Bloom accuracy ablation ───────────────────────────────────────────────────

def run_bloom_accuracy_ablation(examples: list[dict]) -> dict:
    """Sweep bloom_accuracy thresholds across the full golden set.

    All golden examples are assumed to be high-quality (they are the reference
    corpus).  The pass rate at each threshold shows how discriminating the gate
    is: a threshold that passes 95% of golden content is permissive; one that
    passes 40% is too strict for known-good material.

    The recommended threshold is the lowest value that still passes ≥ 70% of
    golden examples — i.e. the gate catches genuinely shallow content without
    rejecting most good content.
    """
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
    results = {}

    for thresh in thresholds:
        scores = [_bloom_accuracy_score(ex["content"], ex["bloom_level"]) for ex in examples]
        passed = [s for s in scores if s >= thresh]
        results[thresh] = {
            "threshold":  thresh,
            "pass_count": len(passed),
            "total":      len(scores),
            "pass_rate":  round(len(passed) / max(1, len(scores)) * 100, 1),
            "mean_score": round(sum(scores) / max(1, len(scores)), 4),
        }

    return results


# ── ROUGE-L × bloom_accuracy grid ────────────────────────────────────────────

def run_rouge_bloom_grid(examples: list[dict]) -> dict:
    """Sweep ROUGE-L threshold × bloom_accuracy threshold on examples with a reference.

    Returns a nested dict: result[rouge_thresh][bloom_thresh] = pass metrics.
    Only examples that have a non-empty reference are included.
    """
    rouge_thresholds = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
    bloom_thresholds = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]

    ref_examples = [ex for ex in examples if ex.get("reference", "").strip()]
    if not ref_examples:
        return {"note": "No examples with reference strings found; ROUGE-L sweep skipped."}

    # Pre-compute both scores for each example
    scored = []
    for ex in ref_examples:
        scored.append({
            "file":           ex["file"],
            "bloom_score":    _bloom_accuracy_score(ex["content"], ex["bloom_level"]),
            "rouge_score":    _rouge_l(ex["content"], ex["reference"]),
        })

    grid: dict = {"example_count": len(scored), "cells": {}}

    for rt in rouge_thresholds:
        grid["cells"][rt] = {}
        for bt in bloom_thresholds:
            passed = [s for s in scored if s["bloom_score"] >= bt and s["rouge_score"] >= rt]
            grid["cells"][rt][bt] = {
                "pass_count": len(passed),
                "total":      len(scored),
                "pass_rate":  round(len(passed) / max(1, len(scored)) * 100, 1),
            }

    return grid


# ── Bloom verb audit ──────────────────────────────────────────────────────────

def run_bloom_audit() -> dict:
    audit = {}
    for level in AK_VERBS:
        ak_set   = set(AK_VERBS[level])
        prod_set = set(PRODUCTION_VERBS.get(level, []))

        in_both      = ak_set & prod_set
        only_in_ak   = ak_set - prod_set       # in A&K but missing from production
        only_in_prod = prod_set - ak_set        # added beyond A&K (Nigerian extensions or custom)

        audit[level] = {
            "ak_count":      len(ak_set),
            "prod_count":    len(prod_set),
            "shared":        sorted(in_both),
            "missing_from_production": sorted(only_in_ak),
            "extensions_beyond_ak":   sorted(only_in_prod),
        }
    return audit


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--golden-dir", default="research/evaluation/golden_set")
    p.add_argument("--output",     default="research/evaluation/results/threshold_ablation.json")
    args = p.parse_args()

    golden_dir = PROJECT_ROOT / args.golden_dir
    examples   = load_golden(golden_dir)
    print(f"Loaded {len(examples)} examples from {golden_dir}\n")

    # --- Cultural threshold ablation ---
    print("=== Cultural Flag Threshold Ablation ===")
    thresh_results = run_threshold_ablation(examples)

    print(f"{'Threshold':>12}  {'Pass Rate':>10}  {'Pass/Applicable':>16}")
    print("-" * 44)
    for t, r in thresh_results.items():
        marker = "  ← current" if t == 0.60 else ""
        print(f"{t:>12.0%}  {r['pass_rate']:>9.1f}%  {r['pass_count']:>6}/{r['applicable']:<6}{marker}")

    optimal_cultural = max(
        (t for t in thresh_results if t <= 0.70),
        key=lambda t: thresh_results[t]["pass_rate"],
    )
    print(f"\nRecommended cultural threshold: {optimal_cultural:.0%} (highest pass rate ≤ 70%)")

    # --- Bloom accuracy ablation ---
    print("\n=== Bloom Accuracy Score Ablation ===")
    bloom_thresh_results = run_bloom_accuracy_ablation(examples)

    print(f"{'Threshold':>12}  {'Pass Rate':>10}  {'Pass/Total':>12}  {'Mean Score':>12}")
    print("-" * 52)
    for t, r in bloom_thresh_results.items():
        print(
            f"{t:>12.2f}  {r['pass_rate']:>9.1f}%  "
            f"{r['pass_count']:>5}/{r['total']:<5}  {r['mean_score']:>12.4f}"
        )

    # Recommended: lowest threshold that passes ≥ 70% of golden examples.
    # Golden examples are known-good; we want a threshold that rejects genuinely
    # shallow content while letting most reference-quality content through.
    passing_70pct = [t for t, r in bloom_thresh_results.items() if r["pass_rate"] >= 70.0]
    optimal_bloom = max(passing_70pct) if passing_70pct else min(bloom_thresh_results)
    print(f"\nRecommended bloom_accuracy gate: {optimal_bloom:.2f}")
    print(
        "  Interpretation (Anderson & Krathwohl 2001): content must contain "
        f"≥{optimal_bloom:.0%} of the expected-level verb set to pass without judge review."
    )

    # --- ROUGE-L × bloom_accuracy grid ---
    print("\n=== ROUGE-L × Bloom Accuracy Grid (examples with reference only) ===")
    grid = run_rouge_bloom_grid(examples)

    if "note" in grid:
        print(f"  {grid['note']}")
        optimal_rouge = None
    else:
        n = grid["example_count"]
        print(f"  ({n} examples with reference)\n")
        bloom_cols = sorted(next(iter(grid["cells"].values())).keys())
        header = f"{'ROUGE-L \\ Bloom':>16}  " + "  ".join(f"{b:.2f}" for b in bloom_cols)
        print(header)
        print("-" * len(header))
        for rt, bloom_row in sorted(grid["cells"].items()):
            row = f"{rt:>16.2f}  " + "  ".join(
                f"{bloom_row[bt]['pass_rate']:>5.1f}%" for bt in bloom_cols
            )
            print(row)

        # Optimal grid cell: highest bloom threshold where pass_rate ≥ 60%
        # (we accept that ROUGE-L pass rate will be lower since references are
        #  curriculum documents, not identical rewrites)
        best_pair = None
        best_bloom = -1.0
        for rt, bloom_row in grid["cells"].items():
            for bt, cell in bloom_row.items():
                if cell["pass_rate"] >= 60.0 and bt > best_bloom:
                    best_bloom = bt
                    best_pair = (rt, bt)
        if best_pair:
            print(f"\nRecommended gate pair: ROUGE-L ≥ {best_pair[0]:.2f}, bloom_accuracy ≥ {best_pair[1]:.2f}")
        optimal_rouge = best_pair[0] if best_pair else None

    # --- Bloom verb audit ---
    print("\n=== Bloom Verb Audit vs Anderson & Krathwohl (2001) ===")
    bloom_audit = run_bloom_audit()

    for level, info in bloom_audit.items():
        print(f"\n{level}:")
        print(f"  A&K canonical: {info['ak_count']} verbs | Production: {info['prod_count']} verbs | Shared: {len(info['shared'])}")
        if info["missing_from_production"]:
            print(f"  Missing from production (add?): {info['missing_from_production']}")
        if info["extensions_beyond_ak"]:
            print(f"  Production extensions beyond A&K: {info['extensions_beyond_ak']}")

    # Save results
    output = {
        "cultural_flag_ablation": thresh_results,
        "recommended_cultural_threshold": optimal_cultural,
        "bloom_accuracy_ablation": bloom_thresh_results,
        "recommended_bloom_accuracy_gate": optimal_bloom,
        "rouge_bloom_grid": grid,
        "recommended_rouge_l_gate": optimal_rouge,
        "bloom_verb_audit": bloom_audit,
        "citation": "Anderson, L.W. & Krathwohl, D.R. (2001). A Taxonomy for Learning, Teaching and Assessing. Longman.",
    }
    out_path = PROJECT_ROOT / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()
