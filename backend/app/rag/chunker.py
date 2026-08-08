"""
Chunking strategy for RAG ingestion.

Uses a sliding-window character splitter that tries to break on
paragraph/sentence boundaries where possible, which works reasonably
well for contract text (clauses are usually paragraph-delimited).
"""
import re
from dataclasses import dataclass

from app.config import settings
from app.rag.pdf_processor import ExtractedDocument

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.;:])\s+")


@dataclass
class Chunk:
    index: int
    content: str
    page_number: int | None


def chunk_document(doc: ExtractedDocument) -> list[Chunk]:
    """Chunk an extracted document while preserving page attribution."""
    chunks: list[Chunk] = []
    idx = 0
    for page in doc.pages:
        if not page.text.strip():
            continue
        for piece in _split_text(page.text):
            chunks.append(Chunk(index=idx, content=piece, page_number=page.page_number))
            idx += 1
    return chunks


def chunk_raw_text(text: str) -> list[Chunk]:
    """Chunk arbitrary text with no page attribution (used for reference corpus)."""
    return [
        Chunk(index=i, content=piece, page_number=None)
        for i, piece in enumerate(_split_text(text))
    ]


def _split_text(text: str) -> list[str]:
    size = settings.chunk_size
    overlap = settings.chunk_overlap
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    sentences = _SENTENCE_BOUNDARY.split(text)
    pieces: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= size:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                pieces.append(current)
            # start new chunk, carrying overlap from the tail of the previous chunk
            tail = current[-overlap:] if overlap and current else ""
            current = f"{tail} {sentence}".strip()

    if current:
        pieces.append(current)

    # Fallback: if sentence splitting failed to reduce size (e.g. no punctuation),
    # hard-split by character window.
    final: list[str] = []
    for p in pieces:
        if len(p) <= size * 1.5:
            final.append(p)
        else:
            for i in range(0, len(p), size - overlap):
                final.append(p[i:i + size])

    return final
