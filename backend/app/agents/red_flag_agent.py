"""
Agent 8 — Red Flag Detection Agent (Phase 2)

Dedicated legal risk intelligence agent. Detects specific named risk
patterns (unlimited liability, one-sided termination, excessive
penalties, ambiguous obligations, missing protections, broad
indemnification, weak confidentiality) in the extracted document
intelligence + compliance findings, with an explanation and evidence
for every flag.

This agent is distinct from Agent 4 (Legal Risk Assessment) which
Phase 1 kept for overall risk-level scoring — Agent 8 produces the
granular, typed "red flags" list; Agent 4 consumes it (alongside
clauses) to set the final overall_risk_level.
"""
import json
import logging

from app.agents.state import LegalAnalysisState
from app.utils.llm_client import chat_completion_json
from app.utils.prompts import RED_FLAG_SYSTEM_PROMPT, RED_FLAG_USER_TEMPLATE

logger = logging.getLogger(__name__)

VALID_SEVERITIES = ["Low", "Moderate", "High", "Critical"]
KNOWN_FLAG_TYPES = {
    "Unlimited Liability",
    "One-Sided Termination",
    "Excessive Penalties",
    "Ambiguous Obligations",
    "Missing Protections",
    "Broad Indemnification",
    "Weak Confidentiality Protection",
}


def red_flag_node(state: LegalAnalysisState) -> dict:
    doc_intel = state.get("document_intelligence") or {}
    compliance_results = state.get("compliance_results") or {}
    errors = list(state.get("errors", []))

    if not doc_intel:
        return {"risk_flags": [], "red_flag_severity": "Low", "errors": errors}

    raw_result = chat_completion_json(
        system_prompt=RED_FLAG_SYSTEM_PROMPT,
        user_prompt=RED_FLAG_USER_TEMPLATE.format(
            document_intelligence_json=json.dumps(doc_intel, indent=2)[:6000],
            compliance_issues_json=json.dumps(
                compliance_results.get("compliance_issues", []), indent=2
            )[:2000],
        ),
    )

    if not raw_result:
        errors.append("Red Flag Detection Agent returned no structured data.")

    flags = _sanitize_flags(raw_result.get("risk_flags") if isinstance(raw_result, dict) else None)
    top_severity = raw_result.get("severity") if isinstance(raw_result, dict) else None

    if top_severity not in VALID_SEVERITIES:
        top_severity = _derive_severity(flags)

    return {
        "risk_flags": flags,
        "red_flag_severity": top_severity,
        "errors": errors,
    }


def _sanitize_flags(raw_flags: object) -> list[dict]:
    if not isinstance(raw_flags, list):
        return []

    sanitized = []
    for item in raw_flags:
        if not isinstance(item, dict) or not item.get("flag_type"):
            continue

        flag_type = str(item["flag_type"])
        severity = item.get("severity", "Moderate")
        if severity not in VALID_SEVERITIES:
            severity = "Moderate"

        evidence = []
        for ev in item.get("evidence", []) or []:
            if isinstance(ev, dict):
                evidence.append({
                    "label": str(ev.get("label", "Evidence")),
                    "quote": ev.get("quote") if isinstance(ev.get("quote"), str) else None,
                    "source": "red_flag_agent",
                })

        sanitized.append({
            "flag_type": flag_type,
            "severity": severity,
            "explanation": str(item.get("explanation", "")),
            "evidence": evidence,
        })
    return sanitized


def _derive_severity(flags: list[dict]) -> str:
    order = {level: i for i, level in enumerate(VALID_SEVERITIES)}
    levels = [f.get("severity") for f in flags if f.get("severity") in order]
    if not levels:
        return "Low"
    return max(levels, key=lambda lv: order[lv])
