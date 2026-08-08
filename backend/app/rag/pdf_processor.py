"""
PDF ingestion: extracts text (and page numbers) from uploaded contracts.

Strategy:
  1. Try pdfplumber (better layout / table handling for contracts).
  2. Fall back to PyPDF2 if pdfplumber fails (e.g. malformed PDF).
"""
import io
import logging
from dataclasses import dataclass

import pdfplumber
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    page_number: int
    text: str


@dataclass
class ExtractedDocument:
    pages: list[PageText]
    full_text: str
    page_count: int


def extract_text_from_pdf(file_bytes: bytes) -> ExtractedDocument:
    """Extract per-page text from PDF bytes. Raises ValueError if unreadable."""
    pages = _extract_with_pdfplumber(file_bytes)
    if not pages:
        pages = _extract_with_pypdf2(file_bytes)

    if not pages:
        raise ValueError("Could not extract any text from the uploaded PDF.")

    full_text = "\n\n".join(p.text for p in pages if p.text.strip())
    return ExtractedDocument(pages=pages, full_text=full_text, page_count=len(pages))


def _extract_with_pdfplumber(file_bytes: bytes) -> list[PageText]:
    pages: list[PageText] = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append(PageText(page_number=i, text=text))
    except Exception as exc:  # noqa: BLE001
        logger.warning("pdfplumber extraction failed: %s", exc)
        return []
    return pages


def _extract_with_pypdf2(file_bytes: bytes) -> list[PageText]:
    pages: list[PageText] = []
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append(PageText(page_number=i, text=text))
    except Exception as exc:  # noqa: BLE001
        logger.error("PyPDF2 fallback extraction failed: %s", exc)
        return []
    return pages
