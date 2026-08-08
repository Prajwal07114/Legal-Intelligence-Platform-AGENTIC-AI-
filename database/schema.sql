-- =========================================================
-- Legal Intelligence Platform — PostgreSQL/pgvector schema
-- Combined Phase 1 + Phase 2 (fresh-install convenience file)
--
-- For version history / incremental upgrades of an existing Phase 1
-- database, use the numbered files in database/migrations/ instead:
--   001_phase1_init.sql
--   002_phase2_tables.sql
-- Both this file and the migrations are idempotent (IF NOT EXISTS).
-- =========================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------
-- user_sessions: lightweight anonymous session tracking
-- (Phase 1 has no auth; sessions just group uploads/reports)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_active_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata_json   JSONB DEFAULT '{}'::jsonb
);

-- ---------------------------------------------------------
-- legal_documents: uploaded contracts (PDF)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS legal_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    filename        VARCHAR(512) NOT NULL,
    file_type       VARCHAR(50) DEFAULT 'pdf',
    page_count      INTEGER DEFAULT 0,
    raw_text        TEXT,
    status          VARCHAR(50) DEFAULT 'uploaded',  -- uploaded | processing | processed | failed
    uploaded_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_legal_documents_session ON legal_documents(session_id);

-- ---------------------------------------------------------
-- document_chunks: RAG chunks for uploaded documents
-- Embedding dimension (384) matches all-MiniLM-L6-v2.
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES legal_documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    page_number     INTEGER,
    embedding       VECTOR(384)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);

-- IVFFlat index for approximate nearest-neighbor cosine search.
-- Requires ANALYZE after bulk inserts for good query planning.
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ---------------------------------------------------------
-- citations: curated reference corpus (statutes, regulations,
-- standard clause library) the Research Agent retrieves against
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS citations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name     VARCHAR(512) NOT NULL,
    source_type     VARCHAR(100) DEFAULT 'statute',  -- statute | regulation | clause_reference | case_law
    content         TEXT NOT NULL,
    url             VARCHAR(1024),
    embedding       VECTOR(384),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_citations_embedding
    ON citations USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ---------------------------------------------------------
-- reports: final generated Legal Intelligence Reports
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    document_id     UUID REFERENCES legal_documents(id) ON DELETE SET NULL,
    user_query      TEXT NOT NULL,
    task_type       VARCHAR(100),
    report_markdown TEXT NOT NULL,
    report_json     JSONB,
    risk_level      VARCHAR(50),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reports_session ON reports(session_id);
CREATE INDEX IF NOT EXISTS idx_reports_document ON reports(document_id);
    ADD COLUMN IF NOT EXISTS workflow_mode VARCHAR(20) DEFAULT 'single';

-- ---------------------------------------------------------
-- compliance_results: output of the Compliance Agent (Agent 7)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS compliance_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id           UUID REFERENCES reports(id) ON DELETE SET NULL,
    document_id         UUID REFERENCES legal_documents(id) ON DELETE SET NULL,
    session_id          UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    compliance_score    INTEGER NOT NULL DEFAULT 0 CHECK (compliance_score BETWEEN 0 AND 100),
    missing_clauses     JSONB DEFAULT '[]'::jsonb,
    compliance_issues   JSONB DEFAULT '[]'::jsonb,  -- each issue includes its evidence[] array
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_compliance_results_document ON compliance_results(document_id);
CREATE INDEX IF NOT EXISTS idx_compliance_results_report ON compliance_results(report_id);

-- ---------------------------------------------------------
-- risk_flags: output of the Red Flag Detection Agent (Agent 8)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_flags (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id           UUID REFERENCES reports(id) ON DELETE SET NULL,
    document_id         UUID REFERENCES legal_documents(id) ON DELETE SET NULL,
    session_id          UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    flags               JSONB NOT NULL DEFAULT '[]'::jsonb,  -- list of {flag_type, severity, explanation, evidence[]}
    severity            VARCHAR(50) DEFAULT 'Low',            -- highest severity across `flags`
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_flags_document ON risk_flags(document_id);
CREATE INDEX IF NOT EXISTS idx_risk_flags_report ON risk_flags(report_id);

-- ---------------------------------------------------------
-- comparison_results: output of the Contract Comparison Agent (Agent 9)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS comparison_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id           UUID REFERENCES reports(id) ON DELETE SET NULL,
    document_id_a       UUID REFERENCES legal_documents(id) ON DELETE SET NULL,
    document_id_b       UUID REFERENCES legal_documents(id) ON DELETE SET NULL,
    session_id          UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    added_clauses       JSONB DEFAULT '[]'::jsonb,
    removed_clauses     JSONB DEFAULT '[]'::jsonb,
    modified_clauses    JSONB DEFAULT '[]'::jsonb,
    summary             TEXT,
    created_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comparison_results_doc_a ON comparison_results(document_id_a);
CREATE INDEX IF NOT EXISTS idx_comparison_results_doc_b ON comparison_results(document_id_b);
CREATE INDEX IF NOT EXISTS idx_comparison_results_report ON comparison_results(report_id);

