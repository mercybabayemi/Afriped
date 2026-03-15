"""All prompt templates for the four AfriPed pillars."""
from __future__ import annotations

from typing import List, Optional

from app.schemas.common import BloomLevel, Language


# ── Bloom verb banks ───────────────────────────────────────────────────────────

BLOOM_VERBS: dict[str, List[str]] = {
    BloomLevel.REMEMBER:   ["define", "list", "recall", "name", "identify", "state", "memorise"],
    BloomLevel.UNDERSTAND: ["explain", "describe", "summarise", "paraphrase", "interpret", "classify", "give examples of"],
    BloomLevel.APPLY:      ["solve", "use", "demonstrate", "calculate", "apply", "carry out", "execute"],
    BloomLevel.ANALYZE:    ["analyse", "compare", "contrast", "distinguish", "examine", "break down", "differentiate"],
    BloomLevel.EVALUATE:   ["evaluate", "justify", "assess", "critique", "judge", "argue", "defend"],
    BloomLevel.CREATE:     ["design", "create", "compose", "construct", "develop", "produce", "plan"],
}

# ── Language-specific instruction map ─────────────────────────────────────────

LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "en":    "Use clear, age-appropriate English.",
    "yo":    "Write in Yoruba with correct tonal diacritics (ẹ, ọ, gb, sh, etc.). Follow Onwu orthography.",
    "ha":    "Write in standard Hausa orthography with tonal marks where required.",
    "ig":    "Write in Igbo using Onwu orthography — the official Nigerian standard.",
    "igl":   "Write in Igala language. Use standard orthographic conventions.",
    "pcm":   "Write in Nigerian Pidgin (Naijá). Use natural spoken patterns.",
    "en-yo": "Write primarily in English; introduce Yoruba terms for key concepts and label them clearly.",
    "en-ha": "Write primarily in English; introduce Hausa terms for key concepts and label them clearly.",
    "en-ig": "Write primarily in English; introduce Igbo terms for key concepts and label them clearly.",
    "tw":    "Write in Twi (Akan). Use standard Asante Twi orthography.",
    "ee":    "Write in Ewe. Use standard Ewe orthographic conventions.",
}

# ── Cultural anchors always injected ──────────────────────────────────────────

CULTURAL_NAMES = "Chukwuemeka, Adaeze, Aminu, Tunde, Kofi, Ama, Fatima, Emeka, Ngozi, Kwame, Abena"
CULTURAL_PLACES = "Balogun Market, Kejetia Market, Niger River, Lake Volta, the Sahel, harmattan season"
CULTURAL_INSTITUTIONS = "NNPC, CBN, GES, WAEC, UBEC, NECO, NABTEB"
CULTURAL_CURRENCIES = "₦ Naira (Nigeria) / ₵ Cedis (Ghana)"

CULTURAL_ANCHOR_BLOCK = f"""
Cultural anchors (use where relevant):
- Names: {CULTURAL_NAMES}
- Places and landmarks: {CULTURAL_PLACES}
- Institutions: {CULTURAL_INSTITUTIONS}
- Currencies: {CULTURAL_CURRENCIES}
""".strip()

# ── Base system prompt ─────────────────────────────────────────────────────────

BASE_SYSTEM = """You are AfriPed (African Pedagogical Evaluation Framework), an expert educational content specialist for Nigerian and West African learners.
You generate culturally authentic, curriculum-aligned educational materials across formal schooling, vocational training, community education, life skills, and youth programmes.

Core principles:
1. Always align content to the specified curriculum board ({curriculum_board}) standards.
2. Target the stated education level ({education_level}) and Bloom's level ({bloom_level}).
3. Use culturally appropriate names, examples, currencies (₦/₵), and institutions.
4. Write in the specified language: {output_language}. {language_instruction}
5. Integrate the target skills: {target_skills}.
6. Never fabricate exam board policies, dates, or official regulations.

{cultural_anchors}
"""


