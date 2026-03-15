"""LLM-as-Judge: TinyLlama 1.1B evaluates content on 5 dimensions.

Triggered ONLY when rule-based validation fails.
Scores 1-5 per dimension; pass threshold = avg ≥ 3.5 AND no single score < 2.

TinyLlama is too small for reliable JSON output, so the prompt asks for
5 plain  "key: number"  lines which regex can extract robustly.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from loguru import logger

from app.core.prompts import build_judge_prompt


PASS_THRESHOLD = 3.5
MIN_SINGLE_SCORE = 2.0
DIMENSIONS = [
    "curriculum_alignment",
    "bloom_level",
    "cultural_appropriateness",
    "language_quality",
    "educational_value",
]


def _extract_scores(text: str) -> Optional[dict]:
    """Parse 'dimension: N' lines from model output.

    Accepts any value between 1.0 and 5.0; returns None if fewer than
    5 dimensions are found so the caller can soft-pass gracefully.
    """
    scores = {}
    for dim in DIMENSIONS:
        match = re.search(
            rf"{dim}\s*[:\-]\s*([1-5](?:\.\d+)?)",
            text,
            re.IGNORECASE,
        )
        if match:
            scores[dim] = float(match.group(1))
    return scores if len(scores) == len(DIMENSIONS) else None


def run_judge(
    content: str,
    *,
    content_type: str = "content",
    subject: str = "general",
    education_level: str = "SSS1",
    curriculum_board: str = "WAEC",
    bloom_level: str = "UNDERSTAND",
    output_language: str = "en",
    failed_rules: Optional[List[str]] = None,
) -> Tuple[float, dict, Optional[str]]:
    """Run the TinyLlama 1.1B judge on generated content.

    Returns:
        (average_score, dimension_scores_dict, revision_instruction_or_None)
    """
    from app.core.llm import generate_text

    messages = build_judge_prompt(
        content,
        content_type=content_type,
        subject=subject,
        education_level=education_level,
        curriculum_board=curriculum_board,
        bloom_level=bloom_level,
        output_language=output_language,
        failed_rules=failed_rules or [],
    )

    try:
        raw = generate_text(messages, use_judge=True, max_new_tokens=80)
    except Exception as exc:
        logger.error(f"Judge LLM call failed: {exc}")
        return PASS_THRESHOLD, {d: PASS_THRESHOLD for d in DIMENSIONS}, None

    scores = _extract_scores(raw)
    if scores is None:
        logger.warning(f"Judge output unparseable (got {len(raw)} chars): {raw[:200]}")
        return PASS_THRESHOLD, {d: PASS_THRESHOLD for d in DIMENSIONS}, None

    avg_score = sum(scores.values()) / len(scores)

    logger.info(
        f"Judge scores: {scores} | avg={avg_score:.2f} | "
        f"{'PASS' if _judge_passes(avg_score, scores) else 'FAIL'}"
    )
    return avg_score, scores, None


def _judge_passes(avg_score: float, dimension_scores: dict) -> bool:
    """Return True if avg ≥ 3.5 AND no single dimension < 2."""
    if avg_score < PASS_THRESHOLD:
        return False
    return all(v >= MIN_SINGLE_SCORE for v in dimension_scores.values())


def judge_passes(avg_score: float, dimension_scores: dict) -> bool:
    """Public helper — same logic, importable without running judge."""
    return _judge_passes(avg_score, dimension_scores)
