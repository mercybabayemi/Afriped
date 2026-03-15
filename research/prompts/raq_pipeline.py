"""Rule-Augmented Questioning (RAQ) — 4-layer prompt pipeline.

This module defines the formal RAQ pipeline introduced in:
  "Adaptive LLM for Curriculum-Aligned Educational Content and Assessment
   in African Contexts"

The 4 layers address the core weakness of standard prompt engineering:
generating shallow, culturally generic content that passes surface-level
metrics (BLEU/ROUGE) but fails pedagogical depth tests.

Layers:
    1  Outline   — JSON-structured scope aligned to Bloom + curriculum board
    2  Expand    — Teacher-ready content expanded from the outline
    3  Retrieve  — RAG query formulated from outline for corpus retrieval
    4  Validate  — RAQ judge scoring on 5 pedagogical dimensions (1–5)

Usage:
    from research.prompts.raq_pipeline import (
        build_layer1_outline_prompt,
        build_layer2_expansion_prompt,
        build_layer3_retrieval_query,
        build_layer4_raq_judge_prompt,
    )
"""
from __future__ import annotations

from typing import Optional


# ── Shared constants ───────────────────────────────────────────────────────────

BLOOM_VERBS: dict[str, list[str]] = {
    "REMEMBER":   ["define", "list", "recall", "name", "identify", "state", "memorise"],
    "UNDERSTAND": ["explain", "describe", "summarise", "paraphrase", "interpret", "classify"],
    "APPLY":      ["solve", "use", "demonstrate", "calculate", "apply", "carry out", "execute"],
    "ANALYZE":    ["analyse", "compare", "contrast", "distinguish", "examine", "break down"],
    "EVALUATE":   ["evaluate", "justify", "assess", "critique", "judge", "argue", "defend"],
    "CREATE":     ["design", "create", "compose", "construct", "develop", "produce", "plan"],
}

CULTURAL_ANCHOR = (
    "Names: Chukwuemeka, Adaeze, Aminu, Tunde, Kofi, Ama, Fatima, Ngozi, Kwame | "
    "Places: Balogun Market, Niger River, Lake Volta, harmattan season | "
    "Institutions: WAEC, NERDC, UBEC, NABTEB, CBN, GES | "
    "Currencies: ₦ Naira / ₵ Cedis"
)


def _bloom_verbs(level: str) -> str:
    return ", ".join(BLOOM_VERBS.get(level.upper(), [level.lower()]))


# ── Layer 1 — Outline Generation ───────────────────────────────────────────────

LAYER1_SYSTEM = """You are a Nigerian curriculum specialist. Your task is to produce
a structured JSON outline aligned to the specified curriculum board and Bloom level.
Output ONLY valid JSON — no prose, no markdown fences."""

LAYER1_HUMAN = """Generate a curriculum-aligned outline for:

Subject:          {subject}
Topic:            {topic}
Grade / Level:    {education_level}
Curriculum Board: {curriculum_board}
Bloom Target:     {bloom_level} (use verbs: {bloom_verbs})
Content Type:     {content_type}
Duration:         {duration_minutes} minutes

Return this exact JSON structure:
{{
  "subject": "{subject}",
  "topic": "{topic}",
  "education_level": "{education_level}",
  "curriculum_board": "{curriculum_board}",
  "bloom_level": "{bloom_level}",
  "learning_objectives": [
    "Students will {bloom_verb_1} ...",
    "Students will {bloom_verb_2} ..."
  ],
  "core_concepts": [
    {{"concept": "...", "definition": "...", "african_example": "..."}}
  ],
  "activities": [
    {{"type": "introduction|main|practice|assessment", "description": "...", "duration_minutes": 0}}
  ],
  "assessment_question": "...",
  "retrieval_query": "..."
}}

Rules:
- Every learning objective MUST start with a Bloom verb for level {bloom_level}
- african_example MUST reference a local context ({cultural_anchor})
- retrieval_query is a 1-sentence query for the RAG vector store
- Total activity durations should sum to approximately {duration_minutes} minutes"""


def build_layer1_outline_prompt(
    subject: str,
    topic: str,
    education_level: str,
    curriculum_board: str,
    bloom_level: str,
    content_type: str = "LESSON_PLAN",
    duration_minutes: int = 40,
) -> list[dict]:
    """Layer 1 — Generate structured JSON outline.

    Returns [system, user] messages. The LLM response is a JSON outline
    that feeds directly into Layer 2 (expansion) and Layer 3 (retrieval).

    Research note: This layer is the key innovation over single-shot prompting.
    It forces explicit Bloom alignment BEFORE content expansion, reducing the
    probability of shallow or off-level outputs.
    """
    human = LAYER1_HUMAN.format(
        subject=subject,
        topic=topic,
        education_level=education_level,
        curriculum_board=curriculum_board,
        bloom_level=bloom_level,
        bloom_verbs=_bloom_verbs(bloom_level),
        bloom_verb_1=BLOOM_VERBS.get(bloom_level.upper(), ["engage with"])[0],
        bloom_verb_2=BLOOM_VERBS.get(bloom_level.upper(), ["identify"])[1] if len(BLOOM_VERBS.get(bloom_level.upper(), [])) > 1 else bloom_level.lower(),
        content_type=content_type,
        duration_minutes=duration_minutes,
        cultural_anchor=CULTURAL_ANCHOR,
    )
    return [
        {"role": "system", "content": LAYER1_SYSTEM},
        {"role": "user", "content": human},
    ]


