"""
---
title: AfriPed Educational AI
emoji: 📚
colorFrom: blue
colorTo: yellow
sdk: gradio
sdk_version: 4.43.0
app_file: app/ui/gradio_app.py
hardware: t4-medium
---

Gradio 5-tab interface for AfriPed on HuggingFace Spaces.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime

import gradio as gr
import httpx

# ── Backend URL ────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:7860")
API = f"{BACKEND_URL}/api/v1"
TIMEOUT = 1800.0  # CPU inference on free Spaces can spike to 25+ minutes


# ── Shared option lists ────────────────────────────────────────────────────────

SUBJECTS = [
    "mathematics", "english_language", "biology", "chemistry", "physics",
    "economics", "government", "geography", "history", "civic_education",
    "social_studies", "yoruba_language", "igbo_language", "hausa_language",
    "french", "computer_science", "basic_science", "agricultural_science",
    "home_economics", "financial_accounting", "commerce", "crs", "irs",
    "financial_literacy", "health_education", "digital_literacy",
    "entrepreneurship", "agriculture_extension", "trade_skill", "custom_subject",
]

EDUCATION_LEVELS = [
    # School-based
    "PRIMARY_1_3", "PRIMARY_4_6", "JSS1", "JSS2", "JSS3",
    "SSS1", "SSS2", "SSS3", "TERTIARY",
    # Vocational & skill-based
    "VOCATIONAL_BASIC", "VOCATIONAL_ADVANCED",
    # Cohort / bootcamp style
    "BEGINNER_COHORT", "INTERMEDIATE_COHORT", "ADVANCED_COHORT",
    # Informal & community
    "ADULT_LITERACY", "YOUTH_GROUP", "COMMUNITY_GROUP",
    # Professional
    "PROFESSIONAL_DEV",
]

CURRICULUM_BOARDS = ["NERDC", "WAEC", "NECO", "NABTEB", "UBEC", "BECE_GH", "WAEC_GH", "GES_GH", "CUSTOM"]

LANGUAGES = [
    ("English", "en"), ("Yoruba", "yo"), ("Igbo", "ig"), ("Hausa", "ha"),
    ("Nigerian Pidgin", "pcm"), ("Mixed English-Yoruba", "en-yo"),
    ("Mixed English-Hausa", "en-ha"), ("Mixed English-Igbo", "en-ig"),
    ("Twi", "tw"), ("Ewe", "ee"),
]
LANGUAGE_CODES = {name: code for name, code in LANGUAGES}
LANGUAGE_NAMES = [name for name, _ in LANGUAGES]

BLOOM_LEVELS = ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]
PROGRAM_TYPES = ["ACADEMIC", "VOCATIONAL", "COMMUNITY", "LIFE_SKILLS", "AGRICULTURAL", "TEACHER_TRAINING", "YOUTH_ENTERPRISE"]

CONTENT_TYPES = [
    "LESSON_PLAN", "UNIT_NOTES", "LECTURE_NOTES", "STUDY_GUIDE", "WORKSHEET",
    "WORKED_EXAMPLE", "FLASHCARDS", "GLOSSARY", "SUMMARY",
    "STORY", "DIALOGUE", "CASE_STUDY",
    "VOCATIONAL_GUIDE", "COMMUNITY_AWARENESS", "EXTENSION_BULLETIN",
]

ASSESSMENT_TYPES = [
    "QUIZ", "EXAM_QUESTIONS", "QUESTION_BANK", "DIAGNOSTIC_TEST",
    "MARKING_SCHEME", "RUBRIC", "REMEDIATION_EXERCISE",
]

QUESTION_FORMATS = [
    "MULTIPLE_CHOICE", "TRUE_FALSE", "SHORT_ANSWER",
    "FILL_IN_THE_BLANK", "ESSAY", "STRUCTURED", "MIXED",
]

DIFFICULTY_LEVELS = ["EASY", "MEDIUM", "HARD", "MIXED"]


# ── API helpers ────────────────────────────────────────────────────────────────

def _post(endpoint: str, payload: dict) -> tuple[str, str]:
    """POST to backend; returns (result_text, status_text)."""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(f"{API}/{endpoint}", json=payload)
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2, ensure_ascii=False), "✅ Success"
        return r.text, f"❌ Error {r.status_code}"
    except httpx.ConnectError:
        return "", "❌ Cannot connect to backend. Is uvicorn running?"
    except Exception as exc:
        return "", f"❌ {exc}"


def _get(endpoint: str, params: dict | None = None) -> tuple[str, str]:
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(f"{API}/{endpoint}", params=params or {})
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2, ensure_ascii=False), "✅ Success"
        return r.text, f"❌ Error {r.status_code}"
    except Exception as exc:
        return "", f"❌ {exc}"


def _post_params(endpoint: str, params: dict) -> tuple[str, str]:
    """POST with query params (no body) — used for trigger-style endpoints."""
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{API}/{endpoint}", params=params)
        if r.status_code == 200:
            return json.dumps(r.json(), indent=2, ensure_ascii=False), "✅ Started"
        return r.text, f"❌ Error {r.status_code}"
    except Exception as exc:
        return "", f"❌ {exc}"


# ── Tab 1: Content Generator ───────────────────────────────────────────────────

def build_content_tab() -> gr.Tab:
    with gr.Tab("📄 Content Generator") as tab:
        gr.Markdown("## Pillar 2 — Lesson Plans, Worksheets, Stories & More")

        with gr.Row():
            with gr.Column(scale=1):
                subject = gr.Dropdown(SUBJECTS, label="Subject", value="mathematics")
                topic = gr.Textbox(label="Topic", placeholder="e.g. Pythagoras Theorem")
                content_type = gr.Dropdown(CONTENT_TYPES, label="Content Type", value="LESSON_PLAN")
                program_type = gr.Dropdown(PROGRAM_TYPES, label="Program Type", value="ACADEMIC")
                education_level = gr.Dropdown(EDUCATION_LEVELS, label="Learner Level", value="SSS1")
                curriculum_board = gr.Dropdown(CURRICULUM_BOARDS, label="Curriculum Board", value="NERDC")

                with gr.Accordion("Language & Culture", open=False):
                    language = gr.Dropdown(LANGUAGE_NAMES, label="Output Language", value="English")
                    use_local_names = gr.Checkbox(label="Use local West African names", value=True)
                    use_local_examples = gr.Checkbox(label="Use local examples", value=True)

                with gr.Accordion("Pedagogical Options", open=False):
                    bloom_level = gr.Dropdown(BLOOM_LEVELS, label="Bloom's Level", value="UNDERSTAND")
                    duration = gr.Slider(20, 120, value=40, step=5, label="Duration (minutes)")
                    target_skills = gr.Textbox(
                        label="Target Skills (comma-separated, from Enum Skill Library)",
                        placeholder="Critical Thinking, Problem Solving",
                    )
                    include_teacher_notes = gr.Checkbox(label="Include Teacher Notes", value=False)
                    include_answer_key = gr.Checkbox(label="Include Answer Key", value=True)
                    use_rag = gr.Checkbox(label="Use RAG (curriculum context)", value=True)
                    max_tokens = gr.Slider(64, 1024, value=512, step=64, label="Max Tokens")

                generate_btn = gr.Button("🚀 Generate Content", variant="primary")

            with gr.Column(scale=2):
                output_box = gr.Textbox(label="Generated Content", lines=30, max_lines=60)
                status_box = gr.Textbox(label="Status", interactive=False)
                skill_tags_box = gr.JSON(label="Skill Tags")
                with gr.Accordion("Validation & Judge Scores", open=False):
                    validation_status_box = gr.Textbox(label="Validation Status", interactive=False)
                    rules_box = gr.JSON(label="Rules (passed / failed)")
                    judge_score_box = gr.Number(label="Judge Avg Score (1–5)", interactive=False)
                    judge_dimensions_box = gr.JSON(label="Judge Dimension Scores")

        def run_content(
            subject, topic, content_type, program_type, education_level, curriculum_board,
            language, use_local_names, use_local_examples,
            bloom_level, duration, target_skills, include_teacher_notes,
            include_answer_key, use_rag, max_tokens,
        ):
            skills = [s.strip() for s in target_skills.split(",") if s.strip()]
            payload = {
                "subject": subject,
                "topic": topic,
                "content_type": content_type,
                "curriculum_board": curriculum_board,
                "learner_profile": {"education_level": education_level, "program_type": program_type},
                "pedagogical_goals": {
                    "bloom_level": bloom_level,
                    "learning_objectives": [],
                    "target_skills": skills,
                    "duration_minutes": int(duration),
                },
                "output_language": LANGUAGE_CODES.get(language, "en"),
                "cultural_context": {
                    "use_local_names": use_local_names,
                    "use_local_examples": use_local_examples,
                },
                "include_teacher_notes": include_teacher_notes,
                "include_answer_key": include_answer_key,
                "use_rag": use_rag,
                "max_tokens": int(max_tokens),
            }
            raw, status = _post("content/generate", payload)
            if raw:
                try:
                    data = json.loads(raw)
                    validation = data.get("validation", {})
                    rules = {
                        "passed": validation.get("rules_passed", []),
                        "failed": validation.get("rules_failed", []),
                        "notes": validation.get("notes", []),
                    }
                    return (
                        data.get("content", raw),
                        status,
                        data.get("skill_tags", []),
                        validation.get("status", ""),
                        rules,
                        validation.get("judge_score"),
                        validation.get("judge_dimensions"),
                    )
                except Exception:
                    return raw, status, [], "", {}, None, None
            return "", status, [], "", {}, None, None

        generate_btn.click(
            run_content,
            inputs=[
                subject, topic, content_type, program_type, education_level, curriculum_board,
                language, use_local_names, use_local_examples,
                bloom_level, duration, target_skills, include_teacher_notes,
                include_answer_key, use_rag, max_tokens,
            ],
            outputs=[
                output_box, status_box, skill_tags_box,
                validation_status_box, rules_box, judge_score_box, judge_dimensions_box,
            ],
        )
    return tab


# ── Tab 2: Curriculum Builder ──────────────────────────────────────────────────

def build_curriculum_tab() -> gr.Tab:
    with gr.Tab("📚 Curriculum Builder") as tab:
        gr.Markdown("## Pillar 1 — Schemes of Work, Term Plans & Scope/Sequence")

        with gr.Row():
            with gr.Column(scale=1):
                subject = gr.Dropdown(SUBJECTS, label="Subject", value="mathematics")
                program_type = gr.Dropdown(PROGRAM_TYPES, label="Program Type", value="ACADEMIC")
                education_level = gr.Dropdown(EDUCATION_LEVELS, label="Learner Level", value="SSS1")
                curriculum_board = gr.Dropdown(CURRICULUM_BOARDS, label="Curriculum Board", value="NERDC")
                output_type = gr.Dropdown(
                    ["SCHEME_OF_WORK", "TERM_PLAN", "UNIT_PLAN", "SCOPE_AND_SEQUENCE", "LEARNING_OUTCOMES"],
                    label="Output Type", value="SCHEME_OF_WORK",
                )
                with gr.Row():
                    num_terms = gr.Slider(1, 4, value=3, step=1, label="Number of Terms")
                    weeks_per_term = gr.Slider(8, 20, value=13, step=1, label="Weeks per Term")

                language = gr.Dropdown(LANGUAGE_NAMES, label="Output Language", value="English")
                bloom_level = gr.Dropdown(BLOOM_LEVELS, label="Bloom's Level", value="UNDERSTAND")
                topics_input = gr.Textbox(
                    label="Specific Topics (optional, comma-separated)",
                    placeholder="Algebra, Geometry, Statistics",
                )
                with gr.Row():
                    include_resources = gr.Checkbox(label="Include Resources", value=True)
                    include_assessment = gr.Checkbox(label="Include Assessment Schedule", value=True)
                use_rag = gr.Checkbox(label="Use RAG", value=True)
                max_tokens = gr.Slider(64, 768, value=384, step=64, label="Max Tokens")
                generate_btn = gr.Button("🏗️ Build Curriculum", variant="primary")

            with gr.Column(scale=2):
                output_box = gr.Textbox(label="Curriculum Output", lines=35, max_lines=70)
                with gr.Row():
                    status_box = gr.Textbox(label="Status", interactive=False)
                    topics_count = gr.Number(label="Topics Generated", interactive=False)
                skill_tags_box = gr.JSON(label="Skill Tags")

        def run_curriculum(
            subject, program_type, education_level, curriculum_board, output_type,
            num_terms, weeks_per_term, language, bloom_level,
            topics_input, include_resources, include_assessment, use_rag, max_tokens,
        ):
            topics = [t.strip() for t in topics_input.split(",") if t.strip()]
            payload = {
                "subject": subject,
                "education_level": education_level,
                "curriculum_board": curriculum_board,
                "output_type": output_type,
                "num_terms": int(num_terms),
                "num_weeks_per_term": int(weeks_per_term),
                "topics": topics,
                "learner_profile": {"education_level": education_level, "program_type": program_type},
                "pedagogical_goals": {"bloom_level": bloom_level, "learning_objectives": []},
                "output_language": LANGUAGE_CODES.get(language, "en"),
                "cultural_context": {"use_local_names": True, "use_local_examples": True},
                "include_resources": include_resources,
                "include_assessment_schedule": include_assessment,
                "use_rag": use_rag,
                "max_tokens": int(max_tokens),
            }
            raw, status = _post("curriculum/generate", payload)
            if raw:
                try:
                    data = json.loads(raw)
                    return (
                        data.get("curriculum_output", raw),
                        status,
                        data.get("num_topics_generated", 0),
                        data.get("skill_tags", []),
                    )
                except Exception:
                    return raw, status, 0, []
            return "", status, 0, []

        generate_btn.click(
            run_curriculum,
            inputs=[
                subject, program_type, education_level, curriculum_board, output_type,
                num_terms, weeks_per_term, language, bloom_level,
                topics_input, include_resources, include_assessment, use_rag, max_tokens,
            ],
            outputs=[output_box, status_box, topics_count, skill_tags_box],
        )
    return tab


# ── Tab 3: Assessment & Question Bank ─────────────────────────────────────────

def build_assessment_tab() -> gr.Tab:
    with gr.Tab("📝 Assessment & Question Bank") as tab:
        gr.Markdown("## Pillar 3 — WAEC-Style Exams, Question Banks & Rubrics")

        with gr.Row():
            with gr.Column(scale=1):
                subject = gr.Dropdown(SUBJECTS, label="Subject", value="mathematics")
                topic = gr.Textbox(label="Topic", placeholder="e.g. Quadratic Equations")
                assessment_type = gr.Dropdown(ASSESSMENT_TYPES, label="Assessment Type", value="EXAM_QUESTIONS")
                program_type = gr.Dropdown(PROGRAM_TYPES, label="Program Type", value="ACADEMIC")
                curriculum_board = gr.Dropdown(CURRICULUM_BOARDS, label="Curriculum Board", value="WAEC")
                education_level = gr.Dropdown(EDUCATION_LEVELS, label="Learner Level", value="SSS3")
                num_questions = gr.Slider(5, 50, value=10, step=5, label="Number of Questions")
                question_format = gr.Dropdown(QUESTION_FORMATS, label="Question Format", value="MIXED")
                difficulty = gr.Dropdown(DIFFICULTY_LEVELS, label="Difficulty", value="MIXED")
                bloom_level = gr.Dropdown(BLOOM_LEVELS, label="Bloom's Level", value="APPLY")

                with gr.Accordion("Advanced Options", open=False):
                    language = gr.Dropdown(LANGUAGE_NAMES, label="Output Language", value="English")
                    target_skills = gr.Textbox(
                        label="Filter by Skills (comma-separated)",
                        placeholder="Critical Thinking, Numerical Reasoning",
                    )
                    with gr.Row():
                        include_answers = gr.Checkbox(label="Include Answer Key", value=True)
                        include_marking = gr.Checkbox(label="Include Marking Guide", value=True)
                    use_rag = gr.Checkbox(label="Use RAG", value=True)
                    max_tokens = gr.Slider(64, 512, value=256, step=32, label="Max Tokens")

                generate_btn = gr.Button("📋 Generate Assessment", variant="primary")

            with gr.Column(scale=2):
                raw_output = gr.Textbox(label="Raw Assessment Output", lines=25, max_lines=50)
                with gr.Row():
                    status_box = gr.Textbox(label="Status", interactive=False)
                    total_marks = gr.Number(label="Total Marks", interactive=False)
                with gr.Row():
                    bloom_dist = gr.JSON(label="Bloom Distribution")
                    skill_dist = gr.JSON(label="Skill Distribution")

        def run_assessment(
            subject, topic, assessment_type, program_type, curriculum_board, education_level,
            num_questions, question_format, difficulty, bloom_level,
            language, target_skills, include_answers, include_marking, use_rag, max_tokens,
        ):
            skills = [s.strip() for s in target_skills.split(",") if s.strip()]
            payload = {
                "subject": subject,
                "topic": topic,
                "assessment_type": assessment_type,
                "curriculum_board": curriculum_board,
                "learner_profile": {"education_level": education_level, "program_type": program_type},
                "bloom_level": bloom_level,
                "difficulty": difficulty,
                "question_format": question_format,
                "num_questions": int(num_questions),
                "target_skills": skills,
                "output_language": LANGUAGE_CODES.get(language, "en"),
                "cultural_context": {"use_local_names": True},
                "include_answer_key": include_answers,
                "include_marking_guide": include_marking,
                "use_rag": use_rag,
                "max_tokens": int(max_tokens),
            }
            raw, status = _post("assessment/generate", payload)
            if raw:
                try:
                    data = json.loads(raw)
                    return (
                        data.get("raw_output", raw),
                        status,
                        data.get("total_marks", 0),
                        data.get("bloom_distribution", {}),
                        data.get("skill_distribution", {}),
                    )
                except Exception:
                    return raw, status, 0, {}, {}
            return "", status, 0, {}, {}

        generate_btn.click(
            run_assessment,
            inputs=[
                subject, topic, assessment_type, program_type, curriculum_board, education_level,
                num_questions, question_format, difficulty, bloom_level,
                language, target_skills, include_answers, include_marking, use_rag, max_tokens,
            ],
            outputs=[raw_output, status_box, total_marks, bloom_dist, skill_dist],
        )
    return tab


# ── Tab 4: Content Diagnostics ─────────────────────────────────────────────────

def build_diagnostics_tab() -> gr.Tab:
    with gr.Tab("🔍 Content Diagnostics") as tab:
        gr.Markdown("## Pillar 4 — Readability · Bloom · Cultural · Skill Gap Analysis")

        with gr.Row():
            with gr.Column(scale=1):
                content_input = gr.Textbox(
                    label="Paste Content to Analyse",
                    placeholder="Paste your lesson plan, worksheet, or any educational content here...",
                    lines=15,
                )
                content_type = gr.Textbox(label="Content Type", value="LESSON_PLAN")
                subject = gr.Dropdown([""] + SUBJECTS, label="Subject (optional)")
                education_level = gr.Dropdown([""] + EDUCATION_LEVELS, label="Education Level (optional)")
                curriculum_board = gr.Dropdown([""] + CURRICULUM_BOARDS, label="Curriculum Board (optional)")

                with gr.Accordion("Expected Standards", open=False):
                    expected_bloom = gr.Dropdown([""] + BLOOM_LEVELS, label="Expected Bloom Level")
                    expected_skills = gr.Textbox(
                        label="Expected Skills (comma-separated)",
                        placeholder="Critical Thinking, Problem Solving",
                    )

                with gr.Row():
                    run_readability = gr.Checkbox(label="Readability", value=True)
                    run_bloom = gr.Checkbox(label="Bloom Analysis", value=True)
                    run_cultural = gr.Checkbox(label="Cultural Analysis", value=True)
                    run_skill_gap = gr.Checkbox(label="Skill Gap", value=True)

                analyse_btn = gr.Button("🔬 Analyse Content", variant="primary")

            with gr.Column(scale=2):
                status_box = gr.Textbox(label="Status", interactive=False)
                quality_score = gr.Number(label="Overall Quality Score (0–1)", interactive=False)
                readability_box = gr.JSON(label="Readability")
                bloom_box = gr.JSON(label="Bloom Analysis")
                cultural_box = gr.JSON(label="Cultural Analysis")
                skill_tags_box = gr.JSON(label="Skills Detected")
                skill_gap_box = gr.JSON(label="Skill Gap Analysis")
                recommendations_box = gr.Textbox(label="Recommendations", lines=6, interactive=False)

        def run_diagnostics(
            content_input, content_type, subject, education_level,
            curriculum_board, expected_bloom, expected_skills,
            run_readability, run_bloom, run_cultural, run_skill_gap,
        ):
            if not content_input.strip():
                return "❌ No content provided", 0, {}, {}, {}, [], {}, ""
            skills = [s.strip() for s in expected_skills.split(",") if s.strip()]
            payload = {
                "content": content_input,
                "content_type": content_type or "general",
                "subject": subject or None,
                "education_level": education_level or None,
                "curriculum_board": curriculum_board or None,
                "expected_bloom_level": expected_bloom or None,
                "expected_skills": skills or None,
                "run_readability": run_readability,
                "run_bloom_analysis": run_bloom,
                "run_cultural_analysis": run_cultural,
                "run_skill_gap_analysis": run_skill_gap,
            }
            raw, status = _post("insights/analyze", payload)
            if raw:
                try:
                    data = json.loads(raw)
                    recs = "\n".join(f"• {r}" for r in data.get("recommendations", []))
                    return (
                        status,
                        data.get("overall_quality_score", 0),
                        data.get("readability", {}),
                        data.get("bloom_analysis", {}),
                        data.get("cultural_analysis", {}),
                        data.get("skill_tags_detected", []),
                        data.get("skill_gap_analysis", {}),
                        recs,
                    )
                except Exception:
                    return status, 0, {}, {}, {}, [], {}, ""
            return status, 0, {}, {}, {}, [], {}, ""

        analyse_btn.click(
            run_diagnostics,
            inputs=[
                content_input, content_type, subject, education_level,
                curriculum_board, expected_bloom, expected_skills,
                run_readability, run_bloom, run_cultural, run_skill_gap,
            ],
            outputs=[
                status_box, quality_score, readability_box, bloom_box,
                cultural_box, skill_tags_box, skill_gap_box, recommendations_box,
            ],
        )
    return tab


# ── Tab 5: System Status ────────────────────────────────────────────────────────

def build_status_tab() -> gr.Tab:
    with gr.Tab("⚙️ System Status") as tab:
        gr.Markdown("## System Health, Skill Library & RAG Tester")

        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")
            health_display = gr.Textbox(label="API Health", interactive=False)

        with gr.Row():
            skill_count = gr.Number(label="Skill Library Items", interactive=False)
            chroma_count = gr.Number(label="ChromaDB Documents", interactive=False)

        with gr.Accordion("Skill Library Browser", open=True):
            domain_filter = gr.Dropdown(
                ["all", "technical", "behavioral", "cognitive", "language"],
                label="Filter by Domain", value="all",
            )
            browse_btn = gr.Button("Browse Skills")
            skills_output = gr.JSON(label="Skills")

        with gr.Accordion("RAG Test Query", open=False):
            rag_query = gr.Textbox(label="Test Query", placeholder="e.g. JSS3 mathematics fractions Nigeria")
            rag_board = gr.Dropdown([""] + CURRICULUM_BOARDS, label="Board Filter")
            rag_subject = gr.Dropdown([""] + SUBJECTS, label="Subject Filter")
            rag_btn = gr.Button("Test RAG Retrieval")
            rag_output = gr.Textbox(label="Retrieved Context", lines=10, interactive=False)

        with gr.Accordion("Bootstrap RAG Vectorstore", open=False):
            gr.Markdown(
                "_Vectorstore is empty after a fresh deploy or model swap. "
                "Generate synthetic curriculum text and load it into ChromaDB so RAG has context._"
            )
            with gr.Row():
                ingest_board = gr.Dropdown(CURRICULUM_BOARDS, label="Board", value="NERDC")
                ingest_subject = gr.Dropdown(SUBJECTS, label="Subject", value="mathematics")
                ingest_level = gr.Dropdown(EDUCATION_LEVELS, label="Level", value="SSS1")
            ingest_btn = gr.Button("⚡ Bootstrap RAG (Synthetic)", variant="primary")
            ingest_status_box = gr.Textbox(label="Ingest Status", interactive=False)
            ingest_doc_count = gr.Number(label="Documents in Store", interactive=False)

        def refresh_status():
            _, health_status = _get("health")
            # Try get skill count
            raw, _ = _get("skills")
            skill_n = 0
            chroma_n = 0
            if raw:
                try:
                    data = json.loads(raw)
                    skill_n = data.get("total", 0)
                except Exception:
                    pass
            try:
                from app.rag.vectorstore import get_document_count
                chroma_n = get_document_count()
            except Exception:
                pass
            return health_status, skill_n, chroma_n

        def browse_skills(domain):
            params = {} if domain == "all" else {"domain": domain}
            raw, status = _get("skills", params)
            if raw:
                try:
                    return json.loads(raw)
                except Exception:
                    return {}
            return {"error": status}

        def test_rag(query, board, subject):
            if not query.strip():
                return "Enter a query to test"
            try:
                from app.rag.retriever import retrieve
                context, meta = retrieve(
                    query,
                    board=board or None,
                    subject=subject or None,
                    top_k=3,
                )
                if context:
                    return f"Retrieved {meta.chunks_used} chunks:\n\n{context[:2000]}"
                return "No chunks found. Try ingesting curriculum documents first."
            except Exception as exc:
                return f"RAG error: {exc}"

        def run_ingest(board, subject, level):
            raw, status = _post_params(
                "ingest/synthetic",
                {"board": board, "subject": subject, "level": level},
            )
            # Also fetch current doc count
            count = 0
            try:
                from app.rag.vectorstore import get_document_count
                count = get_document_count()
            except Exception:
                pass
            msg = f"{status}"
            if raw:
                try:
                    data = json.loads(raw)
                    msg = f"{status} — {data.get('message', '')}"
                except Exception:
                    pass
            return msg, count

        def check_ingest_status():
            raw, _ = _get("ingest/status")
            count = 0
            running = False
            if raw:
                try:
                    data = json.loads(raw)
                    count = data.get("document_count", 0)
                    running = data.get("ingestion_running", False)
                except Exception:
                    pass
            status_msg = "🔄 Ingestion running…" if running else f"Idle — {count} documents"
            return status_msg, count

        refresh_btn.click(refresh_status, outputs=[health_display, skill_count, chroma_count])
        browse_btn.click(browse_skills, inputs=[domain_filter], outputs=[skills_output])
        rag_btn.click(test_rag, inputs=[rag_query, rag_board, rag_subject], outputs=[rag_output])
        ingest_btn.click(
            run_ingest,
            inputs=[ingest_board, ingest_subject, ingest_level],
            outputs=[ingest_status_box, ingest_doc_count],
        )

    return tab


# ── App assembly ───────────────────────────────────────────────────────────────

def create_app() -> gr.Blocks:
    with gr.Blocks(
        title="AfriPed — Knowledge & Skills Content Studio",
        theme=gr.themes.Soft(
            primary_hue="green",
            secondary_hue="yellow",
        ),
        css="""
        .gradio-container { max-width: 1400px !important; }
        footer { display: none !important; }
        """,
    ) as demo:
        gr.Markdown(
            """
            # 📚 AfriPed — Knowledge & Skills Content Studio
            **AI-powered content for Nigerian & West African teachers, trainers & communities**
            *Academic · Vocational · Community · Life Skills · Bootcamp · Informal · English · Yoruba · Igbo · Hausa · Pidgin*
            """
        )

        build_content_tab()
        build_curriculum_tab()
        build_assessment_tab()
        build_diagnostics_tab()
        build_status_tab()
        demo.queue(max_size=20)

    return demo


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
