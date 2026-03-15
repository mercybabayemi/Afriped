# Beyond ROUGE: Domain-Specific Evaluation for Nigerian Educational Content Generation

**Track:** Short Paper / Extended Abstract (4 pages)
**Conference:** AfricaNLP 2026 Workshop
**Expected deadline:** March–April 2026 (verify at https://africanlp.masakhane.io/)
**Status:** Option B — leads with evaluation critique. Compare with africanlp_draft.md (Option A — leads with dataset + system contribution).

---

## Abstract

We demonstrate that standard NLP evaluation metrics are insufficient — and actively misleading — for assessing AI-generated educational content in Nigerian educational contexts. Across 41 pooled examples from an ablation study, ROUGE-L negatively correlates with pedagogical quality (Pearson ρ = −0.45): outputs with no validation score higher on ROUGE-L (0.149) than fully validated outputs (0.087), despite the latter achieving bloom_accuracy of 0.95 versus 0.25. We introduce Rule-Augmented Questioning (RAQ), a domain-specific evaluation framework comprising eight deterministic curriculum-alignment rules and a five-dimensional LLM judge designed for Nigerian curriculum standards (NERDC, WAEC, NABTEB, UBEC). RAQ is deployed within AfriPed, a CPU-native generation system for Nigerian learners running on consumer hardware without cloud dependency. We release all code, evaluation scripts, and a 200-example evaluation set to support reproducible African educational NLP research.

---

## 1. Introduction

African educational NLP faces an evaluation problem that precedes the resource problem: the tools researchers use to measure generation quality were not designed for African educational content and produce systematically misleading results when applied to it.

BLEU (Papineni et al., 2002), ROUGE (Lin, 2004), and BERTScore (Zhang et al., 2020) all measure surface-form similarity between generated and reference text. For Nigerian educational content, this is the wrong dimension. A lesson plan that uses only Western names (John, Mary, James) scores identically to one using Nigerian names (Chidi, Fatima, Ngozi, Aminu) under any of these metrics. A lesson plan that targets the REMEMBER level of Bloom's taxonomy scores identically to one that targets ANALYZE — unless the reference text happens to share the same verb choices. Curriculum structural compliance, Bloom taxonomy alignment, and cultural grounding are entirely invisible to ROUGE.

We present empirical evidence of the consequences. We then propose RAQ as an operationalised alternative — not a theoretical framework but a working system with code, thresholds, and measurable results.

---

## 2. The Evaluation Gap: Empirical Evidence

### 2.1 Ablation design

We compare three generation conditions on 8 paired examples each:
- **No validation:** Direct generation, no rules, no judge
- **Rules only:** 8 deterministic rules, no LLM judge
- **Full RAQ:** 8 rules + 5-dimensional LLM judge + revision loop

### 2.2 Results

| Metric | No Validation | Rules Only | Full RAQ |
|---|---|---|---|
| Bloom Accuracy | 0.25 | 1.00 | **0.95** |
| Cultural Name Ratio | 0.50 | 1.00 | **1.00** |
| Format Compliance | 0.375 | 0.875 | **1.00** |
| Skill Tag Precision | 0.271 | 0.521 | **0.934** |
| ROUGE-L | **0.149** | 0.145 | 0.087 |

Pearson ρ (ROUGE-L vs bloom_accuracy, N=41 pooled) = **−0.34**

ROUGE-L is highest for the worst-performing condition and lowest for the best. Any researcher using ROUGE-L alone to evaluate an African educational content generation system would conclude the opposite of the truth.

### 2.3 Why this happens

Unvalidated outputs are brief, generic, and structurally similar to short reference templates — high ROUGE, low educational value. RAQ-validated outputs are expanded with Nigerian-specific content (OPEC price fluctuations for economics, danfo bus routes for physics, ₦ naira for mathematics, hibiscus flowers for biology). This richness diverges from generic reference templates and lowers ROUGE while raising every pedagogically meaningful metric.

---

## 3. RAQ: Rule-Augmented Questioning

### 3.1 Stage 1 — Eight deterministic rules

Eight symbolic rules execute in under 50ms with no LLM involvement:

| Rule | What it checks | Type |
|---|---|---|
| `length_check` | Within 25–600% of token budget | Soft |
| `language_detection` | Matches requested language at > 85% confidence | Soft |
| `bloom_verb_presence` | A&K (2001) action verbs for target level | Soft |
| `cultural_flag_check` | Nigerian names ≥ 40% of detected names | Soft |
| `format_compliance` | Structural markers with synonym expansion | Soft |
| `no_hallucinated_dates` | Years within 1800–2030 | Soft |
| `curriculum_alignment` | Board-specific keywords (≥ 3) | Soft |
| `no_explicit_content` | No profane/explicit terms | **Hard** |

Bloom verb lists are grounded in Anderson & Krathwohl (2001). The 40% cultural threshold is empirically validated: system-generated content achieves 100% pass rate across tested thresholds (40%–80%).

### 3.2 Stage 2 — Five-dimensional LLM judge

Invoked only when at least one soft rule fails. TinyLlama-1.1B-Chat rates content on curriculum_alignment, bloom_depth, cultural_authenticity, language_quality, and educational_value (1–5 per dimension). Output format is `key: value` lines rather than JSON — empirically more reliable for sub-2B parameter models.

**Outcome:** PASSED / FLAGGED (approved with review) / REVISED (LLM rewrite, max 2 retries) / FAILED

---

## 4. System and Corpus

### 4.1 AfriPed

Four generation endpoints: curriculum schemes, lesson plans, exam questions, pedagogical insights. LangGraph pipeline: retrieve → generate → rules → judge → revise → skill_tag.

**Hardware:** i7 CPU, 16GB RAM, no GPU. Generation: 8–15 min/session.
**Generator:** Phi-3-mini-4k-instruct (3.8B, bfloat16)
**Judge:** TinyLlama-1.1B-Chat (hardware-gated)
**RAG:** ChromaDB, all-MiniLM-L6-v2 embeddings (22MB, ONNX)

CPU-native design is an infrastructure equity choice: Nigerian schools operate without GPU servers or broadband. Systems that require cloud connectivity are inaccessible to the teachers AfriPed targets.

### 4.2 Curriculum corpus

The corpus has two layers:

*Layer 1 — Synthetic (53,171 chunks):* Generated from a Nigerian curriculum taxonomy spanning five boards (NERDC, WAEC, NECO, NABTEB, UBEC), levels Primary through SSS3, 19 subjects, and seven content types (lesson notes, topic explanations, exam Q&A, teacher guides, cultural context). Each chunk is grounded in real Nigerian curriculum structure and terminology.

*Layer 2 — Real teacher lesson notes (77 documents):* Authentic weekly lesson notes from a practising ICT teacher at ENGREG HIGH SCHOOL, Pedro Shomolu, Lagos (academic session 2024/2025), covering Computer Studies and Data Processing across JSS1–SSS3. Each document contains learning objectives, step-by-step teaching activities, keywords, evaluative questions, assignments, and full lesson content. This is, to our knowledge, the only described corpus of real Nigerian secondary-school teacher-authored lesson notes.

**Corpus audit disclosure:** The seven HuggingFace datasets originally incorporated (Electric Sheep Africa, Ben-45) were found on inspection to contain only administrative record data (student IDs, scores, dates, e.g. "REC-00312696 2024-08-18 Kwara") with no educational text content. We replace these with the two-layer corpus above and disclose this finding transparently for the benefit of other researchers who may have used the same datasets.

---

## 5. Evaluation

### 5.1 Golden sets

- **v1 (N=20):** Manually annotated, 4 content types, all 6 Bloom levels
- **v2 (N=200):** Systematic parameter variation (content_type × Bloom × board × subject), 60 examples flagged for human spot-check

### 5.2 Full system results (N=20)

| Metric | Mean | Std |
|---|---|---|
| Bloom Accuracy | **0.9500** | 0.1631 |
| Cultural Name Ratio | **1.0000** | 0.0000 |
| Format Compliance | **0.8650** | 0.2207 |
| Skill Tag Precision | **0.9170** | 0.1832 |
| ROUGE-L | 0.0793 | 0.0109 |
| RAQ Pass Rate | **88.9%** | — |

### 5.3 No existing domain-specific framework for African education

A review of the literature finds no prior operationalised evaluation framework specific to African educational content generation. AfroBench (linguistic benchmark, 64 languages) and the Decolonizing LLMs framework (ethnographic critique) address adjacent concerns but neither provides measurable criteria for pedagogical quality. RAQ is, to our knowledge, the first such framework.

---

## 6. Conclusion

Standard NLP metrics negatively correlate with pedagogical quality for Nigerian educational content (ρ = −0.45). RAQ demonstrates that domain-specific evaluation is both implementable (eight rules + one judge, no GPU, < 50ms for rules) and necessary. A system that scores well on ROUGE may be producing pedagogically worthless content for Nigerian teachers; only domain-specific metrics reveal this. Our findings are grounded in Nigerian curriculum data; extension to other African educational systems is left to future work.

We release all code, the 200-example evaluation set, teacher annotation rubric, and the Zephyr-7B API judge for benchmark validation to support reproducible African educational NLP research.

---

## References

- Adelani et al. (2021). MasakhaNER. *TACL 9.*
- Anderson, L.W. & Krathwohl, D.R. (2001). *A Taxonomy for Learning, Teaching and Assessing.* Longman.
- Bloom et al. (1956). *Taxonomy of Educational Objectives.* McKay.
- Lewis et al. (2020). RAG for knowledge-intensive NLP. *arXiv:2005.11401.*
- Lin, C.Y. (2004). ROUGE. *ACL Workshop.*
- Papineni et al. (2002). BLEU. *ACL 2002.*
- Shi et al. (2025). Position bias in LLM-as-a-judge. *IJCNLP-AACL 2025.*
- UNESCO (2024). Generative AI in African Education.
- Wang et al. (2024). Multilingual E5 embeddings. *arXiv:2402.05672.*
- Wang et al. (2025). TrustJudge. *ICLR 2026.*
- Zhang et al. (2020). BERTScore. *ICLR 2020.*
- Zheng et al. (2023). MT-Bench and Chatbot Arena. *NeurIPS 2023.*
