# RUNBOOK — From Zero to Deployed

A single linear walkthrough. Follow it top to bottom the first time; after
that, jump to whichever section you need.

No Docker anywhere in this project — backend and frontend both run as
native Python processes, locally and on Render.

```
Part 1 — Prerequisites
Part 2 — Run it locally
Part 3 — Verify it actually works (the checks I ran myself)
Part 4 — Run the test suite
Part 5 — Deploy to production (Render)
Part 6 — Post-deploy verification
Part 7 — Common failure modes
```

---

## Part 1 — Prerequisites

You need:

1. **Python 3.11+** and a local **PostgreSQL 15+** with the `pgvector`
   extension available.
2. **A free Groq API key** — sign up at [console.groq.com](https://console.groq.com),
   create a key. Phase 2 uses `llama-3.3-70b-versatile`.
3. **A GitHub account** — only needed for Part 5 (deployment).
4. A sample PDF contract to test with (any real or dummy NDA/vendor agreement works).

Nothing else. No paid embeddings API — embeddings run locally via
`sentence-transformers`.

---

## Part 2 — Run it locally

**2.1 — Database**
```bash
psql -U your_user -d your_db -f database/schema.sql
```

**2.2 — Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # set DATABASE_URL and GROQ_API_KEY
python -m scripts.seed_citations   # optional but recommended
uvicorn app.main:app --reload
```

Backend is now live at http://localhost:8000/docs.

**2.3 — Frontend** (separate terminal)
```bash
cd frontend
pip install -r requirements.txt
export BACKEND_API_URL=http://localhost:8000   # Windows: set BACKEND_API_URL=http://localhost:8000
streamlit run streamlit_app.py
```

Frontend is now live at http://localhost:8501.

---

## Part 3 — Verify it actually works

Don't trust that "it's running" means "it works." Do these four checks in order:

**3.1 — Health check**
```bash
curl http://localhost:8000/health
# expect: {"status":"healthy"}
```

**3.2 — Upload a real PDF**
Go to the frontend, Contract Upload, upload a real PDF. Confirm you get
a page count and a nonzero chunk count back, not an error.

**3.3 — Run one full analysis**
Go to Contract Analysis, select the uploaded document, ask something
concrete like "Review this contract for termination and liability risks",
click Open Investigation.

Check the result actually makes sense:
- Does the Document Intelligence tab show clauses that are genuinely in your PDF (not hallucinated)?
- Does the compliance score look reasonable given what's missing?
- Do the red flags cite evidence that's actually in the document?

This is the step most people skip, and it's the one that actually tells you
whether the LLM prompts are working as designed — everything up to here can
"work" while silently returning garbage.

**3.4 — Check the API docs render**
Open http://localhost:8000/docs and confirm all 10 endpoints are listed with
schemas (upload, analyze, ask, report, compare-contracts, compliance-check,
risk-analysis, and the three GET report-lookup endpoints).

If 3.2 or 3.3 fail, see Part 7 before going further.

---

## Part 4 — Run the test suite

The 32 backend tests need no live database or Groq key — every LLM call is
mocked:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Expected: `32 passed`. If something fails here, fix it before deploying —
these tests exercise the deterministic scoring and defensive parsing that
the whole "no hallucinated compliance findings" claim rests on.

This only proves the logic is sound, not that the live LLM cooperates —
that's what Part 3.3 is for.

---

## Part 5 — Deploy to production (Render)

**5.1 — Push to GitHub**
```bash
git init && git add . && git commit -m "Legal Intelligence Platform"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

**5.2 — Create the database**
Render dashboard, New, PostgreSQL, name it, pick a region.
Copy both the Internal Database URL and External Database URL from
its Connect tab.

Apply the schema from your machine, using the external URL:
```bash
psql "<EXTERNAL_DATABASE_URL>" -f database/schema.sql
```

**5.3 — Deploy the backend (native Python, no Docker)**
Render dashboard, New, Web Service, connect your repo.
- Root directory: `backend`
- Environment: `Python 3` (Render reads `backend/runtime.txt`, pinned to `python-3.11.9`)
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Instance: at least `Starter` (the embedding model needs ~500MB+ RAM)

Environment variables:
```
DATABASE_URL   = <Internal Database URL from 5.2>
GROQ_API_KEY   = <your key>
GROQ_MODEL     = llama-3.3-70b-versatile
APP_ENV        = production
CORS_ORIGINS   = (leave blank for now, set after 5.4)
```

Deploy. Verify: `curl https://<your-backend>.onrender.com/health`

Note: the app object lives at `app/main.py` inside `backend/`, so the
module path is `app.main:app`, not a bare `main:app`. With Root Directory
set to `backend`, the start command runs from inside that folder and
resolves correctly.

**5.4 — Deploy the frontend**
Render dashboard, New, Web Service, same repo.
- Root directory: `frontend`
- Environment: `Python 3` (reads `frontend/runtime.txt`)
- Build command: `pip install -r requirements.txt`
- Start command:
  ```
  streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
  ```
- Env var: `BACKEND_API_URL = https://<your-backend>.onrender.com`

Deploy. Then go back to the backend service, set
`CORS_ORIGINS = https://<your-frontend>.onrender.com`, and redeploy the
backend — otherwise the browser will block requests from the frontend.

**5.5 — Seed the reference corpus**
Backend service, Shell tab (in Render dashboard):
```bash
python -m scripts.seed_citations
```

---

## Part 6 — Post-deploy verification

Repeat Part 3 against the live URLs instead of localhost. Specifically:

```bash
curl https://<your-backend>.onrender.com/health

curl -X POST https://<your-backend>.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What does a force majeure clause typically cover?"}'
```

Then open the live frontend URL and repeat the full upload-to-analyze flow
from 3.2/3.3 against production, not just locally. A build that works
locally but not on Render (usually a memory limit or a missing env var) is
a very common failure mode — don't skip this.

---

## Part 7 — Common failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Backend fails to start | Missing/invalid `GROQ_API_KEY` or bad `DATABASE_URL` | Check `.env` locally, check Render's build/deploy logs |
| `ModuleNotFoundError: No module named 'app'` on Render | Root Directory not set to `backend`, or start command uses bare `main:app` | Root Directory must be `backend`; start command must be `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| `/upload-document` returns 422 | PDF has no extractable text (scanned image, no OCR) | pdfplumber/PyPDF2 need a text layer — Phase 1/2 don't do OCR |
| Analysis returns empty `document_intelligence` | Document text wasn't passed, or LLM call failed silently | Check backend logs for `chat_completion_json` errors; check Groq key quota |
| Compliance score always 0 | `document_intelligence` extraction failed upstream | Check the raw LLM response in logs — likely a JSON-mode parsing failure |
| Frontend can't reach backend | `BACKEND_API_URL` wrong or CORS blocking it | Confirm env var, confirm `CORS_ORIGINS` on backend matches frontend URL exactly |
| Render backend OOM / crashes on first request | Instance too small for `sentence-transformers` | Bump to a larger instance tier |
| First request after idle takes 30-60s | Render free/starter tier cold start + model load | Expected — consider a warm-up ping, or a paid always-on tier |
| pgvector queries error on fresh DB | `citations`/`document_chunks` tables have no rows yet, or extension not enabled | Confirm `CREATE EXTENSION vector;` ran (it's in `schema.sql`), run `seed_citations.py` |

---

## Quick reference — the four things that actually matter

1. `GROQ_API_KEY` must be real before anything downstream works.
2. Run Part 3.3 for real — a green build tells you nothing about output quality.
3. `pytest` passing proves logic, not live LLM behavior — don't conflate the two.
4. CORS must be set after the frontend has a URL, not before — this trips up nearly everyone on first deploy.
