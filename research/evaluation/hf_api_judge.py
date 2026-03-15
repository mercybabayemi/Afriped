"""
Benchmark-only judge using HF Inference API (Mistral-7B-Instruct or Zephyr-7B).

NOT used in production — used only to validate golden set annotations
and report agreement between TinyLlama (production) and a stronger model.

Usage:
    # Set HF token in .env or pass directly
    python research/evaluation/hf_api_judge.py --golden-dir research/evaluation/golden_set
    python research/evaluation/hf_api_judge.py --golden-dir research/evaluation/golden_set_v2
    python research/evaluation/hf_api_judge.py --compare  # compare TinyLlama vs Zephyr
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# HF Inference API endpoint — Zephyr-7B-beta is free for small volumes
HF_MODEL = "HuggingFaceH4/zephyr-7b-beta"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

DIMENSIONS = [
    "curriculum_alignment",
    "bloom_level",
    "cultural_appropriateness",
    "language_quality",
    "educational_value",
]

PASS_THRESHOLD = 3.5


def _get_token() -> str:
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN", "")
    if not token:
        # Try loading from .env
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("HF_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"')
    return token


def _build_judge_prompt(content: str, metadata: dict) -> str:
    board     = metadata.get("board", "NERDC")
    level     = metadata.get("education_level", "SSS1")
    bloom     = metadata.get("bloom_level", "UNDERSTAND")
    lang      = metadata.get("output_language", "en")
    ct        = metadata.get("content_type", "lesson_plan")

    return f"""You are an expert evaluator of Nigerian educational content.

Rate the following {ct} generated for a {board} {level} class.
Target Bloom taxonomy level: {bloom}. Language: {lang}.

Score each dimension from 1 (very poor) to 5 (excellent).
Output ONLY these 5 lines, nothing else:

curriculum_alignment: <score>
bloom_level: <score>
cultural_appropriateness: <score>
language_quality: <score>
educational_value: <score>

CONTENT TO EVALUATE:
{content[:1500]}"""


def _parse_scores(text: str) -> Optional[dict]:
    scores = {}
    for dim in DIMENSIONS:
        m = re.search(rf"{dim}\s*[:\-]\s*([1-5](?:\.\d+)?)", text, re.IGNORECASE)
        if m:
            scores[dim] = float(m.group(1))
    return scores if len(scores) == len(DIMENSIONS) else None


def call_hf_api(prompt: str, token: str, retries: int = 3) -> Optional[str]:
    try:
        import requests
    except ImportError:
        print("pip install requests")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 80, "temperature": 0.1, "return_full_text": False},
    }

    for attempt in range(retries):
        try:
            resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 503:
                # Model loading — wait and retry
                wait = resp.json().get("estimated_time", 20)
                print(f"  Model loading, waiting {wait:.0f}s...")
                time.sleep(min(wait, 30))
                continue
            if resp.status_code == 200:
                result = resp.json()
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", "")
            print(f"  API error {resp.status_code}: {resp.text[:100]}")
        except Exception as e:
            print(f"  Request error: {e}")
        time.sleep(2 ** attempt)
    return None


def judge_file(path: Path, token: str) -> Optional[dict]:
    with open(path) as f:
        ex = json.load(f)

    content  = ex.get("generated", ex.get("content", ""))
    metadata = ex.get("metadata", {})

    if not content:
        return None

    prompt   = _build_judge_prompt(content, metadata)
    raw      = call_hf_api(prompt, token)

    if not raw:
        return None

    scores = _parse_scores(raw)
    if not scores:
        print(f"  Unparseable output for {path.name}: {raw[:100]}")
        return None

    avg = sum(scores.values()) / len(scores)
    return {
        "file": path.name,
        "zephyr_scores": scores,
        "zephyr_avg": round(avg, 3),
        "zephyr_pass": avg >= PASS_THRESHOLD,
        "raw_output": raw,
    }


def run_on_dir(golden_dir: Path, token: str, output_path: Path) -> list[dict]:
    files = sorted(golden_dir.glob("*.json"))
    print(f"Judging {len(files)} files from {golden_dir} using {HF_MODEL}...")

    results = []
    for i, f in enumerate(files):
        print(f"  [{i+1}/{len(files)}] {f.name}", end=" ")
        result = judge_file(f, token)
        if result:
            results.append(result)
            print(f"avg={result['zephyr_avg']:.2f} {'PASS' if result['zephyr_pass'] else 'FAIL'}")
        else:
            print("SKIP")
        time.sleep(0.5)  # rate limiting

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {output_path}")
    return results


def compare_judges(zephyr_results: list[dict], golden_dir: Path) -> None:
    """Compute agreement between TinyLlama production scores and Zephyr API scores."""
    print("\n=== Judge Agreement Analysis ===")

    agreements = []
    for r in zephyr_results:
        fname = golden_dir / r["file"]
        if not fname.exists():
            continue
        with open(fname) as f:
            ex = json.load(f)

        # Check if production judge score exists in the example
        prod_score = None
        if "raq_report" in ex and "judge_score" in ex["raq_report"]:
            prod_score = ex["raq_report"]["judge_score"]
        elif "judge_score" in ex:
            prod_score = ex["judge_score"]

        if prod_score is None:
            continue

        prod_pass    = prod_score >= PASS_THRESHOLD
        zephyr_pass  = r["zephyr_pass"]
        agree        = prod_pass == zephyr_pass
        agreements.append(agree)

        print(f"  {r['file'][:40]:40s} prod={prod_score:.2f} zephyr={r['zephyr_avg']:.2f} {'AGREE' if agree else 'DISAGREE'}")

    if agreements:
        pct = sum(agreements) / len(agreements) * 100
        print(f"\nAgreement: {sum(agreements)}/{len(agreements)} = {pct:.1f}%")
    else:
        print("No production judge scores found in golden set files for comparison.")
        print("Tip: run benchmark.py first to populate judge_score fields.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--golden-dir", default="research/evaluation/golden_set")
    p.add_argument("--output",     default="research/evaluation/results/zephyr_judge.json")
    p.add_argument("--compare",    action="store_true", help="Compare Zephyr vs TinyLlama scores")
    p.add_argument("--token",      default="", help="HF API token (or set HF_TOKEN env var)")
    args = p.parse_args()

    token = args.token or _get_token()
    if not token:
        print("ERROR: HF_TOKEN not set. Add to .env or pass --token <your_token>")
        print("Get a free token at https://huggingface.co/settings/tokens")
        sys.exit(1)

    golden_dir  = PROJECT_ROOT / args.golden_dir
    output_path = PROJECT_ROOT / args.output

    results = run_on_dir(golden_dir, token, output_path)

    if args.compare and results:
        compare_judges(results, golden_dir)

    # Summary stats
    if results:
        avg_scores = [r["zephyr_avg"] for r in results]
        pass_rate  = sum(1 for r in results if r["zephyr_pass"]) / len(results)
        print(f"\nZephyr Judge Summary (N={len(results)}):")
        print(f"  Mean score:  {sum(avg_scores)/len(avg_scores):.3f}")
        print(f"  Pass rate:   {pass_rate:.1%}")


if __name__ == "__main__":
    main()
