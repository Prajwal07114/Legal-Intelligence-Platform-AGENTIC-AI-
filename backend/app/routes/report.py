"""
GET /report/{id}
GET /comparison-report/{id}
GET /compliance-report/{id}
GET /risk-report/{id}

Fetch previously generated reports/results by ID.
"""
import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report, ComparisonResult, ComplianceResult, RiskFlagResult
from app.schemas import (
    ReportResponse,
    ComparisonReportResponse,
    ComplianceReportResponse,
    RiskReportResponse,
)

router = APIRouter(tags=["report"])


@router.get("/report/{report_id}", response_model=ReportResponse)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return ReportResponse(
        id=report.id,
        user_query=report.user_query,
        task_type=report.task_type,
        risk_level=report.risk_level,
        report_markdown=report.report_markdown,
        report_json=report.report_json,
        created_at=report.created_at.isoformat(),
    )


@router.get("/comparison-report/{comparison_id}", response_model=ComparisonReportResponse)
def get_comparison_report(comparison_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.get(ComparisonResult, comparison_id)
    if not row:
        raise HTTPException(status_code=404, detail="Comparison report not found.")

    return ComparisonReportResponse(
        id=row.id,
        document_id_a=row.document_id_a,
        document_id_b=row.document_id_b,
        added_clauses=row.added_clauses or [],
        removed_clauses=row.removed_clauses or [],
        modified_clauses=row.modified_clauses or [],
        summary=row.summary,
        created_at=row.created_at.isoformat(),
    )


@router.get("/compliance-report/{compliance_id}", response_model=ComplianceReportResponse)
def get_compliance_report(compliance_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.get(ComplianceResult, compliance_id)
    if not row:
        raise HTTPException(status_code=404, detail="Compliance report not found.")

    return ComplianceReportResponse(
        id=row.id,
        document_id=row.document_id,
        compliance_score=row.compliance_score,
        missing_clauses=row.missing_clauses or [],
        compliance_issues=row.compliance_issues or [],
        created_at=row.created_at.isoformat(),
    )


@router.get("/risk-report/{risk_flag_id}", response_model=RiskReportResponse)
def get_risk_report(risk_flag_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.get(RiskFlagResult, risk_flag_id)
    if not row:
        raise HTTPException(status_code=404, detail="Risk report not found.")

    return RiskReportResponse(
        id=row.id,
        document_id=row.document_id,
        risk_flags=row.flags or [],
        severity=row.severity,
        created_at=row.created_at.isoformat(),
    )
