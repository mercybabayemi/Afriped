# Related Work
*"Rule-Augmented Questioning (RAQ): Pedagogy-Aligned Evaluation for LLM-Generated Educational Content"*

All citations reference [`../references.bib`](../references.bib).

---

## 2.1 Limitations of Standard Automatic Evaluation Metrics

The dominant automatic evaluation metrics in NLP — BLEU (Papineni et al., 2002) and ROUGE (Lin, 2004) — compute n-gram overlap between generated and reference text. While efficient and reproducible, they are well-documented to fail when meaning is preserved under paraphrase, when no single gold reference exists, or when the evaluation domain requires semantic or expert-criteria judgement (Reiter, 2018). BERTScore (Zhang et al., 2020) addresses lexical brittleness by computing cosine similarity between contextual BERT embeddings, achieving higher correlation with human judgements on machine translation and summarisation benchmarks. MAUVE (Pillutla et al., 2021) further captures distributional differences between human and machine text using divergence frontiers, offering a holistic generation quality signal. Despite these advances, none of these metrics encode *domain-specific* quality criteria — they cannot determine whether generated content meets Bloom taxonomy targets, aligns to a curriculum board's structural requirements, or uses culturally appropriate names and examples. In educational content generation, a lesson plan that paraphrases a reference text perfectly may still fail every pedagogical dimension that matters to a teacher.

---

## 2.2 LLM-as-a-Judge Paradigms

The use of LLMs as quality evaluators — "LLM-as-a-Judge" — has emerged as a practical alternative to human annotation for open-ended generation tasks. Zheng et al. (2023) introduced MT-Bench and Chatbot Arena, demonstrating that GPT-4 judgements correlate strongly with human preference rankings across diverse instruction-following tasks, establishing the LLM-as-a-judge paradigm as a viable evaluation methodology. Subsequent work has identified and characterised systematic biases in this approach: Shi et al. (2025) conducted a systematic study of position bias, showing that LLM judges disproportionately favour responses presented first in pairwise comparisons, with effects varying across model families and task types. Wang et al. (2025; TrustJudge) extended this analysis to transitivity violations and self-preference bias, demonstrating that LLM judges frequently produce inconsistent ordinal rankings and proposing probabilistic scoring mechanisms to improve reliability.

Yu et al. (2025; DeCE) decompose evaluation into precision, recall, and semantic criteria components, moving beyond pointwise scoring toward a structured, multi-criteria framework that better captures domain-specific quality dimensions. Zhang et al. (2024; RevisEval) propose adapting the reference to each response rather than using a fixed gold standard, showing that dynamic reference construction improves judge reliability when no single correct answer exists — a common condition in open-ended educational content generation.

Our Rule-Augmented Questioning (RAQ) framework draws on these insights while addressing their primary limitation: existing LLM-as-a-judge approaches evaluate *general* text quality and are not designed for domain-specific pedagogical criteria. RAQ structures the judge's evaluation task through eight deterministic pre-screening rules — eliminating reliance on the LLM for hard factual checks (e.g., explicit content detection, date hallucination) — and constrains the judge to score five pedagogically-grounded dimensions: curriculum alignment, Bloom depth, cultural authenticity, language quality, and educational value. This structured approach mitigates the position and self-preference biases documented by Shi et al. (2025) and Wang et al. (2025) by preventing the judge from performing holistic scoring without criterion-level anchoring.

---

## 2.3 LLM Evaluation in Educational Settings

The application of LLMs as evaluators in education-specific contexts is emerging but not yet standardised. Seo et al. (2025) examine the consistency and accuracy of LLM feedback across educational criteria, finding that while LLMs show promise as automated evaluators, their performance varies substantially with prompt design and model choice, and they exhibit reliability gaps when assessing complex pedagogical constructs. This variability motivates structured evaluation approaches that do not rely solely on the LLM's implicit understanding of pedagogical quality.

Prior work on automated essay scoring (Ramesh and Sanampudi, 2022) and question generation (Kurdi et al., 2020) has applied NLP to educational tasks but typically addresses narrow sub-tasks rather than full curriculum-aligned module generation. These systems are also predominantly designed for Western educational contexts with standardised rubrics (e.g., SAT, GCSE), providing limited transferability to African curriculum boards such as NERDC, WAEC, and NECO, which have distinct structural requirements, cultural expectations, and examination formats.

---

## 2.4 Low-Resource and African Language NLP

African languages remain severely underrepresented in NLP research. Adelani et al. (2021; MasakhaNER) provided the first large-scale named entity recognition dataset for ten African languages, establishing a template for community-driven resource creation that has since expanded to summarisation, machine translation, and sentiment analysis tasks. The Aya project (Üstün et al., 2024) demonstrated that multilingual coverage including African languages requires active community curation rather than passive web scraping, as low-resource languages are disproportionately underrepresented in common crawl corpora.

