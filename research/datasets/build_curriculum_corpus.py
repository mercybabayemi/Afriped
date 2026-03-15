"""
Build a content-rich Nigerian curriculum corpus for RAG.

Generates structured educational passages covering real curriculum topics
across boards (NERDC, WAEC, NABTEB, UBEC), levels (Primary to SSS3),
subjects, and content types (lesson notes, topic explanations, exam Q&A).

Run:
    python research/datasets/build_curriculum_corpus.py --dry-run   # preview counts
    python research/datasets/build_curriculum_corpus.py              # generate + ingest
    python research/datasets/build_curriculum_corpus.py --output-only  # write CSV only
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

OUT_CSV  = PROJECT_ROOT / "data" / "raw" / "curriculum_corpus" / "curriculum_corpus.csv"
CHROMA_DIR = PROJECT_ROOT / "data" / "vectorstore"
COLLECTION_NAME = "afriped_curriculum"

CHUNK_SIZE    = 400
CHUNK_OVERLAP = 80

# ── Curriculum taxonomy ────────────────────────────────────────────────────────

BOARDS = {
    "NERDC": ["JSS1", "JSS2", "JSS3", "SSS1", "SSS2", "SSS3"],
    "WAEC":  ["SSS2", "SSS3"],
    "NECO":  ["SSS3"],
    "NABTEB":["VOCATIONAL_ADVANCED"],
    "UBEC":  ["PRIMARY_4", "PRIMARY_5", "PRIMARY_6"],
}

SUBJECTS_BY_BOARD: dict[str, list[str]] = {
    "NERDC": [
        "Mathematics", "English Language", "Biology", "Chemistry", "Physics",
        "Geography", "Economics", "Civic Education", "Agricultural Science",
        "Computer Studies", "Further Mathematics", "Literature in English",
        "Government", "History", "Home Economics", "Physical Education",
        "Basic Science", "Social Studies", "Business Studies",
    ],
    "WAEC": [
        "Mathematics", "English Language", "Biology", "Chemistry", "Physics",
        "Geography", "Economics", "Government", "Literature in English",
        "Agricultural Science", "Commerce", "Further Mathematics",
    ],
    "NECO": [
        "Mathematics", "English Language", "Biology", "Chemistry", "Physics",
        "Geography", "Economics", "Civic Education",
    ],
    "NABTEB": [
        "Electrical Installation", "Auto Mechanics", "Welding and Fabrication",
        "Catering and Hotel Services", "Cosmetology", "Plumbing and Pipe Fitting",
        "Building Construction", "Computer Craft Practice",
    ],
    "UBEC": [
        "Mathematics", "English Language", "Basic Science", "Social Studies",
        "Civic Education", "Agricultural Science", "Home Economics",
    ],
}

BLOOM_LEVELS = ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]

# ── Rich template library ──────────────────────────────────────────────────────
# Each template is a callable that returns a text string given subject/level/board

TEMPLATES: list[dict] = [

    # --- LESSON NOTE TEMPLATES ---
    {
        "type": "lesson_note",
        "template": lambda s, l, b: f"""LESSON NOTE
Subject: {s}
Class: {l}
Board: {b}
Topic: Introduction to {s}

Specific Objectives:
By the end of this lesson, students should be able to:
1. Define the basic concepts in {s}
2. Identify and explain at least three key principles
3. Apply learned concepts to solve simple problems related to {s}

Instructional Materials:
Textbook, charts, diagrams, Lagos State approved curriculum guide, marker board

Introduction (5 minutes):
The teacher begins by asking students what they already know about {s}.
Students in Nigeria encounter {s} in daily life, for example through activities in their communities, markets, and homes. Today we link those everyday experiences to formal academic content.

Main Lesson (25 minutes):
{s} is an important subject in the Nigerian curriculum because it develops analytical thinking and prepares students for both WAEC/NECO examinations and real-world application.

Key concepts covered today:
- Foundational definitions and terminology used in {s}
- Historical development of {s} as a discipline in West Africa
- Relationship between {s} and other subjects in the {b} curriculum
- Practical examples drawn from the Nigerian context

Class Activity:
Students are grouped into pairs. Each pair is given a scenario card drawn from everyday Nigerian situations. They must identify which concept from today's lesson applies and explain their reasoning to the class.

Assessment:
Short written quiz: five questions testing recall and understanding of today's concepts. Students who score below 40% receive additional guided practice before the next lesson.

