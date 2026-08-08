"""
POST /analyze-document

Runs the full 5-agent LangGraph pipeline against an uploaded document
(or a general legal query with no document), persists the resulting
report, and returns the structured analysis.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LegalDocument, Report
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.graph import run_legal_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analyze"])


@router.post("/analyze-document", response_model=AnalyzeResponse)
def analyze_document(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    document_text = None

    if payload.document_id:
        document = db.get(LegalDocument, payload.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        document_text = document.raw_text

    try:
        final_state = run_legal_pipeline(
            query=payload.query,
            document_id=payload.document_id,
            document_text=document_text,
            session_id=payload.session_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline execution failed")
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {exc}") from exc

    report = Report(
        session_id=payload.session_id,
        document_id=payload.document_id,
        user_query=payload.query,
        task_type=final_state.get("task_type"),
        report_markdown=final_state.get("report_markdown", ""),
        report_json=final_state.get("report_json", {}),
        risk_level=final_state.get("overall_risk_level"),
        workflow_mode="single",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return AnalyzeResponse(
        report_id=report.id,
        task_type=final_state.get("task_type", ""),
        topics=final_state.get("topics", []),
        clauses=final_state.get("clauses", []),
        obligations=final_state.get("obligations", []),
        deadlines=final_state.get("deadlines", []),
        penalties=final_state.get("penalties", []),
        risks=final_state.get("risks", []),
        overall_risk_level=final_state.get("overall_risk_level", "Low"),
        sources=final_state.get("sources", []),
        report_markdown=final_state.get("report_markdown", ""),
        document_intelligence=final_state.get("document_intelligence"),
        compliance_results=final_state.get("compliance_results"),
        risk_flags=final_state.get("risk_flags"),
        red_flag_severity=final_state.get("red_flag_severity"),
        comparison_results=final_state.get("comparison_results"),
        evidence_references=final_state.get("evidence_references"),
    )
