"""
POST /risk-analysis

Standalone risk analysis on an already-uploaded document — runs
Document Intelligence -> Compliance (needed as red-flag input) -> Red
Flag Detection -> Risk Assessment directly, bypassing Intake/Research,
and persists a `risk_flags` row.

Also persists a lightweight `Report` row via the existing deterministic
report_node — purely so this endpoint's result is exportable through
the same PDF/DOCX/JSON download endpoints as every other report,
without duplicating the export logic. No agent/graph logic changes.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LegalDocument, RiskFlagResult, Report
from app.schemas import RiskAnalysisRequest, RiskAnalysisResponse
from app.agents.document_intelligence_agent import document_intelligence_node
from app.agents.compliance_agent import compliance_node
from app.agents.red_flag_agent import red_flag_node
from app.agents.risk_agent import risk_node
from app.agents.report_agent import report_node

logger = logging.getLogger(__name__)
router = APIRouter(tags=["risk"])


@router.post("/risk-analysis", response_model=RiskAnalysisResponse)
def risk_analysis(payload: RiskAnalysisRequest, db: Session = Depends(get_db)):
    document = db.get(LegalDocument, payload.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        state = {"document_text": document.raw_text, "topics": [], "errors": []}
        state.update(document_intelligence_node(state))
        state.update(compliance_node(state))
        state.update(red_flag_node(state))
        state.update(risk_node(state))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Risk analysis failed")
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {exc}") from exc

    flags = state.get("risk_flags", [])
    severity = state.get("red_flag_severity", "Low")
    overall_risk_level = state.get("overall_risk_level", "Low")

    row = RiskFlagResult(
        document_id=payload.document_id,
        session_id=payload.session_id,
        flags=flags,
        severity=severity,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # Persist an exportable Report row (deterministic template, no LLM call)
    state.setdefault("query", "Standalone risk analysis")
    state.setdefault("task_type", "Risk Analysis")
    report_result = report_node(state)
    report = Report(
        session_id=payload.session_id,
        document_id=payload.document_id,
        user_query=state["query"],
        task_type=state["task_type"],
        report_markdown=report_result.get("report_markdown", ""),
        report_json=report_result.get("report_json", {}),
        risk_level=overall_risk_level,
        workflow_mode="single",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return RiskAnalysisResponse(
        risk_flag_id=row.id,
        document_id=payload.document_id,
        risk_flags=flags,
        severity=severity,
        overall_risk_level=overall_risk_level,
        report_id=report.id,
    )
