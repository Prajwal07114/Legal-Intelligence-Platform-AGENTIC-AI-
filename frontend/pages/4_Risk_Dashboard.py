"""
Page 4: Risk Dashboard — investigation risk center.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import risk_analysis
from session_utils import ensure_session_defaults, document_options
from theme import inject_global_css, eyebrow, section_divider, risk_marker, metrics_header, COLORS
from components import render_download_bar

st.set_page_config(page_title="Risk Dashboard", page_icon="⚠", layout="wide")
inject_global_css()
ensure_session_defaults()

st.markdown(eyebrow("RISK CENTER"), unsafe_allow_html=True)
st.title("Risk Dashboard")
st.caption("NAMED RISK PATTERNS · EVIDENCE-BACKED · RANKED BY SEVERITY")

SEVERITY_ORDER = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}

options = document_options()
if not options:
    st.info("No evidence on file. Visit Contract Upload first.")
    st.stop()

labels = list(options.keys())
selected_label = st.selectbox("Document under investigation", labels)
selected_doc_id = options[selected_label]

if st.button("Run Risk Investigation", type="primary"):
    with st.spinner("Extracting document intelligence and detecting red flags..."):
        try:
            st.session_state.last_risk_result = risk_analysis(selected_doc_id)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Risk investigation failed: {exc}")
            st.session_state.last_risk_result = None

result = st.session_state.get("last_risk_result")
if result:
    st.markdown(section_divider("CASE SUMMARY"), unsafe_allow_html=True)
    severity = result.get("severity", "Low")
    overall = result.get("overall_risk_level", "Low")
    flags = result.get("risk_flags", [])

    st.markdown(metrics_header([
        ("Highest Flag Severity", severity),
        ("Overall Case Risk", overall),
        ("Red Flags Logged", len(flags)),
    ]), unsafe_allow_html=True)

    st.markdown(section_divider("EVIDENCE MARKERS"), unsafe_allow_html=True)
    if not flags:
        st.markdown(risk_marker("Low") + " &nbsp; No red flags detected for this contract.", unsafe_allow_html=True)
    else:
        sorted_flags = sorted(flags, key=lambda f: SEVERITY_ORDER.get(f.get("severity", "Low"), 0), reverse=True)
        cards_html = ""
        for f in sorted_flags:
            evidence_html = "".join(
                f'<div style="font-size:0.75rem; color:{COLORS["evidence"]}; font-family:\'IBM Plex Mono\',monospace; margin-top:0.2rem;">'
                f'EVIDENCE: {ev.get("label")}' + (f' — "{ev["quote"]}"' if ev.get("quote") else "") + '</div>'
                for ev in (f.get("evidence") or [])
            )
            border_color = COLORS["critical"] if f.get("severity") in ("High", "Critical") else COLORS["warning"]
            cards_html += (
                f'<div class="li-panel" style="border-left-color:{border_color}; margin-bottom:0;">'
                f'{risk_marker(f.get("severity", "Low"))}'
                f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:1rem; margin-top:0.4rem; color:{COLORS["text"]};">{f.get("flag_type")}</div>'
                f'<p style="font-size:0.85rem; color:{COLORS["text_muted"]}; margin-top:0.3rem;">{f.get("explanation", "")}</p>'
                f'{evidence_html}'
                f'</div>'
            )
        # Rendered as ONE grid container so the CSS auto-fit rule
        # (repeat(auto-fit, minmax(320px, 1fr))) actually applies —
        # separate st.markdown() calls per card would each become an
        # isolated block and never lay out as a grid together.
        st.markdown(f'<div class="li-grid">{cards_html}</div>', unsafe_allow_html=True)

    st.markdown(section_divider("EXPORT"), unsafe_allow_html=True)
    render_download_bar(str(result.get("report_id")) if result.get("report_id") else None, key_prefix="risk")

    st.caption("OBSERVATIONS ONLY — THIS IS NOT LEGAL ADVICE.")
