# AfriPed — API Reference

**Base URL:** `POST https://<space>/api/v1/`
**Interactive docs:** `/docs` (Swagger UI) · `/redoc`

---

## Shared building blocks

These objects are reused across multiple request bodies.

### `LearnerProfile`

| Field | Type | Required | Values |
|---|---|---|---|
| `education_level` | string | ✅ | `PRIMARY_1_3`, `PRIMARY_4_6`, `JSS1`, `JSS2`, `JSS3`, `SSS1`, `SSS2`, `SSS3`, `TERTIARY`, `VOCATIONAL_BASIC`, `VOCATIONAL_ADVANCED`, `BEGINNER_COHORT`, `INTERMEDIATE_COHORT`, `ADVANCED_COHORT`, `ADULT_LITERACY`, `YOUTH_GROUP`, `COMMUNITY_GROUP`, `PROFESSIONAL_DEV` |
| `program_type` | string | — | `ACADEMIC`, `VOCATIONAL`, `COMMUNITY`, `LIFE_SKILLS`, `AGRICULTURAL`, `TEACHER_TRAINING`, `YOUTH_ENTERPRISE` |
| `class_size` | int | — | e.g. `40` |
| `prior_knowledge` | string | — | free text |

### `PedagogicalGoals`

| Field | Type | Required | Values |
|---|---|---|---|
| `bloom_level` | string | — | `REMEMBER`, `UNDERSTAND`, `APPLY`, `ANALYZE`, `EVALUATE`, `CREATE` |
| `learning_objectives` | string[] | — | list of objective statements |
| `target_skills` | string[] | — | names from the 99-skill library |
| `duration_minutes` | int | — | e.g. `40` |

### `CulturalContext`

| Field | Type | Default | Notes |
|---|---|---|---|
| `use_local_names` | bool | `true` | Enforces West African names (Tunde, Adaeze, Kofi…) |
| `use_local_examples` | bool | `true` | Uses local contexts (markets, rivers, currencies) |
| `custom_cultural_notes` | string | `""` | Free-text cultural guidance injected into the prompt |

### `ValidationReport` (present in every response)

| Field | Type | Notes |
|---|---|---|
| `status` | string | `PASSED` · `FLAGGED` · `REVISED` · `FAILED` — see status meanings below |
| `rules_passed` | string[] | Names of the 8 rules that passed |
| `rules_failed` | string[] | Names of rules that failed |
| `judge_score` | float \| null | Average TinyLlama score 1–5; only present when judge ran |
| `judge_dimensions` | object \| null | Per-dimension scores: `curriculum_alignment`, `bloom_level`, `cultural_appropriateness`, `language_quality`, `educational_value` |
| `revision_count` | int | Number of rewrite attempts (max 2) |
| `notes` | string[] | Human-readable detail on each failure |

**Validation status meanings:**

| Status | Meaning |
|---|---|
| `PASSED` | All 8 rules passed on first attempt |
| `FLAGGED` | At least one rule failed but TinyLlama judge scored ≥ 3.5 — content approved |
| `REVISED` | Content was rewritten by the model and then passed rules |
| `FAILED` | Hard fail (explicit content) or judge scored < 3.5 after max retries |

---

## Pillar 1 — Curriculum

### `POST /api/v1/curriculum/generate`

#### Request body

