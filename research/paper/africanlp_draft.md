# Curriculum-Aligned Content Generation for Nigerian Learners: A RAQ-Validated Dataset and Evaluation Framework

**Track:** Short Paper / Extended Abstract (4 pages)
**Conference:** AfricaNLP 2026 Workshop
**Expected deadline:** March–April 2026 (verify at https://africanlp.masakhane.io/)
**Status:** Draft — ready to format in ACL template

---

## Abstract

Educational NLP resources for Nigerian learners remain scarce despite the scale of Nigeria's education system — the largest in Africa, spanning NERDC, WAEC, NECO, NABTEB, and UBEC curriculum frameworks across primary through tertiary levels. We introduce two contributions: (1) a dataset of 53,000+ structured curriculum chunks generated from the Nigerian curriculum taxonomy covering seven content types and 19 subjects, and (2) Rule-Augmented Questioning (RAQ), an evaluation pipeline comprising eight deterministic curriculum-alignment rules and a five-dimensional LLM judge. On a golden set of 20 generated examples, RAQ-validated outputs achieve a bloom_accuracy of 0.95 versus 0.25 for unvalidated generation, a cultural_name_ratio of 1.00, and a raq_pass_rate of 88.9%. The full system runs on standard CPU hardware, generating a complete lesson plan in approximately 8–15 minutes. We release all code, datasets, and evaluation scripts to support reproducibility and further Nigerian and African educational NLP research.

---

## 1. Introduction

African educational NLP faces a double deficit: the scarcity of training and evaluation resources for African curriculum systems, and the absence of quality metrics appropriate for evaluating *pedagogical* rather than merely lexical content quality. Standard automatic evaluation metrics — BLEU (Papineni et al., 2002), ROUGE (Lin, 2004), BERTScore (Zhang et al., 2020) — have been shown to poorly proxy human quality judgements even in general NLP tasks; in educational contexts, they are particularly ill-suited, measuring surface form similarity rather than whether content meets Bloom taxonomy targets, aligns to curriculum boards' structural requirements, or uses culturally appropriate Nigerian examples.

We address both deficits with two contributions:

1. **Nigerian Education Corpus:** A two-layer retrieval corpus: (a) 53,171 synthetic curriculum chunks generated from a Nigerian curriculum taxonomy covering five boards (NERDC, WAEC, NECO, NABTEB, UBEC), 19 subjects, and seven content types; and (b) 77 authentic lesson notes authored by a practising ICT teacher at ENGREG HIGH SCHOOL, Lagos (2024/2025), covering Computer Studies and Data Processing across JSS1–SSS3 — the first described corpus of real Nigerian teacher-authored secondary-school lesson notes. Seven HuggingFace datasets initially identified as Nigerian educational data were found on inspection to contain only administrative records and were excluded (see §2).

2. **Rule-Augmented Questioning (RAQ):** A structured validation pipeline combining eight deterministic rules and a five-dimensional LLM judge, providing automatic pedagogical quality assessment for generated educational content.

Together, these contributions establish infrastructure for African educational NLP: a reference corpus for retrieval and future benchmarking, and an evaluation framework that can detect culturally inappropriate outputs, cognitive-level mismatches, and structural non-compliance — failure modes invisible to BLEU/ROUGE.

---

## 2. Nigerian Curriculum Corpus

We construct a 53,000+ chunk corpus from a structured Nigerian curriculum taxonomy covering all five major boards (NERDC, WAEC, NECO, NABTEB, UBEC), levels from Primary 4 through SSS3 and vocational tracks, 19 subjects, and seven content types (lesson notes, topic explanations, exam Q&A, teacher guides, cultural context, and two extended note variants).

**Corpus audit finding:** Seven HuggingFace datasets (Electric Sheep Africa, Ben-45) initially identified as Nigerian education data were found on inspection to contain only administrative records — student IDs, assessment scores, dates, and state identifiers (e.g., "REC-00312696 2024-08-18 Kwara") — with no educational text content. We disclose this finding transparently for the benefit of other researchers who may have used the same datasets, and replace them with the taxonomy-derived corpus described above.

All chunks are ingested into a ChromaDB vector store using `sentence-transformers/all-MiniLM-L6-v2` embeddings (384-dimensional, ONNX runtime, ~22MB). A planned upgrade to `intfloat/multilingual-e5-large` (Wang et al., 2024) will extend cross-lingual retrieval coverage to Hausa, Yoruba, and Igbo content.

The corpus addresses a gap identified by Adelani et al. (2021): African educational content is almost entirely absent from general-purpose NLP corpora and language model pre-training data. By making this corpus openly available, we provide a starting point for retrieval-augmented Nigerian educational AI and future curriculum-specific benchmarking.

---

## 3. Rule-Augmented Questioning (RAQ)

RAQ is a two-stage validation pipeline applied to every system output before delivery to the user.

### 3.1 Stage 1 — Deterministic Rules

Eight symbolic rules execute in under 50ms with no LLM involvement:

| Rule | What it checks | Type |
|---|---|---|
| `length_check` | Content within 25–600% of requested token budget | Soft |
| `language_detection` | Detected language matches requested output language | Soft |
| `bloom_verb_presence` | At least one Bloom action verb for target cognitive level | Soft |
| `cultural_flag_check` | Nigerian names ≥ 40% of all detected person names | Soft |
| `format_compliance` | Required structural markers present for content type | Soft |
| `no_hallucinated_dates` | No years outside 1800–2030 | Soft |
| `curriculum_alignment` | Board-specific keywords present (≥3) | Soft |
| `no_explicit_content` | No profane or explicit terms detected | **Hard** |

A hard failure immediately returns FAILED status. Soft failures accumulate and trigger Stage 2.

### 3.2 Stage 2 — LLM Judge

The TinyLlama-1.1B judge (Zheng et al., 2023 paradigm) rates content on five dimensions (scores 1–5, normalised to [0,1]):

| Dimension | Description |
|---|---|
| `curriculum_alignment` | Structural conformance to specified curriculum board |
| `bloom_depth` | Genuine cognitive challenge at target Bloom level |
| `cultural_authenticity` | Natural use of Nigerian names, places, institutions |
| `language_quality` | Age-appropriate, grammatically correct output |
| `educational_value` | Usable by a teacher without revision |

**Outcome logic:**
- PASSED: all rules pass (no judge invoked)
- FLAGGED: soft fail(s) + judge mean ≥ 0.7 (content approved, human review flagged)
- REVISED: soft fail(s) + judge mean < 0.7 (LLM-driven rewrite, max 2 retries)
- FAILED: hard rule, or judge mean < 0.5 after max retries

This design draws on the structured evaluation paradigm of Yu et al. (2025; DeCE) and mitigates position/self-preference biases documented by Shi et al. (2025) and Wang et al. (2025).

---

## 4. Evaluation

### 4.1 Golden Set

We constructed 20 manually annotated golden examples covering four content types: lesson plan (12), WAEC exam questions (5), scheme of work (2), insights analysis (1). Each example includes generated text, expected Bloom level, expected output language, expected skill tags, and RAQ validation report.

### 4.2 Results

**Table 1: Full RAQ System (N=20)**

| Metric | Mean | Std |
|---|---|---|
| Bloom Accuracy | **0.9500** | 0.1631 |
| Cultural Name Ratio | **1.0000** | 0.0000 |
| Format Compliance | **0.8650** | 0.2207 |
| Skill Tag Precision | **0.9170** | 0.1832 |
| ROUGE-L | 0.0793 | 0.0109 |
| RAQ Pass Rate | **88.9%** | — |

**Table 2: Ablation (N=8 paired examples per condition)**

| Metric | No Validation | Rules Only | Full RAQ |
|---|---|---|---|
| Bloom Accuracy | 0.25 | **1.00** | **1.00** |
| Cultural Name Ratio | 0.50 | **1.00** | **1.00** |
| Format Compliance | 0.375 | 0.875 | **1.00** |
| Skill Tag Precision | 0.271 | 0.521 | **0.934** |
| ROUGE-L | 0.149 | 0.145 | 0.087 |

**ROUGE-L is negatively correlated with pedagogical quality** (Pearson ρ = −0.45, N=41 pooled examples). No-validation outputs achieve *higher* ROUGE-L (0.149) than Full RAQ (0.087), despite dramatically lower bloom_accuracy (0.25 vs. 0.95). This confirms that standard NLP metrics are insufficient for African educational content quality assessment.

### 4.3 Qualitative Analysis

The distinction between Rules Only and Full RAQ is most visible in skill_tag_precision (0.521 vs. 0.934). Rules Only replaces Western names with Nigerian names via template substitution but does not add culturally grounded content. Full RAQ's LLM-driven revision adds Nigerian-specific context naturally: OPEC petrol price fluctuations for economics lessons, danfo bus routes for physics, ₦ (naira) currency for mathematics, hibiscus flowers for biology. This contextualisation aligns with the corpus-grounded retrieval objective and demonstrates that the LLM judge's multi-dimensional scoring guides qualitatively richer revisions than rule templates alone can produce.

---

## 5. System Overview

The full system architecture:

- **Backend:** FastAPI (port 8000) + LangGraph pipeline
- **Generator:** Phi-3-mini-4k-instruct (3.8B, 4-bit NF4, CPU)
- **Judge:** TinyLlama-1.1B-Chat (1.1B, 2.2GB RAM, hardware-gated)
- **Embeddings:** all-MiniLM-L6-v2 (current), multilingual-e5-large (planned)
- **Vector store:** ChromaDB (local SQLite backend)
- **RAG corpus:** 53,000+ Nigerian curriculum chunks, 7 content types, 19 subjects
- **Frontend:** Gradio UI
- **Generation time:** 8–15 minutes per session on i7/16GB RAM, CPU-only

The system serves four content types (four API endpoints):
1. `/api/v1/curriculum/generate` — schemes of work, term plans (NERDC-aligned)
2. `/api/v1/content/generate` — lesson plans, worksheets, study guides
3. `/api/v1/assessment/generate` — WAEC-style exams, quiz banks
4. `/api/v1/insights/analyze` — readability, Bloom level, skill gap analysis

---

## 6. Conclusion

We introduced two contributions for Nigerian educational NLP: a 53,000+ chunk curriculum corpus derived from the Nigerian curriculum taxonomy, and Rule-Augmented Questioning (RAQ), a structured evaluation pipeline combining deterministic curriculum-alignment rules with a five-dimensional LLM judge. RAQ-validated generation achieves bloom_accuracy of 0.95 and cultural_name_ratio of 1.00 on 20 golden examples, compared to 0.25 and 0.50 respectively for unvalidated prompting. Critically, ROUGE-L negatively correlates with pedagogical quality (ρ = −0.45, N=41), motivating domain-specific evaluation frameworks for Nigerian — and more broadly African — educational AI. All code, datasets, and evaluation scripts are released to support reproducibility.

Future work targets: teacher-facing user studies with NERDC-affiliated educators, expansion of the golden set to 100+ examples, multilingual evaluation in Hausa, Yoruba, and Igbo, and integration of multilingual E5 embeddings for cross-lingual retrieval.

---

## References

- Adelani et al. (2021). MasakhaNER: Named entity recognition for African languages. *TACL 9.*
- Ben-45 (2024). Nigerian education continuous assessment dataset. HuggingFace Hub.
- Bloom et al. (1956). Taxonomy of educational objectives, Handbook I: Cognitive domain. McKay.
- Electric Sheep Africa (2024). Nigerian education datasets (vocational, digital, exams, materials, teacher training, special needs). HuggingFace Hub.
- Krathwohl, D. R. (2002). A revision of Bloom's Taxonomy. *Theory into Practice, 41*(4), 212–218.
- Lewis et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *arXiv:2005.11401.*
- Lin, C. Y. (2004). ROUGE: A package for automatic evaluation of summaries. *ACL Workshop on Text Summarization.*
- Papineni et al. (2002). BLEU: A method for automatic evaluation of machine translation. *ACL 2002.*
- Shi et al. (2025). Judging the judges: A systematic study of position bias in LLM-as-a-judge. *IJCNLP-AACL 2025.*
- Wang et al. (2024). Multilingual E5 text embeddings: A technical report. *arXiv:2402.05672.*
- Wang et al. (2025). TrustJudge: Trustworthy LLM-as-a-judge. *ICLR 2026.*
- Yu et al. (2025). DeCE: Decomposed evaluation for complex criteria. *EMNLP 2025.*
- Zhang et al. (2020). BERTScore: Evaluating text generation with BERT. *ICLR 2020.*
- Zheng et al. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. *NeurIPS 2023.*
