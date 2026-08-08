"""
Agent 5 — Legal Report Generation Agent

Responsibility: combine the outputs of all prior agents into the final
structured Legal Intelligence Report. Implemented with deterministic
Python templates (see app.utils.report_template) rather than an LLM
call, per the project spec — this keeps report structure 100% reliable.

Phase 2 update: the report now includes Executive Summary, Contract
Overview, Extracted Legal Intelligence, Compliance Assessment, Red Flag
Analysis, Evidence & Citations, and (when applicable) Contract
Comparison sections — still rendered via pure Python templates, no
extra LLM call. `evidence_references` is aggregated here from every
agent's evidence lists so the final report and API response expose a
single consolidated citation trail.
"""
from app.agents.state import LegalAnalysisState
from app.utils.report_template import render_report_markdown


def report_node(state: LegalAnalysisState) -> dict:
    evidence_references = _aggregate_evidence(state)
    markdown = render_report_markdown(state, evidence_references)

    report_json = {
        "task_type": state.get("task_type"),
        "topics": state.get("topics", []),
        "sources": state.get("sources", []),
        "clauses": state.get("clauses", []),
        "obligations": state.get("obligations", []),
        "deadlines": state.get("deadlines", []),
        "penalties": state.get("penalties", []),
        "risks": state.get("risks", []),
        "overall_risk_level": state.get("overall_risk_level", "Low"),
        "document_intelligence": state.get("document_intelligence", {}),
        "compliance_results": state.get("compliance_results", {}),
        "risk_flags": state.get("risk_flags", []),
        "red_flag_severity": state.get("red_flag_severity", "Low"),
        "comparison_results": state.get("comparison_results", {}),
        "evidence_references": evidence_references,
        "errors": state.get("errors", []),
    }

    return {
        "report_markdown": markdown,
        "report_json": report_json,
        "evidence_references": evidence_references,
    }


def _aggregate_evidence(state: LegalAnalysisState) -> list[dict]:
    """Pull every evidence entry from compliance issues, red flags, and
    clause-detail evidence lists into one consolidated list for the
    Evidence & Citations report section / API field."""
    evidence: list[dict] = []

    doc_intel = state.get("document_intelligence") or {}
    for key in ("payment_terms", "confidentiality_clause", "liability_clause",
                "indemnity_clause", "termination_clause"):
        detail = doc_intel.get(key) or {}
        if isinstance(detail, dict):
            evidence.extend(detail.get("evidence", []) or [])

    for issue in (state.get("compliance_results") or {}).get("compliance_issues", []):
        evidence.extend(issue.get("evidence", []) or [])

    for flag in state.get("risk_flags", []):
        evidence.extend(flag.get("evidence", []) or [])

    return evidence
