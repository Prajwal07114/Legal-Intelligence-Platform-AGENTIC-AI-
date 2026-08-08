"""
Legal Intelligence Platform — Streamlit frontend (Phase 2)

Home page: the Command Room. Six functional pages live in `pages/`:
  1_Contract_Upload.py
  2_Contract_Analysis.py
  3_Compliance_Dashboard.py
  4_Risk_Dashboard.py
  5_Contract_Comparison.py
  6_Report_Viewer.py
"""
import streamlit as st
from session_utils import ensure_session_defaults
from theme import inject_global_css, eyebrow, section_divider, pipeline_horizontal, COLORS

st.set_page_config(
    page_title="Legal Intelligence Command Room",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()
ensure_session_defaults()

st.markdown(eyebrow("CASE MANAGEMENT SYSTEM · CONTRACT INTELLIGENCE DIVISION"), unsafe_allow_html=True)
st.title("⚖ Legal Intelligence Command Room")
st.caption("9-AGENT INVESTIGATION PIPELINE · LANGGRAPH · PGVECTOR · GROQ LLAMA 3.3")

st.markdown(
    f"""
    <p style="color:{COLORS['text_muted']}; font-size:0.95rem; line-height:1.6;">
    Every contract that enters this system is treated as a case file. Nine investigation agents
    work the file in sequence — research, extraction, compliance, red-flag detection, risk
    assessment — and every finding they surface is logged with evidence. Nothing is asserted
    without a citation back to the source text.
    </p>
    """,
    unsafe_allow_html=True,
)

st.markdown(section_divider("INVESTIGATION PIPELINE"), unsafe_allow_html=True)

steps = [
    ("Case Intake", "complete"),
    ("Legal Research", "complete"),
    ("Document Intelligence", "complete"),
    ("Compliance Review", "complete"),
    ("Red Flag Detection", "complete"),
    ("Risk Assessment", "complete"),
    ("Legal Report", "complete"),
]
st.markdown(pipeline_horizontal(steps), unsafe_allow_html=True)

st.markdown(section_divider("OPERATING NOTES"), unsafe_allow_html=True)

col_note_a, col_note_b = st.columns(2)
with col_note_a:
    st.markdown(
        f"""
        <div class="li-panel" style="border-left-color:{COLORS['evidence']};">
        {eyebrow("BRANCH: COMPARISON MODE")}
        <p style="font-size:0.85rem; color:{COLORS['text_muted']}; line-height:1.55;">
        When two contracts are filed together, the <b style="color:{COLORS['text']};">Contract
        Comparison Agent</b> replaces Document Intelligence — Contract A and Contract B are
        both extracted, diffed, and the newer contract (B) is carried forward through
        Compliance, Red Flag Detection, and Risk Assessment.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_note_b:
    st.markdown(
        f"""
        <div class="li-panel" style="border-left-color:{COLORS['critical']};">
        {eyebrow("STANDING ORDER")}
        <p style="font-size:0.85rem; color:{COLORS['text_muted']}; line-height:1.55;">
        This system produces AI-generated analysis for informational purposes only.
        It is <b style="color:{COLORS['text']};">not a substitute for professional legal advice</b>.
        Every report can be exported as PDF, DOCX, or JSON for the case file.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(section_divider("CASE FILE STATIONS"), unsafe_allow_html=True)

stations = [
    ("01", "Contract Upload", "File new evidence — upload PDF contracts (two, for comparison mode)"),
    ("02", "Contract Analysis", "Run the full investigation pipeline against a document or open query"),
    ("03", "Compliance Dashboard", "Audit-sheet view — score gauge and missing-clause register"),
    ("04", "Risk Dashboard", "Red flag cards ranked by severity, each with its evidence"),
    ("05", "Contract Comparison", "Redline review — Contract A vs. Contract B, side by side"),
    ("06", "Report Viewer", "Retrieve any closed case file — full dossier, evidence, and exports"),
]
cols = st.columns(6)
for i, (num, title, desc) in enumerate(stations):
    with cols[i]:
        st.markdown(
            f"""
            <div class="li-panel" style="min-height:190px;">
            <div class="li-eyebrow">STATION {num}</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.88rem; color:{COLORS['gold']}; margin-bottom:0.4rem;">{title}</div>
            <div style="font-size:0.76rem; color:{COLORS['text_muted']}; line-height:1.5;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with st.sidebar:
    st.markdown(eyebrow("SESSION LOG"), unsafe_allow_html=True)
    docs = st.session_state.uploaded_documents
    st.markdown(
        f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:0.8rem; color:{COLORS["text"]};">'
        f'DOCUMENTS ON FILE: {len(docs)}</div>',
        unsafe_allow_html=True,
    )
    for d in docs:
        st.markdown(
            f'<div style="font-size:0.78rem; color:{COLORS["text_muted"]}; padding:0.15rem 0;">&bull; {d["filename"]}</div>',
            unsafe_allow_html=True,
        )
