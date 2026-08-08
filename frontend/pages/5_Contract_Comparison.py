"""
Page 5: Contract Comparison — legal redline review.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import compare_contracts
from session_utils import ensure_session_defaults, document_options
from theme import inject_global_css, eyebrow, section_divider, risk_marker, render_dossier, COLORS
from components import render_download_bar

st.set_page_config(page_title="Contract Comparison", page_icon="⇄", layout="wide")
inject_global_css()
ensure_session_defaults()

st.markdown(eyebrow("REDLINE REVIEW"), unsafe_allow_html=True)
st.title("Contract Comparison")
st.caption("CONTRACT A vs. CONTRACT B · ADDED / REMOVED / MODIFIED CLAUSES")

options = document_options()
if len(options) < 2:
    st.info("File at least two contracts on Contract Upload to open a comparison.")
    st.stop()

labels = list(options.keys())
col_a, col_b = st.columns(2)
with col_a:
    label_a = st.selectbox("Contract A — baseline", labels, index=0, key="cmp_a")
with col_b:
    default_b = 1 if len(labels) > 1 else 0
    label_b = st.selectbox("Contract B — comparison target", labels, index=default_b, key="cmp_b")

query = st.text_input(
    "Comparison context",
    value="Compare these two contracts and highlight material differences",
)

run_clicked = st.button("Open Redline", type="primary", disabled=(label_a == label_b))
if label_a == label_b:
    st.warning("Select two different documents to compare.")

if run_clicked:
    with st.spinner("Extracting both contracts and computing the redline..."):
        try:
            st.session_state.last_comparison_result = compare_contracts(query, options[label_a], options[label_b])
        except Exception as exc:  # noqa: BLE001
            st.error(f"Comparison failed: {exc}")
            st.session_state.last_comparison_result = None

result = st.session_state.get("last_comparison_result")
if result:
    st.markdown(section_divider("CASE SUMMARY"), unsafe_allow_html=True)
    st.write(result.get("summary", ""))

    overall = result.get("overall_risk_level", "Low")
    compliance = result.get("compliance_results") or {}
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(eyebrow("OVERALL RISK — CONTRACT B"), unsafe_allow_html=True)
        st.markdown(risk_marker(overall), unsafe_allow_html=True)
    with col2:
        st.metric("Compliance Score — Contract B", f"{compliance.get('compliance_score', '—')}/100" if compliance else "—")

    st.markdown(section_divider("REDLINE — CONTRACT A vs. CONTRACT B"), unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(f'<div class="li-eyebrow">CONTRACT A — {label_a.split(" (")[0]}</div>', unsafe_allow_html=True)
        removed = result.get("removed_clauses", []) or []
        modified = result.get("modified_clauses", []) or []
        html = ""
        for c in removed:
            html += f'<div class="li-redline-removed">− {c.get("clause_title")}<br/><span style="color:{COLORS["text_muted"]};">{c.get("detail","")}</span></div>'
        for c in modified:
            html += f'<div class="li-redline-modified">± {c.get("clause_title")} <i>(prior version)</i></div>'
        st.markdown(f'<div class="li-redline-col">{html or "<span style=\'color:#A0A8B5;\'>No removed or prior-version clauses.</span>"}</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown(f'<div class="li-eyebrow">CONTRACT B — {label_b.split(" (")[0]}</div>', unsafe_allow_html=True)
        added = result.get("added_clauses", []) or []
        html = ""
        for c in added:
            html += f'<div class="li-redline-added">+ {c.get("clause_title")}<br/><span style="color:{COLORS["text_muted"]};">{c.get("detail","")}</span></div>'
        for c in modified:
            html += f'<div class="li-redline-modified">± {c.get("clause_title")}<br/><span style="color:{COLORS["text_muted"]};">{c.get("detail","")}</span></div>'
        st.markdown(f'<div class="li-redline-col">{html or "<span style=\'color:#A0A8B5;\'>No added or modified clauses.</span>"}</div>', unsafe_allow_html=True)

    with st.expander("FULL CASE DOSSIER"):
        st.markdown(
            render_dossier(result.get("report_markdown", "_No report generated._"), case_id=result.get("comparison_id", "")),
            unsafe_allow_html=True,
        )

    st.markdown(section_divider("EXPORT"), unsafe_allow_html=True)
    render_download_bar(str(result.get("report_id")) if result.get("report_id") else None, key_prefix="comparison")
