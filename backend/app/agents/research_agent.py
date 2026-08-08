"""
Agent 2 — Legal Research Agent

Responsibility: query the vector store (pgvector) for relevant statutes,
regulations, clause references, and — if a document was uploaded —
relevant passages from that document. Always returns source attribution
to reduce hallucination risk downstream.
"""
import logging

from app.agents.state import LegalAnalysisState
from app.database import db_session
from app.rag.retriever import retrieve_all

logger = logging.getLogger(__name__)


def research_node(state: LegalAnalysisState) -> dict:
    query = state.get("query", "")
    document_id = state.get("document_id")
    errors = list(state.get("errors", []))

    try:
        with db_session() as db:
            items = retrieve_all(db, query=query, document_id=document_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Research agent retrieval failed: %s", exc)
        errors.append(f"Research retrieval failed: {exc}")
        items = []

    retrieved_context = [item.content for item in items]
    sources = [
        {
            "source_name": item.source_name,
            "source_type": item.source_type,
            "snippet": item.content[:220] + ("..." if len(item.content) > 220 else ""),
            "score": item.similarity,
        }
        for item in items
    ]

    return {
        "retrieved_context": retrieved_context,
        "sources": sources,
        "errors": errors,
    }
