"""
GET /download-report/{report_id}          — format via ?format=pdf|docx|json (default: json)
GET /download-report-pdf/{report_id}       — PDF export
GET /download-report-docx/{report_id}      — DOCX export
GET /download-report-json/{report_id}      — JSON export

All four read the SAME stored `Report` row (no re-run of the LangGraph
pipeline, no new LLM calls) and normalize it through
app.utils.report_export.build_export_data before handing it to the
relevant renderer. This is purely an export layer on top of existing
data — it does not modify the analysis pipeline, agents, or any other
route.
"""
import uuid
import logging

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.models import Report
from app.utils.report_export import build_export_data
from app.utils.pdf_report import generate_pdf_report
from app.utils.docx_report import generate_docx_report

logger = logging.getLogger(__name__)
router = APIRouter(tags=["download"])


def _get_report_or_404(report_id: uuid.UUID, db: Session) -> Report:
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


def _pdf_response(data: dict) -> StreamingResponse:
    pdf_bytes = generate_pdf_report(data)
    filename = f"legal-intelligence-report-{data['case_id'][:8]}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _docx_response(data: dict) -> StreamingResponse:
    docx_bytes = generate_docx_report(data)
    filename = f"legal-intelligence-report-{data['case_id'][:8]}.docx"
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _json_response(data: dict) -> JSONResponse:
    filename = f"legal-intelligence-report-{data['case_id'][:8]}.json"
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/download-report/{report_id}")
def download_report(
    report_id: uuid.UUID,
    format: str = Query("json", pattern="^(pdf|docx|json)$"),
    db: Session = Depends(get_db),
):
    """Generic export entrypoint. ?format=pdf|docx|json (default json)."""
    report = _get_report_or_404(report_id, db)
    data = build_export_data(report)

    if format == "pdf":
        return _pdf_response(data)
    if format == "docx":
        return _docx_response(data)
    return _json_response(data)


@router.get("/download-report-pdf/{report_id}")
def download_report_pdf(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = _get_report_or_404(report_id, db)
    data = build_export_data(report)
    return _pdf_response(data)


@router.get("/download-report-docx/{report_id}")
def download_report_docx(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = _get_report_or_404(report_id, db)
    data = build_export_data(report)
    return _docx_response(data)


@router.get("/download-report-json/{report_id}")
def download_report_json(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = _get_report_or_404(report_id, db)
    data = build_export_data(report)
    return _json_response(data)
