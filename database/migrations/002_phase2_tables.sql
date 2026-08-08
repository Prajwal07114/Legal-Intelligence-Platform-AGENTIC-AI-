-- =========================================================
-- Migration 002 — Phase 2: Compliance, Red Flags, Comparison
-- Run AFTER 001_phase1_init.sql (or database/schema.sql).
-- Idempotent: safe to re-run.
-- =========================================================

-- Track which pipeline mode produced a report ("single" | "comparison").
ALTER TABLE reports
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
