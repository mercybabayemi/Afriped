"""Pillar 3 — Assessment & Question Bank generation node."""
from __future__ import annotations

import re
from typing import List, Optional

from loguru import logger

from app.agents.state import AfriPedState
from app.core.llm import generate_text
from app.core.prompts import build_assessment_prompt
from app.schemas.assessment import QuestionItem
from app.schemas.common import SkillTag


def _parse_questions(raw: str, request) -> List[QuestionItem]:
    """Parse structured question output from LLM text."""
    questions: List[QuestionItem] = []

    # Split on question markers: Q1. / 1. / Question 1
    blocks = re.split(r"(?=^Q?\d+[\.\)]\s)", raw, flags=re.MULTILINE)

    for i, block in enumerate(blocks, start=1):
        if not block.strip():
            continue

        # Extract tags from header line: [MCQ] [Bloom: APPLY] [Difficulty: MEDIUM] [Skills: ...]
        format_match = re.search(r"\[([A-Z_]+)\]", block)
        bloom_match = re.search(r"\[Bloom:\s*([A-Z]+)\]", block, re.IGNORECASE)
        diff_match = re.search(r"\[Difficulty:\s*([A-Z]+)\]", block, re.IGNORECASE)

        skill_match = re.search(r"\[Skills?:\s*([^\]]+)\]", block, re.IGNORECASE)

        q_format = format_match.group(1) if format_match else (
            request.question_format.value if hasattr(request.question_format, "value") else "MIXED"
        )
        bloom = bloom_match.group(1).upper() if bloom_match else (
            request.bloom_level.value if hasattr(request.bloom_level, "value") else "UNDERSTAND"
        )
        difficulty = diff_match.group(1).upper() if diff_match else (
            request.difficulty.value if hasattr(request.difficulty, "value") else "MEDIUM"
        )

        # Extract skill tags from inline text
        skill_tags: List[SkillTag] = []
        if skill_match:
            from app.skills.library import get_skill_library
            lib = get_skill_library()
            skill_names = [s.strip() for s in skill_match.group(1).split(",")]
            skill_tags = lib.match_from_targets(skill_names)

        # Extract question text (first line after header, before "Answer:")
        lines = block.strip().splitlines()
        q_text_lines = []=j 
        options_lines = []
        answer_text: Optional[str] = None
        explanation_text: Optional[str] = None
        marks: Optional[int] = None

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.lower().startswith("answer:"):
                answer_text = stripped[7:].strip()
            elif stripped.lower().startswith("explanation:"):
                explanation_text = stripped[12:].strip()
            elif stripped.lower().startswith("marks:"):
                try:
                    marks = int(re.search(r"\d+", stripped).group())
                except Exception:
                    pass
            elif re.match(r"^[A-Da-d][\.\)]\s", stripped):
                options_lines.append(stripped)
            elif not any(stripped.upper().startswith(tag) for tag in ["[", "Q", "QUESTION"]):
                if stripped:
                    q_text_lines.append(stripped)

        q_text = " ".join(q_text_lines).strip() or f"Question {i}"

        questions.append(QuestionItem(
            question_number=i,
            question_text=q_text,
            question_format=q_format,
            bloom_level=bloom,
            difficulty=difficulty,
            skill_tags=skill_tags,
            topic_tags=[getattr(request, "topic", "")],
            options=options_lines if options_lines else None,
            answer=answer_text,
            explanation=explanation_text,
            marks=marks or 1,
        ))

    return questions[:getattr(request, "num_questions", 10)]


def assessment_node(state: AfriPedState) -> AfriPedState:
    """Generate assessment questions for Pillar 3."""
    request = state.get("request")
    if request is None:
        return {**state, "error": "No request in state", "generated_content": None}

    rag_context = state.get("rag_context")
    max_tokens = getattr(request, "max_tokens", 128)

    try:
        messages = build_assessment_prompt(request, rag_context=rag_context)
        raw = generate_text(messages, max_new_tokens=max_tokens)
        logger.info(f"[assessment_node] Generated {len(raw)} chars")

        questions = _parse_questions(raw, request)
        logger.info(f"[assessment_node] Parsed {len(questions)} questions")

        return {
            **state,
            "generated_content": raw,
            "structured_output": {"questions": [q.model_dump() for q in questions]},
            "error": None,
        }
    except Exception as exc:
        logger.error(f"[assessment_node] Generation failed: {exc}")
        return {**state, "generated_content": None, "structured_output": None, "error": str(exc)}
