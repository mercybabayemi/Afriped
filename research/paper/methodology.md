# Methodology
*"Rule-Augmented Questioning (RAQ): Curriculum-Aligned Educational Content Generation for African Learners"*

For venue-specific abstracts see [`abstract_variants.md`](abstract_variants.md).
For related work citations see [`related_work.md`](related_work.md) + [`../references.bib`](../references.bib).

---

## 3. System Design

### 3.1 Architecture Overview

We design a multi-stage generation and validation pipeline orchestrated via LangGraph (Haskelberg & Chase, 2024), comprising five functional layers: (1) retrieval, (2) generation, (3) symbolic rule validation, (4) LLM-based judging, and (5) revision. The pipeline is parameterised by curriculum board, education level, Bloom taxonomy target, and output language, enabling content generation across four task types: curriculum planning, content generation, assessment construction, and pedagogical insight analysis.

The system runs entirely on consumer CPU hardware using 4-bit NF4-quantised language models (Dettmers et al., 2023) loaded via HuggingFace Transformers (Wolf et al., 2020). This design choice reflects a core constraint of the target deployment context: Nigerian schools commonly operate without GPU servers or reliable cloud connectivity. Full content generation, including retrieval and validation, completes in 8–15 minutes per session on an Intel Core i7 with 16GB RAM — without cloud dependency.

```
Request
  │
  ▼
[Pillar Router] ─────────────────────────┐
  │                                      │
  ▼ (use_rag=True)                       │ (use_rag=False)
[Layer 3: RAG Retrieval]                 │
  │  ChromaDB ← Nigerian edu corpus      │
  │                                      │
  ▼                                      ▼
[Layer 1+2: Generation]  ←──────────────┘
  │  Phi-3-mini-4k-instruct (4-bit)
  │  Structured outline → expanded content
  │
  ▼
[Layer 4: RAQ Validation]
  │  8 deterministic rules (< 50ms)
  │      ↓ soft fail
  │  LLM judge: 5 dimensions, 1–5 score
  │      ↓ score < 3.5
  │  Revision node (max 2 retries)
  │
  ▼
Response + ValidationReport + SkillTags
```

### 3.2 Generation Models

**Primary generator:** `microsoft/Phi-3-mini-4k-instruct` — a 3.8B parameter instruction-tuned model with a 4k token context window. Selected over larger alternatives (LLaMA-3, Mistral-7B) based on three criteria: (a) stable 4-bit quantisation without output degradation on structured generation tasks, (b) acceptable latency on CPU (< 10 min for standard content types), and (c) instruction-following fidelity on multi-section educational formats.

**Judge model:** `TinyLlama/TinyLlama-1.1B-Chat-v1.0` — a 1.1B parameter model used exclusively for quality scoring. Invoked only when the primary generator's output fails at least one soft validation rule, to avoid redundant computation. On CPU hardware, TinyLlama requires approximately 2.2GB RAM.

**Hardware-aware judge gating:** A critical architectural decision is to bypass the judge node entirely on systems with insufficient RAM (< 16GB available) or when no soft rules fail. This prevents cold-start timeouts that occurred when TinyLlama was loaded mid-request on constrained hardware (see Section 3.6). The gating logic evaluates `psutil.virtual_memory().available` at startup and sets a module-level flag used throughout the pipeline's lifetime.

### 3.3 Retrieval-Augmented Generation (RAG)

We index a corpus of Nigerian educational content into a local ChromaDB vector store using `sentence-transformers/all-MiniLM-L6-v2` embeddings (Reimers & Gurevych, 2019) with 384-dimensional vectors. The current deployment uses all-MiniLM-L6-v2 for its low memory footprint (22MB) and CPU inference speed, ensuring the full system runs within the 16GB RAM constraint. A planned upgrade to `intfloat/multilingual-e5-large` (Wang et al., 2024) will extend cross-lingual retrieval to Hausa, Yoruba, and Igbo content once the multilingual corpus is fully indexed; this upgrade is left as future work.

**Corpus construction:** The RAG corpus has two layers.

*Layer 1 — Synthetic curriculum corpus (53,171 chunks):* We generate structured educational content from a Nigerian curriculum taxonomy covering five boards (NERDC, WAEC, NECO, NABTEB, UBEC), education levels from Primary 4 through SSS3 and vocational tracks, 19 subjects, and seven content types (lesson notes, topic explanations, exam Q&A, teacher guides, cultural context). This synthetic corpus ensures broad coverage across all curriculum parameters evaluated in our benchmark.

