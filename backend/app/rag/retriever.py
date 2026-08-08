"""
Semantic retrieval layer used by the Legal Research Agent.

Searches two corpora via pgvector cosine distance:
  1. document_chunks  -> the user's uploaded contract (if any)
  2. citations         -> curated statutes / regulations / clause-reference library

A similarity floor (MIN_SIMILARITY) is applied to reduce hallucination
risk: low-relevance chunks are dropped rather than force-fit into context.
"""
import uuid
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import DocumentChunk, Citation
from app.rag.embeddings import embed_query

logger = logging.getLogger(__name__)

MIN_SIMILARITY = 0.25  # cosine similarity floor (1 - cosine_distance)


@dataclass
class RetrievedItem:
    content: str
    source_name: str
    source_type: str
    similarity: float


def retrieve_document_context(db: Session, document_id: uuid.UUID, query: str) -> list[RetrievedItem]:
    """Retrieve top-k relevant chunks from a specific uploaded document."""
    query_vec = embed_query(query)
    k = settings.top_k_retrieval

    # pgvector cosine distance operator `<=>` (0 = identical, 2 = opposite)
    stmt = (
        select(
            DocumentChunk.content,
            DocumentChunk.page_number,
            DocumentChunk.embedding.cosine_distance(query_vec).label("distance"),
        )
        .where(DocumentChunk.document_id == document_id)
        .order_by("distance")
        .limit(k)
    )
    results = db.execute(stmt).all()

    items = []
    for content, page_number, distance in results:
        similarity = 1 - float(distance)
        if similarity < MIN_SIMILARITY:
            continue
        items.append(
            RetrievedItem(
                content=content,
                source_name=f"Uploaded document (page {page_number})" if page_number else "Uploaded document",
                source_type="uploaded_document",
                similarity=round(similarity, 4),
            )
        )
    return items


def retrieve_reference_context(db: Session, query: str) -> list[RetrievedItem]:
    """Retrieve top-k relevant statutes/regulations/clause references."""
    query_vec = embed_query(query)
    k = settings.top_k_retrieval

    stmt = (
        select(
            Citation.content,
            Citation.source_name,
            Citation.source_type,
            Citation.embedding.cosine_distance(query_vec).label("distance"),
        )
        .order_by("distance")
        .limit(k)
    )
    try:
        results = db.execute(stmt).all()
    except Exception as exc:  # noqa: BLE001
        # Reference corpus may be empty in a fresh install — degrade gracefully.
        logger.warning("Reference corpus retrieval failed/empty: %s", exc)
        return []

    items = []
    for content, source_name, source_type, distance in results:
        similarity = 1 - float(distance)
        if similarity < MIN_SIMILARITY:
            continue
        items.append(
            RetrievedItem(
                content=content,
                source_name=source_name,
                source_type=source_type,
                similarity=round(similarity, 4),
            )
        )
    return items


def retrieve_all(db: Session, query: str, document_id: uuid.UUID | None) -> list[RetrievedItem]:
    """Combined retrieval used by the Research Agent."""
    items: list[RetrievedItem] = []
    if document_id:
        items.extend(retrieve_document_context(db, document_id, query))
    items.extend(retrieve_reference_context(db, query))
    # Highest similarity first
    items.sort(key=lambda i: i.similarity, reverse=True)
    return items
