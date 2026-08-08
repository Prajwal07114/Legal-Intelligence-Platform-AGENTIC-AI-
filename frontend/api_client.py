"""
Small shared HTTP client for talking to the FastAPI backend.
Import via: from api_client import API_BASE, upload_document, analyze_document, ask, get_report
"""
import os
import requests

API_BASE = os.environ.get("BACKEND_API_URL", "http://localhost:8000")

TIMEOUT = 120  # seconds — LLM calls can take a while on free-tier Groq rate limits


def upload_document(file_bytes: bytes, filename: str) -> dict:
    files = {"file": (filename, file_bytes, "application/pdf")}
    resp = requests.post(f"{API_BASE}/upload-document", files=files, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def analyze_document(query: str, document_id: str | None = None, session_id: str | None = None) -> dict:
    payload = {"query": query, "document_id": document_id, "session_id": session_id}
    resp = requests.post(f"{API_BASE}/analyze-document", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def ask(query: str, session_id: str | None = None) -> dict:
    payload = {"query": query, "session_id": session_id}
    resp = requests.post(f"{API_BASE}/ask", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_report(report_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/report/{report_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ---------------- Phase 2 ----------------

def compliance_check(document_id: str, session_id: str | None = None) -> dict:
    payload = {"document_id": document_id, "session_id": session_id}
    resp = requests.post(f"{API_BASE}/compliance-check", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def risk_analysis(document_id: str, session_id: str | None = None) -> dict:
    payload = {"document_id": document_id, "session_id": session_id}
    resp = requests.post(f"{API_BASE}/risk-analysis", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def compare_contracts(query: str, document_id_a: str, document_id_b: str, session_id: str | None = None) -> dict:
    payload = {
        "query": query,
        "document_id_a": document_id_a,
        "document_id_b": document_id_b,
        "session_id": session_id,
    }
    resp = requests.post(f"{API_BASE}/compare-contracts", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_comparison_report(comparison_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/comparison-report/{comparison_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_compliance_report(compliance_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/compliance-report/{compliance_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_risk_report(risk_flag_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/risk-report/{risk_flag_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ---------------- Report downloads ----------------

def download_report_pdf(report_id: str) -> bytes:
    resp = requests.get(f"{API_BASE}/download-report-pdf/{report_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.content


def download_report_docx(report_id: str) -> bytes:
    resp = requests.get(f"{API_BASE}/download-report-docx/{report_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.content


def download_report_json(report_id: str) -> bytes:
    resp = requests.get(f"{API_BASE}/download-report-json/{report_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.content