Homework:
Read Chapter 1 of your approved {b} textbook and write a short paragraph explaining how {s} is relevant to your community in Nigeria.""",
    },

    {
        "type": "lesson_note",
        "template": lambda s, l, b: f"""LESSON NOTE — HIGHER ORDER THINKING
Subject: {s} | Level: {l} | Board: {b}
Topic: Analysis and Application in {s}

Learning Objectives (Bloom Level: ANALYZE and EVALUATE):
Students will be able to:
1. Analyse how concepts in {s} interact with each other
2. Compare and contrast different approaches to problems in {s}
3. Evaluate the strengths and limitations of methods used in {s}
4. Justify their choices using evidence from the {b} curriculum framework

Lesson Procedure:
Step 1 — Review (5 mins): Brief recap of prior knowledge. Teacher uses questioning technique.
Step 2 — New Content (20 mins): Teacher introduces analytical framework specific to {s}.
Step 3 — Group Work (15 mins): Students in groups of four analyse a case study relevant to the Nigerian context. Each group must produce a structured argument.
Step 4 — Presentation (10 mins): One representative per group presents findings.
Step 5 — Synthesis (5 mins): Teacher draws connections between group outputs.
Step 6 — Evaluation (5 mins): Exit ticket — students write one sentence evaluating the most important idea from today.

Nigerian Context Examples:
Real-world applications of {s} in Nigeria include contexts familiar to students: Lagos traffic patterns for physics and mathematics, Niger Delta ecosystem for biology and geography, Aso Rock administrative structure for government and civic education, Okonkwo's tragedy in Chinua Achebe's work for literature analysis.

Assessment Criteria:
Analytical depth (40%), Use of {b} curriculum terminology (30%), Quality of justification (30%)""",
    },

    # --- TOPIC EXPLANATION TEMPLATES ---
    {
        "type": "topic_explanation",
        "template": lambda s, l, b: f"""TOPIC EXPLANATION: {s.upper()} — {b} CURRICULUM

Overview:
This topic is taught at the {l} level under the {b} curriculum framework in Nigeria. Understanding this area is essential for progression through secondary education and success in national examinations.

Core Content:
{s} at the {l} level covers the following key areas:
1. Fundamental concepts and definitions specific to this subject area
2. Theoretical frameworks recognised by the {b} examination board
3. Procedural knowledge and problem-solving methods
4. Contextual application within the Nigerian educational setting

Why This Matters for Nigerian Students:
Students preparing for examinations under {b} need to demonstrate mastery of both content knowledge and the ability to apply that knowledge in structured responses. Examiners look for:
- Correct use of subject-specific vocabulary
- Logical presentation of arguments or solutions
- Evidence of understanding rather than memorisation alone
- Awareness of Nigerian and West African contexts where applicable

Common Student Difficulties:
Teachers frequently report that students at {l} level struggle most with applying abstract concepts to unfamiliar scenarios. The recommended approach is to always connect new content to familiar Nigerian contexts before moving to abstract formulation.

Examination Relevance:
This content area consistently appears in {b} past questions. Students should practise with past papers dating from at least five years back and note the shift toward higher-order questions (analysis, evaluation) in recent years.""",
    },

    {
        "type": "topic_explanation",
        "template": lambda s, l, b: f"""SCHEME OF WORK ENTRY: {s} — {b} — {l}

Week 1: Introduction and Definitions
Objectives: Students identify and define core terms. Teacher uses concept mapping technique.
Resources: {b}-approved textbook, chart paper, markers.
Evaluation: Oral questioning, short class exercise.

Week 2: Principles and Theories
Objectives: Students explain the main theoretical principles governing this topic.
Resources: Supplementary reading from NERDC approved materials, past question papers.
Evaluation: Written summary exercise.

Week 3: Application and Problem Solving
Objectives: Students apply learned principles to solve structured problems.
Resources: Worked examples from WAEC past papers, calculator (where applicable).
Evaluation: Classwork and marking scheme review.

Week 4: Analysis and Critical Thinking
Objectives: Students compare and contrast different approaches; identify strengths and weaknesses.
Resources: Case studies from Nigerian socioeconomic context.
Evaluation: Group presentation, peer assessment.

Week 5: Evaluation and Synthesis
Objectives: Students make reasoned judgements and construct original responses.
Resources: Extended reading, NECO marking guide samples.
Evaluation: Mock examination question (45 minutes, exam conditions).

