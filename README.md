---
title: AfriPed Educational AI
emoji: 📚
colorFrom: green
colorTo: yellow
sdk: docker
hardware: cpu
python_version: "3.11"
---

# AfriPed

AI-powered educational content generation for Nigerian learners.

## Four Pillars

| Pillar | Endpoint | Description |
|--------|----------|-------------|
| 1 — Curriculum | `POST /api/v1/curriculum/generate` | Schemes of work, term plans, scope & sequence |
| 2 — Content | `POST /api/v1/content/generate` | Lesson plans, worksheets, stories, vocational guides |
| 3 — Assessment | `POST /api/v1/assessment/generate` | WAEC-style exams, question banks, rubrics |
| 4 — Insights | `POST /api/v1/insights/analyze` | Readability, Bloom, cultural & skill gap analysis |

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env          # add HF_TOKEN
uvicorn app.main:app --reload
# API docs → http://localhost:8000/docs
```

## Ingest Curriculum Documents

```bash
# From local PDFs
python -m app.rag.ingestion.ingest --input-dir data/raw --board NERDC --subject mathematics --level SSS1

# Synthetic bootstrap
python -m app.rag.ingestion.ingest --synthetic --board NERDC --subject mathematics --level SSS1
```

## Example curl Requests

### Generate a Lesson Plan
```bash
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "mathematics",
    "topic": "Pythagoras Theorem",
    "content_type": "LESSON_PLAN",
    "curriculum_board": "NERDC",
    "learner_profile": {"education_level": "JSS3", "program_type": "ACADEMIC"},
    "pedagogical_goals": {
      "bloom_level": "APPLY",
      "learning_objectives": ["Apply Pythagoras theorem to solve right-angled triangle problems"],
      "target_skills": ["Critical Thinking", "Problem Solving"]
    },
    "output_language": "en",
    "cultural_context": {"use_local_names": true, "use_local_examples": true}
  }'
```

### Browse Skill Library
```bash
curl "http://localhost:8000/api/v1/skills?domain=cognitive"
```

### Generate WAEC Assessment
```bash
curl -X POST http://localhost:8000/api/v1/assessment/generate \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "biology",
    "topic": "Photosynthesis",
    "assessment_type": "EXAM_QUESTIONS",
    "curriculum_board": "WAEC",
    "learner_profile": {"education_level": "SSS2", "program_type": "ACADEMIC"},
    "bloom_level": "ANALYZE",
    "difficulty": "MEDIUM",
    "question_format": "MULTIPLE_CHOICE",
    "num_questions": 10,
    "target_skills": ["Critical Thinking", "Inductive Reasoning"]
  }'
```

## Tech Stack

- **LLM**: Phi-3-mini-4k-instruct (primary) + TinyLlama 1.1B Chat (judge)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: ChromaDB (SQLite) → Qdrant at >100K docs
- **Orchestration**: LangChain + LangGraph StateGraph
- **API**: FastAPI + Pydantic v2
- **UI**: Gradio 4.43.0 on HuggingFace Spaces (CPU)

## Enum Skill Library

Four domains · 119 skills with hierarchical parent→child structure:
- **Technical**: Programming, Data Analysis, Project Management, Financial Management, Cybersecurity, Digital Marketing, Supply Chain, Product Management
- **Behavioral**: Communication, Leadership, Collaboration, Adaptability, Professional Ethics, Time Management, Emotional Intelligence
- **Cognitive**: Critical Thinking, Problem Solving, Numerical Reasoning, Verbal Reasoning, Spatial Reasoning, Attention to Detail, Working Memory, Decision Analysis, Active Learning
- **Language**: English Proficiency, French Proficiency, Business Communication, Technical Writing, Multilingual Communication

Every generated response includes `skill_tags[]` mapped to official library entries.
# Afriped
