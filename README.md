# Meet SmartCV: A Multi-Agent System for Semantic Talent Matching 🤝

> *"The right person for the right role — understood, not just matched."*

---

## What is this?

SmartCV is a custom multi-agent system that takes a candidate's CV and finds the job offers that genuinely fit them — ranked by real semantic compatibility, not keyword overlap.

We built this from scratch. Seven specialized agents, each with a single responsibility, coordinated by an orchestrator that adapts the flow based on what it finds at each step. No pre-packaged agent was used. Every role was designed, justified, and implemented by the team.

The result behaves more like a team of expert reviewers working in parallel than a search engine.

---

## The Problem

Traditional CV screening tools match by keywords. If a CV says `scikit-learn` and the job posting says `supervised ML`, it's a miss — even though they mean the same thing.

We fix this with **semantic embeddings**: both CVs and job requirements are converted into vectors that represent *meaning*, not letters. Skills that are conceptually close end up mathematically close. Then we filter *must-have* constraints, rank semantically, and explain the gaps.

This is not a pipeline. It's a reasoning system.

---

## Meet the Agents

We named each agent after a figure from history whose defining contribution mirrors exactly what that agent does. 

---

### 🟣 JOHN VON NEUMANN — The Orchestrator
*John von Neumann designed the architecture of the modern computer: a central unit that coordinates memory, processing, and I/O. Our orchestrator does the same.*

Built on **LangGraph**, John von Neumann manages the full pipeline state. It decides which agents activate, handles conditional branching (e.g., only waking up Lamarr if grey-zone skills exist), and ensures every agent receives exactly the context it needs .

```
Input:  CV upload
Output: Coordinates the full agent graph
Tool:   LangGraph stateful graph
```

---

### 🟠 ADA LOVELACE — The Interpreter Agent
*Ada Lovelace wrote the first algorithm — the first time anyone converted a human idea into structured instructions a machine could follow. This agent does the same: it takes a CV, a deeply human document, and converts it into structured data a system can reason over.*

The Interpreter Agent reads the raw PDF, extracts a structured candidate profile — skills, years of experience per domain, education level and field, spoken languages — and validates it into a Pydantic schema. CVs are messy, multilingual, and inconsistent. Ada Lovelace handles all of it.

```
Input:  Raw CV text (PDF → string)
Output: Structured CandidateProfile (Pydantic)
Tool:   LLM + Pydantic validation
```

---

🔵 MARIE CURIE — The Qualifier Agent

Marie Curie's work was built on absolute scientific rigor. Either the element was radioactive or it wasn't — no approximations, no negotiation. The first person to win two Nobel Prizes in two different sciences didn't deal in grey areas.

The Qualifier enforces must-have constraints deterministically across four rules:

1. Years of experience — candidate must meet or exceed the vacancy minimum
2. Education level — checked against a hierarchy (No degree → Bachelor's → Master's → PhD)
3. Required languages — each language checked by name and minimum CEFR level
4. Exact skill overlap — a soft bonus for direct name matches, before Alan Turing runs semantic comparison

It runs as pure code — fast, auditable, and immune to LLM hallucination. If a vacancy requires B2 English and the candidate has A1, the answer is no. Not "probably not." No.

> **Why languages go here, not in embeddings:** A semantic model might place "Catalan" near "Spanish" and grant a partial match. But language requirements are operational constraints, not fuzzy preferences. The Qualifier enforces this — which is also the ethically correct call.

```
Input:  CandidateProfile + Vacancy requirements
Output: pass/fail flag + score (0..4) + failed_checks list + reasons list
        failed_checks tells Steve Jobs exactly which rules the candidate failed,
        enabling targeted coaching instead of generic gap analysis
Tool:   Deterministic rule engine (Python)
```

---

### 🟢 ALAN TURING — The Linguist Agent
*Alan Turing asked whether machines could understand meaning. This agent is the answer.*

The Linguist Agent performs semantic skills comparison: it converts every required skill from the vacancy into an embedding vector and compares them against the candidate's skill vectors stored in **ChromaDB**. To generate these vectors, we use **BGE** (a pre-trained open-source AI model from HuggingFace — think of it as the component that reads a piece of text and converts it into a list of numbers that represents its *meaning*. Skills that mean similar things end up as similar numbers). Cosine similarity produces three categories:

| Category | Threshold | Meaning |
|----------|-----------|---------|
| ✅ MATCH | > 0.85 | Semantically equivalent ("PySpark" ≈ "distributed data processing") |
| ⚠️ GREY ZONE | 0.60 – 0.85 | Possibly related — needs reasoning |
| ❌ NO MATCH | < 0.60 | Not covered |

