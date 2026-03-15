"""
CPU hardware characterization benchmark.

Measures generation time, RAM usage, and tokens/sec per content type
on the current hardware (no GPU). Outputs a report suitable for the paper's
infrastructure equity section.

Run:
    python research/evaluation/hardware_benchmark.py
    python research/evaluation/hardware_benchmark.py --quick   # 1 sample per type
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

RESULTS_DIR = PROJECT_ROOT / "research" / "evaluation" / "results"

# Benchmark prompts — one per content type, realistic length
BENCHMARK_PROMPTS = {
    "lesson_plan": [
        {"role": "system", "content": "You are an expert Nigerian educator. Generate a complete, structured lesson plan."},
        {"role": "user",   "content": (
            "Generate a detailed lesson plan for SSS2 Biology (NERDC board). "
            "Topic: Photosynthesis. Bloom level: ANALYZE. "
            "Include: Learning Objectives, Instructional Materials, Introduction (5 min), "
            "Main Lesson (25 min), Class Activity, Assessment, and Homework. "
            "Use Nigerian student names and context. Max 800 words."
        )},
    ],
    "exam_questions": [
        {"role": "system", "content": "You are a WAEC examination question writer for Nigerian secondary schools."},
        {"role": "user",   "content": (
            "Write 5 WAEC-style Chemistry examination questions for SSS3 level. "
            "Topic: Electrochemistry. Bloom level: EVALUATE. "
            "Include 2 objective questions with options A-D, and 3 structured questions "
            "with mark allocations. Use Nigerian context in at least two questions."
        )},
    ],
    "scheme_of_work": [
        {"role": "system", "content": "You are a curriculum specialist aligned with the NERDC scheme of work."},
        {"role": "user",   "content": (
            "Generate a complete Term 1 scheme of work for JSS3 Mathematics (NERDC). "
            "Cover 10 weeks. For each week include: topic, specific objectives (Bloom level: APPLY), "
            "instructional materials, and assessment method. "
            "Subjects: Number and Numeration, Algebraic Processes, Geometry."
        )},
    ],
    "insights": [
        {"role": "system", "content": "You are a pedagogical analyst evaluating educational content quality."},
        {"role": "user",   "content": (
            "Analyse the following lesson note and provide: "
            "(1) Bloom taxonomy level classification with evidence, "
            "(2) cultural authenticity score with specific examples, "
            "(3) readability assessment for SSS1 level, "
            "(4) three specific improvement recommendations aligned to NERDC standards. "
            "Content: 'Students will understand photosynthesis by reading the textbook and answering questions.'"
        )},
    ],
}


def _ram_mb() -> float:
    if HAS_PSUTIL:
        return psutil.Process().memory_info().rss / 1024 / 1024
    return 0.0


def _system_ram() -> dict:
    if not HAS_PSUTIL:
        return {}
    vm = psutil.virtual_memory()
    return {
        "total_gb":     round(vm.total / 1024**3, 1),
        "available_gb": round(vm.available / 1024**3, 1),
        "used_pct":     vm.percent,
    }


def _cpu_info() -> dict:
    if not HAS_PSUTIL:
        return {}
    try:
        import platform
        freq = psutil.cpu_freq()
        return {
            "cpu_count_logical":  psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_freq_mhz":       round(freq.current, 0) if freq else None,
            "platform":           platform.processor() or platform.machine(),
        }
    except Exception:
        return {}


def run_single(content_type: str, messages: list[dict], max_tokens: int = 512) -> dict:
    from app.core.llm import generate_text
    import torch

    ram_before = _ram_mb()
    t_start = time.perf_counter()

    output = generate_text(messages, use_judge=False, max_new_tokens=max_tokens)

    elapsed = time.perf_counter() - t_start
    ram_after = _ram_mb()

    n_tokens = len(output.split())  # word-level approximation
    tps = n_tokens / elapsed if elapsed > 0 else 0

    return {
        "content_type":    content_type,
        "elapsed_sec":     round(elapsed, 1),
        "elapsed_min":     round(elapsed / 60, 2),
        "output_words":    n_tokens,
        "tokens_per_sec":  round(tps, 2),
        "ram_before_mb":   round(ram_before, 0),
        "ram_after_mb":    round(ram_after, 0),
        "ram_delta_mb":    round(ram_after - ram_before, 0),
        "gpu":             torch.cuda.is_available(),
        "output_preview":  output[:200],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--quick",     action="store_true", help="1 sample per type (faster)")
    p.add_argument("--reps",      type=int, default=2,  help="Repetitions per content type")
    p.add_argument("--output",    default="research/evaluation/results/hardware_benchmark.json")
    args = p.parse_args()

    reps = 1 if args.quick else args.reps
    output_path = PROJECT_ROOT / args.output
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=== AfriPed — CPU Hardware Benchmark ===\n")
    system_info = {
        "ram":       _system_ram(),
        "cpu":       _cpu_info(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    print(f"System: {system_info['cpu']}")
    print(f"RAM:    {system_info['ram']}\n")

    print("Loading models (pre-warm)...")
    from app.core.llm import get_phi_pipeline
    get_phi_pipeline()
    print("Models loaded.\n")

    all_results = []
    summary = {}

    for ct, messages in BENCHMARK_PROMPTS.items():
        print(f"Benchmarking: {ct} ({reps} rep{'s' if reps > 1 else ''})...")
        times, tps_list = [], []

        for rep in range(reps):
            result = run_single(ct, messages, max_tokens=512)
            all_results.append({**result, "rep": rep + 1})
            times.append(result["elapsed_sec"])
            tps_list.append(result["tokens_per_sec"])
            print(f"  rep {rep+1}: {result['elapsed_sec']:.1f}s | {result['tokens_per_sec']:.1f} tok/s | "
                  f"RAM delta: {result['ram_delta_mb']:.0f} MB")

        avg_time = sum(times) / len(times)
        avg_tps  = sum(tps_list) / len(tps_list)
        summary[ct] = {
            "avg_sec":    round(avg_time, 1),
            "avg_min":    round(avg_time / 60, 2),
            "avg_tps":    round(avg_tps, 2),
        }

    print("\n=== Summary ===")
    print(f"{'Content Type':<20} {'Avg Time':>10} {'Avg tok/s':>10}")
    print("-" * 44)
    for ct, s in summary.items():
        print(f"{ct:<20} {s['avg_sec']:>8.1f}s  {s['avg_tps']:>9.2f}")

    total_min = sum(s["avg_min"] for s in summary.values())
    print(f"\nEstimated full session (all 4 types): {total_min:.1f} min")

    output = {
        "system_info": system_info,
        "per_run":     all_results,
        "summary":     summary,
        "total_session_min": round(total_min, 2),
        "note": (
            "Benchmark run on CPU-only hardware. No GPU acceleration. "
            "Token count is word-based approximation (output.split()). "
            "RAM delta reflects process RSS growth during generation."
        ),
    }
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results saved to {output_path}")


if __name__ == "__main__":
    main()
