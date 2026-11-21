# MINDTRACE — Adaptive Learning & Reasoning Diagnosis Platform

MINDTRACE is an intelligent learning and cognitive diagnosis platform engineered to analyze how students reason through complex Physics problems. Unlike conventional educational software that merely grades the final numeric answer or relies on opaque end-to-end LLM prompts, MINDTRACE evaluates reasoning step-by-step, detects the exact first point of failure, isolates candidate misconceptions, confirms hypotheses using Bayesian active probing, and adapts subsequent instruction through Bayesian Knowledge Tracing (BKT) and spaced repetition.

---

## Architecture Overview

```
                                      +------------------------------------+
                                      |          Next.js Frontend          |
                                      |   Student Dashboard & Assessment   |
                                      |   Teacher Cohort Analytics         |
                                      +-----------------+------------------+
                                                        |
                                                        | REST API (JSON)
                                                        v
                                      +------------------------------------+
                                      |       FastAPI Unified Backend      |
                                      +-----------------+------------------+
                                                        |
                         +------------------------------+------------------------------+
                         |                                                             |
                         v                                                             v
+--------------------------------------------------+         +--------------------------------------------------+
|      MEMBER 1: REASONING DIAGNOSIS ENGINE        |         |       MEMBER 2: ADAPTIVE LEARNING ENGINE         |
+--------------------------------------------------+         +--------------------------------------------------+
| 1. Concept Graph (23 Physics concepts, DAG)     |         | 1. Learner Model (Student state & mastery store)  |
| 2. Misconception Library (24 benchmark schemas)  |         | 2. Bayesian Knowledge Tracing (BKT) Engine        |
| 3. Step-by-Step Reasoning Extractor (LLM/Offline)|         | 3. 3-Tier Adaptive Difficulty Adjuster            |
| 4. First-Error Detector & Chain Analyzer         |         | 4. Prerequisite-Aware Question Selector          |
| 5. Active Diagnostic Question Selector           | ======> | 5. Targeted Knowledge Repair & Interventions     |
| 6. Bayesian Hypothesis Verification Engine       | Contract| 6. SM-2 Spaced Repetition Scheduling             |
| 7. Persistent SQLite Diagnosis Repository        |         | 7. Unified Student & Teacher Analytics Engine    |
+--------------------------------------------------+         +--------------------------------------------------+
```

---

## Key Modules & Capabilities

### 1. Reasoning Diagnosis (Member 1)
- **Concept Graph**: Directed acyclic graph representing 23 high-school Physics concepts across kinematics, forces, and Newton's laws. Enforces prerequisite ordering, transitive dependency resolution, and missing-prerequisite detection.
- **Misconception Library**: 24 empirically calibrated Physics misconceptions indexed by concept, error category, refutation text, and contrasting cases.
- **Reasoning Extractor**: Splits multi-sentence student explanations into structured reasoning steps (`claim`, `reasoning_type`, `formulas`, `concept_ids`, `evidence_text`). Supported by a deterministic `SmartOfflineLLMProvider` as well as pluggable OpenAI/Gemini providers.
- **First-Error Detector**: Evaluates student reasoning against question rubrics in strict chronological order, distinguishing genuine conceptual flaws, direction/sign errors, and arithmetic slips from downstream propagation errors.
- **Bayesian Active Probing**: Maintains probability distributions across competing misconception hypotheses (and `unknown_or_other`). Selects follow-up probes maximizing information gain (entropy reduction) and halts when diagnostic confidence thresholds are met.

