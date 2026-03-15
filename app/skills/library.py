"""Skill library loader and keyword-based auto-tagger."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from loguru import logger


LIBRARY_PATH = Path(__file__).parent.parent.parent / "data" / "skills" / "skill_library.json"

# ── inline types (avoid circular imports from schemas) ─────────────────────────

class SkillLibraryItem:
    __slots__ = ("skill_name", "skill_domain", "parent_skill", "description")

    def __init__(
        self,
        skill_name: str,
        skill_domain: str,
        parent_skill: Optional[str],
        description: str,
    ) -> None:
        self.skill_name = skill_name
        self.skill_domain = skill_domain
        self.parent_skill = parent_skill
        self.description = description

    def to_dict(self) -> dict:
        return {
            "skill_name": self.skill_name,
            "skill_domain": self.skill_domain,
            "parent_skill": self.parent_skill,
            "description": self.description,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"SkillLibraryItem({self.skill_name!r}, domain={self.skill_domain!r})"


class SkillTag:
    __slots__ = ("skill_name", "skill_domain", "parent_skill")

    def __init__(self, skill_name: str, skill_domain: str, parent_skill: Optional[str]) -> None:
        self.skill_name = skill_name
        self.skill_domain = skill_domain
        self.parent_skill = parent_skill

    def to_dict(self) -> dict:
        return {
            "skill_name": self.skill_name,
            "skill_domain": self.skill_domain,
            "parent_skill": self.parent_skill,
        }


# ── keyword synonyms / aliases used during text matching ──────────────────────

SKILL_ALIASES: dict[str, list[str]] = {
    "Programming and Software Development": ["programming", "software development", "coding", "software engineering"],
    "Algorithms and Data Structures": ["algorithm", "data structure", "sorting", "linked list", "binary tree"],
    "Testing and QA": ["testing", "unit test", "quality assurance", "qa", "test case"],
    "Version Control": ["git", "version control", "github", "branching", "commit"],
    "Secure Development": ["secure coding", "owasp", "security", "encryption", "vulnerability"],
    "API Design": ["api", "rest", "endpoint", "graphql", "swagger"],
    "Data Analysis and Statistical Methods": ["data analysis", "data analytics", "statistics", "dataset"],
    "Statistical Analysis": ["statistical", "mean", "standard deviation", "hypothesis", "regression"],
    "Data Visualization": ["chart", "graph", "visualization", "dashboard", "plot"],
    "SQL": ["sql", "database query", "select from", "join", "relational database"],
    "Machine Learning Fundamentals": ["machine learning", "ml", "neural network", "model training", "classification"],
    "Project Management": ["project management", "project planning", "pm", "milestone"],
    "Scope Management": ["scope", "project scope", "scope creep"],
    "Schedule Management": ["schedule", "timeline", "gantt", "deadline"],
    "Risk Management": ["risk", "risk management", "mitigation", "contingency"],
    "Stakeholder Management": ["stakeholder", "stakeholder engagement", "client relations"],
    "Financial Management and Accounting": ["financial management", "accounting", "finance", "bookkeeping"],
    "Financial Reporting": ["financial report", "income statement", "balance sheet", "p&l"],
    "Budgeting": ["budget", "budgeting", "forecast", "expenditure"],
    "Auditing": ["audit", "auditing", "compliance", "internal control"],
    "Information Security and Cybersecurity": ["cybersecurity", "information security", "infosec", "hacking"],
    "Risk Assessment": ["risk assessment", "threat model", "vulnerability assessment"],
    "Identity and Access Management": ["iam", "identity management", "access control", "authentication"],
    "Incident Response": ["incident response", "breach response", "forensics", "disaster recovery"],
    "Digital Marketing Strategy": ["digital marketing", "marketing strategy", "brand", "campaign"],
    "SEO": ["seo", "search engine", "keyword ranking", "organic traffic"],
    "Marketing Analytics": ["marketing analytics", "conversion rate", "click-through", "roi"],
    "Supply Chain and Operations Management": ["supply chain", "operations", "logistics", "procurement"],
    "Inventory Management": ["inventory", "stock management", "reorder", "warehouse"],
    "Process Optimization": ["process improvement", "lean", "six sigma", "workflow"],
    "Product Management": ["product management", "product manager", "product roadmap"],
    "Product Strategy": ["product strategy", "product vision", "go-to-market"],
    "Product Discovery": ["product discovery", "user research", "mvp", "prototyping"],
    "Agile and Scrum": ["agile", "scrum", "sprint", "kanban", "backlog"],
    # Behavioral
    "Communication": ["communication", "communicate", "convey", "articulate"],
    "Active Listening": ["active listening", "listening skill", "attentive"],
    "Written Communication": ["written communication", "writing skill", "email writing"],
    "Public Speaking": ["public speaking", "presentation skill", "speech", "oratory"],
    "Persuasion": ["persuasion", "persuade", "influence", "negotiate"],
    "Leadership": ["leadership", "lead", "leader", "inspire"],
    "Decision Making": ["decision making", "decision-making", "judgement", "choose"],
    "Delegation": ["delegation", "delegate", "assign task"],
    "Coaching and Mentorship": ["coaching", "mentoring", "mentorship", "mentor", "coach"],
    "Conflict Resolution": ["conflict resolution", "conflict management", "mediation"],
    "Collaboration and Teamwork": ["collaboration", "teamwork", "team player", "cooperative"],
    "Empathy": ["empathy", "empathetic", "compassion"],
    "Accountability": ["accountability", "accountable", "ownership", "responsibility"],
    "Adaptability": ["adaptability", "adaptable", "flexible", "adjust"],
    "Learning Agility": ["learning agility", "quick learner", "rapid learning"],
    "Stress Management": ["stress management", "cope", "resilience", "pressure"],
    "Professional Ethics": ["professional ethics", "ethical conduct", "integrity", "professional behaviour"],
    "Integrity": ["integrity", "honesty", "truthful", "transparent"],
    "Ethical Decision Making": ["ethical decision", "ethics", "moral"],
    "Time Management": ["time management", "manage time", "punctual", "efficiency"],
    "Prioritization": ["prioritization", "prioritise", "prioritize", "priority"],
    "Productivity Planning": ["productivity", "planning", "time blocking", "schedule"],
    "Emotional Intelligence": ["emotional intelligence", "eq", "self-management", "empathy"],
    "Self Awareness": ["self-awareness", "self awareness", "introspection", "reflect"],
    "Emotional Regulation": ["emotional regulation", "manage emotion", "self-control"],
    # Cognitive
    "Critical Thinking": ["critical thinking", "critically", "evaluate argument", "analyse"],
    "Logical Reasoning": ["logical reasoning", "logic", "deduction", "syllogism"],
    "Deductive Reasoning": ["deductive", "deduction", "general to specific"],
    "Inductive Reasoning": ["inductive", "induction", "specific to general"],
    "Problem Solving": ["problem solving", "problem-solving", "solve problem", "solution"],
    "Root Cause Analysis": ["root cause", "rca", "five whys", "fishbone"],
    "Systems Thinking": ["systems thinking", "systems approach", "holistic", "interconnected"],
    "Numerical Reasoning": ["numerical reasoning", "number skill", "arithmetic", "calculation"],
    "Quantitative Analysis": ["quantitative", "quantitative analysis", "data-driven"],
    "Statistical Interpretation": ["interpret statistic", "statistical interpretation", "p-value", "confidence interval"],
    "Verbal Reasoning": ["verbal reasoning", "verbal ability", "language reasoning"],
    "Reading Comprehension": ["reading comprehension", "comprehension", "understand passage"],
    "Inference Drawing": ["inference", "infer", "implication", "conclude"],
    "Spatial Reasoning": ["spatial reasoning", "spatial ability", "visualise", "rotation"],
    "Pattern Recognition": ["pattern recognition", "pattern", "sequence", "regularit"],
    "Attention to Detail": ["attention to detail", "detail-oriented", "meticulous", "accuracy"],
    "Working Memory": ["working memory", "short-term memory", "recall", "retain"],
    "Decision Analysis": ["decision analysis", "decision tree", "cost-benefit"],
    "Scenario Evaluation": ["scenario evaluation", "scenario analysis", "what-if", "case analysis"],
    "Active Learning": ["active learning", "self-directed learning", "autodidact"],
    # Language
    "English Proficiency": ["english proficiency", "english language", "esl", "english skills"],
    "English Reading": ["english reading", "read english", "reading skill"],
    "English Writing": ["english writing", "write english", "writing skill", "composition"],
    "English Listening": ["english listening", "listening skill", "aural comprehension"],
    "English Speaking": ["english speaking", "oral english", "spoken english"],
    "Grammar and Syntax": ["grammar", "syntax", "punctuation", "parts of speech", "tense"],
    "Vocabulary Development": ["vocabulary", "word usage", "lexis", "diction"],
    "French Proficiency": ["french proficiency", "french language", "francophone"],
    "French Reading": ["french reading", "lire en français"],
    "French Writing": ["french writing", "écriture en français"],
    "Business Communication": ["business communication", "professional communication", "workplace communication"],
    "Report Writing": ["report writing", "write report", "formal report"],
    "Presentation Delivery": ["presentation delivery", "deliver presentation", "present to"],
    "Professional Correspondence": ["professional correspondence", "business email", "formal letter"],
    "Technical Writing": ["technical writing", "technical document", "user manual", "specification"],
    "Documentation Structuring": ["documentation", "structure document", "table of contents"],
    "Editing and Proofreading": ["editing", "proofreading", "proofread", "revise text"],
    "Multilingual Communication": ["multilingual", "bilingual", "multilingual communication"],
    "Cross-Cultural Communication": ["cross-cultural", "intercultural", "cultural sensitivity"],
    "Translation Skills": ["translation", "translate", "interpret language"],
}


class SkillLibrary:
    """In-memory skill library loaded from skill_library.json."""

    def __init__(self, path: Path = LIBRARY_PATH) -> None:
        self._path = path
        self._items: List[SkillLibraryItem] = []
        self._by_domain: dict[str, List[SkillLibraryItem]] = {}
        self._by_name: dict[str, SkillLibraryItem] = {}
        self._load()

    # ── loading ────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.error(f"Skill library not found at {self._path}")
            return
        except json.JSONDecodeError as exc:
            logger.error(f"Skill library JSON parse error: {exc}")
            return

        for domain_key, domain_data in data.get("domains", {}).items():
            for raw in domain_data.get("skills", []):
                item = SkillLibraryItem(
                    skill_name=raw["skill_name"],
                    skill_domain=raw["skill_domain"],
                    parent_skill=raw.get("parent_skill"),
                    description=raw.get("description", ""),
                )
                self._items.append(item)
                self._by_name[item.skill_name.lower()] = item
                self._by_domain.setdefault(domain_key, []).append(item)

        logger.info(f"Skill library loaded: {len(self._items)} skills across {len(self._by_domain)} domains")

    # ── public API ─────────────────────────────────────────────────────────────

    def get_all(self) -> List[SkillLibraryItem]:
        return list(self._items)

    def get_by_domain(self, domain: str) -> List[SkillLibraryItem]:
        return list(self._by_domain.get(domain.lower(), []))

    def get_by_name(self, name: str) -> Optional[SkillLibraryItem]:
        return self._by_name.get(name.lower())

    def get_children(self, parent_skill: str) -> List[SkillLibraryItem]:
        return [i for i in self._items if i.parent_skill == parent_skill]

    def match_from_text(self, text: str, domain_filter: Optional[str] = None) -> List[SkillTag]:
        """Keyword-match skill signals from generated text.

        Returns deduplicated SkillTag list ordered by match confidence
        (most aliases matched first).
        """
        if not text:
            return []

        lower = text.lower()
        matches: dict[str, int] = {}  # skill_name → hit count

        for skill_name, aliases in SKILL_ALIASES.items():
            # Optionally restrict to a domain
            item = self._by_name.get(skill_name.lower())
            if item is None:
                continue
            if domain_filter and item.skill_domain != domain_filter.lower():
                continue

            for alias in aliases:
                # whole-word-ish matching (allow partial for compound phrases)
                pattern = re.escape(alias)
                if re.search(pattern, lower):
                    matches[skill_name] = matches.get(skill_name, 0) + 1

        # Sort by hit count descending; deduplicate
        sorted_skills = sorted(matches, key=lambda k: -matches[k])
        tags: List[SkillTag] = []
        seen: set[str] = set()
        for name in sorted_skills:
            if name in seen:
                continue
            seen.add(name)
            item = self._by_name.get(name.lower())
            if item:
                tags.append(SkillTag(
                    skill_name=item.skill_name,
                    skill_domain=item.skill_domain,
                    parent_skill=item.parent_skill,
                ))

        return tags

    def match_from_targets(self, target_skills: List[str]) -> List[SkillTag]:
        """Convert a list of skill name strings to SkillTag objects."""
        tags: List[SkillTag] = []
        for name in target_skills:
            item = self._by_name.get(name.lower())
            if item:
                tags.append(SkillTag(
                    skill_name=item.skill_name,
                    skill_domain=item.skill_domain,
                    parent_skill=item.parent_skill,
                ))
            else:
                logger.warning(f"Skill '{name}' not found in library; skipping")
        return tags

    @property
    def total(self) -> int:
        return len(self._items)

    @property
    def domains(self) -> List[str]:
        return list(self._by_domain.keys())


@lru_cache(maxsize=1)
def get_skill_library() -> SkillLibrary:
    """Singleton accessor — call this everywhere instead of SkillLibrary()."""
    return SkillLibrary()
