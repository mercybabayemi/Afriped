"""POST /api/v1/curriculum/generate — Pillar 1."""
from __future__ import annotations

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.agents.graph import get_compiled_graph
from app.core.config import settings
from app.schemas.common import RAGMetadata, SkillTag, ValidationReport, ValidationStatus
from app.schemas.curriculum import CurriculumGenerationRequest, CurriculumGenerationResponse

router = APIRouter()


@router.post("/curriculum/generate", response_model=CurriculumGenerationResponse)
async def generate_curriculum(request: CurriculumGenerationRequest):
    """Generate a curriculum artefact (scheme of work, term plan, etc.)."""
    if not request.request_id:
        request.request_id = str(uuid.uuid4())

    state = {
        "pillar": "curriculum",
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

    content = final_state.get("generated_content") or ""
    skill_tags_raw = final_state.get("skill_tags") or []
    skill_tags = [
        SkillTag(
            skill_name=t.skill_name if hasattr(t, "skill_name") else t["skill_name"],
            skill_domain=t.skill_domain if hasattr(t, "skill_domain") else t["skill_domain"],
            parent_skill=t.parent_skill if hasattr(t, "parent_skill") else t.get("parent_skill"),
        )
        for t in skill_tags_raw
    ]

    validation = final_state.get("validation_report") or ValidationReport(
        status=ValidationStatus.PASSED,
        rules_passed=[],
        rules_failed=[],
    )

    rag_meta = final_state.get("rag_metadata")

    # Count topics (rough heuristic: lines starting with "Week" or numbered)
    import re
    num_topics = len(re.findall(r"(?i)week\s*\d+|^\d+\.", content, re.MULTILINE))

    return CurriculumGenerationResponse(
        request_id=request.request_id,
        curriculum_output=content,
        output_type=request.output_type.value,
        subject=request.subject.value,
        education_level=request.education_level.value,
        curriculum_board=request.curriculum_board.value,
        num_topics_generated=num_topics,
        skill_tags=skill_tags,
        validation=validation,
        rag_metadata=rag_meta,
        model_used=settings.main_model_id,
        generation_time_seconds=elapsed,
        token_count=len(content.split()),
        created_at=datetime.utcnow(),
        warnings=[],
    )
