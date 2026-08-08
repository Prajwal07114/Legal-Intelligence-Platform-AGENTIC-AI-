"""
Shared UI components that need real Streamlit widgets (not just HTML),
so they can't live in theme.py's pure-string builders.
"""
import streamlit as st
from api_client import download_report_pdf, download_report_docx, download_report_json


def render_download_bar(report_id: str, key_prefix: str):
    """Renders [Download PDF] [Download DOCX] [Export JSON] buttons for
    a given report_id. Used on Contract Analysis, Compliance Dashboard,
    Risk Dashboard, and Report Viewer — all four call this with the
    same report_id so the export is always consistent across pages.
    """
    if not report_id:
        return

    st.markdown('<div class="li-download-label">EXPORT CASE FILE</div>', unsafe_allow_html=True)
    col_pdf, col_docx, col_json = st.columns(3)

    with col_pdf:
        if st.button("Prepare PDF", key=f"{key_prefix}_prep_pdf", use_container_width=True):
            with st.spinner("Rendering PDF..."):
                try:
                    st.session_state[f"{key_prefix}_pdf_bytes"] = download_report_pdf(report_id)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"PDF export failed: {exc}")
        if st.session_state.get(f"{key_prefix}_pdf_bytes"):
            st.download_button(
                "Download PDF",
                data=st.session_state[f"{key_prefix}_pdf_bytes"],
                file_name=f"legal-intelligence-report-{report_id[:8]}.pdf",
                mime="application/pdf",
                key=f"{key_prefix}_dl_pdf",
                use_container_width=True,
            )

    with col_docx:
        if st.button("Prepare DOCX", key=f"{key_prefix}_prep_docx", use_container_width=True):
            with st.spinner("Rendering DOCX..."):
                try:
                    st.session_state[f"{key_prefix}_docx_bytes"] = download_report_docx(report_id)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"DOCX export failed: {exc}")
        if st.session_state.get(f"{key_prefix}_docx_bytes"):
            st.download_button(
                "Download DOCX",
                data=st.session_state[f"{key_prefix}_docx_bytes"],
                file_name=f"legal-intelligence-report-{report_id[:8]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"{key_prefix}_dl_docx",
                use_container_width=True,
            )

    with col_json:
        if st.button("Prepare JSON", key=f"{key_prefix}_prep_json", use_container_width=True):
            with st.spinner("Preparing JSON export..."):
                try:
                    st.session_state[f"{key_prefix}_json_bytes"] = download_report_json(report_id)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"JSON export failed: {exc}")
        if st.session_state.get(f"{key_prefix}_json_bytes"):
            st.download_button(
                "Export JSON",
                data=st.session_state[f"{key_prefix}_json_bytes"],
                file_name=f"legal-intelligence-report-{report_id[:8]}.json",
                mime="application/json",
                key=f"{key_prefix}_dl_json",
                use_container_width=True,
            )