# ── Environment format addendum ────────────────────────────────────────────────

ENV_INSTRUCTIONS: dict[str, str] = {
    "STANDARD_DIGITAL":  "Format for on-screen reading. Use headings, bullet points, tables where helpful.",
    "LOW_BANDWIDTH":     "Use plain text only. No tables. No markdown. Short paragraphs.",
    "PRINT_READY":       "Format for printing. Use clear section headings. Avoid colour references.",
    "OFFLINE_COMMUNITY": "Use simple, spoken-style language. Avoid technical jargon. Format for oral delivery or community posters.",
}


# ── Helper to render Bloom verbs ───────────────────────────────────────────────

def _bloom_verb_str(bloom_level: str) -> str:
    verbs = BLOOM_VERBS.get(bloom_level, [])
    return ", ".join(verbs) if verbs else bloom_level.lower()


# ── Pillar 1 — Curriculum prompt ───────────────────────────────────────────────

CURRICULUM_HUMAN = """Generate a {output_type} for:
- Subject: {subject}
- Education Level: {education_level}
- Curriculum Board: {curriculum_board}
- Number of Terms: {num_terms}
- Weeks per Term: {num_weeks_per_term}
- Output Language: {output_language}
- Bloom Target: {bloom_level} (use verbs: {bloom_verbs})
- Target Skills: {target_skills}
- Learning Objectives: {learning_objectives}
- Duration per session: {duration_minutes} minutes
- Environment: {environment}
{topics_block}
{rag_block}
{resource_block}
{assessment_schedule_block}
{cultural_block}

{format_instructions}
"""

CURRICULUM_FORMAT = """Format the scheme of work as a structured table or hierarchical outline with:
- Term / Week numbers
- Topic / Sub-topic
- Learning objectives (using Bloom verbs)
- Teaching activities
- Learning resources
- Assessment method
{resource_line}
{assessment_line}

Ensure every topic aligns with {curriculum_board} standards for {education_level} {subject}."""


def build_curriculum_prompt(
    request,
    rag_context: Optional[str] = None,
) -> list[dict]:
    """Build [system, user] messages for curriculum generation."""
    lang_code = request.output_language.value if hasattr(request.output_language, "value") else request.output_language
    bloom = request.pedagogical_goals.bloom_level
    bloom_val = bloom.value if hasattr(bloom, "value") else str(bloom)

    system = BASE_SYSTEM.format(
        curriculum_board=request.curriculum_board.value,
        education_level=request.education_level.value,
        bloom_level=bloom_val,
        output_language=lang_code,
        language_instruction=LANGUAGE_INSTRUCTIONS.get(lang_code, ""),
        target_skills=", ".join(request.pedagogical_goals.target_skills) or "general curriculum skills",
        cultural_anchors=CULTURAL_ANCHOR_BLOCK,
    )

    topics_block = ""
    if request.topics:
        topics_block = f"- Specified topics to cover: {', '.join(request.topics)}"

    rag_block = ""
    if rag_context:
        rag_block = f"\nRelevant curriculum reference material:\n---\n{rag_context}\n---"

    resource_block = "- Include recommended resources (textbooks, community materials)" if request.include_resources else ""
    assessment_schedule_block = "- Include an assessment schedule with dates/weeks" if request.include_assessment_schedule else ""

    env_val = request.environment.value if hasattr(request.environment, "value") else str(request.environment)

    format_instr = CURRICULUM_FORMAT.format(
        curriculum_board=request.curriculum_board.value,
        education_level=request.education_level.value,
        subject=request.subject.value,
        resource_line="- Teaching/learning resources column" if request.include_resources else "",
        assessment_line="- Assessment schedule column" if request.include_assessment_schedule else "",
    )

    cultural_notes = ""
    ctx = request.cultural_context
    if ctx.custom_cultural_notes:
        cultural_notes = f"Additional cultural notes: {ctx.custom_cultural_notes}"
    elif ctx.use_local_examples:
        cultural_notes = "Use local West African / Nigerian examples throughout."

    human = CURRICULUM_HUMAN.format(
        output_type=request.output_type.value,
        subject=request.subject.value,
        education_level=request.education_level.value,
        curriculum_board=request.curriculum_board.value,
        num_terms=request.num_terms,
        num_weeks_per_term=request.num_weeks_per_term,
        output_language=lang_code,
        bloom_level=bloom_val,
        bloom_verbs=_bloom_verb_str(bloom_val),
        target_skills=", ".join(request.pedagogical_goals.target_skills) or "none specified",
        learning_objectives="\n  - ".join(request.pedagogical_goals.learning_objectives) or "To be determined by teacher",
        duration_minutes=request.pedagogical_goals.duration_minutes or "standard period",
        environment=ENV_INSTRUCTIONS.get(env_val, ""),
        topics_block=topics_block,
        rag_block=rag_block,
        resource_block=resource_block,
        assessment_schedule_block=assessment_schedule_block,
        cultural_block=cultural_notes,
        format_instructions=format_instr,
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": human},
    ]


