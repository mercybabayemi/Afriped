"""
Expand the golden evaluation set from 20 to 200 examples.

Systematically varies: content_type x bloom_level x board x subject
to generate diverse configurations. Outputs annotated JSON files
compatible with benchmark.py.

Run:
    python research/evaluation/expand_golden_set.py --dry-run
    python research/evaluation/expand_golden_set.py --count 200
    python research/evaluation/expand_golden_set.py --count 200 --spot-check-pct 30
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from itertools import product
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR    = PROJECT_ROOT / "research" / "evaluation" / "golden_set_v2"
SPOT_CHECK_DIR = PROJECT_ROOT / "research" / "evaluation" / "spot_check"

random.seed(42)

# ── Parameter space ────────────────────────────────────────────────────────────

CONTENT_TYPES = ["lesson_plan", "exam_questions", "scheme_of_work", "insights"]

BLOOM_LEVELS = ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]

BOARDS_LEVELS = {
    "NERDC": ["JSS2", "JSS3", "SSS1", "SSS2", "SSS3"],
    "WAEC":  ["SSS2", "SSS3"],
    "NECO":  ["SSS3"],
    "NABTEB":["VOCATIONAL_ADVANCED"],
    "UBEC":  ["PRIMARY_5", "PRIMARY_6"],
}

SUBJECTS_BY_BOARD = {
    "NERDC":  ["Mathematics", "Biology", "Chemistry", "Physics", "English Language",
               "Geography", "Economics", "Civic Education", "Agricultural Science",
               "Computer Studies", "Government", "History", "Home Economics"],
    "WAEC":   ["Mathematics", "Biology", "Chemistry", "Physics", "Geography",
               "Economics", "Government", "Literature in English", "Agricultural Science"],
    "NECO":   ["Mathematics", "Biology", "Chemistry", "Physics", "Economics"],
    "NABTEB": ["Electrical Installation", "Auto Mechanics", "Catering and Hotel Services",
               "Computer Craft Practice", "Building Construction"],
    "UBEC":   ["Mathematics", "English Language", "Basic Science", "Social Studies",
               "Agricultural Science"],
}

LANGUAGES = ["en", "en", "en", "en", "yo", "ha"]  # weighted toward English

# ── Bloom verb banks (for auto-annotation) ────────────────────────────────────

BLOOM_VERBS = {
    "REMEMBER":   ["define", "list", "recall", "identify", "state", "name"],
    "UNDERSTAND": ["explain", "describe", "summarise", "classify", "interpret"],
    "APPLY":      ["solve", "calculate", "demonstrate", "apply", "use", "show"],
    "ANALYZE":    ["analyse", "compare", "contrast", "examine", "differentiate"],
    "EVALUATE":   ["evaluate", "justify", "assess", "critique", "judge", "argue"],
    "CREATE":     ["design", "create", "compose", "construct", "develop", "propose"],
}

# ── Content type skill mappings ───────────────────────────────────────────────

SKILL_TAGS_BY_TYPE = {
    "lesson_plan":    ["lesson_planning", "curriculum_design", "pedagogical_structuring"],
    "exam_questions": ["assessment_design", "question_construction", "bloom_alignment"],
    "scheme_of_work": ["curriculum_planning", "term_structuring", "scope_and_sequence"],
    "insights":       ["content_analysis", "bloom_classification", "readability_assessment"],
}

# ── Format requirements (for format_compliance auto-annotation) ───────────────

FORMAT_MARKERS = {
    "lesson_plan":    ["objective", "activity", "assessment"],
    "exam_questions": ["question", "answer", "mark"],
    "scheme_of_work": ["week", "term", "objective"],
    "insights":       ["analysis", "recommendation", "level"],
}

# ── Reference text generator (for ROUGE baseline) ────────────────────────────

def _reference(content_type: str, subject: str, board: str, bloom: str, level: str) -> str:
    verb = BLOOM_VERBS[bloom][0]
    if content_type == "lesson_plan":
        return (
            f"Lesson Plan: {subject} | {board} | {level}\n"
            f"Objective: Students will {verb} key concepts in {subject}.\n"
            f"Activity: Guided class exercise with Nigerian context examples.\n"
            f"Assessment: Short quiz to check understanding."
        )
    elif content_type == "exam_questions":
        return (
            f"WAEC-style {subject} questions at {level}.\n"
            f"1. {verb.capitalize()} the key principles of {subject}. [5 marks]\n"
            f"2. Apply your knowledge to a Nigerian context scenario. [10 marks]"
        )
    elif content_type == "scheme_of_work":
        return (
            f"Scheme of Work: {subject} | {board} | {level}\n"
            f"Week 1: Introduction. Week 2: Core concepts. Week 3: Application.\n"
            f"Term objective: Students will {verb} all major topics."
        )
    else:
        return (
            f"Insights: {subject} content analysis for {level} level.\n"
            f"Bloom level detected: {bloom}. Recommendation: add more {verb} activities."
        )


def _make_example(
    content_type: str,
    bloom_level: str,
    board: str,
    level: str,
    subject: str,
    language: str,
    idx: int,
) -> dict:
    verb = random.choice(BLOOM_VERBS[bloom_level])
    skill_tags = SKILL_TAGS_BY_TYPE[content_type]
    fmt_markers = FORMAT_MARKERS[content_type]

    # Generate a plausible output text for this configuration
    if content_type == "lesson_plan":
        generated = (
            f"LESSON PLAN\nSubject: {subject} | Class: {level} | Board: {board}\n\n"
            f"Objective: By the end of this lesson, students will be able to "
            f"{verb} the key concepts in {subject} as specified by the {board} curriculum.\n\n"
            f"Activity: Students work in groups of four. Each group receives a scenario "
            f"card based on a familiar Nigerian context. They must {verb} the relevant "
            f"concept and present their findings to the class. Names used: Chidi, Fatima, "
            f"Ngozi, Aminu, Taiwo, Adaeze.\n\n"
            f"Assessment: Exit quiz of five questions. Students scoring below 40% receive "
            f"guided practice. Marks allocated per {board} continuous assessment guidelines."
        )
    elif content_type == "exam_questions":
        generated = (
            f"{board} EXAMINATION — {subject} | {level}\n\n"
            f"Question 1: {verb.capitalize()} the fundamental principles of {subject}. "
            f"Use examples relevant to the Nigerian context. [8 marks]\n\n"
            f"Question 2: A student named Ngozi is studying {subject}. She must "
            f"{verb} the relationship between two key concepts. Explain the steps "
            f"she should follow and justify each step. [12 marks]\n\n"
            f"Question 3: Evaluate the importance of {subject} in the Nigerian "
            f"secondary school curriculum. Support your answer with specific examples. [10 marks]"
        )
    elif content_type == "scheme_of_work":
        generated = (
            f"SCHEME OF WORK: {subject} | {board} | {level}\n\n"
            f"Term 1, Week 1: Introduction to {subject}. Objective: Students {verb} core definitions.\n"
            f"Term 1, Week 2: Principles and theories. Objective: Students explain key frameworks.\n"
            f"Term 1, Week 3: Application. Objective: Students apply concepts to Nigerian scenarios.\n"
            f"Term 1, Week 4: Analysis. Objective: Students compare and contrast approaches.\n"
            f"Term 1, Week 5: Evaluation. Objective: Students justify their reasoning.\n"
            f"Term 1, Week 6: Revision and assessment. Objective: Students demonstrate full understanding."
        )
    else:  # insights
        generated = (
            f"CONTENT ANALYSIS — {subject} | {level}\n\n"
            f"Bloom Level Detected: {bloom_level}\n"
            f"Cultural Authenticity: Nigerian names and contexts present (Aminu, Kemi, Okonkwo)\n"
            f"Readability: Appropriate for {level} level\n"
            f"Format Compliance: All required sections present\n"
            f"Recommendations: Content effectively requires students to {verb}. "
            f"Consider adding more open-ended questions targeting the EVALUATE level."
        )

    return {
        "id": f"gen_{content_type}_{bloom_level}_{board}_{level}_{subject.replace(' ', '_')}_{idx:04d}",
        "generated": generated,
        "reference": _reference(content_type, subject, board, bloom_level, level),
        "metadata": {
            "content_type": content_type,
            "bloom_level": bloom_level,
            "board": board,
            "education_level": level,
            "subject": subject,
            "output_language": language,
            "generation_method": "systematic_parameter_variation",
        },
        "expected": {
            "bloom_level": bloom_level,
            "output_language": language,
            "skill_tags": skill_tags,
            "format_markers": fmt_markers,
        },
        "spot_check_required": False,  # set externally for 30% sample
        "human_validated": False,
        "annotation_notes": "",
    }


def build_parameter_grid(count: int) -> list[dict]:
    """Build a balanced parameter grid of `count` configurations."""
    configs = []
    # Full combinatorial pass first
    for ct, bloom, (board, levels) in product(
        CONTENT_TYPES, BLOOM_LEVELS, BOARDS_LEVELS.items()
    ):
        for level in levels:
            subjects = SUBJECTS_BY_BOARD.get(board, [])
            for subject in subjects[:3]:  # cap per board to keep diversity
                lang = random.choice(LANGUAGES)
                configs.append((ct, bloom, board, level, subject, lang))

    random.shuffle(configs)
    configs = configs[:count]

    examples = []
    for idx, (ct, bloom, board, level, subject, lang) in enumerate(configs):
        examples.append(_make_example(ct, bloom, board, level, subject, lang, idx))

    # Mark 30% for spot check
    spot_indices = random.sample(range(len(examples)), k=max(1, len(examples) * 30 // 100))
    for i in spot_indices:
        examples[i]["spot_check_required"] = True

    return examples


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--count",           type=int, default=200)
    p.add_argument("--spot-check-pct",  type=int, default=30)
    p.add_argument("--dry-run",         action="store_true")
    args = p.parse_args()

    print(f"Building {args.count} evaluation examples...")
    examples = build_parameter_grid(args.count)

    if args.dry_run:
        from collections import Counter
        print(f"Total: {len(examples)}")
        print("By content_type:", Counter(e["metadata"]["content_type"] for e in examples))
        print("By bloom_level:",  Counter(e["metadata"]["bloom_level"]  for e in examples))
        print("By board:",        Counter(e["metadata"]["board"]        for e in examples))
        print(f"Spot check ({args.spot_check_pct}%): {sum(1 for e in examples if e['spot_check_required'])}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SPOT_CHECK_DIR.mkdir(parents=True, exist_ok=True)

    for ex in examples:
        fname = f"{ex['id']}.json"
        with open(OUTPUT_DIR / fname, "w") as f:
            json.dump(ex, f, indent=2)
        if ex["spot_check_required"]:
            with open(SPOT_CHECK_DIR / fname, "w") as f:
                json.dump(ex, f, indent=2)

    spot_count = sum(1 for e in examples if e["spot_check_required"])
    print(f"Written {len(examples)} examples to {OUTPUT_DIR}")
    print(f"Spot check ({spot_count} examples, {spot_count*100//len(examples)}%) written to {SPOT_CHECK_DIR}")
    print(f"\nNext step: manually review files in {SPOT_CHECK_DIR}")
    print("Set 'human_validated': true and fill 'annotation_notes' for each reviewed file.")


if __name__ == "__main__":
    main()
