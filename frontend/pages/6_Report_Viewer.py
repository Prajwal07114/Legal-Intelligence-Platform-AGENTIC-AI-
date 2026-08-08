"""
Page 6: Report Viewer — enterprise report workspace.

Layout: LEFT = Report Navigation (record type + ID lookup),
CENTER = Report Content (dossier), RIGHT = Evidence / Citations.
Full browser width, no fixed/centered container.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import get_report, get_compliance_report, get_risk_report, get_comparison_report
from theme import inject_global_css, eyebrow, section_divider, risk_marker, render_dossier, evidence_item, COLORS
from components import render_download_bar

st.set_page_config(page_title="Report Viewer", page_icon="🗂", layout="wide")
inject_global_css()

st.markdown(eyebrow("CASE FILE ARCHIVE"), unsafe_allow_html=True)
st.title("Report Viewer")
st.caption("RETRIEVE A CLOSED CASE FILE BY ITS RECORD ID")

RECORD_TYPES = ["Full Report", "Compliance Record", "Risk Record", "Comparison Record"]

col_nav, col_content, col_evidence = st.columns([0.9, 2.2, 1])

# ---------------- LEFT: Report Navigation ----------------
with col_nav:
    st.markdown(eyebrow("REPORT NAVIGATION"), unsafe_allow_html=True)
    record_type = st.radio("Record type", RECORD_TYPES, label_visibility="collapsed")
    record_id = st.text_input("Record ID", placeholder="e.g. 3fa85f64-5717-4562-...")
    fetch_clicked = st.button("Retrieve Case File", type="primary", disabled=not record_id.strip())

    if fetch_clicked:
        rid = record_id.strip()
        try:
            with st.spinner("Retrieving case file..."):
                if record_type == "Full Report":
                    st.session_state.viewer_record = ("report", get_report(rid))
                elif record_type == "Compliance Record":
                    st.session_state.viewer_record = ("compliance", get_compliance_report(rid))
                elif record_type == "Risk Record":
                    st.session_state.viewer_record = ("risk", get_risk_report(rid))
                else:
                    st.session_state.viewer_record = ("comparison", get_comparison_report(rid))
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not retrieve record: {exc}")
            st.session_state.viewer_record = None

    st.markdown(section_divider("RECENT LOOKUPS"), unsafe_allow_html=True)
    kind_labels = {"report": "Full Report", "compliance": "Compliance", "risk": "Risk", "comparison": "Comparison"}
    current = st.session_state.get("viewer_record")
    if current:
        kind, _ = current
        st.markdown(
            f'<div class="li-panel" style="border-left-color:{COLORS["gold"]};">'
            f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.78rem;">{kind_labels.get(kind, kind)}</div>'
            f'<div style="font-size:0.7rem; color:{COLORS["text_muted"]};">Currently open</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div style="color:#A0A8B5; font-size:0.8rem;">No record open.</div>', unsafe_allow_html=True)

record = st.session_state.get("viewer_record")

# ---------------- CENTER: Report Content ----------------
with col_content:
    st.markdown(eyebrow("REPORT CONTENT"), unsafe_allow_html=True)

    if not record:
        st.markdown('<div class="li-panel">Select a record type, enter its ID, and retrieve to view the case file here.</div>', unsafe_allow_html=True)
    else:
        kind, data = record

        if kind == "report":
            col1, col2, col3 = st.columns(3)
            col1.metric("Task Type", data.get("task_type", "—"))
            with col2:
                st.markdown(eyebrow("RISK LEVEL"), unsafe_allow_html=True)
                st.markdown(risk_marker(data.get("risk_level", "Low")), unsafe_allow_html=True)
            col3.metric("Filed", (data.get("created_at", "—") or "—")[:19])
            st.markdown(
                render_dossier(data.get("report_markdown", "_No content._"), case_id=data.get("id", "")),
                unsafe_allow_html=True,
            )
            st.markdown(section_divider("EXPORT"), unsafe_allow_html=True)
            render_download_bar(str(data.get("id")), key_prefix="viewer_report")

        elif kind == "compliance":
            st.metric("Compliance Score", f"{data.get('compliance_score', 0)}/100")
            st.markdown(eyebrow("MISSING CLAUSES"), unsafe_allow_html=True)
            for m in data.get("missing_clauses", []) or ["—"]:
                st.write(f"- {m}")
            st.markdown(eyebrow("COMPLIANCE ISSUES"), unsafe_allow_html=True)
            for issue in data.get("compliance_issues", []) or []:
                st.markdown(risk_marker(issue.get("severity", "Low")) + f" &nbsp; {issue.get('issue')}", unsafe_allow_html=True)

        elif kind == "risk":
            st.markdown(eyebrow("SEVERITY"), unsafe_allow_html=True)
            st.markdown(risk_marker(data.get("severity", "Low")), unsafe_allow_html=True)
            for f in data.get("risk_flags", []) or []:
                st.markdown(
                    risk_marker(f.get("severity", "Low")) + f' <b>{f.get("flag_type")}</b><br/>{f.get("explanation", "")}',
                    unsafe_allow_html=True,
                )

        elif kind == "comparison":
            st.write(data.get("summary", ""))
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(eyebrow("ADDED"), unsafe_allow_html=True)
                for c in data.get("added_clauses", []) or ["—"]:
                    st.write(f"- {c if isinstance(c, str) else c.get('clause_title')}")
            with col_b:
                st.markdown(eyebrow("REMOVED"), unsafe_allow_html=True)
                for c in data.get("removed_clauses", []) or ["—"]:
                    st.write(f"- {c if isinstance(c, str) else c.get('clause_title')}")
            with col_c:
                st.markdown(eyebrow("MODIFIED"), unsafe_allow_html=True)
                for c in data.get("modified_clauses", []) or ["—"]:
                    st.write(f"- {c if isinstance(c, str) else c.get('clause_title')}")

# ---------------- RIGHT: Evidence / Citations ----------------
with col_evidence:
    st.markdown(eyebrow("EVIDENCE / CITATIONS"), unsafe_allow_html=True)
    if not record:
        st.markdown('<div style="color:#A0A8B5; font-size:0.8rem;">No record open.</div>', unsafe_allow_html=True)
    else:
        kind, data = record
        evidence_refs = []
        if kind == "report":
            rj = data.get("report_json") or {}
            evidence_refs = rj.get("evidence_references") or []
        elif kind == "compliance":
            for issue in data.get("compliance_issues", []) or []:
                evidence_refs.extend(issue.get("evidence") or [])
        elif kind == "risk":
            for f in data.get("risk_flags", []) or []:
                evidence_refs.extend(f.get("evidence") or [])

        if evidence_refs:
            seen = set()
            for ev in evidence_refs:
                key = (ev.get("label"), ev.get("source"))
                if key in seen:
                    continue
                seen.add(key)
                st.markdown(evidence_item(ev.get("label", ""), ev.get("source", ""), ev.get("quote")), unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#A0A8B5; font-size:0.8rem;">No evidence references for this record type.</div>', unsafe_allow_html=True)
