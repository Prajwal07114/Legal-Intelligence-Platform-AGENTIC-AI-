"""
Deterministic report renderer — Phase 2.

Per the project spec, the Report Generation Agent assembles the final
report using Python templates rather than another LLM call — this
keeps the final report fast, cheap, and 100% consistent in structure.

Phase 2 section order:
  Executive Summary
  Contract Overview
  Extracted Legal Intelligence
  Compliance Assessment
  Red Flag Analysis
  Risk Assessment
  Evidence & Citations
  Contract Comparison (if applicable)
  Recommended Review Areas
  Disclaimer

All Phase 1 data (clauses, obligations, deadlines, penalties, sources,
risks) is still rendered — folded into "Extracted Legal Intelligence"
and "Risk Assessment" — so no information from the original report is
lost, only reorganized under the richer Phase 2 structure.
"""
from app.agents.state import LegalAnalysisState

RISK_BADGE = {
    "Low": "🟢 LOW",
    "Moderate": "🟡 MODERATE",
    "High": "🟠 HIGH",
    "Critical": "🔴 CRITICAL",
}

DISCLAIMER = (
    "This report is AI-generated and is not a substitute for professional "
    "legal advice. Consult a licensed attorney before making decisions "
    "based on this analysis."
)


def render_report_markdown(state: LegalAnalysisState, evidence_references: list[dict] | None = None) -> str:
    evidence_references = evidence_references or []

    query = state.get("query", "")
    task_type = state.get("task_type", "Legal Research")
    topics = state.get("topics", [])
    sources = state.get("sources", [])
    clauses = state.get("clauses", [])
    obligations = state.get("obligations", [])
    deadlines = state.get("deadlines", [])
    penalties = state.get("penalties", [])
    risks = state.get("risks", [])
    overall_risk = state.get("overall_risk_level", "Low")

    doc_intel = state.get("document_intelligence") or {}
    compliance = state.get("compliance_results") or {}
    risk_flags = state.get("risk_flags", [])
    red_flag_severity = state.get("red_flag_severity", "Low")
    comparison = state.get("comparison_results") or {}
    is_comparison = state.get("workflow_mode") == "comparison"

    lines: list[str] = []
    lines.append("# Legal Intelligence Report\n")

    # ---------------- Executive Summary ----------------
    lines.append("## Executive Summary")
    lines.append(_executive_summary(
        task_type=task_type, overall_risk=overall_risk,
        compliance=compliance, risk_flags=risk_flags, is_comparison=is_comparison,
    ))
    lines.append("")

    # ---------------- Contract Overview ----------------
    lines.append("## Contract Overview")
    lines.append(f"- **Task type:** {task_type}")
    lines.append(f"- **User query:** {query}")
    if topics:
        lines.append(f"- **Topics identified:** {', '.join(topics)}")
    lines.append(_contract_overview_fields(doc_intel))
    lines.append("")

    # ---------------- Extracted Legal Intelligence ----------------
    lines.append("## Extracted Legal Intelligence")
    lines.append(_clause_detail_block("Payment Terms", doc_intel.get("payment_terms")))
    lines.append(_clause_detail_block("Confidentiality Clause", doc_intel.get("confidentiality_clause")))
    lines.append(_clause_detail_block("Liability Clause", doc_intel.get("liability_clause")))
    lines.append(_clause_detail_block("Indemnity Clause", doc_intel.get("indemnity_clause")))
    lines.append(_clause_detail_block("Termination Clause", doc_intel.get("termination_clause")))

    if clauses and not doc_intel:
        # Fallback: pure Phase-1-style clause list (e.g. Clause Analysis Agent used standalone)
        lines.append("**Other extracted clauses:**")
        for c in clauses:
            category = f" _{c.get('category')}_" if c.get("category") else ""
            lines.append(f"- **{c.get('title', 'Untitled clause')}**{category}\n  {c.get('text', '')}")

    lines.append("\n**Obligations**")
    lines.append(_bullet_list(obligations, "No obligations identified."))
    lines.append("\n**Deadlines**")
    lines.append(_bullet_list(deadlines, "No deadlines identified."))
    if penalties:
        lines.append("\n**Penalties**")
        lines.append(_bullet_list(penalties, "No penalties identified."))
    lines.append("")

    lines.append("### Relevant Legal References")
    if sources:
        for s in sources:
            score = f" (relevance: {s['score']})" if s.get("score") is not None else ""
            lines.append(f"- **[{s['source_type']}] {s['source_name']}**{score}\n  > {s['snippet']}")
    else:
        lines.append("_No relevant references were retrieved for this query._")
    lines.append("")

    # ---------------- Compliance Assessment ----------------
    lines.append("## Compliance Assessment")
    lines.append(_compliance_section(compliance))
    lines.append("")

    # ---------------- Red Flag Analysis ----------------
    lines.append("## Red Flag Analysis")
    lines.append(_red_flag_section(risk_flags, red_flag_severity))
    lines.append("")

    # ---------------- Risk Assessment ----------------
    lines.append("## Risk Assessment")
    lines.append(f"**Overall risk level:** {RISK_BADGE.get(overall_risk, overall_risk)}\n")
    if risks:
        for r in risks:
            badge = RISK_BADGE.get(r.get("risk_level", ""), r.get("risk_level", ""))
            related = f" (related to: {r['related_clause']})" if r.get("related_clause") else ""
            lines.append(f"- {badge} — {r.get('reason', '')}{related}")
    else:
        lines.append("_No additional clause-level risks flagged beyond the Red Flag Analysis above._")
    lines.append("")

    # ---------------- Evidence & Citations ----------------
    lines.append("## Evidence & Citations")
    lines.append(_evidence_section(evidence_references))
    lines.append("")

    # ---------------- Contract Comparison (if applicable) ----------------
    if is_comparison:
        lines.append("## Contract Comparison")
        lines.append(_comparison_section(comparison))
        lines.append("")

    # ---------------- Recommended Review Areas ----------------
    lines.append("## Recommended Review Areas")
    lines.append(_recommended_review_areas(overall_risk, compliance, risk_flags))
    lines.append("")

    # ---------------- Disclaimer ----------------
    lines.append("## Disclaimer")
    lines.append(f"> {DISCLAIMER}")

    return "\n".join(lines)


