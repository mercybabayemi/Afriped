"""GET /api/v1/skills — Enum Skill Library browser."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.skills import SkillLibraryItem, SkillLibraryResponse
from app.skills.library import get_skill_library

router = APIRouter()


@router.get("/skills", response_model=SkillLibraryResponse)
async def list_skills(
    domain: Optional[str] = Query(None, description="Filter by domain: technical | behavioral | cognitive | language"),
):
    """Return all skills from the Enum Skill Library, optionally filtered by domain."""
    lib = get_skill_library()

    if domain:
        items_raw = lib.get_by_domain(domain)
    else:
        items_raw = lib.get_all()

    items = [
        SkillLibraryItem(
            skill_name=i.skill_name,
            skill_domain=i.skill_domain,
            parent_skill=i.parent_skill,
            description=i.description,
        )
        for i in items_raw
    ]

    # Group by domain for the domains dict
    domains: dict = {}
    for item in items:
        domains.setdefault(item.skill_domain, []).append(item)

    return SkillLibraryResponse(
        total=len(items),
        domains=domains,
        skills=items,
    )