# ── Layer 2 — Content Expansion ────────────────────────────────────────────────

LAYER2_SYSTEM = """You are AfriPed (African Pedagogical Evaluation Framework), an expert educational content specialist for
Nigerian and West African learners. Expand the provided curriculum outline into
complete, teacher-ready {content_type} content. Use culturally appropriate West African
names, places, and examples. Write in academic but accessible English appropriate
for {education_level} learners."""

LAYER2_HUMAN = """Expand the following curriculum outline into complete {content_type} content.

OUTLINE (JSON):
---
{outline_json}
---

{rag_context_block}

Expansion requirements:
- Each core concept: full explanation + worked example using African context ({cultural_anchor})
- Each activity: detailed teacher instructions + student tasks
- Assessment: one question aligned to Bloom level {bloom_level}
- Include answer key / marking guide
- Total length: approximately {target_words} words
- DO NOT restate the JSON outline — write teacher-ready prose

{format_requirements}"""

CONTENT_FORMAT_REQUIREMENTS: dict[str, str] = {
    "LESSON_PLAN": (
        "Structure with labelled sections: Lesson Overview | Learning Objectives | "
        "Materials | Introduction (warm-up) | Main Activity | Guided Practice | "
        "Assessment | Closure | (optional) Teacher Notes"
    ),
    "WORKSHEET": (
        "Student-facing worksheet with title, clear instructions, varied question types, "
        "answer spaces, and an answer key at the end."
    ),
    "EXAM_QUESTIONS": (
        "WAEC-style questions with format tag [MCQ/SHORT_ANSWER/ESSAY], "
        "Bloom tag, difficulty tag, answer, explanation, and marks per question."
    ),
    "STUDY_GUIDE": (
        "Summary notes with key terms, concept maps, worked examples, and "
        "self-check questions at the end."
    ),
}


def build_layer2_expansion_prompt(
    outline_json: str,
    content_type: str = "LESSON_PLAN",
    education_level: str = "SSS1",
    bloom_level: str = "UNDERSTAND",
    rag_context: Optional[str] = None,
    target_words: int = 500,
) -> list[dict]:
    """Layer 2 — Expand JSON outline into full educational content.

    Takes the Layer 1 JSON outline and the Layer 3 RAG context as inputs.

    Research note: Separating outline (Layer 1) from expansion (Layer 2) is
    the core RAQ innovation. In single-shot prompting the model simultaneously
    decides scope AND writes content, often under-specifying objectives.
    """
    rag_block = ""
    if rag_context:
        rag_block = (
            "RETRIEVAL CONTEXT (from Nigerian education corpus):\n"
            f"---\n{rag_context}\n---\n"
            "Incorporate relevant facts, examples, or phrasing from the above."
        )

    fmt = CONTENT_FORMAT_REQUIREMENTS.get(
        content_type.upper(), "Organise with clear headings and examples."
    )

    system = LAYER2_SYSTEM.format(
        content_type=content_type,
        education_level=education_level,
    )
    human = LAYER2_HUMAN.format(
        content_type=content_type,
        outline_json=outline_json,
        rag_context_block=rag_block,
        cultural_anchor=CULTURAL_ANCHOR,
        bloom_level=bloom_level,
        target_words=target_words,
        format_requirements=fmt,
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": human},
    ]


# ── Layer 3 — Retrieval Query Formulation ──────────────────────────────────────

def build_layer3_retrieval_query(
    subject: str,
    topic: str,
    education_level: str,
    curriculum_board: str,
    content_type: str = "LESSON_PLAN",
    outline_retrieval_query: Optional[str] = None,
) -> str:
    """Layer 3 — Formulate a retrieval query for the RAG vector store.

    If the Layer 1 outline already generated a retrieval_query field, use it;
    otherwise construct one from the request parameters.

    Returns a plain string query (not a prompt) to pass to the vector store.

    Research note: Grounding generation in a curriculum corpus (rather than
    relying on parametric LLM knowledge alone) is the RAG component of RAQ.
    The retrieval query is explicitly scoped to the curriculum board so that
    retrieved chunks are board-aligned.
    """
    if outline_retrieval_query:
        return outline_retrieval_query

    return (
        f"{curriculum_board} curriculum {subject} {topic} "
        f"{education_level} learning objectives activities assessment"
    )


# ── Layer 4 — RAQ Judge Validation ─────────────────────────────────────────────

LAYER4_SYSTEM = (
    "You are an expert pedagogical evaluator specialising in Nigerian and "
    "West African education. Score content strictly and output ONLY the 5 "
    "key:value lines — no prose, no explanation."
)