# ── Pillar 2 — Content Generation prompt ──────────────────────────────────────

CONTENT_HUMAN = """Create a {content_type} on the topic: "{topic}"

- Subject: {subject}
- Education Level: {education_level}
- Curriculum Board: {curriculum_board}
- Output Language: {output_language}
- Bloom Target: {bloom_level} (verbs: {bloom_verbs})
- Target Skills: {target_skills}
- Learning Objectives:
  - {learning_objectives}
- Duration: {duration_minutes}
- Environment: {environment}
{teacher_notes_block}
{answer_key_block}
{rag_block}
{cultural_block}

{format_instructions}

Begin the content immediately. Do NOT restate the parameters above as a header or preamble.
"""

CONTENT_FORMAT_MAP: dict[str, str] = {
    "LESSON_PLAN": (
        "You MUST include all of these labelled sections in this order:\n"
        "1. Lesson Overview — subject, topic, class, duration\n"
        "2. Learning Objective(s) — Bloom-aligned goals (use the word 'Objective')\n"
        "3. Materials and Resources\n"
        "4. Introduction / Warm-up (5–10 min)\n"
        "5. Main Activity — teaching steps and student tasks (use the word 'Activity')\n"
        "6. Guided Practice\n"
        "7. Assessment — how learning will be checked (use the word 'Assessment')\n"
        "8. Closure and Summary\n"
        "{teacher_notes_section}"
    ),
    "WORKSHEET": (
        "Create a student-facing worksheet with:\n"
        "- Clear title and instructions\n"
        "- Varied question types matching Bloom level\n"
        "- Space for answers\n"
        "{answer_key_section}"
    ),
    "STORY": (
        "Write a narrative story that:\n"
        "- Features West African characters and settings\n"
        "- Embeds the educational concept naturally\n"
        "- Is age-appropriate for the education level\n"
        "- Ends with 2–3 comprehension questions"
    ),
    "FLASHCARDS": (
        "Generate flashcard pairs (Front | Back) in a table:\n"
        "- At least 10 cards\n"
        "- Cover key terms, concepts, and examples"
    ),
    "VOCATIONAL_GUIDE": (
        "Structure the vocational guide with:\n"
        "1. Trade/Skill overview\n"
        "2. Tools and materials (with local suppliers where relevant)\n"
        "3. Step-by-step procedure\n"
        "4. Safety precautions\n"
        "5. Quality checks\n"
        "6. Income/business potential in Nigeria/Ghana"
    ),
    "COMMUNITY_AWARENESS": (
        "Write a community awareness material:\n"
        "- Simple, spoken-style language\n"
        "- Clear call-to-action\n"
        "- Localised examples\n"
        "- Suitable for notice boards, radio announcements, or community meetings"
    ),
}

