"""
Page 3: Compliance Dashboard — legal audit sheet.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go

from api_client import compliance_check
from session_utils import ensure_session_defaults, document_options
from theme import inject_global_css, eyebrow, section_divider, risk_marker, clause_tag, COLORS
from components import render_download_bar

st.set_page_config(page_title="Compliance Dashboard", page_icon="✅", layout="wide")
inject_global_css()
ensure_session_defaults()

st.markdown(eyebrow("COMPLIANCE AUDIT"), unsafe_allow_html=True)
st.title("Compliance Dashboard")
st.caption("MANDATORY-CLAUSE CHECKLIST · DETERMINISTIC SCORING")

options = document_options()
if not options:
    st.info("No evidence on file. Visit Contract Upload first.")
    st.stop()

labels = list(options.keys())
selected_label = st.selectbox("Document under audit", labels)
selected_doc_id = options[selected_label]

if st.button("Run Compliance Audit", type="primary"):
    with st.spinner("Extracting document intelligence and auditing compliance..."):
        try:
            st.session_state.last_compliance_result = compliance_check(selected_doc_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Audit failed: {exc}")
            st.session_state.last_compliance_result = None

result = st.session_state.get("last_compliance_result")
if result:
    st.markdown(section_divider("AUDIT RESULT"), unsafe_allow_html=True)
    score = result.get("compliance_score", 0)

    col_gauge, col_info = st.columns([1, 2])
    with col_gauge:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "COMPLIANCE SCORE", "font": {"family": "IBM Plex Mono", "size": 13, "color": COLORS["text_muted"]}},
            number={"font": {"family": "IBM Plex Mono", "color": COLORS["gold"]}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": COLORS["text_muted"]},
                "bar": {"color": COLORS["gold"]},
                "bgcolor": COLORS["panel"],
                "bordercolor": "#2A3346",
                "steps": [
                    {"range": [0, 50], "color": "#3a1f22"},
                    {"range": [50, 75], "color": "#3a2f18"},
                    {"range": [75, 100], "color": "#1c2e20"},
                ],
            },
        ))
        fig.update_layout(
            height=280, margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor="rgba(0,0,0,0)", font={"color": COLORS["text"]},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.markdown(f"CASE ID: `{result.get('compliance_id')}`")
        st.markdown(f"DOCUMENT: `{result.get('document_id')}`")
        if score >= 75:
            st.markdown(clause_tag("compliance", "AUDIT PASSED — MOST MANDATORY CLAUSES ON FILE"), unsafe_allow_html=True)
        elif score >= 50:
            st.markdown(clause_tag("modified", "AUDIT FLAGGED — SEVERAL CLAUSES MISSING"), unsafe_allow_html=True)
        else:
            st.markdown(clause_tag("risk", "AUDIT FAILED — MAJOR PROTECTIONS MISSING"), unsafe_allow_html=True)

    st.markdown(section_divider("MISSING CLAUSE REGISTER"), unsafe_allow_html=True)
    missing = result.get("missing_clauses", [])
    if missing:
        for m in missing:
            st.markdown(clause_tag("missing", m), unsafe_allow_html=True)
    else:
        st.markdown(clause_tag("compliance", "NO MISSING CLAUSES"), unsafe_allow_html=True)

    st.markdown(section_divider("COMPLIANCE ISSUES — AUDIT SHEET"), unsafe_allow_html=True)
    issues = result.get("compliance_issues", [])
    if issues:
        rows = "".join(
            f'<tr><td>{i.get("issue")}</td><td>{risk_marker(i.get("severity","Low"))}</td>'
            f'<td>{"; ".join(ev.get("label","") for ev in (i.get("evidence") or []))}</td></tr>'
            for i in issues
        )
        st.markdown(
            f'<table class="li-matrix"><tr><th>Issue</th><th>Severity</th><th>Evidence</th></tr>{rows}</table>',
            unsafe_allow_html=True,
        )
    else:
        st.write("_No compliance issues identified._")

    st.markdown(section_divider("EXPORT"), unsafe_allow_html=True)
    render_download_bar(str(result.get("report_id")) if result.get("report_id") else None, key_prefix="compliance")