Week 6: Revision and Consolidation
Objectives: Identify gaps; address common errors; practise examination technique.
Resources: Compiled list of student errors from previous assessments.
Evaluation: Full topic test under examination conditions.""",
    },

    # --- EXAM QUESTION TEMPLATES ---
    {
        "type": "exam_questions",
        "template": lambda s, l, b: f"""EXAMINATION QUESTIONS — {b} FORMAT
Subject: {s} | Level: {l}
Section A: Objectives (Answer ALL questions)

1. Which of the following best describes a fundamental principle in {s}?
   A. A concept with no practical application
   B. A theoretical framework validated through evidence and practice
   C. An observation that applies only outside Nigeria
   D. A definition that changes depending on the examination board
   Answer: B

2. In the context of {b} curriculum requirements, a student at {l} level is expected to:
   A. Memorise all definitions without application
   B. Demonstrate understanding and apply concepts to new situations
   C. Only answer multiple choice questions
   D. Focus exclusively on past questions
   Answer: B

3. Which of the following is NOT a characteristic of good performance in {s} at {l} level?
   A. Clear and logical presentation of ideas
   B. Use of subject-specific vocabulary
   C. Copying definitions word-for-word without explanation
   D. Relating concepts to familiar Nigerian contexts
   Answer: C

4. A student named Aminu is preparing for his {b} examination in {s}. The best strategy for him is to:
   A. Read the textbook cover to cover the night before
   B. Practise with past questions and understand the marking scheme
   C. Memorise every definition in the glossary
   D. Focus only on the topics he finds easy
   Answer: B

5. Which term is most closely associated with higher-order thinking in {s}?
   A. Memorisation
   B. Recitation
   C. Analysis and evaluation
   D. Copying from the board
   Answer: C

Section B: Short Answer (Answer 3 of 5)

Question 6: Define and explain two key concepts in {s} as required by the {b} curriculum at {l} level. Use examples from the Nigerian context. [6 marks]

Question 7: Describe three ways in which understanding {s} is relevant to everyday life in Nigeria. [6 marks]

Question 8: Compare and contrast two different approaches or methods in {s}. State which you consider more effective and justify your answer with at least two reasons. [8 marks]

Question 9: A Nigerian secondary school student is asked to solve a problem in {s}. Outline the steps she should follow, explaining the reasoning behind each step. [6 marks]

Question 10 (Essay): Evaluate the importance of {s} in the Nigerian educational curriculum. In your answer, discuss both the content knowledge and the skills developed through studying this subject. [15 marks]""",
    },

    # --- TEACHER NOTES / PEDAGOGY TEMPLATES ---
    {
        "type": "teacher_notes",
        "template": lambda s, l, b: f"""TEACHER'S GUIDE: TEACHING {s.upper()} AT {l} LEVEL ({b})

Pedagogical Approach:
Teaching {s} at the {l} level in the Nigerian context requires balancing examination preparation with genuine conceptual understanding. The {b} marking scheme rewards students who can explain, apply, and evaluate — not just recall.

Lesson Planning Principles:
1. Always begin with what students already know from their community experience.
2. Introduce new concepts using Nigerian examples before abstract formulations.
3. Build toward higher-order objectives (ANALYZE, EVALUATE, CREATE) progressively across the term.
4. Check understanding through questioning before moving on — do not assume silence means understanding.

Culturally Grounded Teaching Strategies:
For {s} at {l} level, the following Nigerian-specific approaches have proven effective:
- Use names like Chidi, Fatima, Ngozi, Aminu, and Taiwo in word problems and scenarios.
- Reference familiar landmarks: markets, NEPA situations, farming seasons, Lagos traffic.
- Connect abstract concepts to institutions students recognise: NNPC, CBN, JAMB, WAEC, state governments.

Differentiation for Mixed Ability Classes:
Nigerian classrooms often have 40 to 80 students with widely varying preparation levels. Practical strategies:
- Seat stronger students alongside weaker students for peer teaching.
- Provide two versions of class exercises: standard and extended.
- Use choral response for foundational content, individual response for application.

Assessment Design:
Align your continuous assessment questions directly to the {b} examination format so students are familiar with question types before the main examination. A ratio of 40% objective to 60% essay/structured questions mirrors the {b} format and prepares students effectively.

