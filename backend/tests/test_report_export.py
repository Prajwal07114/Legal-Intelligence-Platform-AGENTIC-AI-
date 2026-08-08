"""
Unit tests — report export system (app.utils.report_export,
app.utils.pdf_report, app.utils.docx_report).

Verifies the export data builder normalizes report_json correctly, and
that the PDF/DOCX generators produce real, parseable files (not just
non-empty byte strings) from that data — including the defensive path
where report_json is missing pieces.
"""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.utils.report_export import build_export_data
from app.utils.pdf_report import generate_pdf_report
from app.utils.docx_report import generate_docx_report


def _fake_report(report_json=None, **overrides) -> SimpleNamespace:
    defaults = dict(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        user_query="Review this contract",
        task_type="Contract Review",
        workflow_mode="single",
        risk_level="Moderate",
        created_at=datetime.now(timezone.utc),
        report_markdown=(
            "# Legal Intelligence Report\n\n"
            "## Recommended Review Areas\n"
            "- Review clause X.\n"
            "- Consult counsel.\n\n"
            "## Disclaimer\n> not legal advice\n"
        ),
        report_json=report_json or {},
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_build_export_data_handles_empty_report_json():
    report = _fake_report(report_json={})
    data = build_export_data(report)

    assert data["case_id"] == str(report.id)
    assert data["compliance_score"] is None
    assert data["clauses_extracted"] == 0
    assert data["high_risk_clause_count"] == 0
    assert data["findings"] == []
    assert data["recommendations"] == ["Review clause X.", "Consult counsel."]


def test_build_export_data_extracts_high_risk_flags():
    report = _fake_report(report_json={
        "risk_flags": [
            {"flag_type": "Unlimited Liability", "severity": "Critical", "explanation": "...", "evidence": []},
            {"flag_type": "Ambiguous Obligations", "severity": "Low", "explanation": "...", "evidence": []},
        ],
        "compliance_results": {"compliance_score": 60, "missing_clauses": [], "compliance_issues": []},
    })
    data = build_export_data(report)

    assert data["high_risk_clause_count"] == 1
    assert data["compliance_score"] == 60
    assert len(data["findings"]) == 2
    # Findings sorted by severity, highest first
    assert data["findings"][0]["severity"] == "Critical"


def test_pdf_generation_produces_valid_pdf():
    report = _fake_report(report_json={
        "document_intelligence": {
            "parties": [{"name": "Acme Corp", "role": "Vendor"}],
            "liability_clause": {"present": True, "summary": "Uncapped", "evidence": []},
        },
        "compliance_results": {"compliance_score": 50, "missing_clauses": ["Termination Clause"], "compliance_issues": []},
        "risk_flags": [{"flag_type": "Unlimited Liability", "severity": "Critical", "explanation": "No cap", "evidence": [{"label": "Clause 8.2"}]}],
        "evidence_references": [{"label": "Clause 8.2", "quote": "unlimited", "source": "document_intelligence"}],
    })
    data = build_export_data(report)
    pdf_bytes = generate_pdf_report(data)

    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 1000


def test_docx_generation_produces_valid_docx():
    report = _fake_report(report_json={
        "document_intelligence": {"parties": [{"name": "Acme Corp", "role": "Vendor"}]},
        "compliance_results": {"compliance_score": 80, "missing_clauses": [], "compliance_issues": []},
        "risk_flags": [],
    })
    data = build_export_data(report)
    docx_bytes = generate_docx_report(data)

    # DOCX is a zip archive — PK magic bytes
    assert docx_bytes[:2] == b"PK"
    assert len(docx_bytes) > 1000


def test_pdf_and_docx_never_crash_on_missing_optional_fields():
    """Report with almost nothing populated — export must degrade
    gracefully, matching the platform-wide 'never crash on malformed/
    missing data' requirement."""
    report = _fake_report(report_json=None, report_markdown="")
    data = build_export_data(report)

    pdf_bytes = generate_pdf_report(data)
    docx_bytes = generate_docx_report(data)

    assert pdf_bytes[:4] == b"%PDF"
    assert docx_bytes[:2] == b"PK"


def test_recommendations_extraction_handles_missing_section():
    report = _fake_report(report_markdown="# Report\n\n## Executive Summary\nSome text.\n")
    data = build_export_data(report)
    assert data["recommendations"] == []
