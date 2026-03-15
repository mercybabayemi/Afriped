"""LangGraph StateGraph — master orchestration for all 4 pillars."""
from __future__ import annotations

from typing import Literal

from langgraph.graph import StateGraph, END

from app.agents.state import AfriPedState
from app.agents.nodes.retrieve_node import retrieve_node
from app.agents.nodes.curriculum_node import curriculum_node
from app.agents.nodes.generate_node import generate_node
from app.agents.nodes.assessment_node import assessment_node
from app.agents.nodes.insights_node import insights_node
from app.agents.nodes.skill_tag_node import skill_tag_node
from app.agents.nodes.rules_node import rules_node
from app.agents.nodes.judge_node import judge_node
from app.agents.nodes.revise_node import revise_node
from app.agents.routing import after_rules, after_judge, BLOOM_ACCURACY_GATE  # noqa: F401


# ── Pillar routing ─────────────────────────────────────────────────────────────

def route_by_pillar(state: AfriPedState) -> Literal[
    "curriculum", "content", "assessment", "insights"
]:
    return state.get("pillar", "content")


def should_use_rag(state: AfriPedState) -> Literal["retrieve", "curriculum", "content", "assessment"]:
    request = state.get("request")
    use_rag = getattr(request, "use_rag", True) if request else False
    pillar = state.get("pillar", "content")
    if use_rag:
        return "retrieve"
    return pillar  # skip retrieval


def after_retrieve(state: AfriPedState) -> Literal["curriculum", "content", "assessment"]:
    return state.get("pillar", "content")


# ── Build graph ────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(AfriPedState)

    # Add all nodes
    g.add_node("retrieve", retrieve_node)
    g.add_node("curriculum", curriculum_node)
    g.add_node("content", generate_node)
    g.add_node("assessment", assessment_node)
    g.add_node("insights", insights_node)
    g.add_node("skill_tag", skill_tag_node)
    g.add_node("rules", rules_node)
    g.add_node("judge", judge_node)
    g.add_node("revise", revise_node)

    # Entry: route by pillar
    g.set_conditional_entry_point(
        route_by_pillar,
        {
            "curriculum": "retrieve",
            "content": "retrieve",
            "assessment": "retrieve",
            "insights": "insights",
        },
    )

    # After retrieval → dispatch to correct pillar node
    g.add_conditional_edges(
        "retrieve",
        after_retrieve,
        {"curriculum": "curriculum", "content": "content", "assessment": "assessment"},
    )

    # Pillar nodes → skill tagging
    g.add_edge("curriculum", "skill_tag")
    g.add_edge("content", "skill_tag")
    g.add_edge("assessment", "skill_tag")

    # Skill tag → rules validation
    g.add_edge("skill_tag", "rules")

    # Rules → pass or judge
    g.add_conditional_edges(
        "rules",
        after_rules,
        {"end": END, "judge": "judge"},
    )

    # Judge → pass or revise
    g.add_conditional_edges(
        "judge",
        after_judge,
        {"end": END, "revise": "revise"},
    )

    # Revise → back to rules
    g.add_edge("revise", "rules")

    # Insights → END directly
    g.add_edge("insights", END)

    return g


# ── Compiled singleton ─────────────────────────────────────────────────────────

from functools import lru_cache

@lru_cache(maxsize=1)
def get_compiled_graph():
    """Return a compiled, cached LangGraph app."""
    graph = build_graph()
    return graph.compile()
