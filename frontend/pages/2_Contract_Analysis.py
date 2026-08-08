"""
Page 2: Contract Analysis — enterprise investigation workspace.

Layout: LEFT = Document Intelligence, CENTER = Clause / Obligation
register + full dossier, RIGHT = Compliance + Risk + Evidence. Full
browser width, no fixed/centered container.
"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import analyze_document, ask
from session_utils import ensure_session_defaults, document_options
from theme import (
    inject_global_css, eyebrow, section_divider, risk_marker, clause_tag,
    render_dossier, metrics_header, agent_timeline, evidence_item, COLORS,
)
from components import render_download_bar

st.set_page_config(page_title="Contract Analysis", page_icon="🔎", layout="wide")
inject_global_css()
ensure_session_defaults()

st.markdown(eyebrow("CASE FILE ANALYSIS"), unsafe_allow_html=True)
st.title("Contract Analysis")

options = document_options()
use_document = False
selected_doc_id = None

query_col, toggle_col = st.columns([4, 1])
with query_col:
    if options:
        selected_label = st.selectbox("Evidence under review", list(options.keys()), index=0)
        selected_doc_id = options[selected_label]
    else:
        st.info(
            "No evidence on file — this runs as a general research inquiry. "
            "File a contract on Contract Upload for full extraction, compliance, and risk review."
        )
with toggle_col:
    if options:
        use_document = st.checkbox("Ground in document", value=True)

query = st.text_area(
    "Investigation query",
    placeholder="e.g. Review this contract for termination and liability risks",
    height=90,
)

run_clicked = st.button("Open Investigation", type="primary", disabled=not query.strip())

if run_clicked:
    with st.spinner("Working the case - Intake to Research to Document Intelligence to Compliance to Red Flag to Risk to Report..."):
        try:
            if use_document and selected_doc_id:
                result = analyze_document(query, document_id=selected_doc_id)
            else:
                result = ask(query)
            st.session_state.last_result = result
            st.session_state.last_result_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Investigation failed: {exc}")
            st.session_state.last_result = None

result = st.session_state.get("last_result")
if result:
    doc_intel = result.get("document_intelligence") or {}
    compliance = result.get("compliance_results") or {}
    flags = result.get("risk_flags") or []
    high_flags = [f for f in flags if f.get("severity") in ("High", "Critical")]

    st.markdown(section_divider("CASE METRICS"), unsafe_allow_html=True)
    st.markdown(metrics_header([
        ("Clauses Extracted", len(result.get("clauses", []))),
        ("High Risk Clauses", len(high_flags)),
        ("Compliance Score", f"{compliance.get('compliance_score', '—')}/100" if compliance else "—"),
        ("Risk Level", result.get("overall_risk_level", "Low")),
        ("Jurisdiction", doc_intel.get("jurisdiction") or "—"),
    ]), unsafe_allow_html=True)

    st.markdown(section_divider("INVESTIGATION WORKSPACE"), unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 1.3, 1])

    with col_left:
        st.markdown(eyebrow("DOCUMENT INTELLIGENCE"), unsafe_allow_html=True)
        if not doc_intel:
            st.markdown('<div class="li-panel">No document intelligence extracted.</div>', unsafe_allow_html=True)
        else:
            parties_html = "".join(
                f'<div style="font-size:0.82rem; padding:0.15rem 0;">&bull; {p.get("name","")} '
                f'<span style="color:{COLORS["text_muted"]};">({p.get("role","n/a")})</span></div>'
                if isinstance(p, dict) else f'<div style="font-size:0.82rem;">&bull; {p}</div>'
                for p in doc_intel.get("parties", [])
            ) or f'<div style="color:{COLORS["text_muted"]}; font-size:0.82rem;">No parties identified</div>'
            st.markdown(
                f"""
                <div class="li-panel">
                {eyebrow("PARTIES")}
                {parties_html}
                <div style="margin-top:0.6rem; font-size:0.8rem;"><b>Effective:</b> {doc_intel.get('effective_date') or '—'}</div>
                <div style="font-size:0.8rem;"><b>Expires:</b> {doc_intel.get('expiration_date') or '—'}</div>
                <div style="font-size:0.8rem;"><b>Governing law:</b> {doc_intel.get('governing_law') or '—'}</div>
                <div style="font-size:0.8rem;"><b>Jurisdiction:</b> {doc_intel.get('jurisdiction') or '—'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(eyebrow("CLAUSE REGISTER"), unsafe_allow_html=True)
            for key, label in [
                ("payment_terms", "Payment Terms"), ("confidentiality_clause", "Confidentiality"),
                ("liability_clause", "Liability"), ("indemnity_clause", "Indemnity"),
                ("termination_clause", "Termination"),
            ]:
                detail = doc_intel.get(key, {}) or {}
                kind = "compliance" if detail.get("present") else "missing"
                tag_label = f"{label} — {'ON FILE' if detail.get('present') else 'NOT FOUND'}"
                st.markdown(clause_tag(kind, tag_label), unsafe_allow_html=True)
                if detail.get("present") and detail.get("summary"):
                    st.caption(detail["summary"])

        st.markdown(eyebrow("AGENT EXECUTION TIMELINE"), unsafe_allow_html=True)
        ts = st.session_state.get("last_result_timestamp", "")
        stages = [
            ("Case Intake", ts), ("Legal Research", ts), ("Document Intelligence", ts),
            ("Compliance Review", ts), ("Red Flag Detection", ts), ("Risk Assessment", ts),
            ("Legal Report", ts),
        ]
        st.markdown(agent_timeline(stages), unsafe_allow_html=True)

    with col_center:
        st.markdown(eyebrow("CLAUSE & OBLIGATION ANALYSIS"), unsafe_allow_html=True)
        col_o, col_d, col_p = st.columns(3)
        with col_o:
            st.markdown('<div class="li-eyebrow">OBLIGATIONS</div>', unsafe_allow_html=True)
            for o in result.get("obligations", []) or ["—"]:
                st.markdown(f'<div style="font-size:0.78rem; padding:0.1rem 0;">&bull; {o}</div>', unsafe_allow_html=True)
        with col_d:
            st.markdown('<div class="li-eyebrow">DEADLINES</div>', unsafe_allow_html=True)
            for d in result.get("deadlines", []) or ["—"]:
                st.markdown(f'<div style="font-size:0.78rem; padding:0.1rem 0;">&bull; {d}</div>', unsafe_allow_html=True)
        with col_p:
            st.markdown('<div class="li-eyebrow">PENALTIES</div>', unsafe_allow_html=True)
            for p in result.get("penalties", []) or ["—"]:
                st.markdown(f'<div style="font-size:0.78rem; padding:0.1rem 0;">&bull; {p}</div>', unsafe_allow_html=True)

        st.markdown(eyebrow("CASE DOSSIER"), unsafe_allow_html=True)
        st.markdown(
            render_dossier(result.get("report_markdown", "_No report generated._"), case_id=result.get("report_id", "")),
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(eyebrow("RISK & COMPLIANCE"), unsafe_allow_html=True)
        st.markdown(risk_marker(result.get("overall_risk_level", "Low")), unsafe_allow_html=True)

        if compliance:
            st.markdown(f'<div class="li-panel">{eyebrow("COMPLIANCE")}'
                        f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:1.4rem; color:{COLORS["gold"]};">'
                        f'{compliance.get("compliance_score", 0)}/100</div></div>', unsafe_allow_html=True)
            for issue in compliance.get("compliance_issues", []) or []:
                st.markdown(risk_marker(issue.get("severity", "Low")) + f" &nbsp; {issue.get('issue')}", unsafe_allow_html=True)

        st.markdown(eyebrow("RED FLAGS"), unsafe_allow_html=True)
        if flags:
            for f in flags:
                st.markdown(
                    f'<div class="li-panel" style="border-left-color:{COLORS["critical"]};">'
                    f'{risk_marker(f.get("severity","Low"))}<br/>'
                    f'<b style="font-family:\'IBM Plex Mono\',monospace; font-size:0.82rem;">{f.get("flag_type")}</b>'
                    f'<p style="font-size:0.78rem; color:{COLORS["text_muted"]};">{f.get("explanation","")}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div class="li-panel">No red flags detected.</div>', unsafe_allow_html=True)

        st.markdown(eyebrow("EVIDENCE / CITATIONS"), unsafe_allow_html=True)
        evidence_refs = result.get("evidence_references") or []
        sources = result.get("sources") or []
        if evidence_refs:
            for ev in evidence_refs[:12]:
                st.markdown(evidence_item(ev.get("label", ""), ev.get("source", ""), ev.get("quote")), unsafe_allow_html=True)
        elif sources:
            for s in sources[:8]:
                st.markdown(evidence_item(s.get("source_name", ""), s.get("source_type", ""), None, s.get("score")), unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#A0A8B5; font-size:0.8rem;">No evidence recorded.</div>', unsafe_allow_html=True)

    st.markdown(section_divider("EXPORT"), unsafe_allow_html=True)
    render_download_bar(result.get("report_id"), key_prefix="analysis")

    st.caption("STANDING ORDER: AI-generated analysis — not a substitute for professional legal advice.")