Our work extends this trajectory to the educational domain. We curate a corpus of 21,000 entries from seven Nigerian education datasets (Electric Sheep Africa, 2024; Ben-45, 2024), embedded using multilingual E5 embeddings (Wang et al., 2024) that support Hausa, Yoruba, and Igbo retrieval. Beyond language coverage, our dataset addresses *curriculum-specific knowledge* — the NERDC scheme of work structure, WAEC examination format, and NECO assessment conventions — that parametric LLM knowledge does not reliably encode.

---

## 2.5 Retrieval-Augmented Generation

Lewis et al. (2020) introduced Retrieval-Augmented Generation (RAG), grounding LLM outputs in retrieved documents to reduce hallucination and improve factual accuracy. RAG has since been applied to knowledge-intensive tasks including open-domain QA, medical diagnosis support, and legal reasoning. In educational contexts, retrieval grounds generated content in curriculum documents rather than relying on the LLM's parametric knowledge of local standards — directly addressing the hallucination risk identified in our context (generating content that claims to align with NERDC standards but does not).

Our implementation uses a locally-deployed ChromaDB vector store indexed on the Nigerian education corpus, with multilingual E5 embeddings enabling cross-lingual retrieval. Unlike cloud-based RAG deployments, our system operates entirely offline — a critical design constraint for deployment in African schools without reliable internet connectivity.

---

## 2.6 Bloom's Taxonomy as a Computational Evaluation Criterion

Bloom's Taxonomy (Bloom et al., 1956; revised Krathwohl, 2002) provides a hierarchical framework for classifying cognitive learning objectives across six levels: Remember, Understand, Apply, Analyse, Evaluate, and Create. In computational form, Bloom level detection relies on identifying characteristic action verbs associated with each level (e.g., "explain" for Understand, "solve" for Apply, "evaluate" for Evaluate). While Bloom alignment is a standard pedagogical quality criterion used by curriculum boards globally, it has received limited attention in NLP evaluation frameworks. We operationalise it as a deterministic rule (bloom_verb_presence) and as a scored judge dimension (bloom_depth), enabling both binary compliance checking and continuous quality scoring within the RAQ pipeline.

---

## Summary of Positioning

| Prior work | What it does | What it lacks | How RAQ extends it |
|---|---|---|---|
| BLEU/ROUGE (Papineni 2002; Lin 2004) | Lexical overlap evaluation | Domain criteria, semantics | RAQ adds pedagogical dimensions |
| BERTScore (Zhang 2020) | Semantic similarity | Domain-specific criteria | RAQ adds Bloom/cultural/alignment |
| LLM-as-a-Judge (Zheng 2023) | General preference scoring | Position bias, domain criteria | RAQ adds deterministic pre-screening |
| TrustJudge (Wang 2025) | Bias analysis | No domain-specific solution | RAQ's rules reduce bias surface |
| DeCE (Yu 2025) | Decomposed criteria scoring | General NLP, not pedagogical | RAQ applies same principle to education |
| Seo et al. 2025 | LLM evaluation in education | No structured criteria | RAQ formalises the criteria |
| MasakhaNER (Adelani 2021) | African language resources | Educational domain | RAQ builds on this trajectory |
| RAG (Lewis 2020) | Grounding in retrieved docs | No pedagogical validation | RAQ adds validation post-retrieval |

---

## References (inline BibTeX keys → [`../references.bib`](../references.bib))

- `\citep{papineni2002bleu}` — BLEU
- `\citep{lin2004rouge}` — ROUGE
- `\citep{zhang2020bertscore}` — BERTScore
- `\citep{pillutla2021mauve}` — MAUVE
- `\citep{zheng2023judging}` — MT-Bench / LLM-as-a-Judge
- `\citep{shi2025judging}` — Position bias in LLM judges
- `\citep{wang2025trustjudge}` — TrustJudge
- `\citep{yu2025dece}` — DeCE
- `\citep{zhang2024reviseval}` — RevisEval
- `\citep{seo2025llmeducation}` — LLMs as evaluators in education
- `\citep{adelani2021masakhaner}` — MasakhaNER / African NLP
- `\citep{lewis2020rag}` — RAG
- `\citep{bloom1956taxonomy}` — Bloom's Taxonomy
- `\citep{krathwohl2002revision}` — Bloom's Taxonomy revised
- `\citep{wang2024multilingual}` — Multilingual E5 embeddings
- `\citep{electricsheepafrica2024vocational}` — Nigerian education datasets
