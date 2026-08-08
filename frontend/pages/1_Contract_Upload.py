"""
Page 1: Contract Upload — evidence intake.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from api_client import upload_document
from session_utils import ensure_session_defaults, add_uploaded_document
from theme import inject_global_css, eyebrow, section_divider, COLORS

st.set_page_config(page_title="Contract Upload", page_icon="📄", layout="wide")
inject_global_css()
ensure_session_defaults()

st.markdown(eyebrow("EVIDENCE INTAKE"), unsafe_allow_html=True)
st.title("Contract Upload")
st.caption("FILE NEW EVIDENCE FOR INVESTIGATION · UPLOAD A SECOND CONTRACT TO ENABLE COMPARISON MODE")

uploaded_file = st.file_uploader("Submit PDF contract", type=["pdf"])

col1, _ = st.columns([1, 3])
with col1:
    upload_clicked = st.button("Log Evidence", type="primary", disabled=uploaded_file is None)

if upload_clicked and uploaded_file is not None:
    with st.spinner("Extracting text, chunking, and generating embeddings..."):
        try:
            result = upload_document(uploaded_file.getvalue(), uploaded_file.name)
            add_uploaded_document(result["document_id"], result["filename"])
            st.success(
                f"Logged **{result['filename']}** — "
                f"{result['page_count']} pages, {result['chunk_count']} evidence chunks indexed."
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Intake failed: {exc}")

st.markdown(section_divider("CASE FILE REGISTER"), unsafe_allow_html=True)

if not st.session_state.uploaded_documents:
    st.markdown(
        f'<div class="li-panel"><span style="color:{COLORS["text_muted"]};">No evidence on file yet.</span></div>',
        unsafe_allow_html=True,
    )
else:
    for doc in st.session_state.uploaded_documents:
        active = doc["id"] == st.session_state.document_id
        badge = (
            f'<span class="li-tag" style="border-color:{COLORS["gold"]}; color:{COLORS["gold"]};">'
            f'<span class="li-dot" style="background:{COLORS["gold"]};"></span>ACTIVE</span>'
            if active else ""
        )
        st.markdown(
            f"""
            <div class="li-panel">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.9rem; color:{COLORS['text']};">{doc['filename']}</div>
                    <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:{COLORS['text_muted']}; margin-top:0.2rem;">CASE ID: {doc['id']}</div>
                </div>
                <div>{badge}</div>
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        "Proceed to Contract Analysis, Compliance Dashboard, Risk Dashboard, or Contract Comparison.",
        icon="➡️",
    )

    if st.button("Clear register"):
        st.session_state.uploaded_documents = []
        st.session_state.document_id = None
        st.session_state.document_filename = None
        st.rerun()
