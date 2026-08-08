# ⚖️ Legal Intelligence Platform — Phase 2

An **enterprise-grade Multi-Agent Legal Intelligence Platform**: a 9-agent
**LangGraph** pipeline with conditional routing that ingests contracts,
performs RAG-grounded legal research, extracts deep structured intelligence,
runs deterministic compliance checks, detects named legal red flags, compares
contract versions, and generates an evidence-backed, structured legal
analysis report.

Built as a portfolio-grade GenAI/AI engineering project. Phase 2 builds
directly on top of Phase 1 — nothing from Phase 1 was removed; the original
5-agent pipeline, endpoints, and database tables are all still present and
functional (see "Phase 1 → Phase 2" below).

---

## ✨ What it does

- Accepts legal questions (with or without an attached document)
- Accepts contract PDFs — single documents or two-way comparisons
- Performs legal research using **RAG** over a vector database (pgvector)
- **Extracts deep document intelligence**: parties, effective/expiration
  dates, obligations, payment terms, confidentiality/liability/indemnity/
  termination clauses, governing law, jurisdiction, deadlines, penalties —
  every finding backed by evidence
- **Runs a deterministic compliance check** (0-100 score, computed in pure
  Python — never hallucinated) against a mandatory-clause checklist
- **Detects named legal red flags** (unlimited liability, one-sided
  termination, excessive penalties, ambiguous obligations, missing
  protections, broad indemnification, weak confidentiality) with an
  explanation and evidence for every flag
- **Compares two contracts** (V1 vs V2, Vendor A vs Vendor B) and reports
  added / removed / modified clauses
- Aggregates every risk signal into one overall risk level (Low / Moderate /
  High / Critical) — deterministically, not via LLM guesswork
- Generates a structured **Legal Intelligence Report**, not a chat reply —
  with a full evidence & citations trail

---

## 🏗️ Architecture

### Single-contract pipeline (`workflow_mode="single"`, the default)

```
User Query / PDF Upload
        │
        ▼
┌─────────────────────────┐
│ 1. Legal Intake Agent    │  classifies task_type + topics
└────────────┬─────────────┘
             ▼
┌─────────────────────────┐
│ 2. Legal Research Agent  │  RAG retrieval (pgvector)
└────────────┬─────────────┘
             ▼
┌─────────────────────────┐
│ 6. Legal Document         │  parties, dates, obligations, payment terms,
│    Intelligence Agent     │  confidentiality/liability/indemnity/
│                            │  termination clauses — with evidence
└────────────┬─────────────┘
             ▼
┌─────────────────────────┐
│ 7. Compliance Agent       │  deterministic 0-100 score,
│                            │  missing-clause detection
└────────────┬─────────────┘
             ▼
┌─────────────────────────┐
│ 8. Red Flag Detection     │  named risk patterns + explanations
│    Agent                  │  + evidence
└────────────┬─────────────┘
             ▼
┌─────────────────────────┐
│ 4. Legal Risk Assessment  │  aggregates every severity signal into
│    Agent                  │  one overall_risk_level (deterministic)
└────────────┬─────────────┘
             ▼
┌─────────────────────────┐
│ 5. Legal Report            │  deterministic Python template —
│    Generation Agent        │  no extra LLM call
└────────────┬─────────────┘
             ▼
   Final Legal Intelligence Report
```

### Comparison pipeline (`workflow_mode="comparison"`)

```
Contract A ─┐
            ├──▶ Legal Intake → Legal Research
Contract B ─┘                        │
                                      ▼
                        9. Contract Comparison Agent
                     (extracts + diffs A vs B; B's structured
                      intelligence feeds the rest of the pipeline)
                                      │
                                      ▼
                     Compliance → Red Flag → Risk → Report
                     (identical tail to the single-contract pipeline)
```

Implemented as a **LangGraph `StateGraph` with real conditional routing**
(`add_conditional_edges`), branching on `state["workflow_mode"]` right after
the Research Agent. Both branches converge back into a shared
Compliance → Red Flag → Risk → Report tail — see `backend/app/graph.py`.

### Phase 1 → Phase 2: what changed, what didn't

