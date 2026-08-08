"""
Report export data builder.

Takes a `Report` ORM row (whose `report_json` column already holds the
full Phase 2 pipeline output — document_intelligence, compliance_results,
risk_flags, comparison_results, evidence_references, sources, etc.,
assembled by app.agents.report_agent) and normalizes it into ONE flat
export dict. The PDF generator, DOCX generator, and JSON export endpoint
all consume this same dict, so the three formats can never drift out of
sync with each other.

This module only reads/reshapes data that already exists on the Report
row — it does not call the LLM, does not touch the LangGraph pipeline,
and does not query any other table. Adding it does not modify backend
architecture beyond the new /download-report-* routes that use it.
"""
import re
from datetime import datetime, timezone

SEVERITY_ORDER = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
HIGH_SEVERITIES = {"High", "Critical"}

RECOMMENDATIONS_HEADER = "## Recommended Review Areas"
NEXT_SECTION_PATTERN = re.compile(r"^## ", re.MULTILINE)


def build_export_data(report) -> dict:
    """report: an app.models.Report ORM instance."""
    rj = report.report_json or {}

    doc_intel = rj.get("document_intelligence") or {}
    compliance = rj.get("compliance_results") or {}
    risk_flags = rj.get("risk_flags") or []
    comparison = rj.get("comparison_results") or {}
    sources = rj.get("sources") or []
    evidence_refs = rj.get("evidence_references") or []
    clauses = rj.get("clauses") or []
    risks = rj.get("risks") or []
    compliance_issues = compliance.get("compliance_issues") or []

    high_risk_flags = [f for f in risk_flags if f.get("severity") in HIGH_SEVERITIES]
    generated_on = report.created_at.replace(tzinfo=timezone.utc).isoformat() \
        if report.created_at else datetime.now(timezone.utc).isoformat()

    findings = _build_findings(compliance_issues, risk_flags)
    recommendations = _extract_recommendations(report.report_markdown or "")

    return {
        # ---- Case Information ----
        "case_id": str(report.id),
        "report_id": str(report.id),
        "document_id": str(report.document_id) if report.document_id else None,
        "user_query": report.user_query,
        "task_type": report.task_type or rj.get("task_type") or "Legal Research",
        "workflow_mode": getattr(report, "workflow_mode", "single") or "single",
        "topics": rj.get("topics") or [],
        "generated_on": generated_on,
        "generated_by": "Legal Intelligence Command Room",
        "agent_workflow_version": "Phase 2 — 9-Agent Investigation Pipeline",

        # ---- Metrics header ----
        "risk_level": report.risk_level or rj.get("overall_risk_level") or "Low",
        "compliance_score": compliance.get("compliance_score"),
        "clauses_extracted": len(clauses),
        "high_risk_clause_count": len(high_risk_flags),
        "jurisdiction": doc_intel.get("jurisdiction"),
        "governing_law": doc_intel.get("governing_law"),

        # ---- Contract analysis ----
        "parties": doc_intel.get("parties") or [],
        "effective_date": doc_intel.get("effective_date"),
        "expiration_date": doc_intel.get("expiration_date"),
        "document_intelligence": doc_intel,
        "clauses": clauses,
        "obligations": rj.get("obligations") or [],
        "deadlines": rj.get("deadlines") or [],
        "penalties": rj.get("penalties") or [],

        # ---- Compliance findings ----
        "compliance_score_value": compliance.get("compliance_score", 0),
        "missing_clauses": compliance.get("missing_clauses") or [],
        "compliance_issues": compliance_issues,

        # ---- Risk assessment / high-risk clauses ----
        "risks": risks,
        "risk_flags": risk_flags,
        "high_risk_flags": high_risk_flags,
        "red_flag_severity": rj.get("red_flag_severity") or "Low",

        # ---- Contract comparison (only populated in comparison mode) ----
        "comparison": comparison,

        # ---- Unified findings + recommendations (JSON export shape) ----
        "findings": findings,
        "recommendations": recommendations,

        # ---- Evidence & sources ----
        "sources": sources,
        "evidence": evidence_refs,

        # ---- Raw narrative report (used for the on-screen dossier view) ----
        "report_markdown": report.report_markdown or "",
    }


def _build_findings(compliance_issues: list[dict], risk_flags: list[dict]) -> list[dict]:
    """Unifies compliance issues and red flags into one findings list,
    each tagged with its origin, for the JSON export / findings table."""
    findings = []
    for issue in compliance_issues:
        findings.append({
            "type": "compliance",
            "title": issue.get("issue", ""),
            "severity": issue.get("severity", "Low"),
            "evidence": issue.get("evidence") or [],
        })
    for flag in risk_flags:
        findings.append({
            "type": "red_flag",
            "title": flag.get("flag_type", ""),
            "severity": flag.get("severity", "Low"),
            "explanation": flag.get("explanation", ""),
            "evidence": flag.get("evidence") or [],
        })
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.get("severity", "Low"), 0), reverse=True)
    return findings


def _extract_recommendations(report_markdown: str) -> list[str]:
    """Pulls the bullet list out of the deterministic report's
    '## Recommended Review Areas' section. Falls back to an empty list
    if the section isn't present (e.g. malformed/legacy report)."""
    if not report_markdown or RECOMMENDATIONS_HEADER not in report_markdown:
        return []

    start = report_markdown.index(RECOMMENDATIONS_HEADER) + len(RECOMMENDATIONS_HEADER)
    rest = report_markdown[start:]
    next_match = NEXT_SECTION_PATTERN.search(rest)
    section = rest[:next_match.start()] if next_match else rest

    return [
        line.strip().lstrip("-").strip()
        for line in section.splitlines()
        if line.strip().startswith("-")
    ]
