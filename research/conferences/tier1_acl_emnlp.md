# Tier 1 — ACL · EMNLP · EACL · CoNLL
*Honest assessment as of March 4, 2026*

---

## ACL 2026 — Main Conference

**Dates:** July 2–7, 2026, San Diego, CA, USA
**Main paper ARR deadline:** February 15, 2026 → **CLOSED**
**System Demo deadline:** ~April 2026 → **OPEN** (verify at https://2026.aclweb.org)
**Submission portal:** https://openreview.net/group?id=aclweb.org/ACL/ARR/2026/January

### Honest odds
| Track | Odds | Why |
|---|---|---|
| Main paper | 0% | ARR Feb deadline passed; cannot commit a new paper |
| System Demonstrations | **80%** | Separate deadline ~April; needs working demo + GitHub |
| Findings of ACL | 45% | Via EMNLP ARR commitment if accepted |

### ACL 2026 Special Theme: Explainability & Evaluation
ACL 2026 explicitly themes around explainability of LLMs and evaluation methodology — your RAQ framework is directly relevant. However, you missed the main paper window.

### Recent winners relevant to your work
- **ACL 2024:** Aya Model (Cohere for AI) — multilingual model covering 101 languages including African languages. Won for dataset contribution + multilingual coverage. *Lesson: African language + dataset = real recognition.*
- **ACL 2024 Best Resource Paper:** Papers providing high-quality corpora for underrepresented languages consistently win. Your Nigerian education dataset is directly this category.
- **ACL 2023 Best Paper:** LIMA — showing that data quality beats data quantity. *Lesson: 21K curated Nigerian education examples > millions of generic web text.*

### Demo track strategy (submit April 2026)
**What they want:** Running system, clean UI, live demo, GitHub with reproducible code.
**Your assets:** Gradio UI on HuggingFace Spaces, FastAPI backend, 4 working endpoints.
**Title:** *"AfriPed: A CPU-Deployable Educational AI System for African Curriculum Alignment"*
**Key demo moment:** Show the same prompt with RAQ on vs. RAQ off — let reviewers see the difference in Bloom depth and cultural authenticity.

---

## EMNLP 2026 — Empirical Methods in NLP

**Dates:** November 2026, Budapest, Hungary
**ARR submission deadline:** ~April 15, 2026 → **OPEN** *(submit in 6 weeks)*
**ARR commitment deadline:** ~May 25, 2026
**Portal:** https://openreview.net (ARR submission)

### Honest odds
| Track | Odds | Notes |
|---|---|---|
| Main paper | 35% | Rigorous; need solid empirical results |
| Findings of EMNLP | 55% | Lower bar; strong framing enough |
| Workshops | 65% | Multiple relevant workshops (see below) |

### What EMNLP reviewers look for (2024–2025 pattern)
- **Empirical rigour:** Three reviewers, each scoring 1–5 on soundness, substance, replicability, clarity
- **Reproducibility:** Code + data released; results runnable
- **The "so what" test:** Why does this matter beyond the specific domain?

### Recent winners relevant to your work
- **EMNLP 2024 Best Paper:** Papers on evaluation methodology that showed *existing metrics are wrong* won disproportionately. Your claim that BLEU/ROUGE fail for pedagogical content is exactly this pattern.
- **EMNLP 2024 Outstanding:** Work demonstrating LLM-as-judge biases (positional, verbosity). Your RAQ rules explicitly counter these biases — cite Shi et al. (2025) and Wang et al. (2025) to show you're aware of them.
- **EMNLP 2023:** Papers on low-resource settings with new benchmarks performed well. Nigerian education = low-resource domain benchmark.

### The vibe
EMNLP wants you to *prove things empirically*. "RAQ produces better content" is not enough. You need:
- Table comparing bloom_accuracy: full RAQ vs. rules-only vs. judge-only vs. no validation
- Statistical significance (even a t-test on 20+ examples)
- Error analysis: what types of content fail RAQ most often and why?

### EMNLP workshops (open ~June 2026)
- **Eval4NLP** — Evaluation of NLP systems (direct fit for RAQ as evaluation framework)
- **NLP for Positive Impact** — AI for underserved communities
- **EffNLP** — Efficient NLP (CPU deployment angle)

---

## EACL 2026 — European Chapter of ACL

**Dates:** March 24–29, 2026, Rabat, Morocco
**Main deadline:** January 2026 → **CLOSED**
**Workshop deadlines:** Some workshops still accepting → verify at https://2026.eacl.org

### Status: Closed for main paper. Check workshops.
The main paper deadline has passed. However, EACL workshops often have later deadlines. Specifically:
- Workshops on African NLP or low-resource languages co-located with EACL may still be open
- Non-archival poster submissions sometimes accepted until early March

### Why EACL was your strongest main-paper shot (for future reference)
**The Vibe:** Historically values "Resources" and "Low-Resource Languages." EACL is held in Rabat — the first time at an African venue. There is a genuine appetite for African-centric NLP research from the programme committee.

**Recent winners (pattern):**
- EACL 2024: Efficient summarisation for long documents (LOCOST) — won for doing more with less compute. *Lesson: CPU efficiency is valued, not dismissed.*
- EACL 2023: Low-resource language resources won Best Paper. Turkic language benchmarks, cross-lingual transfer for underrepresented languages. *Lesson: Dataset + benchmark is a primary contribution.*
- EACL 2024 Social Impact: Papers demonstrating AI for marginalised communities. African education = direct fit.

**Your strength:** If you had submitted, framing as "Benchmark for West African Educational Alignment" — the dataset as primary contribution, RAQ as secondary — would have had ~70% odds.

**Lesson for ACL/EMNLP:** Apply this same framing. The dataset IS a contribution. Name it clearly.

---

## CoNLL 2026 — Computational Natural Language Learning

**Dates:** July 3–4, 2026, San Diego (co-located with ACL)
**Deadline:** Follows ACL ARR → **CLOSED for this cycle**

### Honest odds: 0% for main paper (missed window); 40% if resubmitting next year

### The vibe
CoNLL is hardcore linguistics + cognitive modelling. Recent winners reconstruct proto-languages from daughter languages, model psycholinguistic phenomena, study acquisition of grammar. This is *not* a systems or applications conference.

**Your angle (if submitting in future):**
Frame the Bloom taxonomy verb distribution as a *linguistic learning signal* — does RAQ-constrained generation show different syntactic patterns than unconstrained generation? This is a CoNLL paper; a systems demo is not.

---

## What to do right now for Tier 1

```
Priority 1 (this week):   → Submit AfricaNLP workshop abstract
Priority 2 (by Apr 15):   → Submit EMNLP 2026 full paper via ARR
Priority 3 (April):       → Submit ACL 2026 Demo track
Priority 4 (June):        → Submit to EMNLP workshops (Eval4NLP, NLP for Positive Impact)
```

**Before any of these:** Run `python research/evaluation/benchmark.py --paper-table` and get real numbers into the abstract.
