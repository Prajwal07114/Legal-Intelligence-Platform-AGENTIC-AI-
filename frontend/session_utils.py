"""
Shared session-state helpers.

Phase 2 pages (Compliance Dashboard, Risk Dashboard, Contract
Comparison) all need to pick from the set of documents uploaded so
far in this browser session — this module centralizes that instead of
duplicating session_state bookkeeping in every page.
"""
import streamlit as st


def ensure_session_defaults():
    if "uploaded_documents" not in st.session_state:
        st.session_state.uploaded_documents = []  # list of {"id": ..., "filename": ...}
    # Legacy Phase 1 single-document fields (kept for the Contract Analysis page)
    if "document_id" not in st.session_state:
        st.session_state.document_id = None
    if "document_filename" not in st.session_state:
        st.session_state.document_filename = None


def add_uploaded_document(document_id: str, filename: str):
    ensure_session_defaults()
    st.session_state.uploaded_documents.append({"id": document_id, "filename": filename})
    # Also set as the "active" Phase 1 document for the Contract Analysis page
    st.session_state.document_id = document_id
    st.session_state.document_filename = filename


def document_options() -> dict[str, str]:
    """Returns {label: document_id} for use in a selectbox."""
    ensure_session_defaults()
    return {
        f"{d['filename']} ({d['id'][:8]}...)": d["id"]
        for d in st.session_state.uploaded_documents
    }
