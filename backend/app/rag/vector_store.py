"""
Vector store operations: persisting document chunks (with embeddings)
into PostgreSQL/pgvector via SQLAlchemy.
"""
import uuid
import logging

from sqlalchemy.orm import Session

from app.models import DocumentChunk
from app.rag.chunker import Chunk
from app.rag.embeddings import embed_texts

logger = logging.getLogger(__name__)


def persist_chunks(db: Session, document_id: uuid.UUID, chunks: list[Chunk]) -> int:
    """Embed and store chunks for a given document. Returns count stored."""
    if not chunks:
        return 0

    texts = [c.content for c in chunks]
    vectors = embed_texts(texts)

    rows = [
        DocumentChunk(
            document_id=document_id,
            chunk_index=chunk.index,
            content=chunk.content,
            page_number=chunk.page_number,
            embedding=vector,
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    db.bulk_save_objects(rows)
    db.commit()
    logger.info("Persisted %d chunks for document %s", len(rows), document_id)
    return len(rows)
