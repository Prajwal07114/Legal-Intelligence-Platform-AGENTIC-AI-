"""
Pydantic schemas for API request/response bodies.
Kept separate from ORM models (app.models) on purpose.
"""
import uuid
from typing import Optional, Any
from pydantic import BaseModel, Field


# ---------- Upload ----------

class UploadDocumentResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    page_count: int
    chunk_count: int
    status: str


# ---------- Ask / Analyze (shared) ----------

class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The user's legal question or instruction")
    document_id: Optional[uuid.UUID] = Field(
        None, description="Optional document to analyze/ground the answer in"
    )
    session_id: Optional[uuid.UUID] = None


class AskRequest(BaseModel):
    query: str = Field(..., min_length=3)
    session_id: Optional[uuid.UUID] = None


class ClauseItem(BaseModel):
    title: str
    text: str
    category: Optional[str] = None


class RiskItem(BaseModel):
    risk_level: str
    reason: str
    related_clause: Optional[str] = None


class SourceItem(BaseModel):
    source_name: str
    source_type: str
    snippet: str
    score: Optional[float] = None


class AnalyzeResponse(BaseModel):
    report_id: uuid.UUID
    task_type: str
    topics: list[str]
    clauses: list[ClauseItem]
    obligations: list[str]
    deadlines: list[str]
    penalties: list[str]
    risks: list[RiskItem]
    overall_risk_level: str
    sources: list[SourceItem]
    report_markdown: str
    # ---- Phase 2 additions (all optional/additive — Phase 1 clients unaffected) ----
    document_intelligence: Optional[dict[str, Any]] = None
    compliance_results: Optional[dict[str, Any]] = None
    risk_flags: Optional[list[dict[str, Any]]] = None
    red_flag_severity: Optional[str] = None
    comparison_results: Optional[dict[str, Any]] = None
    evidence_references: Optional[list[dict[str, Any]]] = None


class ReportResponse(BaseModel):
    id: uuid.UUID
    user_query: str
    task_type: Optional[str]
    risk_level: Optional[str]
    report_markdown: str
    report_json: Optional[dict[str, Any]]
    created_at: str


# ==========================================================
# Phase 2 schemas
# ==========================================================

class EvidenceItem(BaseModel):
    label: str
    quote: Optional[str] = None
    source: str


class CompareContractsRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Instruction/context for the comparison, e.g. 'Compare these two vendor agreements'")
    document_id_a: uuid.UUID
    document_id_b: uuid.UUID
    session_id: Optional[uuid.UUID] = None


class ComplianceCheckRequest(BaseModel):
    document_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None


class RiskAnalysisRequest(BaseModel):
    document_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None


class ComplianceIssueItem(BaseModel):
    issue: str
    severity: str
    evidence: list[EvidenceItem] = []


class ComplianceCheckResponse(BaseModel):
    compliance_id: uuid.UUID
    document_id: uuid.UUID
    compliance_score: int
    missing_clauses: list[str]
    compliance_issues: list[ComplianceIssueItem]
    report_id: Optional[uuid.UUID] = None  # exportable via /download-report-*


class RiskFlagItem(BaseModel):
    flag_type: str
    severity: str
    explanation: str
    evidence: list[EvidenceItem] = []


class RiskAnalysisResponse(BaseModel):
    risk_flag_id: uuid.UUID
    document_id: uuid.UUID
    risk_flags: list[RiskFlagItem]
    severity: str
    overall_risk_level: str
    report_id: Optional[uuid.UUID] = None  # exportable via /download-report-*


class ClauseDiffItem(BaseModel):
    clause_title: str
    detail: str


class CompareContractsResponse(BaseModel):
    comparison_id: uuid.UUID
    report_id: uuid.UUID
    document_id_a: uuid.UUID
    document_id_b: uuid.UUID
    added_clauses: list[ClauseDiffItem]
    removed_clauses: list[ClauseDiffItem]
    modified_clauses: list[ClauseDiffItem]
    summary: str
    compliance_results: Optional[dict[str, Any]] = None
    risk_flags: Optional[list[dict[str, Any]]] = None
    overall_risk_level: str
    report_markdown: str


class ComparisonReportResponse(BaseModel):
    id: uuid.UUID
    document_id_a: Optional[uuid.UUID]
    document_id_b: Optional[uuid.UUID]
    added_clauses: list[ClauseDiffItem]
    removed_clauses: list[ClauseDiffItem]
    modified_clauses: list[ClauseDiffItem]
    summary: Optional[str]
    created_at: str


class ComplianceReportResponse(BaseModel):
    id: uuid.UUID
    document_id: Optional[uuid.UUID]
    compliance_score: int
    missing_clauses: list[str]
    compliance_issues: list[ComplianceIssueItem]
    created_at: str


class RiskReportResponse(BaseModel):
    id: uuid.UUID
    document_id: Optional[uuid.UUID]
    risk_flags: list[RiskFlagItem]
    severity: str
    created_at: str