```json
{
  "request_id": "abc123",
  "subject": "mathematics",
  "education_level": "SSS1",
  "curriculum_board": "NERDC",
  "output_type": "SCHEME_OF_WORK",
  "num_terms": 3,
  "num_weeks_per_term": 13,
  "topics": ["Algebra", "Geometry"],
  "learner_profile": {
    "education_level": "SSS1",
    "program_type": "ACADEMIC"
  },
  "pedagogical_goals": {
    "bloom_level": "UNDERSTAND",
    "learning_objectives": [],
    "target_skills": [],
    "duration_minutes": 40
  },
  "output_language": "en",
  "cultural_context": {
    "use_local_names": true,
    "use_local_examples": true
  },
  "include_resources": true,
  "include_assessment_schedule": true,
  "use_rag": true,
  "max_tokens": 2048
}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `subject` | ✅ | — | See enum values below |
| `education_level` | ✅ | — | See `LearnerProfile` |
| `output_type` | ✅ | — | `SCHEME_OF_WORK`, `TERM_PLAN`, `UNIT_PLAN`, `SCOPE_AND_SEQUENCE`, `LEARNING_OUTCOMES` |
| `curriculum_board` | — | `NERDC` | `NERDC`, `WAEC`, `NECO`, `NABTEB`, `UBEC`, `GES_GH`, `WAEC_GH`, `BECE_GH`, `CUSTOM` |
| `num_terms` | — | `3` | 1–4 |
| `num_weeks_per_term` | — | `13` | 1–20 |
| `topics` | — | `[]` | Specific topics to cover |
| `max_tokens` | — | `2048` | 256–4096 |

#### Response body

```json
{
  "request_id": "abc123",
  "curriculum_output": "## SSS1 Mathematics Scheme of Work...",
  "output_type": "SCHEME_OF_WORK",
  "subject": "mathematics",
  "education_level": "SSS1",
  "curriculum_board": "NERDC",
  "num_topics_generated": 9,
  "skill_tags": [
    { "skill_name": "Critical Thinking", "skill_domain": "cognitive", "parent_skill": null }
  ],
  "validation": { ... },
  "rag_metadata": {
    "chunks_used": 4,
    "sources": ["synthetic"],
    "similarity_scores": [0.87, 0.82],
    "synthetic_chunks": 4
  },
  "model_used": "microsoft/Phi-3-mini-4k-instruct",
  "generation_time_seconds": 387.4,
  "token_count": 412,
  "created_at": "2026-02-26T10:44:17Z",
  "warnings": []
}
```

---

## Pillar 2 — Content

### `POST /api/v1/content/generate`

#### Request body

```json
{
  "request_id": "abc123",
  "subject": "mathematics",
  "topic": "Pythagoras Theorem",
  "content_type": "LESSON_PLAN",
  "curriculum_board": "NERDC",
  "learner_profile": {
    "education_level": "SSS1",
    "program_type": "ACADEMIC"
  },
  "pedagogical_goals": {
    "bloom_level": "UNDERSTAND",
    "learning_objectives": [
      "Students will explain the Pythagorean theorem"
    ],
    "target_skills": ["Critical Thinking", "Problem Solving"],
    "duration_minutes": 40
  },
  "output_language": "en",
  "cultural_context": {
    "use_local_names": true,
    "use_local_examples": true
  },
  "include_teacher_notes": false,
  "include_answer_key": true,
  "use_rag": true,
  "max_tokens": 512
}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `subject` | ✅ | — | |
| `topic` | ✅ | — | 3–200 characters |
| `content_type` | ✅ | — | `LESSON_PLAN`, `UNIT_NOTES`, `LECTURE_NOTES`, `STUDY_GUIDE`, `WORKSHEET`, `WORKED_EXAMPLE`, `FLASHCARDS`, `GLOSSARY`, `SUMMARY`, `STORY`, `DIALOGUE`, `CASE_STUDY`, `VOCATIONAL_GUIDE`, `COMMUNITY_AWARENESS`, `EXTENSION_BULLETIN` |
| `curriculum_board` | — | `NERDC` | |
| `include_teacher_notes` | — | `false` | Appends a teacher notes section |
| `include_answer_key` | — | `true` | Appends answer key / marking guide |
| `max_tokens` | — | `1024` | 128–4096 |

#### Response body

```json
{
  "request_id": "abc123",
  "content": "## Lesson Plan: Pythagoras Theorem...",
  "content_type": "LESSON_PLAN",
  "subject": "mathematics",
  "topic": "Pythagoras Theorem",
  "output_language": "en",
  "curriculum_board": "NERDC",
  "bloom_level": "UNDERSTAND",
  "skill_tags": [
    { "skill_name": "Critical Thinking", "skill_domain": "cognitive", "parent_skill": null }
  ],
  "validation": {
    "status": "FLAGGED",
    "rules_passed": [
      "length_check", "language_detection", "bloom_verb_presence",
      "cultural_flag_check", "no_hallucinated_dates",
      "no_explicit_content", "curriculum_alignment"
    ],
    "rules_failed": ["format_compliance"],
    "judge_score": 4.05,
    "judge_dimensions": {
      "curriculum_alignment": 3.5,
      "bloom_level": 4.0,
      "cultural_appropriateness": 5.0,
      "language_quality": 4.0,
      "educational_value": 3.75
    },
    "revision_count": 0,
    "notes": ["format_compliance: Lesson plan missing sections: assessment"]
  },
  "rag_metadata": { ... },
  "model_used": "microsoft/Phi-3-mini-4k-instruct",
  "generation_time_seconds": 622.1,
  "token_count": 387,
  "created_at": "2026-02-26T11:36:58Z",
  "warnings": []
}
```

