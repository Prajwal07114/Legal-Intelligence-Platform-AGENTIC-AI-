-- =========================================================
-- Migration 001 — Phase 1 initial schema
-- (Mirrors database/schema.sql at the time Phase 1 shipped.
--  Kept here so `database/migrations/` reflects full history;
--  running database/schema.sql directly also works for a fresh
--  install since it is idempotent via IF NOT EXISTS.)
-- =========================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS user_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    last_active_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata_json   JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS legal_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES user_sessions(id) ON DELETE SET NULL,
    filename        VARCHAR(512) NOT NULL,
    file_type       VARCHAR(50) DEFAULT 'pdf',
    page_count      INTEGER DEFAULT 0,
    raw_text        TEXT,
    status          VARCHAR(50) DEFAULT 'uploaded',
    uploaded_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_legal_documents_session ON legal_documents(session_id);

CREATE TABLE IF NOT EXISTS document_chunks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES legal_documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    page_number     INTEGER,
    embedding       VECTOR(384)
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS citations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name     VARCHAR(512) NOT NULL,
    source_type     VARCHAR(100) DEFAULT 'statute',
    content         TEXT NOT NULL,
    url             VARCHAR(1024),
    embedding       VECTOR(384),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_citations_embedding
    ON citations USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

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