DEFAULT_CONTENT_FORMAT = (
    "Organise the content clearly with headings, sub-headings, and examples. "
    "Make it educationally rigorous yet accessible."
)


def build_content_prompt(
    request,
    rag_context: Optional[str] = None,
) -> list[dict]:
    """Build [system, user] messages for content generation."""
    lang_code = request.output_language.value if hasattr(request.output_language, "value") else request.output_language
    bloom = request.pedagogical_goals.bloom_level
    bloom_val = bloom.value if hasattr(bloom, "value") else str(bloom)
    content_type = request.content_type.value if hasattr(request.content_type, "value") else str(request.content_type)

    system = BASE_SYSTEM.format(
        curriculum_board=request.curriculum_board.value,
        education_level=request.learner_profile.education_level.value,
        bloom_level=bloom_val,
        output_language=lang_code,
        language_instruction=LANGUAGE_INSTRUCTIONS.get(lang_code, ""),
        target_skills=", ".join(request.pedagogical_goals.target_skills) or "general skills",
        cultural_anchors=CULTURAL_ANCHOR_BLOCK,
    )

    env_val = request.environment.value if hasattr(request.environment, "value") else str(request.environment)
    teacher_notes_block = "- Include teacher notes section at the end" if request.include_teacher_notes else ""
    answer_key_block = "- Include an answer key / marking guide" if request.include_answer_key else ""

    rag_block = ""
    if rag_context:
        rag_block = f"\nRelevant curriculum reference material:\n---\n{rag_context}\n---"

    ctx = request.cultural_context
    if ctx.custom_cultural_notes:
        cultural_block = f"Cultural guidance: {ctx.custom_cultural_notes}"
    elif ctx.use_local_examples and ctx.use_local_names:
        cultural_block = "Use local West African names, places, and examples throughout."
    else:
        cultural_block = ""

    fmt_template = CONTENT_FORMAT_MAP.get(content_type, DEFAULT_CONTENT_FORMAT)
    format_instructions = fmt_template.format(
        teacher_notes_section="10. Teacher Notes (methodology, differentiation tips)" if request.include_teacher_notes else "",
        answer_key_section="\n**Answer Key** (at end)" if request.include_answer_key else "",
    )

    human = CONTENT_HUMAN.format(
        content_type=content_type,
        topic=request.topic,
        subject=request.subject.value,
        education_level=request.learner_profile.education_level.value,
        curriculum_board=request.curriculum_board.value,
        output_language=lang_code,
        bloom_level=bloom_val,
        bloom_verbs=_bloom_verb_str(bloom_val),
        target_skills=", ".join(request.pedagogical_goals.target_skills) or "none specified",
        learning_objectives="\n  - ".join(request.pedagogical_goals.learning_objectives) or "Teacher-defined",
        duration_minutes=request.pedagogical_goals.duration_minutes or "standard period",
        environment=ENV_INSTRUCTIONS.get(env_val, ""),
        teacher_notes_block=teacher_notes_block,
        answer_key_block=answer_key_block,
        rag_block=rag_block,
        cultural_block=cultural_block,
        format_instructions=format_instructions,
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": human},
    ]


# ── Pillar 3 — Assessment prompt ───────────────────────────────────────────────

ASSESSMENT_HUMAN = """Generate {num_questions} {question_format} questions for a {assessment_type} on:
- Subject: {subject}
- Topic: {topic}
- Education Level: {education_level}
- Curriculum Board: {curriculum_board}
- Bloom Level: {bloom_level} (verbs: {bloom_verbs})
- Difficulty: {difficulty}
- Target Skills: {target_skills}
- Output Language: {output_language}
{answer_key_block}
{marking_guide_block}
{bloom_tag_block}
{difficulty_tag_block}
{topic_tag_block}
{rag_block}
{cultural_block}

{format_instructions}
"""