---

## Pillar 3 — Assessment

### `POST /api/v1/assessment/generate`

#### Request body

```json
{
  "request_id": "abc123",
  "subject": "mathematics",
  "topic": "Quadratic Equations",
  "assessment_type": "EXAM_QUESTIONS",
  "curriculum_board": "WAEC",
  "learner_profile": {
    "education_level": "SSS3",
    "program_type": "ACADEMIC"
  },
  "bloom_level": "APPLY",
  "difficulty": "MIXED",
  "question_format": "MIXED",
  "num_questions": 10,
  "target_skills": ["Numerical Reasoning"],
  "output_language": "en",
  "cultural_context": { "use_local_names": true },
  "include_answer_key": true,
  "include_marking_guide": true,
  "include_bloom_tags": true,
  "include_difficulty_tags": true,
  "include_topic_tags": true,
  "use_rag": true,
  "max_tokens": 2048
}
```

| Field | Required | Default | Notes |
|---|---|---|---|
| `subject` | ✅ | — | |
| `topic` | ✅ | — | 3–200 characters |
| `assessment_type` | ✅ | — | `QUIZ`, `EXAM_QUESTIONS`, `QUESTION_BANK`, `DIAGNOSTIC_TEST`, `MARKING_SCHEME`, `RUBRIC`, `REMEDIATION_EXERCISE` |
| `curriculum_board` | — | `WAEC` | |
| `bloom_level` | — | `UNDERSTAND` | |
| `difficulty` | — | `MEDIUM` | `EASY`, `MEDIUM`, `HARD`, `MIXED` |
| `question_format` | — | `MIXED` | `MULTIPLE_CHOICE`, `TRUE_FALSE`, `SHORT_ANSWER`, `FILL_IN_THE_BLANK`, `ESSAY`, `STRUCTURED`, `MIXED` |
| `num_questions` | — | `10` | 1–100 |
| `max_tokens` | — | `2048` | 256–4096 |

#### Response body

```json
{
  "request_id": "abc123",
  "assessment_type": "EXAM_QUESTIONS",
  "subject": "mathematics",
  "topic": "Quadratic Equations",
  "curriculum_board": "WAEC",
  "questions": [
    {
      "question_number": 1,
      "question_text": "Solve x² - 5x + 6 = 0",
      "question_format": "SHORT_ANSWER",
      "bloom_level": "APPLY",
      "difficulty": "MEDIUM",
      "skill_tags": [
        { "skill_name": "Numerical Reasoning", "skill_domain": "cognitive", "parent_skill": null }
      ],
      "topic_tags": ["quadratic", "algebra"],
      "options": null,
      "answer": "x = 2 or x = 3",
      "explanation": "Factorise as (x-2)(x-3) = 0",
      "marks": 3
    }
  ],
  "raw_output": "Q1. [SHORT_ANSWER] [Bloom: APPLY]...",
  "total_marks": 30,
  "estimated_duration_minutes": 60,
  "bloom_distribution": { "APPLY": 7, "ANALYZE": 3 },
  "difficulty_distribution": { "EASY": 2, "MEDIUM": 5, "HARD": 3 },
  "skill_distribution": { "Numerical Reasoning": 6, "Critical Thinking": 4 },
  "validation": { ... },
  "model_used": "microsoft/Phi-3-mini-4k-instruct",
  "generation_time_seconds": 598.2,
  "created_at": "2026-02-26T10:50:49Z",
  "warnings": []
}
```

---

## Pillar 4 — Insights (Diagnostics)

### `POST /api/v1/insights/analyze`

Send existing content to get a quality diagnostic — no generation happens.

#### Request body

