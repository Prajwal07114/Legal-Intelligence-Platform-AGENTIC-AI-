"""
POST /compare-contracts

Runs the LangGraph pipeline in comparison_mode against two already-
uploaded documents (Contract A vs Contract B), persisting both a
`reports` row (full markdown report, consistent with the other
endpoints) and a `comparison_results` row (structured diff, for the
dedicated GET /comparison-report/{id} endpoint).
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LegalDocument, Report, ComparisonResult
from app.schemas import CompareContractsRequest, CompareContractsResponse
from app.graph import run_legal_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["compare"])


@router.post("/compare-contracts", response_model=CompareContractsResponse)
def compare_contracts(payload: CompareContractsRequest, db: Session = Depends(get_db)):
    doc_a = db.get(LegalDocument, payload.document_id_a)
    doc_b = db.get(LegalDocument, payload.document_id_b)
    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents were not found.")

    try:
        final_state = run_legal_pipeline(
            query=payload.query,
            document_id=payload.document_id_a,
            document_text=doc_a.raw_text,
            session_id=payload.session_id,
            workflow_mode="comparison",
            document_id_b=payload.document_id_b,
            document_text_b=doc_b.raw_text,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Comparison pipeline execution failed")
        raise HTTPException(status_code=500, detail=f"Comparison pipeline failed: {exc}") from exc

    comparison = final_state.get("comparison_results", {}) or {}

    report = Report(
        session_id=payload.session_id,
        document_id=payload.document_id_b,
        user_query=payload.query,
        task_type=final_state.get("task_type"),
        report_markdown=final_state.get("report_markdown", ""),
        report_json=final_state.get("report_json", {}),
        risk_level=final_state.get("overall_risk_level"),
        workflow_mode="comparison",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    comparison_row = ComparisonResult(
        report_id=report.id,
        document_id_a=payload.document_id_a,
        document_id_b=payload.document_id_b,
        session_id=payload.session_id,
        added_clauses=comparison.get("added_clauses", []),
        removed_clauses=comparison.get("removed_clauses", []),
        modified_clauses=comparison.get("modified_clauses", []),
        summary=comparison.get("summary", ""),
    )
    db.add(comparison_row)
    db.commit()
    db.refresh(comparison_row)

    return CompareContractsResponse(
        comparison_id=comparison_row.id,
        report_id=report.id,
        document_id_a=payload.document_id_a,
        document_id_b=payload.document_id_b,
        added_clauses=comparison.get("added_clauses", []),
        removed_clauses=comparison.get("removed_clauses", []),
        modified_clauses=comparison.get("modified_clauses", []),
        summary=comparison.get("summary", ""),
        compliance_results=final_state.get("compliance_results"),
        risk_flags=final_state.get("risk_flags"),
        overall_risk_level=final_state.get("overall_risk_level", "Low"),
        report_markdown=final_state.get("report_markdown", ""),
    )