# ---------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------

def _executive_summary(task_type, overall_risk, compliance, risk_flags, is_comparison) -> str:
    score = compliance.get("compliance_score")
    score_txt = f"{score}/100" if isinstance(score, int) else "not computed"
    flag_count = len(risk_flags)
    mode_txt = "a contract comparison" if is_comparison else f"a {task_type.lower()}"

    parts = [
        f"This report presents the results of {mode_txt}. "
        f"The overall risk level is **{overall_risk}**, based on "
        f"{flag_count} detected red flag(s) and a compliance score of {score_txt}.",
    ]
    if overall_risk in ("High", "Critical"):
        parts.append("Several findings in this report warrant prompt attention before this agreement is finalized or renewed.")
    else:
        parts.append("No critical structural issues were identified, though the detailed sections below should still be reviewed.")
    return " ".join(parts)


def _contract_overview_fields(doc_intel: dict) -> str:
    if not doc_intel:
        return "- _No document-level metadata available (no document uploaded, or general research query)._"

    lines = []
    parties = doc_intel.get("parties") or []
    if parties:
        party_strs = [f"{p.get('name')}" + (f" ({p['role']})" if p.get("role") else "") for p in parties]
        lines.append(f"- **Parties:** {', '.join(party_strs)}")
    if doc_intel.get("effective_date"):
        lines.append(f"- **Effective date:** {doc_intel['effective_date']}")
    if doc_intel.get("expiration_date"):
        lines.append(f"- **Expiration date:** {doc_intel['expiration_date']}")
    if doc_intel.get("governing_law"):
        lines.append(f"- **Governing law:** {doc_intel['governing_law']}")
    if doc_intel.get("jurisdiction"):
        lines.append(f"- **Jurisdiction:** {doc_intel['jurisdiction']}")
    return "\n".join(lines) if lines else "- _No document-level metadata extracted._"


def _clause_detail_block(title: str, detail: dict | None) -> str:
    detail = detail or {}
    if not detail.get("present"):
        return f"**{title}:** _Not detected in the contract._\n"
    summary = detail.get("summary") or "Present, no summary generated."
    evidence = detail.get("evidence") or []
    ev_txt = ""
    if evidence:
        first = evidence[0]
        ev_txt = f" _(evidence: {first.get('label', 'see source')})_"
    return f"**{title}:** {summary}{ev_txt}\n"