```json
{
  "request_id": "abc123",
  "content": "## Lesson Plan: Pythagoras Theorem...",
  "content_type": "LESSON_PLAN",
  "subject": "mathematics",
  "education_level": "SSS1",
  "curriculum_board": "NERDC",
  "expected_bloom_level": "UNDERSTAND",
  "expected_language": "en",
  "expected_skills": ["Critical Thinking", "Problem Solving"],
  "run_readability": true,
  "run_bloom_analysis": true,
  "run_cultural_analysis": true,
  "run_skill_gap_analysis": true,
  "run_curriculum_gap_analysis": false
}
```

| Field | Required | Notes |
|---|---|---|
| `content` | ✅ | Min 10 characters — the text to analyse |
| `content_type` | ✅ | Free string e.g. `"LESSON_PLAN"` |
| All other fields | — | Optional; used to compute gap analysis |

#### Response body

```json
{
  "request_id": "abc123",
  "readability": {
    "flesch_kincaid_grade": 9.2,
    "complexity_band": "secondary"
  },
  "bloom_analysis": {
    "detected_level": "UNDERSTAND",
    "verbs_found": ["explain", "describe", "summarise"],
    "confidence": 0.91
  },
  "cultural_analysis": {
    "local_name_ratio": 0.78,
    "local_example_count": 4,
    "flags": []
  },
  "skill_tags_detected": [
    { "skill_name": "Critical Thinking", "skill_domain": "cognitive", "parent_skill": null }
  ],
  "skill_gap_analysis": {
    "expected": ["Critical Thinking", "Problem Solving"],
    "detected": ["Critical Thinking"],
    "missing": ["Problem Solving"]
  },
  "curriculum_coverage": null,
  "gap_analysis": null,
  "overall_quality_score": 0.82,
  "recommendations": [
    "Add problem-solving activities targeting APPLY level",
    "Include local market-based examples"
  ],
  "created_at": "2026-02-26T11:00:00Z"
}
```

---

## Enum quick reference

### `subject`
`mathematics` · `english_language` · `biology` · `chemistry` · `physics` · `further_mathematics` · `economics` · `government` · `geography` · `history` · `civic_education` · `social_studies` · `yoruba_language` · `igbo_language` · `hausa_language` · `french` · `computer_science` · `basic_science` · `agricultural_science` · `home_economics` · `visual_art` · `music` · `physical_education` · `financial_accounting` · `commerce` · `crs` · `irs` · `financial_literacy` · `health_education` · `digital_literacy` · `entrepreneurship` · `agriculture_extension` · `trade_skill` · `custom_subject`

### `output_language`
| Code | Language |
|---|---|
| `en` | English |
| `yo` | Yoruba |
| `ig` | Igbo |
| `ha` | Hausa |
| `pcm` | Nigerian Pidgin |
| `en-yo` | Mixed English–Yoruba |
| `en-ha` | Mixed English–Hausa |
| `en-ig` | Mixed English–Igbo |
| `tw` | Twi (Akan) |
| `ee` | Ewe |

---

## The 8 validation rules

Every generated response includes a `validation` object. These rules run in ~50ms with no LLM involved. The file is `app/validation/rules.py`.

| Rule | What it checks | Fail type |
|---|---|---|
| `length_check` | Content length is between 25% and 600% of `max_tokens` (in chars) | Soft |
| `language_detection` | Detected language matches `output_language` at >85% confidence | Soft |
| `bloom_verb_presence` | At least one Bloom verb for the requested level appears in the text | Soft |
| `cultural_flag_check` | Western name ratio does not exceed 60% of all names found | Soft |
| `format_compliance` | Structural requirements per type (lesson plan needs objective/activity/assessment sections; assessments need question marks; schemes need week/term numbers) | Soft |
| `no_hallucinated_dates` | No years outside 1800–2030 | Soft |
| `no_explicit_content` | No profane or explicit terms (context-aware regex) | **Hard** — blocks immediately, judge never runs |
| `curriculum_alignment` | At least 3 board-specific keywords appear (NERDC: objective, activity, evaluation… WAEC: question, mark, answer…) | Soft |

**Soft fail** → TinyLlama judge runs and scores 1–5. If average ≥ 3.5 the content is approved (`FLAGGED`). If < 3.5 the content is rewritten (up to 2 attempts).
**Hard fail** → content is rejected immediately (`FAILED`), no judge.
