"""Skill tagging node — maps generated content to Enum Skill Library entries."""
from __future__ import annotations

from loguru import logger

from app.agents.state import AfriPedState
from app.skills.library import get_skill_library
from app.schemas.common import SkillTag


def skill_tag_node(state: AfriPedState) -> AfriPedState:
    """Auto-tag generated content with matching skill library entries.

    Strategy:
    1. If the request specifies target_skills → resolve those directly.
    2. Run keyword matching over the generated content.
    3. Merge both lists (target skills first, then detected).
    """
    content = state.get("generated_content") or ""
    request = state.get("request")
    lib = get_skill_library()

    tags: list[SkillTag] = []
    seen: set[str] = set()

    # 1. Explicitly requested skills take priority
    target_skills: list[str] = []
    if request:
        goals = getattr(request, "pedagogical_goals", None)
        if goals:
            target_skills = getattr(goals, "target_skills", []) or []
        else:
            target_skills = getattr(request, "target_skills", []) or []

    for raw_tag in lib.match_from_targets(target_skills):
        if raw_tag.skill_name not in seen:
            seen.add(raw_tag.skill_name)
            tags.append(SkillTag(
                skill_name=raw_tag.skill_name,
                skill_domain=raw_tag.skill_domain,
                parent_skill=raw_tag.parent_skill,
            ))

    # 2. Keyword-match the generated content
    domain_filter = None
    if request:
        goals = getattr(request, "pedagogical_goals", None)
        if goals:
            sd = getattr(goals, "skill_domain", None)
            if sd:
                domain_filter = sd.value if hasattr(sd, "value") else str(sd)

    if content:
        for raw_tag in lib.match_from_text(content, domain_filter=domain_filter):
            if raw_tag.skill_name not in seen:
                seen.add(raw_tag.skill_name)
                tags.append(SkillTag(
                    skill_name=raw_tag.skill_name,
                    skill_domain=raw_tag.skill_domain,
                    parent_skill=raw_tag.parent_skill,
                ))

    logger.info(f"[skill_tag_node] Tagged {len(tags)} skills ({len(target_skills)} from request)")
    return {**state, "skill_tags": tags}
