"""
Shared LangGraph state schema.

Every agent node reads from and writes back to this single TypedDict.
LangGraph merges partial dict returns from each node into this state,
so nodes only need to return the keys they modify.

Phase 2 note: the original Phase 1 fields (clauses, obligations,
deadlines, penalties, risks, overall_risk_level) are PRESERVED for
backward compatibility — the new Document Intelligence Agent (Agent 6)
populates them alongside its richer structured output, and the
existing Clause Analysis Agent (app/agents/clause_agent.py) remains in
the codebase and importable, even though the default graph now uses
Agent 6 in its place.
"""
from typing import TypedDict, Optional, Any, Literal
import uuid


class ClauseDict(TypedDict):
    title: str
    text: str
    category: Optional[str]


class RiskDict(TypedDict):
    risk_level: str
    reason: str
    related_clause: Optional[str]


class SourceDict(TypedDict):
    source_name: str
    source_type: str
    snippet: str
    score: Optional[float]


# ---------------------------------------------------------------
# Phase 2 additions
# ---------------------------------------------------------------

class EvidenceRef(TypedDict):
    """A pointer from a finding (risk/compliance issue) back to the
    contract text that supports it. Required on every observation so
    the platform stays explainable / evidence-backed rather than
    asserting unverifiable claims."""
    label: str          # e.g. "Clause 8.2" or "No termination section detected"
    quote: Optional[str]  # short supporting excerpt (kept short — copyright-safe, non-verbatim reproduction of long text)
    source: str          # "document_intelligence" | "compliance_agent" | "red_flag_agent" | ...


class PartyDict(TypedDict):
    name: str
    role: Optional[str]  # e.g. "Disclosing Party", "Vendor", "Client"


class ClauseDetail(TypedDict):
    """Richer structured clause representation used by the Document
    Intelligence Agent (vs. the simpler ClauseDict from Phase 1)."""
    present: bool
    summary: Optional[str]
    evidence: list[EvidenceRef]


class DocumentIntelligence(TypedDict, total=False):
    parties: list[PartyDict]
    effective_date: Optional[str]
    expiration_date: Optional[str]
    obligations: list[str]
    payment_terms: ClauseDetail
    confidentiality_clause: ClauseDetail
    liability_clause: ClauseDetail
    indemnity_clause: ClauseDetail
    termination_clause: ClauseDetail
    governing_law: Optional[str]
    jurisdiction: Optional[str]
    deadlines: list[str]
    penalties: list[str]


class ComplianceIssue(TypedDict):
    issue: str
    severity: str  # Low | Moderate | High | Critical
    evidence: list[EvidenceRef]


class ComplianceResults(TypedDict, total=False):
    compliance_score: int  # 0-100, deterministic
    missing_clauses: list[str]
    compliance_issues: list[ComplianceIssue]


class RiskFlag(TypedDict):
    flag_type: str  # e.g. "Unlimited Liability", "One-Sided Termination"
    severity: str    # Low | Moderate | High | Critical
    explanation: str
    evidence: list[EvidenceRef]


class RiskFlagResults(TypedDict, total=False):
    risk_flags: list[RiskFlag]
    severity: str  # highest severity across all flags


class ClauseDiff(TypedDict):
    clause_title: str
    detail: str


class ComparisonResults(TypedDict, total=False):
    added_clauses: list[ClauseDiff]
    removed_clauses: list[ClauseDiff]
    modified_clauses: list[ClauseDiff]
    summary: str


WorkflowMode = Literal["single", "comparison"]


class LegalAnalysisState(TypedDict, total=False):
    # ---- Input ----
    query: str
    document_id: Optional[uuid.UUID]
    document_text: Optional[str]
    session_id: Optional[uuid.UUID]

    # Phase 2: comparison-mode inputs
    workflow_mode: WorkflowMode          # "single" (default) | "comparison"
    document_id_b: Optional[uuid.UUID]
    document_text_b: Optional[str]

    # ---- Agent 1: Intake ----
    task_type: str
    topics: list[str]

    # ---- Agent 2: Research ----
    retrieved_context: list[str]
    sources: list[SourceDict]

    # ---- Agent 3 / Agent 6: Clause & Document Intelligence ----
    # Phase 1 fields (preserved, populated by Agent 6 by default now)
    clauses: list[ClauseDict]
    obligations: list[str]
    deadlines: list[str]
    penalties: list[str]
    # Phase 2 field (richer structured extraction)
    document_intelligence: DocumentIntelligence

    # ---- Agent 9: Contract Comparison (comparison mode only) ----
    comparison_results: ComparisonResults

    # ---- Agent 7: Compliance ----
    compliance_results: ComplianceResults

    # ---- Agent 8: Red Flag Detection ----
    risk_flags: list[RiskFlag]
    red_flag_severity: str

    # ---- Agent 4: Risk Assessment (Phase 1, preserved) ----
    risks: list[RiskDict]
    overall_risk_level: str

    # ---- Evidence / citations aggregated across all agents ----
    evidence_references: list[EvidenceRef]
    citations: list[SourceDict]

    # ---- Agent 5: Report Generation ----
    report_markdown: str
    report_json: dict[str, Any]

    # ---- Error tracking (soft-fail between nodes) ----
    errors: list[str]