Common Misconceptions in {s}:
Document the errors your specific students make during classwork and compile a running error log. Return to these errors explicitly in revision weeks. Teaching from students' actual mistakes is more effective than generic revision.""",
    },

    # --- CULTURAL CONTEXT TEMPLATES ---
    {
        "type": "cultural_context",
        "template": lambda s, l, b: f"""NIGERIAN CONTEXT: {s} IN EVERYDAY LIFE

Connecting {s} to the Nigerian Experience ({b} | {l}):

The National Curriculum Framework:
In Nigeria, {s} is taught within the {b} curriculum framework, which structures content into three school terms per academic year. The first term typically introduces new topics, the second deepens understanding, and the third focuses on revision and assessment preparation. Students at {l} level are expected to have mastered foundational content and are building toward examination readiness.

West African Cultural Connections:
When teaching {s}, the following connections to Nigerian and West African life make content more relevant and memorable:

Economic Context: Nigeria's economy — including petrol prices at filling stations, exchange rates at Bureau de Change, market pricing in Onitsha or Balogun Market, and agricultural seasons in Kano or Plateau State — provides rich real-world data for mathematical reasoning and economic analysis.

Environmental Context: The Niger Delta ecosystem, Lake Chad basin, Guinea savanna, and coastal mangroves of the South-South provide geographical and biological contexts that are locally authentic and examination-relevant.

Social Context: Nigerian family structures, community governance (traditional rulers, LGA administration), and civic institutions (INEC, EFCC, CBN) provide material for civic education, government, and social studies.

Cultural Context: Yoruba, Igbo, Hausa, and other Nigerian cultural traditions provide material for literature, history, and social studies that is far more engaging for Nigerian students than content drawn exclusively from British or American sources.

Examination Alignment:
The {b} examination board has progressively increased the proportion of questions that require students to apply knowledge to Nigerian-specific scenarios. Students who have been taught with Nigerian context examples from the beginning consistently perform better on these questions than students taught with exclusively Western examples.""",
    },
]


# ── Topic banks per subject (for variety) ─────────────────────────────────────

TOPIC_BANKS: dict[str, list[str]] = {
    "Mathematics":          ["Number and Numeration", "Algebraic Processes", "Geometry", "Statistics and Probability", "Trigonometry", "Calculus", "Mensuration"],
    "English Language":     ["Comprehension", "Summary Writing", "Essay Writing", "Oral English", "Literature", "Grammar", "Vocabulary Development"],
    "Biology":              ["Cell Biology", "Genetics and Heredity", "Ecology", "Reproduction", "Evolution", "Nutrition", "Excretion and Homeostasis"],
    "Chemistry":            ["Atomic Structure", "Chemical Bonding", "Electrochemistry", "Organic Chemistry", "Rates of Reaction", "Acids Bases and Salts", "Quantitative Chemistry"],
    "Physics":              ["Mechanics", "Waves and Sound", "Light and Optics", "Electricity and Magnetism", "Nuclear Physics", "Heat and Temperature", "Measurements"],
    "Geography":            ["Map Reading", "Physical Geography", "Population Geography", "Climate and Vegetation", "Economic Geography", "West Africa", "Nigeria's Geopolitical Zones"],
    "Economics":            ["Supply and Demand", "National Income", "Money and Banking", "International Trade", "Agricultural Economics", "Public Finance", "Economic Development in Nigeria"],
    "Civic Education":      ["Democracy and Governance", "Human Rights", "Rule of Law", "National Values", "Citizenship", "Constitutional Development in Nigeria", "Electoral Process"],
    "Agricultural Science": ["Crop Production", "Animal Production", "Soil Science", "Farm Mechanisation", "Pest and Disease Control", "Agricultural Economics", "Irrigation and Water Management"],
    "Computer Studies":     ["Computer Hardware", "Operating Systems", "Word Processing", "Spreadsheets", "Internet and Networking", "Programming Basics", "Information Security"],
    "Government":           ["Political Concepts", "Arms of Government", "Nigerian Constitution", "Local Government", "Federal System", "International Organisations", "Electoral Systems"],
    "History":              ["Pre-Colonial Nigeria", "Colonialism in West Africa", "Nigerian Independence", "Post-Independence Politics", "African Nationalism", "Slavery and its Abolition", "World Wars and Africa"],
    "Home Economics":       ["Food and Nutrition", "Clothing and Textiles", "Family Living", "Home Management", "Child Development", "Consumer Education", "Hygiene and Sanitation"],
    "Basic Science":        ["Living and Non-Living Things", "Matter and Materials", "Energy", "Simple Machines", "Health and Nutrition", "Plants and Animals", "Environment"],
    "Social Studies":       ["Family and Society", "Culture and Values", "Community Development", "Natural Resources", "Environment and Sustainability", "National Unity", "Nigeria's Neighbours"],
    "Electrical Installation": ["Electrical Safety", "Circuit Design", "Wiring Regulations", "Motor Control", "Lighting Systems", "Earthing and Bonding", "NEPA and Power Distribution"],
    "Auto Mechanics":       ["Engine Systems", "Transmission", "Braking Systems", "Electrical Systems", "Vehicle Maintenance", "Fuel Systems", "Suspension and Steering"],
    "Literature in English":["Prose Fiction", "Drama", "Poetry", "Oral Literature", "African Literature", "Chinua Achebe", "Wole Soyinka", "Ola Rotimi"],
    "Further Mathematics":  ["Complex Numbers", "Matrices", "Vectors", "Differential Equations", "Mechanics", "Statistics", "Numerical Methods"],
}

