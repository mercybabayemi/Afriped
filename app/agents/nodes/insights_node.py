"""Pillar 4 — Insights & Diagnostics node."""
from __future__ import annotations

import json
import re
from typing import List

from loguru import logger

from app.agents.state import AfriPedState
from app.skills.library import get_skill_library


def _flesch_kincaid_grade(text: str) -> float:
    """Approximate Flesch-Kincaid Grade Level."""
    try:
        import textstat  # type: ignore
        return textstat.flesch_kincaid_grade(text)
    except ImportError:
        sentences = max(1, len(re.findall(r"[.!?]+", text)))
        words = max(1, len(text.split()))
        syllables = sum(_count_syllables(w) for w in text.split())
        return 0.39 * (words / sentences) + 11.8 * (syllables / words) - 15.59


def _count_syllables(word: str) -> int:
    word = word.lower().strip(".,;:!?\"'")
    if len(word) <= 3:
        return 1
    count = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e"):
        count = max(1, count - 1)
    return max(1, count)


def _complexity_band(grade: float) -> str:
    if grade < 4:
        return "Very Easy (Primary)"
    elif grade < 7:
        return "Easy (Upper Primary / JSS)"
    elif grade < 10:
        return "Moderate (SSS)"
    elif grade < 13:
        return "Advanced (Tertiary)"
    return "Very Advanced"


BLOOM_VERB_SETS = {
    "REMEMBER":   ["define", "list", "recall", "name", "identify", "state"],
    "UNDERSTAND": ["explain", "describe", "summarise", "paraphrase", "interpret", "classify"],
    "APPLY":      ["solve", "use", "demonstrate", "calculate", "apply", "carry out"],
    "ANALYZE":    ["analyse", "compare", "contrast", "distinguish", "examine", "differentiate"],
    "EVALUATE":   ["evaluate", "justify", "assess", "critique", "judge", "argue"],
    "CREATE":     ["design", "create", "compose", "construct", "develop", "produce"],
}

LOCAL_NAMES = {
    "chukwuemeka", "adaeze", "aminu", "tunde", "kofi", "ama", "fatima",
    "emeka", "ngozi", "kwame", "abena", "bola", "sola", "kemi", "biodun",
    "chioma", "nkechi", "uchenna", "obiora", "chiamaka", "obinna", "chidi",
    "aisha", "musa", "ibrahim", "halima", "zainab", "binta", "garba",
    "efua", "akosua", "adjoa", "esi", "yaw", "kojo", "nana", "afia",
}
WESTERN_NAMES = {
    "john", "james", "peter", "michael", "david", "william", "robert",
    "mary", "jennifer", "jessica", "emily", "sarah", "elizabeth", "lisa",
    "matthew", "andrew", "daniel", "christopher", "mark", "joshua",
}
LOCAL_EXAMPLES = [
    "balogun market", "kejetia market", "niger river", "lake volta",
    "harmattan", "sahel", "naira", "cedis", "nnpc", "cbn", "waec", "ubec",
    "neco", "nabteb", "ges", "bece", "lagos", "abuja", "accra", "kumasi",
    "kano", "ibadan", "enugu", "port harcourt",
]


def _analyse_bloom(text: str):
    lower = text.lower()
    detected = {}
    for level, verbs in BLOOM_VERB_SETS.items():
        found = [v for v in verbs if v in lower]
        if found:
            detected[level] = found
    if not detected:
        return {"detected_level": "UNKNOWN", "verbs_found": [], "confidence": 0.0}
    top_level = max(detected, key=lambda k: len(detected[k]))
    all_verbs = [v for vlist in detected.values() for v in vlist]
    return {
        "detected_level": top_level,
        "verbs_found": all_verbs,
        "level_breakdown": {k: v for k, v in detected.items()},
        "confidence": min(1.0, len(all_verbs) / 5),
    }


