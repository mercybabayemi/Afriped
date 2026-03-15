# Conference Targeting Strategy

**Paper title:** Adaptive LLM for Curriculum-Aligned Educational Content and Assessment in African Contexts

**Core angle for all submissions:** Rethinking LLM evaluation beyond BLEU/ROUGE metrics — introducing pedagogically-grounded, culturally-aware evaluation for CPU-accessible education AI in underserved African contexts.

---

## Tier 1 — Primary Targets (Full Paper)

### ACL 2026 — Main Conference
- **Venue:** San Diego, CA, USA · July 2–7, 2026
- **Submission:** ACL Rolling Review (ARR) — openreview.net/group?id=aclweb.org/ACL/ARR/2026/January
- **Fit:** RAQ as a novel evaluation framework for educational NLP; African curriculum corpora as language resources; empirical comparison of pedagogical depth vs baseline prompting
- **Emphasis:** Methodology + evaluation rigour. Frame RAQ as a domain-aware evaluation paradigm.
- **Tracks:** NLP for social good, generative systems, evaluation methods, explainability

### EACL 2026 — European Chapter of ACL
- **Venue:** Rabat, Morocco · March 24–29, 2026
- **Submission:** https://2026.eacl.org/calls/papers/
- **Fit:** Low-resource African education datasets + CPU-efficient inference + structured evaluation pipeline. EACL explicitly welcomes resource creation + evaluation methodology papers.
- **Emphasis:** Low-resource NLP angle + dataset contribution + RAQ as an evaluation standard
- **Topics:** Low-resource methods, generation, interpretability, resources/evaluation

### EMNLP 2026 — Empirical Methods in NLP
- **ARR submission deadline:** ~May 25, 2026
- **Fit:** Empirical measurement of model behaviour against pedagogical criteria — directly aligns with EMNLP's interest in "LLM evaluation beyond static leaderboards"
- **Emphasis:** Quantitative results showing RAQ outperforms standard prompting on curriculum alignment %; show CPU constraints are a real-world scenario
- **Key angle:** "Evaluation beyond BLEU/ROUGE" — explicitly a stated EMNLP priority

---

## Tier 2 — Secondary Targets (Short Paper / System Demo)

### CoNLL 2026 — Computational Natural Language Learning
- **Venue:** San Diego, CA, USA · July 3–4, 2026 (co-located with ACL)
- **Submission:** https://www.conll.org/
- **Fit:** Framing curriculum objective alignment as a language learning task; how LLMs model Bloom taxonomy progression
- **Angle:** Linguistically grounded learning — Bloom verb banks as a cognitive learning signal

### NLDB 2026 — Natural Language & Information Systems
- **Deadline:** Feb 20, 2026
- **Fit:** RAQ + Judge LLM as explainable AI; CPU deployment touches sustainability and reliable systems
- **Angle:** Interpretability, evaluation, retrieval systems

### NLPI 2026 — NLP & Information Retrieval
- **Fit:** RAG pipeline with African curriculum corpora; efficient retrieval + CPU inference as a practical IR contribution
- **Angle:** RAG / LLM integration, responsible AI

---

## Tier 3 — Applied / Industry Tracks

### ICMLAI 2026 — Machine Learning & AI Conference
- **Venue:** Madrid, Spain · May 18–20, 2026
- **Fit:** CPU-based efficient LLM → edge/efficient AI + adaptive automation; RAQ → trustworthy AI
- **Angle:** ML systems + deployment efficiency + educational impact

### AIMLA 2026 — Applications of AI/ML (Sydney, Australia)
- **Submission:** https://www.ccnet2026.org/aimla/index
- **Fit:** Applied AI for education in real contexts — practical system design, accessibility, case studies
- **Angle:** CPU constraints + African context = underserved settings story

### AMLC 2026 — Applied Machine Learning Conference
- **Venue:** Virginia, USA · April 17–18, 2026
- **Submission:** https://appliedml.us/2026/cfp/
- **Fit:** Case study of applied AI tool development with metrics; practitioner audience
- **Angle:** Applied system design + lessons learned + measurable outcomes

### AAIML 2026 — Advances in AI & ML (Tokyo, Japan)
- **Dates:** March 20–22, 2026
- **Submission:** https://easychair.org/conferences/?conf=aaiml2026
- **Note:** Accepts abstract-only submissions — good for early work with preliminary results

### ICNLP 2026 — International Conference on NLP
- **Venue:** Xi'an, China · March 20–22, 2026
- **Fit:** Text generation + evaluation + culturally grounded content fits NLP systems category

---

## Submission Strategy

### For ACL / EACL / EMNLP (top tier):

1. **Lead with the evaluation novelty**: RAQ as domain-aware NLP evaluation, not just a prompting trick
2. **Formal RAQ definition**: Define RAQ mathematically — rules as Boolean predicates, judge as a 5-dimensional scoring function
3. **Empirical results table**: RAQ vs no-RAQ vs BLEU/ROUGE on bloom_accuracy, cultural_name_ratio, format_compliance, raq_pass_rate
4. **CPU constraint as a design choice**: Position it as accessibility research — 8–15 min/session on CPU is a result, not a limitation
5. **African dataset contribution**: Clearly quantify corpus size, coverage, and how retrieval improves alignment scores

### For workshops (ACL / EMNLP satellite):
- ACL Workshop on Efficient NLP & Multilingual Systems
- EMNLP Evaluation Paradigms Workshop
- These have later deadlines and are less competitive but still peer-reviewed publications

### On mentioning Claude / AI platform:
- **In academic methods section**: Fine to state platform/model for reproducibility (e.g., "using Phi-3-mini-4k-instruct for generation and TinyLlama-1.1B as judge")
- **Do NOT headline**: Avoid "Built with Claude" as a contribution claim — focus on RAQ methodology and curriculum metrics
- **For social/GitHub**: Mention tools freely to attract developer attention; separate research claims from marketing

---

## Conference Quick Reference

| Conference | Deadline | Venue | Link |
|---|---|---|---|
| ACL 2026 (ARR) | Rolling | San Diego, USA | openreview.net/group?id=aclweb.org/ACL/ARR/2026/January |
| EACL 2026 | Past (March 2026) | Rabat, Morocco | 2026.eacl.org/calls/papers/ |
| EMNLP 2026 | ~May 2026 | TBA | ARR submission |
| CoNLL 2026 | With ACL | San Diego, USA | conll.org |
| NLDB 2026 | Feb 20, 2026 | Online | — |
| ICMLAI 2026 | TBA | Madrid, Spain | — |
| AIMLA 2026 | TBA | Sydney, Australia | ccnet2026.org/aimla/ |
| AMLC 2026 | TBA | Virginia, USA | appliedml.us/2026/cfp/ |
| AAIML 2026 | TBA | Tokyo, Japan | easychair.org/conferences/?conf=aaiml2026 |
| ICNLP 2026 | TBA | Xi'an, China | — |
