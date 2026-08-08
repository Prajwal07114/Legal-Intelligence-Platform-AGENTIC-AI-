"""
Agent 4 — Legal Risk Assessment Agent

Responsibility: analyze extracted clauses to flag risky provisions and
missing protections. This agent explicitly does NOT provide legal advice —
it only surfaces observations with a severity rating for a human (or a
licensed attorney) to review.

Phase 2 update: this agent now also acts as the final risk-level
AGGREGATOR — it deterministically combines its own LLM-derived "risks"
with Agent 8's typed `risk_flags` and Agent 7's `compliance_issues`
severities, so `overall_risk_level` reflects the single most severe
finding across the whole pipeline (not just clause-level risks).
"""
import json
import logging

from app.agents.state import LegalAnalysisState
from app.utils.llm_client import chat_completion_json
from app.utils.prompts import RISK_SYSTEM_PROMPT, RISK_USER_TEMPLATE

logger = logging.getLogger(__name__)

VALID_LEVELS = ["Low", "Moderate", "High", "Critical"]


def risk_node(state: LegalAnalysisState) -> dict:
    clauses = state.get("clauses", [])
    errors = list(state.get("errors", []))

    risks: list[dict] = []
    if clauses:
        result = chat_completion_json(
            system_prompt=RISK_SYSTEM_PROMPT,
            user_prompt=RISK_USER_TEMPLATE.format(
                clauses_json=json.dumps(clauses, indent=2)[:6000],
                obligations=state.get("obligations", []),
                penalties=state.get("penalties", []),
            ),
        )
        risks = result.get("risks") or [] if result else []
        if not result:
            errors.append("Risk assessment returned no structured data.")

    # ---- Deterministic aggregation across all Phase 2 severity sources ----
    overall = _aggregate_overall_severity(
        risks=risks,
        risk_flags=state.get("risk_flags", []),
        red_flag_severity=state.get("red_flag_severity"),
        compliance_issues=(state.get("compliance_results") or {}).get("compliance_issues", []),
    )

    return {
        "risks": risks,
        "overall_risk_level": overall,
        "errors": errors,
    }


def _aggregate_overall_severity(
    risks: list[dict],
    risk_flags: list[dict],
    red_flag_severity: str | None,
    compliance_issues: list[dict],
) -> str:
    """Take the single highest severity across every severity-bearing
    finding in the pipeline (Agent 4's own risks, Agent 8's red flags,
    Agent 7's compliance issues). Purely deterministic — no LLM call."""
    order = {level: i for i, level in enumerate(VALID_LEVELS)}
    candidates: list[str] = []

    candidates += [r.get("risk_level") for r in risks if r.get("risk_level") in order]
    candidates += [f.get("severity") for f in risk_flags if f.get("severity") in order]
    candidates += [c.get("severity") for c in compliance_issues if c.get("severity") in order]
    if red_flag_severity in order:
        candidates.append(red_flag_severity)

    if not candidates:
        return "Low"
    return max(candidates, key=lambda lv: order[lv])