| | Phase 1 | Phase 2 |
|---|---|---|
| Agents | 5 (Intake, Research, Clause Analysis, Risk, Report) | 9 (adds Document Intelligence, Compliance, Red Flag Detection, Contract Comparison) |
| Graph | Linear `StateGraph` | `StateGraph` with conditional routing (single vs. comparison) |
| Clause extraction | Agent 3 (`clause_agent.py`) — **still in the codebase, still importable/testable, just not wired into the default graph** | Agent 6 (`document_intelligence_agent.py`) — richer, evidence-backed, also populates the Phase 1 `clauses`/`obligations`/`deadlines`/`penalties` fields for backward compatibility |
| Risk scoring | LLM-only | Agent 4 now deterministically aggregates the highest severity across its own LLM risks + Agent 8's red flags + Agent 7's compliance issues |
| Report sections | Document Summary, References, Clauses, Obligations, Deadlines, Risk Assessment, Recommendations, Disclaimer | Executive Summary, Contract Overview, Extracted Legal Intelligence, Compliance Assessment, Red Flag Analysis, Risk Assessment, Evidence & Citations, Contract Comparison (if applicable), Recommended Review Areas, Disclaimer — **all Phase 1 data still rendered**, just reorganized |
| Endpoints | `/upload-document`, `/analyze-document`, `/ask`, `/report/{id}` (unchanged, still work) | + `/compare-contracts`, `/compliance-check`, `/risk-analysis`, `/comparison-report/{id}`, `/compliance-report/{id}`, `/risk-report/{id}` |
| Database | 5 tables | + `compliance_results`, `risk_flags`, `comparison_results` (migration `002_phase2_tables.sql`) |
| Frontend pages | Document Upload, Legal Query, Report Viewer | Contract Upload, Contract Analysis, **Compliance Dashboard**, **Risk Dashboard**, **Contract Comparison**, Report Viewer |

This is still explicitly **NOT a legal advice system** — the Risk and Red
Flag agents surface observations with evidence, never instructions or
guarantees.

---

## 🕵️ Visual Identity — "Contract Intelligence Command Room"

The frontend is a fully custom dark investigation-room theme (`frontend/theme.py`),
not a default Streamlit/SaaS look:

- **Palette**: near-black panels (`#0A0E17` / `#141A26` / `#1C2433`), gold case-file
  accents (`#C6A15B` / `#9C7A3B`), and warm paper (`#F5F1E8`) reserved only for
  contract/report text — so documents read as physical exhibits inside a dark room.
- **Type**: IBM Plex Mono for case-file labels, evidence tags, and risk markers;
  Source Serif 4 for contract/report text; IBM Plex Sans for ordinary UI chrome.
- **Signature motif — the Evidence Tag**: a small dashed-border rectangle with a
  colored dot + uppercase monospace label, reused everywhere: risk markers
  (`● HIGH RISK`), clause-type flags, pipeline stage stamps, and compliance-matrix
  indicators.
- **Contract Comparison** renders as a GitHub-diff-style redline (Contract A left,
  Contract B right, added/removed/modified highlighted), not a comparison table.
- **Reports** render as a paper "dossier" (`render_dossier()` in `theme.py`, backed
  by the `markdown` package) with a case-file cover header, not raw markdown blocks.
- **Compliance Dashboard** uses a custom-colored Plotly gauge and an audit-sheet
  `<table>` (`li-matrix` CSS class) instead of generic KPI cards.

## 🧰 Tech Stack

| Layer            | Technology                                   |
|-------------------|-----------------------------------------------|
| Frontend          | Streamlit (+ Plotly for the compliance gauge) — custom "Legal Investigation Center" dark theme, see below |
| Backend           | FastAPI                                       |
| LLM               | Groq — Llama 3.3 (70B versatile)              |
| Agent Orchestration | LangGraph (`StateGraph` + conditional edges) |
| Database          | PostgreSQL                                    |
| Vector Search     | pgvector (cosine similarity)                  |
| Embeddings        | sentence-transformers (`all-MiniLM-L6-v2`, local, free) |
| PDF Processing    | pdfplumber (primary) + PyPDF2 (fallback)      |
| Testing           | pytest (32 unit/agent/workflow tests, no live DB/Groq required) |
| Deployment        | Render (backend + Postgres), Streamlit Community Cloud or Render (frontend) |

---

## 📁 Project Structure