> **On thresholds:** The values 0.85 and 0.60 are heuristic starting points, informed by common practice in semantic similarity tasks. We adjust them based on three signals: (1) **false positives** — if clearly unrelated skills are landing in MATCH, we raise the upper threshold; (2) **false negatives** — if obviously equivalent skills like "Python" vs "Python 3" are falling into GREY ZONE instead of MATCH, we lower it; (3) **grey zone volume** — if too many skills end up in GREY ZONE, The Detective Agent becomes a bottleneck and slows the system down, so we tune the boundaries until the grey zone catches only genuinely ambiguous cases. The goal is a grey zone that is small, meaningful, and worth the cost of calling an LLM.

```
Input:  Candidate skills + Vacancy skill requirements
Output: Per-skill classification (MATCH / GREY ZONE / NO MATCH)
Tool:   BGE (meaning-vector model) + ChromaDB nearest-neighbor search
```

---

### 🟡 HEDY LAMARR — The Detective Agent
*Hedy Lamarr invented frequency-hopping spread spectrum — the ability to detect a clear signal by intelligently navigating through noise and ambiguity. The basis of WiFi, Bluetooth, and GPS. This agent does the same: it finds the real signal in skills that are too noisy for a simple match.*

The Detective Agent handles ambiguity reasoning — it only activates when Alan Turing flags GREY ZONE skills. It reads the actual CV context — project descriptions, job history, tool mentions — and judges whether the candidate likely has the skill implicitly. It always cites the specific evidence it used. No silent decisions.

```
Input:  Grey-zone skills + full CV context
Output: MATCH / NO MATCH verdict per skill + quoted evidence
Tool:   LLM with chain-of-thought
Activation: Conditional — only when grey zones exist
```

---

### 🔴 SERENA WILLIAMS — The Podium Agent
*Serena Williams dominated the WTA ranking for over 20 years. Her legacy is not just the trophies — it is the points, accumulated consistently, relentlessly, across every surface and every era. This agent does the same: it aggregates every signal into a final score and ranks without hesitation.*

The Podium Agent handles scoring and ranking: it aggregates the outputs from Marie Curie, Alan Turing, and Lamarr into a single weighted compatibility score per vacancy. Weights are calibrated per skill category (must-have vs. nice-to-have) and role seniority. The result is a ranked list of vacancies, each with a transparent, decomposed score.

**Handling the no-match case.** The Podium Agent never returns an empty result. Even when scores are universally low — meaning the candidate does not match any vacancy well — the ranking is still produced and surfaced. A low score is not a dead end; it is the most honest and useful input The Visionary Agent could ever receive. The worse the match, the richer the coaching output. A candidate with zero strong matches does not see a blank screen — they see a precise, personalised roadmap of exactly what to build to become competitive. The system turns its own worst-case scenario into its most valuable output.

```
Input:  Qualification results + skill match results (all agents)
Output: Compatibility score (0–100) per vacancy, ranked — always, regardless of score
Tool:   Weighted scoring formula (Python)
```

---

### 🟤 STEVE JOBS — The Visionary Agent
*Steve Jobs never accepted "good enough." He identified gaps, cut the noise, and told people exactly what they needed to build — and why it mattered. This agent does the same for your career.*

The Visionary Agent acts as career coach: it receives the gap analysis (skills missing or weak across top-ranked vacancies) and generates personalized, prioritized recommendations. It accounts for what the candidate already knows and suggests the highest-leverage next steps — not a generic list of skills, but a reasoned development path.

When scores are high, Steve Jobs fine-tunes — *"one more skill and you jump from rank 3 to rank 1"*. When scores are universally low, Steve Jobs takes over completely: it reframes the entire output from a ranking into a development plan, telling the candidate not just what they are missing but in which order to tackle it and why — prioritised by impact on employability across all vacancies simultaneously.

> **Strong match example:** *"You have the ML foundations for Data Scientist roles. Adding MLflow (you already use Docker — it's a 2-day ramp) would make you competitive for 3 more vacancies in this list."*

> **No match example:** *"None of the current vacancies are a strong fit yet — but you are closer than you think. Your Python base covers 60% of what Data Analyst Junior requires. Focus on SQL and Power BI first: those two skills unlock 5 of the 8 vacancies in the dataset. You could be competitive within 3 months."*

```
Input:  CandidateProfile + top vacancies + gap analysis
Output: Ranked skill recommendations with impact justification
Tool:   LLM with structured output
```

---