*Layer 2 — Real teacher lesson notes (77 documents):* We obtain 77 authentic weekly lesson notes from a practising ICT teacher at ENGREG HIGH SCHOOL, Pedro Shomolu, Lagos (academic session 2024/2025). These cover Computer Studies and Data Processing across JSS1–3 and SS1–3, and follow the standard Nigerian lesson note format: learning objectives, step-by-step teaching activities, keywords, evaluative questions, assignments, and full lesson content. This is, to our knowledge, the only publicly described corpus of real Nigerian secondary-school teacher-authored lesson notes.

**Corpus audit disclosure:** Seven HuggingFace datasets (Electric Sheep Africa, 2024; Ben-45, 2024) initially identified as Nigerian educational data were found on inspection to contain only administrative records — student ID codes, assessment scores, dates, and state identifiers (e.g., "REC-00312696 2024-08-18 Kwara") — with no educational text content (maximum field length: 43 characters; continuous assessment records all contained the identical string "subject: Mathematics"). We disclose this finding transparently so other researchers can avoid using these sources as educational corpora.

Retrieved chunks are prepended to the generation prompt as curriculum reference context, grounding outputs in local standards rather than relying on the LLM's parametric knowledge of NERDC, WAEC, and NECO requirements.

### 3.4 Rule-Augmented Questioning (RAQ)

RAQ is a two-stage validation layer applied to every generated output before delivery. The first stage comprises eight deterministic symbolic rules executing in under 50ms with no LLM involvement. The second stage is an LLM-based judge that scores content along five pedagogical dimensions.

**Stage 1 — Deterministic rules:**

| Rule | What it checks | Type |
|---|---|---|
| `length_check` | Content length within 25–600% of `max_tokens` | Soft |
| `language_detection` | Detected language matches requested `output_language` at > 85% confidence | Soft |
| `bloom_verb_presence` | At least one Bloom action verb for the target level appears in the text | Soft |
| `cultural_flag_check` | Western name ratio does not exceed 60% of all names detected | Soft |
| `format_compliance` | Structural markers present (lesson plans: objective, activity, assessment; exams: question marks, numbering; schemes: week/term markers) | Soft |
| `no_hallucinated_dates` | No years outside 1800–2030 | Soft |
| `curriculum_alignment` | Board-specific keywords present (≥ 3 of: objective, activity, evaluation for NERDC; question, mark, answer for WAEC) | Soft |
| `no_explicit_content` | No profane or explicit terms detected via context-aware regex | **Hard** |

Soft rule failures accumulate and trigger Stage 2. A single hard failure immediately returns `FAILED` status with no judge invocation.

**Stage 2 — LLM judge (five dimensions):**

The judge prompt (see `research/prompts/raq_pipeline.py:build_layer4_raq_judge_prompt`) requests scoring on:

| Dimension | Definition |
|---|---|
| `curriculum_alignment` | Alignment to the specified curriculum board's structural standards |
| `bloom_depth` | Whether content genuinely requires the target cognitive level (not mere recall) |
| `cultural_authenticity` | Nigerian names, places, institutions, and currencies used naturally |
| `language_quality` | Age-appropriate, grammatically correct output in the requested language |
| `educational_value` | Whether a teacher could use this content as-is, without revision |

Scores are integers 1–5 per dimension. The average determines the validation outcome:

- **PASSED**: all 8 rules pass (no judge invoked)
- **FLAGGED**: ≥ 1 soft rule fails, judge average ≥ 3.5 (content approved)
- **REVISED**: judge average < 3.5 → content rewritten (max 2 retries)
- **FAILED**: hard rule triggered, or judge average < 2.5 after max retries

This structured approach mitigates the position and self-preference biases documented in LLM-as-a-judge literature (Shi et al., 2025; Wang et al., 2025) by (a) preventing holistic scoring without criterion-level anchoring, and (b) using deterministic pre-screening to eliminate hard failures before the judge is invoked.

### 3.5 Semantic Rule Expansion

Initial deployment revealed that the `bloom_verb_presence` and `format_compliance` rules produced false failures when the generator used semantically equivalent but lexically distinct terms. For example, the model frequently produced "Learning Goal" in place of "Objective," "Task" in place of "Activity," and "Evaluation" in place of "Assessment." Since these terms are pedagogically equivalent, the literal rule incorrectly flagged structurally compliant content.

We address this by expanding each rule to match synonym groups rather than exact keywords:

```python
OBJECTIVE_SYNONYMS  = {"objective", "goal", "aim", "target", "learning outcome", "purpose"}
ACTIVITY_SYNONYMS   = {"activity", "task", "procedure", "method", "exercise", "practise"}
ASSESSMENT_SYNONYMS = {"assessment", "evaluation", "quiz", "test", "assignment", "check"}
```

This change reduced false negative rule firings, decreased unnecessary judge invocations, and improved overall pipeline latency.

### 3.6 Cold-Start Mitigation and Latency Stabilisation

A critical failure mode during initial deployment was mid-request model loading: the judge model (TinyLlama, 2.2GB) was lazy-loaded on first invocation, causing request latency to exceed the Gradio UI's 120-second HTTP timeout. The server correctly completed processing, but the client had already reported a connection error, creating a misleading failure signal.

We resolve this with a two-part fix:

**1. Pre-warming at startup:** A `_warmup_models()` function is registered in the FastAPI application lifespan, loading both the primary generator and judge model into RAM during the startup phase before any requests are accepted. This eliminates in-request download and load time, reducing first-token latency from > 300 seconds to approximately 12 seconds on warm hardware.

**2. Hardware-aware gating:** On systems where available RAM falls below a configurable threshold, the judge node is bypassed entirely. The pipeline relies exclusively on the deterministic rules for validation, returning `PASSED` or `FAILED` without the judge score. This ensures stable operation on constrained hardware at the cost of reduced evaluation granularity.

The Gradio interface timeout was simultaneously increased from 120 to 1,800 seconds (30 minutes) as a secondary safeguard for complex generation tasks on slower hardware.

### 3.7 Token Budget and Output Completeness

Initial configuration set `max_tokens = 512` with a default UI slider value of 256. This was insufficient for structured content types: lesson plans requiring eight labelled sections (overview, objectives, materials, introduction, main activity, guided practice, assessment, closure) were consistently truncated, triggering `format_compliance` failures and unnecessary judge + revision cycles.

We increase the CPU token budget to 1,024 tokens (configurable via UI slider, default 256) and add content-type-specific minimum length enforcement in the rules engine, ensuring that the length check lower bound scales with the structural complexity of the requested content type.

---

## 4. Evaluation

### 4.1 Golden Set

We construct a golden evaluation set of 20 manually annotated examples covering four content types: lesson plan (12 examples), WAEC-style exam questions (5), scheme of work (2), and insights analysis (1). Each example contains the generated text, an optional reference, expected Bloom level, expected output language, expected skill tags, and (where available) a RAQ validation report from the production system.

Golden set path: `research/evaluation/golden_set/`

### 4.2 Metrics

We evaluate along eight dimensions. The first five are the core RAQ contribution — pedagogically meaningful metrics orthogonal to lexical overlap:

| Metric | Measures | Implementation |
|---|---|---|
| `bloom_accuracy` | Bloom verb presence at target level | `tests/eval/metrics.py` |
| `cultural_name_ratio` | Nigerian / total detected names | `tests/eval/metrics.py` |
| `format_compliance` | Structural section presence | `tests/eval/metrics.py` |
| `skill_tag_precision` | Skill tag prediction vs. expected | `tests/eval/metrics.py` |
| `readability_ease` | Flesch reading ease | `tests/eval/metrics.py` |
| `rouge_l` | Lexical overlap (reference baseline) | `tests/eval/metrics.py` |
| `raq_judge_score` | LLM judge average (1–5) | `app/validation/judge.py` |
| `raq_pass_rate` | % outputs passing full RAQ pipeline | `research/evaluation/benchmark.py` |

### 4.3 Ablation Conditions

To isolate the contribution of RAQ, we compare three conditions on the golden set:

| Condition | Description |
|---|---|
| **Full RAQ** | 8 rules + 5-dim judge + revision (production system) |
| **Rules only** | 8 rules, no judge, no revision |
| **No validation** | Direct generation, no rules, no judge |

Run: `python research/evaluation/benchmark.py --paper-table`

---

## Commands

```bash
# Run full evaluation and get paper-ready numbers
python research/evaluation/benchmark.py --paper-table \
  --golden-dir research/evaluation/golden_set \
  --output research/evaluation/results/benchmark_$(date +%Y%m%d).json

# Ingest cached Nigerian education corpus into ChromaDB
python -m app.rag.ingestion.ingest --nigerian-education

# Download remaining datasets (requires internet)
conda run -n datasci python research/datasets/download_hf_datasets.py --all --save-only
```