### 2. Adaptive Learning & Remediation (Member 2)
- **Bayesian Knowledge Tracing (BKT)**: Calibrates prior mastery, transit ($P(T)$), guess ($P(G)$), and slip ($P(S)$) parameters. Consumes Member 1 diagnostic exports directly to initialize or penalize specific concept priors without client-side recalculation.
- **Adaptive Question Selection**: Dynamically matches question difficulty (Foundation $\to$ Application $\to$ Challenge) to student performance streaks and diverts to foundational prerequisites when unmastered blockers are identified.
- **Knowledge Repair Interventions**: Generates 3-stage targeted pedagogical interventions:
  1. *Conceptual Refutation*: Addresses the specific diagnosed misconception directly.
  2. *Contrasting Case*: Juxtaposes the erroneous intuition against the physical law.
  3. *Prerequisite Refresh*: Re-anchors understanding to foundational concepts.
- **Spaced Repetition Engine**: Modified SM-2 algorithm tracking repetition counts, intervals, and easiness factors ($E$-Factor) for long-term retention.

### 3. Unified Web Interface (Member 3)
- **Student Dashboard (`/student/dashboard`)**: Displays real-time overall proficiency, accuracy rates, radar/progress breakdowns across 23 concepts, strength/weakness classifications, and recommended next topics.
- **Diagnostic Assessment (`/student/assessment`)**:
  - *Step A (Concept Selection)*: 23-concept grid with topic filters and prerequisite indicators.
  - *Step B (Reasoning Submission)*: Dual input for final answer and step-by-step justification.
  - *Step C (Reasoning & First-Error Timeline)*: Interactive claim breakdown highlighting the earliest error point and downstream cascades.
  - *Step D (Active Bayesian Probing)*: Dynamic progress distribution across competing hypotheses with an explicit illustrative calibration banner.
  - *Step E (Diagnosis Synthesis & Export)*: Clear pedagogical diagnosis, prerequisite repair path, and inspection of the Member 2 handoff JSON.
- **Adaptive Practice (`/student/learning`)**: Dynamic question prompt, option picker / numeric input, timer, prerequisite diversion alert, and immediate BKT mastery progression.
- **Spaced Repetition Queue (`/student/reviews`)**: SM-2 flashcard interface with 0–5 quality rating buttons and instant scheduling feedback.
- **Teacher Cohort Dashboard (`/teacher/dashboard`)**: Class-wide proficiency metrics, concept mastery heatmaps, misconception prevalence charts, and a student intervention table with 1-click drill-down.

---

## 15-Stage End-to-End Learning Journey

The complete student and teacher journey is verified via automated integration tests (`tests/test_e2e_full_workflow.py`):

1. **Dashboard Entry**: Student opens `/student/dashboard`; initial mastery breakdown loads.
2. **Concept Selection**: Student selects `net_force` from the 23-concept catalog.
3. **Reasoning Submission**: Student submits solution with an intentional direction error.
4. **Reasoning Extraction**: Backend parses claims, formulas, and exact evidence text.
5. **First-Error Detection**: Engine identifies vector addition of opposing forces as the root failure.
6. **Active Question Selection**: Bayesian engine chooses follow-up probe maximizing entropy reduction.
7. **Probe Response**: Student answers the targeted diagnostic follow-up question.
8. **Bayesian Belief Update**: Posterior probabilities update; `unknown_or_other` hypothesis is preserved.
9. **Member 2 Export**: Normalized diagnosis contract is handed off to the adaptive engine.
10. **Adaptive Question Selection**: Learning engine serves difficulty-matched practice question.
11. **Practice Submission**: Student answers correctly; BKT updates mastery ($P(L_t) > P(L_{t-1})$).
12. **Intervention Generation**: Multi-stage knowledge repair generated for remaining weaknesses.
13. **Spaced Review Recording**: Student reviews flashcard; SM-2 recalculates next interval.
14. **Student Dashboard Refresh**: Student metrics (total assessments, accuracy, mastery) update.
15. **Teacher Dashboard Aggregation**: Teacher cohort views updated class heatmaps and alert lists.

---

## Project Structure

