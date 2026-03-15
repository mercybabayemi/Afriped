"""POST /api/v1/assessment/generate — Pillar 3."""
from __future__ import annotations

import time
import uuid
from collections import Counter
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from app.agents.graph import get_compiled_graph
from app.schemas.assessment import (
    AssessmentGenerationRequest,
    AssessmentGenerationResponse,
    QuestionItem,
)
from app.core.config import settings
from app.schemas.common import SkillTag, ValidationReport, ValidationStatus

router = APIRouter()


def _build_distributions(questions: List[QuestionItem]) -> tuple[dict, dict, dict]:
    bloom_dist = Counter(q.bloom_level for q in questions)
    diff_dist = Counter(q.difficulty for q in questions)
    skill_dist: Counter = Counter()
    for q in questions:
        for tag in q.skill_tags:
            skill_dist[tag.skill_name] += 1
    return dict(bloom_dist), dict(diff_dist), dict(skill_dist)


@router.post("/assessment/generate", response_model=AssessmentGenerationResponse)
async def generate_assessment(request: AssessmentGenerationRequest):
    """Generate WAEC-style assessment questions with per-question skill tags."""
    if not request.request_id:
        request.request_id = str(uuid.uuid4())

    state = {
        "pillar": "assessment",
        "request": request,
        "rag_context": None,
        "rag_metadata": None,
        "generated_content": None,
        "structured_output": None,
        "skill_tags": [],
        "validation_report": None,
        "revision_instruction": None,
        "revision_count": 0,
        "final_content": None,
        "error": None,
    }

    t0 = time.time()
    try:
        graph = get_compiled_graph()
        final_state = graph.invoke(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")

    elapsed = round(time.time() - t0, 2)

    if final_state.get("error"):
        raise HTTPException(status_code=500, detail=final_state["error"])

    raw_output = final_state.get("generated_content") or ""
    structured = final_state.get("structured_output") or {}
    raw_questions = structured.get("questions", [])

    questions: List[QuestionItem] = []
    for q_dict in raw_questions:
        # Re-inflate SkillTag objects
        st_raw = q_dict.pop("skill_tags", [])
        skill_tags = [
            SkillTag(
                skill_name=t["skill_name"],
                skill_domain=t["skill_domain"],
                parent_skill=t.get("parent_skill"),
            )
            for t in st_raw
        ]
        questions.append(QuestionItem(**q_dict, skill_tags=skill_tags))

    bloom_dist, diff_dist, skill_dist = _build_distributions(questions)
    total_marks = sum(q.marks or 1 for q in questions)
    est_duration = total_marks * 2  # 2 min per mark heuristic

    validation = final_state.get("validation_report") or ValidationReport(
        status=ValidationStatus.PASSED,
        rules_passed=[],
        rules_failed=[],
    )

    return AssessmentGenerationResponse(
        request_id=request.request_id,
        assessment_type=request.assessment_type.value,
        subject=request.subject.value,
        topic=request.topic,
        curriculum_board=request.curriculum_board.value,
        questions=questions,
        raw_output=raw_output,
        total_marks=total_marks,
        estimated_duration_minutes=est_duration,
        bloom_distribution=bloom_dist,
        difficulty_distribution=diff_dist,
        skill_distribution=skill_dist,
        validation=validation,
        rag_metadata=final_state.get("rag_metadata"),
        model_used=settings.main_model_id,
        generation_time_seconds=elapsed,
        created_at=datetime.utcnow(),
        warnings=[],
    )