LAYER4_HUMAN = """Evaluate this {content_type} against 5 pedagogical dimensions.
Score each 1 (poor) to 5 (excellent). Reply with ONLY these 5 lines:

curriculum_alignment: <1-5>
bloom_depth: <1-5>
cultural_authenticity: <1-5>
language_quality: <1-5>
educational_value: <1-5>

Scoring criteria:
- curriculum_alignment (5=perfectly aligned to {curriculum_board} standards for {education_level})
- bloom_depth (5=content genuinely requires {bloom_level}-level cognition, not just recall)
- cultural_authenticity (5=West African names/places/institutions used naturally throughout)
- language_quality (5=clear, age-appropriate, grammatically correct {output_language})
- educational_value (5=a teacher could use this as-is; rich worked examples and tasks)

Context: {subject} | {education_level} | {curriculum_board} | Bloom:{bloom_level} | Lang:{output_language}
Rules failed: {failed_rules}
Outline used: {outline_used}

Content to evaluate:
---
{content}
---"""

# RAQ decision thresholds (used by the validation pipeline)
RAQ_PASS_THRESHOLD = 3.5      # avg score >= 3.5 → FLAGGED (approved)
RAQ_REVISE_THRESHOLD = 2.5    # avg score >= 2.5 → attempt revision
# avg score < 2.5 → FAILED


def build_layer4_raq_judge_prompt(
    content: str,
    *,
    content_type: str = "LESSON_PLAN",
    subject: str = "general",
    education_level: str = "SSS1",
    curriculum_board: str = "NERDC",
    bloom_level: str = "UNDERSTAND",
    output_language: str = "en",
    failed_rules: Optional[list[str]] = None,
    outline_used: bool = False,
) -> list[dict]:
    """Layer 4 — RAQ judge prompt.

    Enhanced version of the production judge with:
    - bloom_depth replaces generic 'bloom_level' to probe cognitive depth
    - cultural_authenticity is more explicit than 'cultural_appropriateness'
    - outline_used flag helps the judge calibrate expectations

    Research note: This is the evaluation-beyond-BLEU/ROUGE contribution.
    The 5 dimensions measure pedagogical quality orthogonal to lexical overlap.
    A content piece can score high ROUGE-L (close to reference) but low
    bloom_depth (if it copies surface phrasing without cognitive depth).
    """
    human = LAYER4_HUMAN.format(
        content=content[:3500],
        content_type=content_type,
        subject=subject,
        education_level=education_level,
        curriculum_board=curriculum_board,
        bloom_level=bloom_level,
        output_language=output_language,
        failed_rules=", ".join(failed_rules or []) or "none",
        outline_used="yes (Layer 1 outline was used)" if outline_used else "no (single-shot)",
    )
    return [
        {"role": "system", "content": LAYER4_SYSTEM},
        {"role": "user", "content": human},
    ]


def parse_layer4_scores(judge_output: str) -> dict[str, float]:
    """Parse the 5-line Layer 4 judge output into a scores dict.

    Returns:
        {
          "curriculum_alignment": float,
          "bloom_depth": float,
          "cultural_authenticity": float,
          "language_quality": float,
          "educational_value": float,
          "average": float,
        }
    """
    import re

    dimensions = [
        "curriculum_alignment",
        "bloom_depth",
        "cultural_authenticity",
        "language_quality",
        "educational_value",
    ]
    scores: dict[str, float] = {}
    for dim in dimensions:
        match = re.search(rf"{dim}\s*:\s*([1-5](?:\.\d+)?)", judge_output, re.IGNORECASE)
        if match:
            scores[dim] = float(match.group(1))

    if scores:
        scores["average"] = round(sum(scores[d] for d in dimensions if d in scores) / len(scores), 3)
    return scores


# ── Full pipeline convenience wrapper ──────────────────────────────────────────

def raq_pipeline_summary() -> str:
    """Return a human-readable summary of the RAQ pipeline for paper methods section."""
    return """\
RAQ Pipeline Summary
====================

Layer 1 — Outline Generation
  Input : subject, topic, level, board, Bloom target
  Output: JSON outline {objectives, concepts, activities, retrieval_query}
  Role  : Forces explicit curriculum scope BEFORE content generation

Layer 2 — Content Expansion
  Input : Layer 1 JSON outline + Layer 3 RAG context
  Output: Full teacher-ready content (~300–600 words)
  Role  : Expands grounded outline into pedagogically rich material

Layer 3 — RAG Retrieval
  Input : retrieval_query from Layer 1 outline
  Output: Top-k chunks from Nigerian education corpus (ChromaDB)
  Role  : Grounds generation in real curriculum data

Layer 4 — RAQ Validation
  Input : Generated content + generation context
  Output: 5 dimension scores (1–5) + PASSED/FLAGGED/REVISED/FAILED status
  Role  : Replaces BLEU/ROUGE with pedagogically meaningful metrics

Decision logic:
  all 8 rules pass          → PASSED
  soft rule fail + avg ≥ 3.5 → FLAGGED (approved)
  hard rule fail             → FAILED (no judge)
  avg < 3.5                  → REVISED (up to 2 retries)
  avg < 2.5 after retries    → FAILED
"""
