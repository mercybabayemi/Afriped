# Pedagogically-Constrained LLM Generation for Nigerian Classrooms: Early Results from a CPU-Deployed System

**Track:** Late Breaking Results
**Conference:** AIED 2026 — 27th International Conference on Artificial Intelligence in Education
**Target venue:** Recife, Brazil, July 2026
**Submission deadline:** ~March 15–20, 2026 (verify at https://aied2026.org)
**Format:** 2–4 pages
**Status:** Draft — ready to format in ACM or Springer LNCs template

---

## Abstract

We present early results from an AI system that generates Bloom-taxonomy-aligned lesson plans, WAEC-style assessments, and pedagogical insights for Nigerian learners, running entirely on consumer CPU hardware. The key design contribution is Rule-Augmented Questioning (RAQ) — a validation layer that filters outputs against eight curriculum-alignment rules and scores them across five pedagogical dimensions using a lightweight LLM judge. In contrast to existing educational AI systems requiring GPU infrastructure, our system completes a full lesson plan in 8–15 minutes per session without cloud dependency. On 20 golden examples, RAQ-validated content achieves a bloom_accuracy of 0.95 vs. 0.25 for unvalidated prompting. We discuss implications for teacher-facing AI tools in under-resourced African school contexts and outline planned user studies with NERDC-affiliated educators.

---

## 1. Introduction

Generating high-quality educational content for Nigerian classrooms faces two intersecting challenges. First, the *content challenge*: curriculum frameworks used in Nigeria — the National Educational Research and Development Council (NERDC) scheme of work, the West African Examinations Council (WAEC) examination format, and the National Examinations Council (NECO) standards — are structurally distinct from curricula represented in general-purpose LLM pre-training data. Second, the *infrastructure challenge*: Nigerian schools predominantly operate without GPU servers or reliable broadband connectivity, placing state-of-the-art large language models out of reach for most educators.

We present AfriPed, a system that addresses both challenges. AfriPed generates NERDC- and WAEC-aligned lesson plans, assessments, curriculum schemes, and pedagogical insights using 4-bit quantised models on consumer CPU hardware. Critically, we introduce Rule-Augmented Questioning (RAQ), a structured validation layer that automatically checks whether generated content meets Bloom taxonomy targets, uses culturally appropriate Nigerian examples, and conforms to curriculum board structural requirements.

The central finding of this early-results paper is that RAQ-validated generation dramatically outperforms unvalidated prompting on all pedagogical quality dimensions (bloom_accuracy: 0.95 vs. 0.25), while standard NLP metrics such as ROUGE-L *negatively* correlate with these pedagogical gains (ρ = −0.45, N=41) — demonstrating that existing automatic evaluation metrics are insufficient for educational content quality assessment.

---

## 2. System Design

### 2.1 Pipeline

The AfriPed pipeline is orchestrated via LangGraph and comprises five stages:

1. **RAG Retrieval:** Retrieve top-k passages from a ChromaDB vector store indexed on two corpus layers: (a) 53,171 synthetic curriculum chunks spanning five Nigerian boards, 19 subjects, and seven content types; and (b) 77 authentic weekly lesson notes from a practising ICT teacher at ENGREG HIGH SCHOOL, Lagos (2024/2025 session), covering Computer Studies and Data Processing across JSS1–SSS3. Note: seven HuggingFace datasets initially identified as Nigerian educational data were found on audit to contain only administrative records (student IDs, scores) with no educational text, and were replaced by this two-layer corpus.
2. **Generation:** Phi-3-mini-4k-instruct (3.8B, 4-bit NF4 quantisation) generates structured content in a two-pass process: outline → expanded output.
3. **Symbolic Rule Validation:** Eight deterministic rules execute in under 50ms, checking length, language, Bloom verb presence, cultural name ratio, format compliance, hallucinated dates, curriculum alignment, and explicit content.
4. **LLM Judge:** TinyLlama-1.1B-Chat rates content on five pedagogical dimensions (curriculum alignment, Bloom depth, cultural authenticity, language quality, educational value) using a 1–5 integer scale per dimension.
5. **Revision:** If the judge average falls below 0.7 (normalised), the pipeline sends a targeted correction prompt and regenerates (max 2 retries).

The hardware-aware design bypasses the judge on systems with insufficient available RAM, ensuring stable operation on constrained hardware.

### 2.2 The RAQ Validation Layer

Formally, let G denote a generated output and P the prompt parameters (curriculum board b, education level l, Bloom target t, output language λ). The eight deterministic rules R = {r₁,...,r₈} are typed as:

- **Hard rules** (1 rule: `no_explicit_content`): a single positive result immediately returns FAILED status without judge invocation
- **Soft rules** (7 rules): failures accumulate into a set S; if S ≠ ∅, the LLM judge is invoked

The judge J(G, P) computes the mean of five dimension scores ∈ [0,1]. The final outcome:
- **PASSED:** S = ∅ (all rules pass, no judge needed)
- **FLAGGED:** S ≠ ∅ and J ≥ 0.7 (issues detected, human review recommended)
- **REVISED:** S ≠ ∅ and J < 0.7 (LLM-driven rewrite, up to 2 retries)
- **FAILED:** hard rule triggered, or J < 0.5 after max retries

This design mitigates position and self-preference biases documented in LLM-as-a-judge literature (Shi et al., 2025; Wang et al., 2025) by enforcing criterion-level scoring rather than holistic preference judgements.

### 2.3 CPU Deployment

The system runs on an Intel Core i7, 16GB RAM without GPU. Key techniques:

- 4-bit NF4 quantisation via bitsandbytes reduces Phi-3-mini memory footprint from ~7.6GB (FP32) to ~2.2GB
- TinyLlama-1.1B requires ~2.2GB RAM; hardware-gating prevents OOM on constrained hardware
- Pre-warming at FastAPI startup eliminates cold-start latency during requests
- Full lesson plan generation: approximately 8–15 minutes per session

---

## 3. Evaluation

### 3.1 Golden Set

We constructed a golden evaluation set of 20 manually annotated examples covering four content types: lesson plan (12), WAEC-style exam questions (5), scheme of work (2), and insights analysis (1). Each example contains the generated text, an optional reference, the expected Bloom taxonomy level, expected output language, expected skill tags, and (where available) the RAQ validation report from the production system.

### 3.2 Metrics

We evaluate on eight dimensions; the first five capture pedagogical quality beyond what BLEU/ROUGE measures:

| Metric | Description |
|---|---|
| `bloom_accuracy` | Presence of Bloom action verbs at target cognitive level (0–1) |
| `cultural_name_ratio` | Nigerian names as fraction of all detected names (0–1; higher = better) |
| `format_compliance` | Structural section presence score for content type (0–1) |
| `skill_tag_precision` | Predicted skill tags vs. expected (0–1) |
| `rouge_l` | Standard lexical overlap metric (included as baseline comparison) |

### 3.3 Results

**Table 1: Full RAQ System (N=20 golden examples)**

| Metric | Mean | Std |
|---|---|---|
| Bloom Accuracy | **0.9500** | 0.1631 |
| Cultural Name Ratio | **1.0000** | 0.0000 |
| Format Compliance | **0.8650** | 0.2207 |
| Skill Tag Precision | **0.9170** | 0.1832 |
| ROUGE-L | 0.0793 | 0.0109 |
| RAQ Pass Rate | **88.9%** | — |

**Table 2: Ablation Study (N=8 paired examples per condition)**

| Metric | No Validation | Rules Only | Full RAQ |
|---|---|---|---|
| Bloom Accuracy | 0.25 | **1.00** | **1.00** |
| Cultural Name Ratio | 0.50 | **1.00** | **1.00** |
| Format Compliance | 0.375 | 0.875 | **1.00** |
| Skill Tag Precision | 0.271 | 0.521 | **0.934** |
| ROUGE-L | 0.149 | 0.145 | 0.087 |

**Key finding:** ROUGE-L is *inversely* related to pedagogical quality across conditions (Pearson ρ = −0.45 across N=41 pooled examples). No-validation outputs achieve higher ROUGE-L (0.149) than Full RAQ outputs (0.087), despite being dramatically worse on all pedagogical dimensions. This demonstrates that existing automatic evaluation metrics are insufficient for educational content quality assessment — the core motivation for RAQ.

### 3.4 Qualitative Observations

The ablation study reveals a qualitatively important distinction between Rules Only and Full RAQ. While both conditions achieve similar bloom_accuracy and cultural_name_ratio scores, the full RAQ revision produces qualitatively richer outputs: where Rules Only replaces Western names with Nigerian names via template substitution, Full RAQ's LLM-driven revision adds Nigerian-specific context (e.g., OPEC petrol prices for economics, danfo buses for physics, ₦ currency for mathematics), resulting in higher skill_tag_precision (0.934 vs. 0.521). This suggests that the LLM judge's five-dimensional scoring provides guidance that improves not just surface compliance but content depth.

---

## 4. Discussion

### 4.1 Pedagogical Implications

RAQ embeds curriculum standards as structural generation constraints, not post-hoc quality checks. The bloom_verb_presence rule ensures that generated lesson objectives actively target the requested cognitive level; the cultural_flag_check rule ensures that Nigerian student names and cultural contexts appear naturally in content rather than as afterthoughts. Together, these constraints address the two most common failures of general-purpose LLMs when applied to African educational content: cognitive-level drift (producing REMEMBER-level content when ANALYZE or CREATE was requested) and cultural defaulting (using Western names and contexts despite an African target audience).

### 4.2 Infrastructure Equity

A core argument of this paper is that CPU efficiency is not a technical compromise but an ethical design choice. The 8–15 minute generation time on a 16GB RAM consumer laptop is acceptable for a teacher preparing content the evening before a lesson — a common use case in Nigerian schools where lesson preparation happens at home without school infrastructure access. Cloud-dependent systems would require internet connectivity that is frequently unavailable or unaffordable in rural Nigerian school contexts.

### 4.3 Limitations and Future Work

Several limitations constrain our current findings:

1. **Golden set size (N=20):** Sufficient for LBR but not for main paper claims. We are expanding to 100+ examples and plan live API comparison.
2. **No user study:** We have not yet tested with actual NERDC-affiliated teachers. Planned user studies will assess perceived quality, trust, and pedagogical utility.
3. **Readability metric reliability:** The textstat library returned neutral defaults (50.0) for all examples, indicating the library may not have been correctly installed; this metric is excluded from primary claims.
4. **Multilingual support:** Current system generates primarily in English; Hausa, Yoruba, and Igbo output is functional but not yet systematically evaluated.

---

## 5. Conclusion

We presented early results from AfriPed, a CPU-deployed educational content generation system for Nigerian learners. Our Rule-Augmented Questioning (RAQ) framework achieves bloom_accuracy of 0.95 and cultural_name_ratio of 1.00 on a 20-example golden set, with an 88.9% RAQ pass rate. Ablation study results confirm that both deterministic rules and LLM-guided revision contribute to quality improvement, with the LLM judge enabling richer content depth (skill_tag_precision 0.934 vs. 0.521 for rules-only). Crucially, ROUGE-L negatively correlates with pedagogical quality (ρ = −0.45, N=41), motivating domain-specific evaluation frameworks for educational AI systems.

Future work includes teacher-facing user studies, expansion of the golden set, multilingual evaluation (Hausa, Yoruba, Igbo), and integration of multilingual embeddings for cross-lingual RAG retrieval.

---

## References

- Papineni et al. (2002). BLEU: A method for automatic evaluation of machine translation. *ACL 2002.*
- Lin, C. Y. (2004). ROUGE: A package for automatic evaluation of summaries. *ACL Workshop 2004.*
- Zhang et al. (2020). BERTScore: Evaluating text generation with BERT. *ICLR 2020.*
- Zheng et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. *NeurIPS 2023.*
- Shi et al. (2025). Judging the judges: A systematic study of position bias in LLM-as-a-judge. *IJCNLP-AACL 2025.*
- Wang et al. (2025). TrustJudge: Trustworthy LLM-as-a-judge with consistency and calibration. *ICLR 2026.*
- Adelani et al. (2021). MasakhaNER: Named entity recognition for African languages. *TACL 2021.*
- Lewis et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *arXiv 2020.*
- Bloom et al. (1956). Taxonomy of educational objectives: The classification of educational goals. Handbook I: Cognitive domain.
- Krathwohl, D. R. (2002). A revision of Bloom's Taxonomy. *Theory into Practice, 41*(4), 212–218.