def _analyse_cultural(text: str):
    lower = text.lower()
    words = re.findall(r"\b[a-z]+\b", lower)
    name_words = [w for w in words if w in LOCAL_NAMES or w in WESTERN_NAMES]
    local_name_count = sum(1 for w in name_words if w in LOCAL_NAMES)
    western_name_count = sum(1 for w in name_words if w in WESTERN_NAMES)
    total_names = max(1, local_name_count + western_name_count)
    local_ratio = local_name_count / total_names

    local_ex_count = sum(1 for ex in LOCAL_EXAMPLES if ex in lower)

    flags = []
    if local_ratio < 0.4 and total_names > 1:
        flags.append("Low local name ratio — consider using more West African names")
    if local_ex_count < 2:
        flags.append("Few local examples — add references to Nigerian/Ghanaian contexts")

    return {
        "local_name_ratio": round(local_ratio, 2),
        "western_name_count": western_name_count,
        "local_name_count": local_name_count,
        "local_example_count": local_ex_count,
        "flags": flags,
    }


def insights_node(state: AfriPedState) -> AfriPedState:
    """Run all enabled diagnostic checks and populate state with results."""
    request = state.get("request")
    if request is None:
        return {**state, "error": "No request in state"}

    content = getattr(request, "content", "")
    if not content:
        return {**state, "error": "No content provided for analysis"}

    results: dict = {}

    # ── Readability ────────────────────────────────────────────────────────────
    if getattr(request, "run_readability", True):
        grade = _flesch_kincaid_grade(content)
        results["readability"] = {
            "flesch_kincaid_grade": round(grade, 1),
            "complexity_band": _complexity_band(grade),
            "word_count": len(content.split()),
            "sentence_count": len(re.findall(r"[.!?]+", content)),
        }

    # ── Bloom analysis ─────────────────────────────────────────────────────────
    if getattr(request, "run_bloom_analysis", True):
        results["bloom_analysis"] = _analyse_bloom(content)

    # ── Cultural analysis ──────────────────────────────────────────────────────
    if getattr(request, "run_cultural_analysis", True):
        results["cultural_analysis"] = _analyse_cultural(content)

    # ── Skill detection ────────────────────────────────────────────────────────
    lib = get_skill_library()
    detected_tags = lib.match_from_text(content)

    # ── Skill gap analysis ─────────────────────────────────────────────────────
    skill_gap: dict | None = None
    if getattr(request, "run_skill_gap_analysis", True) and request.expected_skills:
        expected_names = set(s.lower() for s in request.expected_skills)
        detected_names = set(t.skill_name.lower() for t in detected_tags)
        missing = expected_names - detected_names
        extra = detected_names - expected_names
        skill_gap = {
            "expected": list(expected_names),
            "detected": list(detected_names),
            "missing_from_content": list(missing),
            "extra_skills_found": list(extra),
            "coverage_ratio": round(
                len(expected_names & detected_names) / max(1, len(expected_names)), 2
            ),
        }

    # ── Overall quality score (composite) ─────────────────────────────────────
    scores = []
    bloom = results.get("bloom_analysis", {})
    if bloom:
        scores.append(min(1.0, bloom.get("confidence", 0.5)))

    cultural = results.get("cultural_analysis", {})
    if cultural:
        flags_penalty = len(cultural.get("flags", [])) * 0.15
        scores.append(max(0.0, 1.0 - flags_penalty))

    if skill_gap:
        scores.append(skill_gap.get("coverage_ratio", 0.5))

    overall = round(sum(scores) / max(1, len(scores)), 2) if scores else 0.5

    # ── Recommendations ────────────────────────────────────────────────────────
    recommendations: List[str] = []
    for flag in cultural.get("flags", []):
        recommendations.append(flag)
    if bloom.get("detected_level") == "UNKNOWN":
        recommendations.append("Add explicit Bloom-level verbs to clarify cognitive demand")
    if skill_gap and skill_gap.get("missing_from_content"):
        missing_list = ", ".join(list(skill_gap["missing_from_content"])[:3])
        recommendations.append(f"Expected skills not found in content: {missing_list}")

    state["skill_tags"] = detected_tags
    return {
        **state,
        "structured_output": {
            "readability": results.get("readability", {}),
            "bloom_analysis": results.get("bloom_analysis", {}),
            "cultural_analysis": results.get("cultural_analysis", {}),
            "skill_tags_detected": [t.to_dict() for t in detected_tags],
            "skill_gap_analysis": skill_gap,
            "overall_quality_score": overall,
            "recommendations": recommendations,
        },
        "error": None,
    }
