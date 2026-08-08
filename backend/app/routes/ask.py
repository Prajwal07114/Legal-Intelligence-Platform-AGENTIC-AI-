"""
POST /ask

Lightweight entrypoint for pure legal-research questions with no
document attached (e.g. "What does force majeure mean?"). Internally
reuses the same LangGraph pipeline — the Clause/Risk agents simply
no-op when there's no document text, so the report degrades gracefully
into a research-only report.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas import AskRequest, AnalyzeResponse
from app.graph import run_legal_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AnalyzeResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    try:
        final_state = run_legal_pipeline(
            query=payload.query,
            document_id=None,
            document_text=None,
            session_id=payload.session_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline execution failed")
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {exc}") from exc

    report = Report(
        session_id=payload.session_id,
        document_id=None,
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