DEFAULT_TOPICS = ["Core Concepts", "Principles and Theories", "Application", "Analysis", "Evaluation", "Nigerian Context"]


def _topics_for(subject: str) -> list[str]:
    return TOPIC_BANKS.get(subject, DEFAULT_TOPICS)


def _doc_id(text: str, source: str, idx: int) -> str:
    key = text[:200] + source + str(idx)
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def _chunk(text: str) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) >= 40]


def generate_records() -> Iterator[dict]:
    """Yield content records covering the full curriculum taxonomy."""
    global_idx = 0
    for board, levels in BOARDS.items():
        for level in levels:
            subjects = SUBJECTS_BY_BOARD.get(board, SUBJECTS_BY_BOARD["NERDC"])
            for subject in subjects:
                topics = _topics_for(subject)
                for topic in topics:
                    for tmpl in TEMPLATES:
                        text = tmpl["template"](subject, level, board)
                        # Inject topic into the text naturally
                        text = text.replace("Introduction to", f"Introduction to {topic}:", 1) if "Introduction to" in text else text
                        for chunk in _chunk(text):
                            yield {
                                "id": _doc_id(chunk, f"{board}:{level}:{subject}:{topic}:{tmpl['type']}", global_idx),
                                "text": chunk,
                                "board": board,
                                "level": level,
                                "subject": subject,
                                "topic": topic,
                                "content_type": tmpl["type"],
                                "source": "afriped:synthetic_curriculum_v1",
                                "synthetic": True,
                            }
                            global_idx += 1


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "board", "level", "subject", "topic", "content_type", "source", "synthetic"])
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records):,} records to {path}")


def ingest_to_chroma(records: list[dict]) -> int:
    try:
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    except ImportError:
        print("chromadb not found. Run: pip install 'chromadb[default]'")
        return 0

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    ef = DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(COLLECTION_NAME, embedding_function=ef)

    texts     = [r["text"] for r in records]
    ids       = [r["id"]   for r in records]
    metadatas = [{k: v for k, v in r.items() if k not in ("text", "id")} for r in records]

    batch = 500
    total = len(texts)
    for i in range(0, total, batch):
        collection.upsert(
            documents=texts[i:i+batch],
            metadatas=metadatas[i:i+batch],
            ids=ids[i:i+batch],
        )
        print(f"  batch {i//batch + 1}/{-(-total//batch)} ingested")

    final_count = collection.count()
    print(f"\nCollection '{COLLECTION_NAME}' now has {final_count:,} documents")
    return len(records)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",     action="store_true", help="Count records without writing")
    p.add_argument("--output-only", action="store_true", help="Write CSV but skip ChromaDB")
    args = p.parse_args()

    print("Generating curriculum records...")
    records = list(generate_records())
    print(f"Generated {len(records):,} chunks from {len(TEMPLATES)} templates x curriculum taxonomy\n")

    if args.dry_run:
        # breakdown
        from collections import Counter
        by_type  = Counter(r["content_type"] for r in records)
        by_board = Counter(r["board"]        for r in records)
        print("By content type:", dict(by_type))
        print("By board:",        dict(by_board))
        return

    write_csv(records, OUT_CSV)

    if not args.output_only:
        print("\nIngesting into ChromaDB...")
        ingest_to_chroma(records)


if __name__ == "__main__":
    main()