ASSESSMENT_FORMAT = """For each question, use this exact format:

Q{{n}}. [{{FORMAT}}] [Bloom: {{BLOOM}}] [Difficulty: {{DIFFICULTY}}] [Skills: {{SKILLS}}]
{{question text}}
{{options if MCQ}}
Answer: {{answer}}
Explanation: {{brief explanation}}
Marks: {{marks}}

Use WAEC-style phrasing. Every question must be clearly answerable from the topic."""


def build_assessment_prompt(
    request,
    rag_context: Optional[str] = None,
) -> list[dict]:
    """Build [system, user] messages for assessment generation."""
    lang_code = request.output_language.value if hasattr(request.output_language, "value") else request.output_language
    bloom_val = request.bloom_level.value if hasattr(request.bloom_level, "value") else str(request.bloom_level)
    assessment_type = request.assessment_type.value if hasattr(request.assessment_type, "value") else str(request.assessment_type)
    question_format = request.question_format.value if hasattr(request.question_format, "value") else str(request.question_format)
    difficulty = request.difficulty.value if hasattr(request.difficulty, "value") else str(request.difficulty)

    system = BASE_SYSTEM.format(
        curriculum_board=request.curriculum_board.value,
        education_level=request.learner_profile.education_level.value,
        bloom_level=bloom_val,
        output_language=lang_code,
        language_instruction=LANGUAGE_INSTRUCTIONS.get(lang_code, ""),
        target_skills=", ".join(request.target_skills) or "general skills",
        cultural_anchors=CULTURAL_ANCHOR_BLOCK,
    )

    answer_key_block = "- Include answer key at end" if request.include_answer_key else ""
    marking_guide_block = "- Include a marking guide with point allocation" if request.include_marking_guide else ""
    bloom_tag_block = "- Tag each question with its Bloom level" if request.include_bloom_tags else ""
    difficulty_tag_block = "- Tag each question with its difficulty (EASY/MEDIUM/HARD)" if request.include_difficulty_tags else ""
    topic_tag_block = "- Tag each question with relevant topic keywords" if request.include_topic_tags else ""

    rag_block = ""
    if rag_context:
        rag_block = f"\nRelevant curriculum reference:\n---\n{rag_context}\n---"

    ctx = request.cultural_context
    cultural_block = "Use local West African names and real-world contexts." if ctx.use_local_names else ""

    human = ASSESSMENT_HUMAN.format(
        num_questions=request.num_questions,
        question_format=question_format,
        assessment_type=assessment_type,
        subject=request.subject.value,
        topic=request.topic,
        education_level=request.learner_profile.education_level.value,
        curriculum_board=request.curriculum_board.value,
        bloom_level=bloom_val,
        bloom_verbs=_bloom_verb_str(bloom_val),
        difficulty=difficulty,
        target_skills=", ".join(request.target_skills) or "none specified",
        output_language=lang_code,
        answer_key_block=answer_key_block,
        marking_guide_block=marking_guide_block,
        bloom_tag_block=bloom_tag_block,
        difficulty_tag_block=difficulty_tag_block,
        topic_tag_block=topic_tag_block,
        rag_block=rag_block,
        cultural_block=cultural_block,
        format_instructions=ASSESSMENT_FORMAT,
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": human},
    ]


# ── Pillar 4 — Insights prompt ─────────────────────────────────────────────────

INSIGHTS_SYSTEM = """You are AfriPed Diagnostics, an expert at analysing educational content quality.
Evaluate the provided content across multiple dimensions and return a structured JSON analysis."""

INSIGHTS_HUMAN = """Analyse the following educational content for quality and curriculum alignment:

CONTENT:
---
{content}
---

Content type: {content_type}
Subject: {subject}
Education level: {education_level}
Curriculum board: {curriculum_board}
Expected Bloom level: {expected_bloom_level}
Expected language: {expected_language}
Expected skills: {expected_skills}

Provide a JSON analysis with keys:
- "bloom_analysis": {{"detected_level": str, "verbs_found": [str], "confidence": float}}
- "cultural_analysis": {{"local_name_ratio": float, "local_example_count": int, "flags": [str]}}
- "recommendations": [str]
- "overall_quality_score": float (0.0-1.0)
"""


