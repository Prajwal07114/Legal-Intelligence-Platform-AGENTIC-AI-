"""
Agent 7 — Compliance Agent (Phase 2)

Responsibility: check the Document Intelligence Agent's structured
extraction against a mandatory-clause checklist, flag missing clauses,
and compute a DETERMINISTIC compliance score in Python (not the LLM) —
so the score is reproducible and never hallucinated. An LLM call is
still used for narrative "compliance_issues" explanations, but those
issues must be grounded in the extraction (enforced by prompt +
defensive post-filtering below).
"""
import logging

from app.agents.state import LegalAnalysisState
from app.utils.llm_client import chat_completion_json
from app.utils.prompts import COMPLIANCE_SYSTEM_PROMPT, COMPLIANCE_USER_TEMPLATE
import json

logger = logging.getLogger(__name__)

# (state key, human label, weight) — weights sum to 100
REQUIRED_CLAUSES = [
    ("confidentiality_clause", "Confidentiality Clause", 15),
    ("termination_clause", "Termination Clause", 20),
    ("liability_clause", "Liability Clause", 15),
    ("indemnity_clause", "Indemnity Clause", 15),
    ("payment_terms", "Payment Terms", 15),
]
# governing_law / jurisdiction are plain strings, not clause-detail objects
REQUIRED_STRING_FIELDS = [
    ("governing_law", "Governing Law Clause", 10),
    ("jurisdiction", "Dispute Resolution / Jurisdiction Clause", 10),
]

VALID_SEVERITIES = {"Low", "Moderate", "High", "Critical"}


def compliance_node(state: LegalAnalysisState) -> dict:
    doc_intel = state.get("document_intelligence") or {}
    errors = list(state.get("errors", []))

    if not doc_intel:
        return {
            "compliance_results": {
                "compliance_score": 0,
                "missing_clauses": [label for _, label, _ in REQUIRED_CLAUSES + REQUIRED_STRING_FIELDS],
                "compliance_issues": [],
            },
            "errors": errors,
        }

    # ---- Deterministic scoring (pure Python, no LLM) ----
    score = 0
    missing_clauses: list[str] = []

    for key, label, weight in REQUIRED_CLAUSES:
        detail = doc_intel.get(key) or {}
        if isinstance(detail, dict) and detail.get("present"):
            score += weight
        else:
            missing_clauses.append(label)

    for key, label, weight in REQUIRED_STRING_FIELDS:
        value = doc_intel.get(key)
        if value:
            score += weight
        else:
            missing_clauses.append(label)

    score = max(0, min(100, score))

    # ---- LLM call for narrative issue explanations (evidence-grounded) ----
    raw_result = chat_completion_json(
        system_prompt=COMPLIANCE_SYSTEM_PROMPT,
        user_prompt=COMPLIANCE_USER_TEMPLATE.format(
            document_intelligence_json=json.dumps(doc_intel, indent=2)[:6000],
        ),
    )

    llm_issues = raw_result.get("compliance_issues", []) if isinstance(raw_result, dict) else []
    compliance_issues = _sanitize_issues(llm_issues)

    # Deterministically append one issue per missing clause too, so the
    # issue list is never solely dependent on the LLM call succeeding.
    existing_issue_texts = {i["issue"].lower() for i in compliance_issues}
    for label in missing_clauses:
        issue_text = f"Missing {label}"
        if issue_text.lower() not in existing_issue_texts:
            compliance_issues.append({
                "issue": issue_text,
                "severity": "High" if label in ("Termination Clause", "Liability Clause") else "Moderate",
                "evidence": [{
                    "label": "Document Intelligence extraction",
                    "quote": f"No {label.lower()} detected in contract text",
                    "source": "compliance_agent",
                }],
            })

    if not raw_result:
        errors.append("Compliance Agent LLM call returned no data — falling back to deterministic-only issues.")

    return {
        "compliance_results": {
            "compliance_score": score,
            "missing_clauses": missing_clauses,
            "compliance_issues": compliance_issues,
        },
        "errors": errors,
    }


def _sanitize_issues(raw_issues: object) -> list[dict]:
    """Defensively normalize LLM-returned compliance issues; drop
    anything malformed rather than crash."""
    if not isinstance(raw_issues, list):
        return []

    sanitized = []
    for item in raw_issues:
        if not isinstance(item, dict) or not item.get("issue"):
            continue
        severity = item.get("severity", "Moderate")
        if severity not in VALID_SEVERITIES:
            severity = "Moderate"

        evidence = []
        for ev in item.get("evidence", []) or []:
            if isinstance(ev, dict):
                evidence.append({
                    "label": str(ev.get("label", "Evidence")),
                    "quote": ev.get("quote") if isinstance(ev.get("quote"), str) else None,
                    "source": "compliance_agent",
                })

        sanitized.append({
            "issue": str(item["issue"]),
            "severity": severity,
            "evidence": evidence,
        })
    return sanitized
