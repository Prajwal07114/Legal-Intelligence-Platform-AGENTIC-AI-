"""
POST /compliance-check

Standalone compliance check on an already-uploaded document — runs
just the Document Intelligence Agent + Compliance Agent directly
(bypassing Intake/Research/Red-Flag/Risk for a faster, focused result)
and persists a `compliance_results` row.

Also persists a lightweight `Report` row via the existing deterministic
report_node — purely so this endpoint's result is exportable through
the same PDF/DOCX/JSON download endpoints as every other report,
without duplicating the export logic. No agent/graph logic changes.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LegalDocument, ComplianceResult, Report
from app.schemas import ComplianceCheckRequest, ComplianceCheckResponse
from app.agents.document_intelligence_agent import document_intelligence_node
from app.agents.compliance_agent import compliance_node
from app.agents.report_agent import report_node

logger = logging.getLogger(__name__)
router = APIRouter(tags=["compliance"])


@router.post("/compliance-check", response_model=ComplianceCheckResponse)
def compliance_check(payload: ComplianceCheckRequest, db: Session = Depends(get_db)):
    document = db.get(LegalDocument, payload.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        state = {"document_text": document.raw_text, "topics": [], "errors": []}
        state.update(document_intelligence_node(state))
        state.update(compliance_node(state))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Compliance check failed")
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {exc}") from exc

    compliance = state.get("compliance_results", {}) or {}

    row = ComplianceResult(
        document_id=payload.document_id,
        session_id=payload.session_id,
        compliance_score=compliance.get("compliance_score", 0),
        missing_clauses=compliance.get("missing_clauses", []),
        compliance_issues=compliance.get("compliance_issues", []),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # Persist an exportable Report row (deterministic template, no LLM call)
    state.setdefault("query", "Standalone compliance check")
    state.setdefault("task_type", "Compliance Check")
    report_result = report_node(state)
    report = Report(
        session_id=payload.session_id,
        document_id=payload.document_id,
        user_query=state["query"],
        task_type=state["task_type"],
        report_markdown=report_result.get("report_markdown", ""),
        report_json=report_result.get("report_json", {}),
        risk_level="Low",
        workflow_mode="single",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ComplianceCheckResponse(
        compliance_id=row.id,
        document_id=payload.document_id,
        compliance_score=row.compliance_score,
        missing_clauses=row.missing_clauses,
        compliance_issues=row.compliance_issues,
        report_id=report.id,
    )