def build_insights_prompt(request) -> list[dict]:
    """Build [system, user] messages for insights analysis."""
    subject_val = request.subject.value if request.subject and hasattr(request.subject, "value") else str(request.subject or "unspecified")
    level_val = request.education_level.value if request.education_level and hasattr(request.education_level, "value") else str(request.education_level or "unspecified")
    board_val = request.curriculum_board.value if request.curriculum_board and hasattr(request.curriculum_board, "value") else str(request.curriculum_board or "unspecified")
    bloom_val = request.expected_bloom_level.value if request.expected_bloom_level and hasattr(request.expected_bloom_level, "value") else "unspecified"
    lang_val = request.expected_language.value if request.expected_language and hasattr(request.expected_language, "value") else "unspecified"

    human = INSIGHTS_HUMAN.format(
        content=request.content[:3000],  # truncate very long content
        content_type=request.content_type,
        subject=subject_val,
        education_level=level_val,
        curriculum_board=board_val,
        expected_bloom_level=bloom_val,
        expected_language=lang_val,
        expected_skills=", ".join(request.expected_skills or []) or "not specified",
    )

    return [
        {"role": "system", "content": INSIGHTS_SYSTEM},
        {"role": "user", "content": human},
    ]


# ── Judge prompt ───────────────────────────────────────────────────────────────

JUDGE_SYSTEM = "You are an educational content quality scorer. You only output scores as numbers."

JUDGE_HUMAN = """Score this {content_type} content on 5 dimensions (1=poor, 5=excellent).
Reply with ONLY these 5 lines — no other text, no explanation:

curriculum_alignment: <1-5>
bloom_level: <1-5>
cultural_appropriateness: <1-5>
language_quality: <1-5>
educational_value: <1-5>

Context: {subject} | {education_level} | {curriculum_board} | Bloom:{bloom_level} | Lang:{output_language}
Failed rules: {failed_rules}

Content:
---
{content}
---"""


def build_judge_prompt(
    content: str,
    *,
    content_type: str = "content",
    subject: str = "general",
    education_level: str = "SSS1",
    curriculum_board: str = "WAEC",
    bloom_level: str = "UNDERSTAND",
    output_language: str = "en",
    failed_rules: List[str] = None,
) -> list[dict]:
    """Build [system, user] messages for the TinyLlama judge."""
    human = JUDGE_HUMAN.format(
        content=content[:3000],
        content_type=content_type,
        subject=subject,
        education_level=education_level,
        curriculum_board=curriculum_board,
        bloom_level=bloom_level,
        output_language=output_language,
        failed_rules=", ".join(failed_rules or []) or "none",
    )
    return [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": human},
    ]


# ── Revision prompt ────────────────────────────────────────────────────────────

REVISE_HUMAN = """The following educational content was flagged for quality issues.

ORIGINAL CONTENT:
---
{original_content}
---

REVISION INSTRUCTION:
{revision_instruction}

FAILED QUALITY RULES:
{failed_rules}

Please rewrite the content addressing all the issues above while maintaining educational value and cultural authenticity."""


def build_revision_prompt(
    original_content: str,
    revision_instruction: str,
    failed_rules: List[str],
    system_context: str,
) -> list[dict]:
    """Build [system, user] messages for the revision node."""
    human = REVISE_HUMAN.format(
        original_content=original_content[:3000],
        revision_instruction=revision_instruction,
        failed_rules="\n- ".join(failed_rules) if failed_rules else "none",
    )
    return [
        {"role": "system", "content": system_context},
        {"role": "user", "content": human},
    ]
