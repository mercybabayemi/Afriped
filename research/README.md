# Adaptive LLM — Research Index

**Full title:** *Rule-Augmented Questioning (RAQ): Curriculum-Aligned Educational Content Generation for African Learners*

**Abstract (working):** See [`paper/abstract_variants.md`](paper/abstract_variants.md) — venue-specific versions ready to submit.

---

## Folder Structure

```
research/
├── README.md                        ← You are here (master index)
├── references.bib                   ← All BibTeX citations (16 entries)
│
├── paper/                           ← Writing artifacts
│   ├── abstract_variants.md         ← 5 venue-specific abstracts
│   ├── related_work.md              ← Scholarly related work (real citations)
│   └── results_tables.md            ← Paper tables (fill after benchmark run)
│
├── conferences/                     ← Submission strategy
│   ├── README.md                    ← Master deadlines + odds table
│   ├── immediate.md                 ← Submit THIS WEEK (AfricaNLP, AIED, EMNLP)
│   ├── tier1_acl_emnlp.md          ← ACL, EMNLP, EACL, CoNLL with recent winners
│   └── tier2_applied.md            ← AIML India, AIMLA, AMLC, EDM, AIED
│
├── datasets/                        ← Data pipeline
│   ├── dataset_registry.yaml        ← 7 HF datasets + 2 external benchmarks
│   └── download_hf_datasets.py      ← Download, cache (Parquet), ingest to ChromaDB
│
├── prompts/                         ← RAQ pipeline
│   └── raq_pipeline.py             ← 4-layer RAQ prompt templates + parser
│
├── evaluation/                      ← Evaluation infrastructure
│   ├── benchmark.py                 ← RAQ vs baseline metrics runner
│   ├── golden_set/                  ← 4 annotated examples (lesson plan, exam, scheme, insights)
│   └── results/                     ← Benchmark outputs (gitignored)
│
└── notebooks/                       ← Jupyter experiments
    ├── 00_model_verification.ipynb  ← Phi-3-mini-4k-instruct load + inference test (CPU/Colab)
    ├── 01_dataset_exploration.ipynb ← HF dataset schema, distributions, keyword coverage
    ├── 02_raq_pipeline_demo.ipynb   ← Full 4-layer pipeline walkthrough
    └── 03_evaluation_results.ipynb  ← Benchmark results + paper figures
```

---

## Core Research Contributions

| # | Contribution | Novelty | Location |
|---|---|---|---|
| 1 | **RAQ evaluation layer** | Domain-aware evaluation beyond BLEU/ROUGE (Papineni et al., 2002; Lin, 2004) | `app/validation/`, `research/prompts/raq_pipeline.py` |
| 2 | **5-dimensional pedagogical judge** | Bloom depth + cultural authenticity vs. generic LLM judge (Zheng et al., 2023) | `app/validation/judge.py` |
| 3 | **CPU-optimised inference** | 4-bit quantised LLM on consumer hardware | `app/core/llm.py` |
| 4 | **Nigerian education corpus** | 21,000 entries across 7 domains for NERDC/WAEC/NECO alignment | `research/datasets/` |
| 5 | **4-layer generation pipeline** | Structured outline → expand → retrieve → validate | `app/agents/graph.py` |

---

## Key Argument (for paper framing)

> Standard NLP metrics — BLEU (Papineni et al., 2002), ROUGE (Lin, 2004), BERTScore (Zhang et al., 2020) — are insensitive to pedagogical quality. A lesson plan can achieve high ROUGE-L against a reference while failing every Bloom taxonomy criterion. RAQ addresses this by combining deterministic curriculum-alignment rules with a five-dimensional LLM judge (cf. Zheng et al., 2023; Yu et al., 2025), structured to mitigate the position and consistency biases documented by Shi et al. (2025) and Wang et al. (2025; TrustJudge).

---

## Datasets Status

| Dataset | HF ID | Cached | Rows | RAG Role |
|---|---|---|---|---|
| vocational | electricsheepafrica/nigerian_education_vocational_technical | ✓ | 3,000 | Curriculum content |
| continuous_assessment | Ben-45/nigerian_education_continuous_assessment | ✗ | — | Difficulty calibration |
| digital_learning | electricsheepafrica/nigerian_education_digital_learning | ✗ | — | ICT content |
| online_exams | electricsheepafrica/nigerian_education_online_exams | ✗ | — | Assessment Q&A |
| learning_materials | electricsheepafrica/nigerian_education_learning_materials | ✗ | — | Retrieval context |
| teacher_training | electricsheepafrica/nigerian_education_teacher_training | ✗ | — | Pedagogy reference |
| special_needs | electricsheepafrica/nigerian_education_special_needs | ✗ | — | Inclusive content |

**Download remaining 6** (requires internet access):
```bash
conda run -n datasci python research/datasets/download_hf_datasets.py --all --save-only --max-examples 3000
```

---

## How to Run Experiments

```bash
# 1. Get real numbers for your abstract
conda run -n datasci python research/evaluation/benchmark.py --paper-table

# 2. Download datasets (when internet available)
conda run -n datasci python research/datasets/download_hf_datasets.py --all --save-only

# 3. Check what's cached
conda run -n datasci python research/datasets/download_hf_datasets.py --status

# 4. Explore datasets interactively
conda run -n datasci jupyter notebook research/notebooks/01_dataset_exploration.ipynb

# 5. Full RAQ pipeline demo
conda run -n datasci jupyter notebook research/notebooks/02_raq_pipeline_demo.ipynb
```

---

## Submission Checklist (Priority Order)

- [ ] **Run benchmark** → get bloom_accuracy, raq_pass_rate numbers
- [ ] **Verify AfricaNLP deadline** → https://africanlp.masakhane.io/
- [ ] **Verify AIED LBR deadline** → https://aied2026.org
- [ ] **Register on OpenReview** → https://openreview.net (needed for EMNLP ARR)
- [ ] **Submit AfricaNLP abstract** this week (highest odds: 85%)
- [ ] **Begin EMNLP full paper** → due April 15 via ARR
- [ ] **Download remaining 6 datasets** when internet available
- [ ] **Add results to golden set** → `research/evaluation/golden_set/`

---

## References Quick-Cite

See [`references.bib`](references.bib) for full BibTeX. Key entries:

| Cite key | Paper |
|---|---|
| `papineni2002bleu` | BLEU (ACL 2002) |
| `lin2004rouge` | ROUGE (ACL Workshop 2004) |
| `zhang2020bertscore` | BERTScore (ICLR 2020) |
| `zheng2023judging` | MT-Bench / LLM-as-a-Judge (NeurIPS 2023) |
| `yu2025dece` | DeCE / decomposed evaluation (EMNLP 2025) |
| `wang2025trustjudge` | TrustJudge (ICLR 2026) |
| `shi2025judging` | Position bias in LLM judges (IJCNLP-AACL 2025) |
| `zhang2024reviseval` | RevisEval (arXiv 2024) |
| `seo2025llmeducation` | LLMs as evaluators in education (MDPI 2025) |
| `adelani2021masakhaner` | MasakhaNER / African NLP (TACL 2021) |
| `lewis2020rag` | RAG (arXiv 2020) |
| `bloom1956taxonomy` | Bloom's Taxonomy (1956) |
| `krathwohl2002revision` | Bloom's Taxonomy revised (2002) |