### 🏆 JOHANNES GUTENBERG — The Publisher Agent
*Johannes Gutenberg invented the printing press — the original act of making information displayable and accessible to the masses. Johannes Gutenberg turns the pipeline's output into something a human can actually read and act on.*

The Publisher Agent handles results and display: it persists all results to **SQLite** — including the analysis results, the vacancy descriptions, and the submitted CV profile — structures the output for the interface, and drives what the candidate actually sees: the ranked list, the per-skill breakdown, and the Steve Jobs coaching output — all rendered in a clean **Gradio** interface.

> **Why Gradio over Streamlit?** Gradio is HuggingFace-native, has first-class support for file uploads, chat-style output, and model demo UX. Since we're using BGE (our open-source embedding model) from HuggingFace and the Coach output is conversational, Gradio's component set fits this use case more naturally than Streamlit's data-dashboard paradigm.

```
Input:  Final ranked results + coaching output
Output: Rendered Gradio interface for the candidate
Tool:   SQLite + Gradio
```

---

## Full System Architecture

```
                        ┌─────────────────────┐
                        │   Gradio Interface  │
                        │  (candidate uploads │
                        │     CV as PDF)      │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟣 JOHN VON NEUMANN   │
                        │     Orchestrator    │
                        │    (LangGraph)      │
                        └──────────┬──────────┘
               ┌───────────────────┼───────────────────┐
               │                   │                   │
    ┌──────────▼──────────┐        │        ┌──────────▼──────────┐
    │  🟠 ADA LOVELACE     │        │        │   🔵 MARIE CURIE      │
    │ The Interpreter Agt │        │        │  The Qualifier Agt  │
    │  LLM + Pydantic     │        │        │   Rule Engine       │
    └──────────┬──────────┘        │        └──────────┬──────────┘
               │                   │                   │
               └───────────────────▼───────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟢 ALAN TURING        │
                        │  The Linguist Agent │
                        │ BGE vectors+ChromaDB│
                        └──────────┬──────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Grey zones found?           │
                    │  YES ──► 🟡 HEDY LAMARR    │
                    │        The Detective Agent    │
                    │          LLM + Evidence      │
                    │  NO  ──► skip               │
                    └──────────────┬──────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  🔴 SERENA WILLIAMS  │
                        │   The Podium Agent  │
                        │  Weighted Ranking   │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    🟤 STEVE JOBS          │
                        │ The Visionary Agent │
                        │  LLM + Gap Analysis │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   🏆 JOHANNES GUTENBERG     │
                        │ The Publisher Agent │
                        │  SQLite + Gradio    │
                        └─────────────────────┘
```

### Agent legend

| Symbol | Agent | Type |
|--------|-------|---------|
| 🟣 | John von Neumann | Orchestrator — LangGraph |
| 🟠 | Ada Lovelace | LLM Agent — Interpreter |
| 🔵 | Marie Curie | Deterministic — Rule engine |
| 🟢 | Alan Turing | Data Agent — BGE + ChromaDB |
| 🟡 | Hedy Lamarr | LLM Agent — Chain-of-thought |
| 🔴 | Serena Williams | Deterministic — Scoring formula |
| 🟤 | Steve Jobs | LLM Agent — Gap analysis |
| 🏆 | Johannes Gutenberg | Deterministic — SQLite + Gradio |

---

## Tech Stack

| Component | Tool | Reason |
|-----------|------|--------|
| Orchestration | LangGraph | Stateful, conditional agent graph — not a fixed pipeline |
| LLM | Llama 3 (Ollama) | Open source, local, zero API cost |
| Embedding model | **BGE** (BAAI/bge-base-en-v1.5) | Open-source AI model that converts text into meaning-vectors. Pre-trained by HuggingFace — we use it off the shelf, no training required. Top-ranked for semantic search tasks. |
| Vector DB | ChromaDB | Nearest-neighbor search native, file-local, zero server |
| Relational DB | SQLite | Stores analysis results, scores, vacancy descriptions, and submitted CV profiles |
| Data validation | Pydantic | Structured, typed output from LLM agents |
| Frontend | Gradio | HuggingFace-native, chat + file upload UX, ideal for AI demos |

---

## Data

- **Job offers:** 8 positions across the AI/Data stack — from Data Analyst Junior to AI Researcher and MLOps Engineer
- **CVs:** 10 synthetic candidate profiles, covering a range of seniority levels, skill combinations, and backgrounds

---

## How to Run