```
legal-intelligence-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── config.py                 # Settings (pydantic-settings)
│   │   ├── database.py               # SQLAlchemy engine/session
│   │   ├── models.py                 # ORM models (Phase 1 + Phase 2 tables)
│   │   ├── schemas.py                # Pydantic request/response schemas
│   │   ├── graph.py                  # LangGraph workflow (conditional routing)
│   │   ├── agents/
│   │   │   ├── state.py              # Shared LangGraph state schema
│   │   │   ├── intake_agent.py       # Agent 1
│   │   │   ├── research_agent.py     # Agent 2
│   │   │   ├── clause_agent.py       # Agent 3 (Phase 1 — preserved, standalone)
│   │   │   ├── risk_agent.py         # Agent 4 (Phase 2: now a deterministic aggregator)
│   │   │   ├── report_agent.py       # Agent 5 (deterministic, upgraded sections)
│   │   │   ├── document_intelligence_agent.py  # Agent 6 (Phase 2)
│   │   │   ├── compliance_agent.py   # Agent 7 (Phase 2)
│   │   │   ├── red_flag_agent.py     # Agent 8 (Phase 2)
│   │   │   └── comparison_agent.py   # Agent 9 (Phase 2)
│   │   ├── rag/                      # PDF processing, chunking, embeddings, retrieval
│   │   ├── routes/
│   │   │   ├── upload.py             # POST /upload-document
│   │   │   ├── analyze.py            # POST /analyze-document
│   │   │   ├── ask.py                # POST /ask
│   │   │   ├── report.py             # GET /report/{id}, /comparison-report/{id}, ...
│   │   │   ├── compare.py            # POST /compare-contracts (Phase 2)
│   │   │   ├── compliance.py         # POST /compliance-check (Phase 2)
│   │   │   └── risk_analysis.py      # POST /risk-analysis (Phase 2)
│   │   └── utils/
│   │       ├── llm_client.py         # Groq client wrapper
│   │       ├── prompts.py            # All agent prompt templates
│   │       └── report_template.py    # Deterministic report renderer
│   ├── scripts/
│   │   └── seed_citations.py         # Seeds sample statutes/clause refs
│   ├── tests/                        # 32 tests — agent, workflow, scenario
│   │   ├── conftest.py
│   │   ├── test_document_intelligence_agent.py
│   │   ├── test_compliance_agent.py
│   │   ├── test_red_flag_agent.py
│   │   ├── test_risk_agent.py
│   │   ├── test_comparison_agent.py
│   │   ├── test_workflow_graph.py
│   │   └── test_report_template.py
│   ├── requirements.txt
│   ├── requirements-dev.txt          # + pytest
│   ├── pytest.ini
│   ├── runtime.txt                   # Render Python version pin
│   └── .env.example
├── database/
│   ├── schema.sql                    # Combined Phase 1 + Phase 2 (fresh installs)
│   └── migrations/
│       ├── 001_phase1_init.sql
│       └── 002_phase2_tables.sql     # compliance_results, risk_flags, comparison_results
├── frontend/
│   ├── streamlit_app.py              # Home page
│   ├── api_client.py                 # Shared HTTP client
│   ├── session_utils.py              # Multi-document session-state helpers (Phase 2)
│   ├── theme.py                      # Visual identity / design system
│   ├── pages/
│   │   ├── 1_Contract_Upload.py
│   │   ├── 2_Contract_Analysis.py
│   │   ├── 3_Compliance_Dashboard.py # Compliance score gauge + missing clauses
│   │   ├── 4_Risk_Dashboard.py       # Red flag cards with severity + evidence
│   │   ├── 5_Contract_Comparison.py  # Side-by-side clause diff
│   │   └── 6_Report_Viewer.py        # Full / compliance / risk / comparison reports
│   ├── requirements.txt
│   └── runtime.txt                   # Render Python version pin
├── DEPLOYMENT.md
├── RUNBOOK.md
└── README.md
```

---

## 🗄️ Database Schema

Eight tables total. Run `database/schema.sql` for a fresh install, or apply
the numbered files in `database/migrations/` in order against an existing
Phase 1 database:

**Phase 1** (`001_phase1_init.sql`):
- `user_sessions`, `legal_documents`, `document_chunks`, `citations`, `reports`

**Phase 2** (`002_phase2_tables.sql`):
- `compliance_results` — Agent 7 output: score, missing clauses, issues (with evidence)
- `risk_flags` — Agent 8 output: typed flags with severity + evidence
- `comparison_results` — Agent 9 output: added/removed/modified clauses
- `reports.workflow_mode` column added (`"single"` | `"comparison"`)

All JSONB columns store structured evidence (`{label, quote, source}`) so
every finding is traceable back to its source text.

---

## 🔌 API Endpoints