def _compliance_section(compliance: dict) -> str:
    if not compliance:
        return "_Compliance check was not run for this request._"

    score = compliance.get("compliance_score", 0)
    missing = compliance.get("missing_clauses", [])
    issues = compliance.get("compliance_issues", [])

    lines = [f"**Compliance score:** {score}/100"]
    lines.append("\n**Missing clauses:**")
    lines.append(_bullet_list(missing, "None — all mandatory clauses were detected."))

    lines.append("\n**Compliance issues:**")
    if issues:
        for issue in issues:
            badge = RISK_BADGE.get(issue.get("severity", ""), issue.get("severity", ""))
            evidence = issue.get("evidence", [])
            ev_txt = f" _(evidence: {evidence[0].get('label')})_" if evidence else ""
            lines.append(f"- {badge} — {issue.get('issue', '')}{ev_txt}")
    else:
        lines.append("_No compliance issues identified._")

    return "\n".join(lines)


def _red_flag_section(risk_flags: list[dict], severity: str) -> str:
    if not risk_flags:
        return f"**Highest red flag severity:** {RISK_BADGE.get(severity, severity)}\n\n_No red flags detected._"

    lines = [f"**Highest red flag severity:** {RISK_BADGE.get(severity, severity)}\n"]
    for flag in risk_flags:
        badge = RISK_BADGE.get(flag.get("severity", ""), flag.get("severity", ""))
        evidence = flag.get("evidence", [])
        ev_txt = f" _(evidence: {evidence[0].get('label')})_" if evidence else ""
        lines.append(f"- {badge} **{flag.get('flag_type', 'Unknown')}** — {flag.get('explanation', '')}{ev_txt}")
    return "\n".join(lines)


def _evidence_section(evidence_references: list[dict]) -> str:
    if not evidence_references:
        return "_No evidence references were recorded for this analysis._"

    # De-duplicate by (label, source) to keep this section readable.
    seen = set()
    lines = []
    for ev in evidence_references:
        key = (ev.get("label"), ev.get("source"))
        if key in seen:
            continue
        seen.add(key)
        quote = f" — \"{ev['quote']}\"" if ev.get("quote") else ""
        lines.append(f"- **{ev.get('label', 'Evidence')}** _(from {ev.get('source', 'analysis')})_{quote}")
    return "\n".join(lines)


def _comparison_section(comparison: dict) -> str:
    if not comparison:
        return "_Comparison data unavailable._"

    lines = [comparison.get("summary", ""), ""]

    lines.append("**Added clauses:**")
    lines.append(_diff_list(comparison.get("added_clauses", [])))
    lines.append("\n**Removed clauses:**")
    lines.append(_diff_list(comparison.get("removed_clauses", [])))
    lines.append("\n**Modified clauses:**")
    lines.append(_diff_list(comparison.get("modified_clauses", [])))

    return "\n".join(lines)


def _diff_list(items: list[dict]) -> str:
    if not items:
        return "_None._"
    return "\n".join(f"- **{i.get('clause_title', 'Untitled')}** — {i.get('detail', '')}" for i in items)


def _bullet_list(items: list[str], empty_message: str) -> str:
    if not items:
        return f"_{empty_message}_"
    return "\n".join(f"- {item}" for item in items)


def _recommended_review_areas(overall_risk: str, compliance: dict, risk_flags: list[dict]) -> str:
    """Non-advisory, procedural next-steps only — intentionally generic
    so this stays observation-based rather than legal advice."""
    areas = []

    missing = compliance.get("missing_clauses", []) if compliance else []
    if missing:
        areas.append(f"Clarify or add the following missing clauses: {', '.join(missing)}.")

    critical_flags = [f for f in risk_flags if f.get("severity") in ("High", "Critical")]
    if critical_flags:
        flag_names = ", ".join(f.get("flag_type", "") for f in critical_flags)
        areas.append(f"Review the following high-severity red flags closely: {flag_names}.")

    areas.append("Review the flagged clauses and risk items above alongside the full document text.")

    if overall_risk in ("High", "Critical"):
        areas.append("Given the overall risk level, review by a licensed attorney is strongly suggested before signing.")

    return "\n".join(f"- {a}" for a in areas)
