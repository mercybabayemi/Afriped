"""Schemas for GET /api/v1/skills — skill library browser."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.common import SkillDomain


class SkillLibraryItem(BaseModel):
    skill_name: str
    skill_domain: SkillDomain
    parent_skill: Optional[str] = None
    description: str


class SkillLibraryResponse(BaseModel):
    total: int
    domains: Dict[str, List[SkillLibraryItem]]
    skills: List[SkillLibraryItem]
