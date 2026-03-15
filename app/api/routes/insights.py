"""POST /api/v1/insights/analyze — Pillar 4."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.agents.graph import get_compiled_graph
from app.schemas.common import SkillTag
from app.schemas.insights import InsightsRequest, InsightsResponse

router = APIRouter()


@router.post("/insights/analyze", response_model=InsightsResponse)
async def analyze_insights(request: InsightsRequest):
    """Run diagnostic analysis on provided educational content."""
    if not request.request_id:
        request.request_id = str(uuid.uuid4())

    state = {
        "pillar": "insights",
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

    try:
        graph = get_compiled_graph()
        final_state = graph.invoke(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    if final_state.get("error"):
        raise HTTPException(status_code=500, detail=final_state["error"])

    structured = final_state.get("structured_output") or {}
    skill_tags_raw = final_state.get("skill_tags") or structured.get("skill_tags_detected", [])

    skill_tags = [
        SkillTag(
            skill_name=t.skill_name if hasattr(t, "skill_name") else t["skill_name"],
            skill_domain=t.skill_domain if hasattr(t, "skill_domain") else t["skill_domain"],
            parent_skill=t.parent_skill if hasattr(t, "parent_skill") else t.get("parent_skill"),
        )
        for t in skill_tags_raw
    ]

    return InsightsResponse(
        request_id=request.request_id,
        readability=structured.get("readability", {}),
        bloom_analysis=structured.get("bloom_analysis", {}),
        cultural_analysis=structured.get("cultural_analysis", {}),
        skill_tags_detected=skill_tags,
        skill_gap_analysis=structured.get("skill_gap_analysis"),
        curriculum_coverage=structured.get("curriculum_coverage"),
        gap_analysis=structured.get("gap_analysis"),
        overall_quality_score=structured.get("overall_quality_score", 0.0),
        recommendations=structured.get("recommendations", []),
        created_at=datetime.utcnow(),
    )