```
mindtrace/
|-- backend/
|   |-- app/
|   |   |-- adaptive_learning/    # BKT, difficulty engine, question bank, SM-2
|   |   |-- dashboard/            # Student & teacher analytics aggregation
|   |   |-- diagnosis/            # Concept graph, extractor, error detector, Bayesian engine
|   |   |-- main.py               # FastAPI application, route handlers, lifecycle management
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |   |-- student/
|   |   |   |   |-- assessment/   # 5-step diagnostic reasoning interface
|   |   |   |   |-- dashboard/    # Student mastery dashboard
|   |   |   |   |-- learning/     # Adaptive practice session
|   |   |   |   |-- reviews/      # Spaced repetition flashcards
|   |   |   |-- teacher/
|   |   |       |-- dashboard/    # Teacher cohort analytics & drill-down
|   |   |-- components/           # Modular UI widgets (assessment, learning, teacher, layout)
|   |   |-- context/              # StudentContext (multi-profile switching, active session)
|   |   |-- services/             # Typed API clients for FastAPI backend
|   |   |-- types/                # TypeScript models mirroring backend Pydantic schemas
|-- data/
|   |-- concepts/                 # physics_force_motion.json (23 concepts DAG)
|   |-- misconceptions/           # physics_force_motion.json (24 misconceptions)
|   |-- questions/                # diagnostic_rubrics.json & physics_practice_questions.json
|-- tests/
|   |-- adaptive/                 # Member 2 unit & integration tests
|   |-- dashboard/                # Analytics engine tests
|   |-- diagnosis/                # Member 1 unit & integration tests
|   |-- test_e2e_full_workflow.py # Full 15-stage end-to-end journey test
|-- README.md
|-- requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Node.js 18+ & npm 9+
- SQLite 3

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Nimalan07/mindtrace.git
cd mindtrace

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend test suite (130 tests)
python -m pytest -v

# Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be live at: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run linting check
npm run lint

# Build for production
npm run build

# Start development server
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## API Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | API and engine status check |
| `GET` | `/api/diagnosis/concepts` | Retrieve all 23 Physics concepts in learning order |
| `GET` | `/api/diagnosis/questions` | Catalog of diagnostic tasks with structured rubrics |
| `POST` | `/api/diagnosis/submit` | Submit student reasoning for extraction & first-error analysis |
| `POST` | `/api/diagnosis/followup` | Submit follow-up response for Bayesian belief update |
| `GET` | `/api/diagnosis/session/{id}/export` | Export Member 2 standardized diagnostic handoff |
| `POST` | `/api/adaptive/question/next` | Fetch next adaptive practice question (prerequisite-aware) |
| `POST` | `/api/adaptive/assessment/submit` | Submit answer, grade, and trigger BKT mastery updates |
| `GET` | `/api/adaptive/intervention/{student_id}/{concept_id}` | Generate 3-stage knowledge repair intervention plan |
| `GET` | `/api/adaptive/spaced-repetition/due/{student_id}` | Retrieve cards due for spaced review |
| `POST` | `/api/adaptive/spaced-repetition/review` | Record SM-2 review score (0–5) and update interval |
| `GET` | `/api/analytics/student/{student_id}` | Aggregated student proficiency & concept mastery breakdown |
| `GET` | `/api/analytics/teacher` | Cohort mastery heatmap, misconception prevalence & alerts |

---

## Verification & Test Results

- **Automated Pytest Suite**: **130 / 130 Passed** (100% pass rate in 3.04s)
  - Unit tests for concept graph traversal, cycle rejection, and prerequisite ordering.
  - Bayesian updating, normalization, entropy reduction, and `unknown_or_other` preservation.
  - First-error isolation, downstream cascade tracking, and candidate misconception retrieval.
  - BKT mathematical updates, ceiling asymptotic behavior, and SM-2 interval expansion.
  - Complete 15-stage student/teacher journey integration test.
- **Frontend Code Quality**:
  - `npm run lint`: **0 errors, 0 warnings**.
  - `npm run build`: **9/9 Next.js App Router routes compiled cleanly**.
