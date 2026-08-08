"""
POST /upload-document

Accepts a PDF contract, extracts text, chunks it, embeds the chunks,
and stores everything in PostgreSQL/pgvector.
"""
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import LegalDocument
from app.rag.pdf_processor import extract_text_from_pdf
from app.rag.chunker import chunk_document
from app.rag.vector_store import persist_chunks
from app.schemas import UploadDocumentResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])


@router.post("/upload-document", response_model=UploadDocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported in Phase 1.")

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f}MB). Max allowed is {settings.max_upload_mb}MB.",
        )

    try:
        extracted = extract_text_from_pdf(file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    document = LegalDocument(
        filename=file.filename,
        file_type="pdf",
        page_count=extracted.page_count,
        raw_text=extracted.full_text,
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        chunks = chunk_document(extracted)
        chunk_count = persist_chunks(db, document.id, chunks)
        document.status = "processed"
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to chunk/embed document %s", document.id)
        document.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {exc}") from exc

    return UploadDocumentResponse(
        document_id=document.id,
        filename=document.filename,
        page_count=document.page_count,
        chunk_count=chunk_count,
        status=document.status,
    )
