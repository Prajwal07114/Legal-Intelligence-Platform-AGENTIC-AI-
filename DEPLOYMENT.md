# Deployment Guide — Render

This guide deploys the Legal Intelligence Platform using
[Render](https://render.com): a managed PostgreSQL instance (with pgvector),
the FastAPI backend as a native-Python Web Service, and the Streamlit
frontend as a second native-Python Web Service. No Docker is used anywhere
in this deployment.

---

## 1. Push the project to GitHub

Render deploys from a Git repository.

```bash
git init
git add .
git commit -m "Legal Intelligence Platform - Phase 1"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

---

## 2. Create the PostgreSQL database

1. In the Render dashboard: **New → PostgreSQL**.
2. Name it e.g. `legal-intel-db`, choose a region close to your backend service.
3. After creation, open the database's **Connect** tab and copy the
   **Internal Database URL** (used by the backend service) and the
   **External Database URL** (used to run the schema migration from your
   local machine).
4. Render's managed Postgres supports the `pgvector` extension — enable it by
   connecting with `psql` (external URL) and running:

```bash
# Fresh install — everything in one file (Phase 1 + Phase 2):
psql "<EXTERNAL_DATABASE_URL>" -f database/schema.sql
```

   This creates the `vector` extension and all eight tables/indexes in one
   step.

   **Upgrading an existing Phase 1 deployment?** Run only the new migration
   instead, to add Phase 2 tables without touching existing data:

```bash
psql "<EXTERNAL_DATABASE_URL>" -f database/migrations/002_phase2_tables.sql
```

5. (Optional but recommended) Seed the reference corpus once the backend is
   deployed — see step 5 below.

---

## 3. Deploy the backend (FastAPI, native Python runtime)

1. In Render: **New → Web Service** → connect your GitHub repo.
2. Configure:
   - **Root Directory:** `backend`
   - **Environment:** `Python 3` (Render reads `backend/runtime.txt` to pin the exact version — `python-3.11.9`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** at least `Starter` (embeddings model needs ~500MB+ RAM)
3. Add environment variables (Render dashboard → Environment):

   | Key                | Value                                                     |
   |--------------------|------------------------------------------------------------|
   | `DATABASE_URL`      | the **Internal Database URL** from step 2                  |
   | `GROQ_API_KEY`      | your Groq API key                                           |
   | `GROQ_MODEL`        | `llama-3.3-70b-versatile`                                   |
   | `APP_ENV`           | `production`                                                 |
   | `CORS_ORIGINS`      | the frontend's Render URL (set after step 4, then redeploy) |

4. Deploy. Render will install dependencies with pip and run the start
   command directly (no image build step) — the service will be available at
   `https://<your-backend>.onrender.com`. Verify with:

```bash
curl https://<your-backend>.onrender.com/health
```

> **Note on the start command:** the FastAPI app object lives at
> `app/main.py` inside `backend/` (i.e. the importable path is `app.main:app`,
> not a bare `main:app`). With **Root Directory** set to `backend`, Render
> runs the start command from inside that directory, so `app.main:app`
> resolves correctly.

---

## 4. Deploy the frontend (Streamlit)

1. In Render: **New → Web Service** → same repo.
2. Configure:
   - **Root Directory:** `frontend`
   - **Environment:** `Python 3` (Render reads `frontend/runtime.txt` — `python-3.11.9`)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:**
     ```
     streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
     ```
3. Add environment variable:

   | Key                | Value                                          |
   |--------------------|--------------------------------------------------|
   | `BACKEND_API_URL`   | `https://<your-backend>.onrender.com`             |

4. Deploy. The frontend will be live at `https://<your-frontend>.onrender.com`.
5. Go back to the **backend** service's `CORS_ORIGINS` env var, set it to
   `https://<your-frontend>.onrender.com`, and redeploy the backend so
   browser requests from the frontend aren't blocked by CORS.

---

## 5. Seed the reference corpus (one-time)

Render's Shell tab (on the backend service) lets you run one-off commands
against the live environment:

```bash
python -m scripts.seed_citations
```

This populates the `citations` table with sample statutes/regulations/clause
references so the Research Agent has something to retrieve on a fresh
database.

---

## 6. Smoke test

```bash
# Health check
curl https://<your-backend>.onrender.com/health

# Document-free legal research query
curl -X POST https://<your-backend>.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What does a force majeure clause typically cover?"}'
```

Then open the frontend URL in a browser, upload a sample contract PDF, and
run a query end-to-end.

### Phase 2 endpoint checks

After uploading a document via `/upload-document` and noting its
`document_id`:

```bash
# Standalone compliance check
curl -X POST https://<your-backend>.onrender.com/compliance-check \
  -H "Content-Type: application/json" \
  -d '{"document_id": "<DOCUMENT_ID>"}'

# Standalone risk/red-flag analysis
curl -X POST https://<your-backend>.onrender.com/risk-analysis \
  -H "Content-Type: application/json" \
  -d '{"document_id": "<DOCUMENT_ID>"}'

# Contract comparison (requires two uploaded document_ids)
curl -X POST https://<your-backend>.onrender.com/compare-contracts \
  -H "Content-Type: application/json" \
  -d '{"query": "Compare these two vendor agreements", "document_id_a": "<ID_A>", "document_id_b": "<ID_B>"}'
```

---

## Notes & gotchas

- **Cold starts:** Render's free/starter tiers spin down idle services;
  the first request after idling can take 30-60s (plus embedding model
  load time on backend cold start).
- **Embedding model download:** `sentence-transformers` downloads the
  `all-MiniLM-L6-v2` model (~90MB) on first use. This happens at request
  time on a cold instance — consider pre-warming with a `/health`-triggered
  ping, or add a download step to the build command
  (`pip install -r requirements.txt && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`)
  so the model is cached before the service starts serving traffic.
- **Groq rate limits:** free-tier Groq API keys are rate-limited; the
  `llm_client.py` wrapper retries with exponential backoff (3 attempts) to
  smooth over transient 429s.
- **pgvector index tuning:** the `ivfflat` indexes use `lists = 100`, tuned
  for small-to-medium corpora. Run `ANALYZE document_chunks;` and
  `ANALYZE citations;` after large bulk inserts for better query planning.
