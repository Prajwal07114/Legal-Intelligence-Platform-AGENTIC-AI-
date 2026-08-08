"""
Shared pytest fixtures.

Agent unit tests should not require a live PostgreSQL/pgvector
instance, a live Groq API key, or heavy ML dependencies
(sentence-transformers) to be installed — they test agent LOGIC
(defensive parsing, deterministic scoring, aggregation, graph
routing) with the LLM call mocked out.

This conftest stubs the heavy/network-dependent modules at import
time so `pytest` can run in a lightweight CI environment. Real
integration testing against a live Postgres + Groq instance is a
separate concern (see tests/test_integration_smoke.py, skipped by
default).
"""
import os
import sys
import types

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_db")

# ---- Stub sentence_transformers (heavy, not needed for agent logic tests) ----
if "sentence_transformers" not in sys.modules:
    fake_st_module = types.ModuleType("sentence_transformers")

    class _FakeSentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, texts, **kwargs):
            return [[0.0] * 384 for _ in texts]

    fake_st_module.SentenceTransformer = _FakeSentenceTransformer
    sys.modules["sentence_transformers"] = fake_st_module

# ---- Stub pdfplumber / PyPDF2 (not needed for agent logic tests) ----
if "pdfplumber" not in sys.modules:
    sys.modules["pdfplumber"] = types.ModuleType("pdfplumber")

if "PyPDF2" not in sys.modules:
    fake_pypdf2 = types.ModuleType("PyPDF2")
    fake_pypdf2.PdfReader = object
    sys.modules["PyPDF2"] = fake_pypdf2

import pytest  # noqa: E402


@pytest.fixture
def sample_document_intelligence() -> dict:
    """A realistic, fully-populated document_intelligence payload for
    downstream agent tests (Compliance, Red Flag, Report)."""
    return {
        "parties": [
            {"name": "Acme Corp", "role": "Vendor"},
            {"name": "Beta Inc", "role": "Client"},
        ],
        "effective_date": "2024-01-01",
        "expiration_date": None,
        "obligations": ["Vendor shall deliver services monthly"],
        "deadlines": ["Payment due within 30 days"],
        "penalties": ["2% late fee per month"],
        "payment_terms": {
            "present": True,
            "summary": "Net 30 payment terms",
            "evidence": [{"label": "Clause 3.1", "quote": "payment due within 30 days", "source": "document_intelligence"}],
        },
        "confidentiality_clause": {"present": False, "summary": None, "evidence": []},
        "liability_clause": {
            "present": True,
            "summary": "Unlimited liability for vendor",
            "evidence": [{"label": "Clause 8.2", "quote": "unlimited liability", "source": "document_intelligence"}],
        },
        "indemnity_clause": {
            "present": True,
            "summary": "Broad mutual indemnification",
            "evidence": [{"label": "Clause 9.1", "quote": None, "source": "document_intelligence"}],
        },
        "termination_clause": {"present": False, "summary": None, "evidence": []},
        "governing_law": "State of Delaware",
        "jurisdiction": None,
    }


@pytest.fixture
def empty_document_intelligence() -> dict:
    """A document_intelligence payload where nothing was detected —
    used to test the "everything missing" compliance/red-flag path."""
    return {
        "parties": [],
        "effective_date": None,
        "expiration_date": None,
        "obligations": [],
        "deadlines": [],
        "penalties": [],
        "payment_terms": {"present": False, "summary": None, "evidence": []},
        "confidentiality_clause": {"present": False, "summary": None, "evidence": []},
        "liability_clause": {"present": False, "summary": None, "evidence": []},
        "indemnity_clause": {"present": False, "summary": None, "evidence": []},
        "termination_clause": {"present": False, "summary": None, "evidence": []},
        "governing_law": None,
        "jurisdiction": None,
    }