```bash
# 1. Clone and install
git clone https://github.com/sonixse/Challenge3-SmartCV
cd Challenge3-SmartCV
pip install -r requirements.txt

# 2. Start Ollama with Llama 3
ollama run llama3

# 3. Index the job vacancies into ChromaDB (run once)
python scripts/index_vacancies.py

# 4. Launch the interface
python app.py
```

Upload a CV (PDF). In seconds:
- Top-ranked job matches with compatibility scores
- Per-skill breakdown: MATCH / GREY ZONE (with Lamarr's reasoning) / NO MATCH
- Jobs' personalized gap analysis and development roadmap

---

## Why This Is a Genuine Multi-Agent System

The constraint was clear: no pre-built agents. Here is how we comply — and go further:

- **7 agents, 7 roles** — every agent has a single, defined responsibility with typed inputs and outputs
- **Conditional activation** — Lamarr only runs when Turing finds ambiguity. Johannes Gutenberg only renders once Serena Williams has a final score. The system is not a fixed pipeline; it adapts.
- **Deliberate LLM vs. code separation** — Marie Curie and Serena Williams run as pure code because their tasks are deterministic. Ada Lovelace, Lamarr, and Steve Jobs use LLMs because their tasks require language understanding. This is an architectural decision, not a default.
- **The orchestrator has state** — Von Neumann tracks what has run, what is pending, and what the current candidate profile looks like at each step.

---

## The 5 Evaluation Dimensions

**1. Innovation & Originality**
Semantic embeddings + a conditional reasoning layer (Lamarr) + a personalized career coaching agent (Steve Jobs). Most CV tools do keyword matching. We do semantic understanding with explainability and a development roadmap. The agent naming is not decoration — it's a communication strategy that makes the architecture instantly memorable.

**2. Feasibility & Scalability**
Every component is production-realistic. ChromaDB scales to millions of vectors. BGE (our embedding model) is fast enough for real-time queries. SQLite swaps to PostgreSQL with one config change. The Gradio interface becomes a REST API endpoint. The LangGraph orchestrator pattern works at any scale.

**3. Clarity & Conciseness**
One agent, one job. The architecture is legible: you can point at any node and explain what it does, why it's there, and why it uses the tool it uses. The conditional branching is a single decision point (grey zones exist?).

**4. Collaboration & Engagement**
Jobs makes the system valuable to *candidates*, not just recruiters. This turns a B2B screening tool into something with direct user value — a career advisor that gives you a ranked to-do list for your next role.

**5. Ethical Considerations**
- No protected attributes (age, gender, nationality) enter the scoring
- Marie Curie's rules are transparent and auditable — no silent LLM disqualifications
- Lamarr always cites its evidence — no black-box decisions in grey zones
- Language requirements are operational constraints, not cultural signals (handled by Marie Curie, not Alan Turing)
- All models run locally — no candidate data leaves the system

---

## What We'd Build With More Time

- **Two-stage retrieval:** use a lighter version of BGE for fast top-50 candidate retrieval, then the full model for final reranking. This is how production semantic search systems work — we prototyped it in theory and would implement it in a production version.
- **Feedback loop:** Collect recruiter accept/reject decisions and adjust Serena Williams's weights over time. Light online learning with zero retraining.
- **Explainability dashboard:** Johannes Gutenberg extended with a visual breakdown of each score component — useful for HR audits and regulatory compliance.
- **Multi-language CV support:** BGE (our embedding model) handles multilingual text; Ada Lovelace would be extended to parse CVs natively in Spanish, Catalan, and English without preprocessing.
- **REST API layer:** Expose the full agent graph as an API so it can plug into existing ATS systems. John von Neumann becomes a service, not a script.
- **Synthetic CV generation at scale:** Programmatic generation of edge-case CVs to stress-test Lamarr and calibrate Alan Turing's thresholds.

---

## Download external resume data

* https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
* Place files in `data/kaggle/` once out of `data/`

## The Team

Five people, two tracks, one system.

**Backend · Agents · Orchestration · Pipeline**
An industrial engineer, a computer engineer, and an AI engineer — the people who built the agents and made them talk to each other.

**Frontend · Presentation · Documentation · Impact**
A biomedicine specialist and a business & technology expert — the people who made the system legible, defensible, and worth presenting.

The agent names are a small tribute to that structure: each one carries the spirit of a discipline that someone on this team lives in.

---

> *"We did not use a prebuilt agent. We designed a custom multi-agent architecture where each of the seven agents has a specific, justified role — from CV parsing to semantic matching, hard filtering, ambiguity reasoning, scoring, coaching, and display — coordinated by an orchestrator that adapts the flow based on what it finds at every step."*