| Method | Path                    | Description                                             |
|--------|--------------------------|-----------------------------------------------------------|
| POST   | `/upload-document`        | Upload a PDF, extract/chunk/embed, store in pgvector       |
| POST   | `/analyze-document`        | Full pipeline against a query (+ optional document) — now returns Phase 2 fields too |
| POST   | `/ask`                     | Full pipeline for a document-free legal research query    |
| GET    | `/report/{id}`             | Fetch a previously generated full report                  |
| POST   | `/compare-contracts`       | **(Phase 2)** Run the comparison pipeline on two documents |
| POST   | `/compliance-check`        | **(Phase 2)** Standalone compliance check on one document  |
| POST   | `/risk-analysis`           | **(Phase 2)** Standalone red-flag + risk analysis          |
| GET    | `/comparison-report/{id}`  | **(Phase 2)** Fetch a stored comparison result             |
| GET    | `/compliance-report/{id}`  | **(Phase 2)** Fetch a stored compliance result             |
| GET    | `/risk-report/{id}`        | **(Phase 2)** Fetch a stored risk-flags result              |
| GET    | `/health`                  | Health check                                                |

Interactive API docs (OpenAPI) available at `http://localhost:8000/docs`.

`/analyze-document` and `/ask` responses gained new **optional** fields
(`document_intelligence`, `compliance_results`, `risk_flags`,
`red_flag_severity`, `comparison_results`, `evidence_references`) — this is
purely additive, so any Phase 1 client code still works unchanged.

---

## 🚀 Running locally

No Docker required — native Python only.

**1. PostgreSQL + pgvector**

```bash
# Fresh install:
psql -U your_user -d your_db -f database/schema.sql

# OR, upgrading an existing Phase 1 database:
psql -U your_user -d your_db -f database/migrations/002_phase2_tables.sql
```

**2. Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in DATABASE_URL and GROQ_API_KEY
python -m scripts.seed_citations   # optional but recommended
uvicorn app.main:app --reload
```

Backend is now live at http://localhost:8000 (docs at `/docs`).

> Note: the app entrypoint is `app.main:app` (i.e. `app/main.py` inside
> `backend/`), run from the `backend/` directory — not a bare `main.py`
> at the repo root.

**3. Frontend**

```bash
cd frontend
pip install -r requirements.txt
export BACKEND_API_URL=http://localhost:8000   # Windows: set BACKEND_API_URL=http://localhost:8000
streamlit run streamlit_app.py
```

Frontend is now live at http://localhost:8501.

### Running tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

The 32 tests run **without** a live PostgreSQL or Groq connection — every
LLM call is mocked, and heavy ML dependencies (`sentence-transformers`,
`pdfplumber`) are stubbed in `tests/conftest.py`. This keeps the suite fast
and CI-friendly while still exercising real agent logic: defensive parsing
of malformed LLM output, deterministic compliance scoring, severity
aggregation, and LangGraph conditional routing (including one end-to-end run
of the real compiled graph with every LLM call mocked).

---

## 🔑 Getting a Groq API key

Create a free key at [console.groq.com](https://console.groq.com), then set
`GROQ_API_KEY` in your `.env`. Uses `llama-3.3-70b-versatile`.

---

## 🧪 Example flows

**Single-contract analysis:**
1. Upload a contract PDF on **Contract Upload**.
2. Go to **Contract Analysis**, ask: *"Review this contract for termination
   and liability risks"*.
3. View the Document Intelligence, Compliance, Red Flag, and Risk tabs, plus
   the full evidence-backed report.

**Compliance / Risk dashboards:**
- **Compliance Dashboard** — select a document, run the check, see the score
  gauge and missing-clauses table.
- **Risk Dashboard** — select a document, see red flag cards sorted by
  severity with evidence.

**Contract comparison:**
1. Upload two contracts (e.g. Vendor A's terms and Vendor B's terms).
2. Go to **Contract Comparison**, select both, run the comparison.
3. View the added / removed / modified clause diff, plus compliance and risk
   computed against Contract B.

---

## ⚠️ Explicitly out of scope

Per the original Phase 1 spec, still not implemented (candidates for a
future phase):

- A supervisor/orchestrator agent with full dynamic multi-agent planning
  (Phase 2 conditional routing is rule-based on `workflow_mode`, not an
  LLM-driven supervisor)
- Session memory across requests / conversations
- Human-in-the-loop review steps
- Multi-jurisdiction support beyond whatever the extracted `governing_law`/
  `jurisdiction` fields surface

---

## ⚖️ Disclaimer

This system produces AI-generated analysis for informational and portfolio
purposes only. It is **not** a substitute for professional legal advice.
The Risk Assessment and Red Flag Detection agents are explicitly designed to
surface evidence-backed observations, not recommendations or legal
conclusions.
