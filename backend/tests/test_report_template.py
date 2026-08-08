"""
Unit tests — deterministic report renderer (app.utils.report_template)

Verifies the Phase 2 section structure is always present, and that
comparison mode adds the Contract Comparison section while single mode
omits it.
"""
from app.utils.report_template import render_report_markdown

EXPECTED_SECTIONS = [
    "## Executive Summary",
    "## Contract Overview",
    "## Extracted Legal Intelligence",
    "## Compliance Assessment",
    "## Red Flag Analysis",
    "## Risk Assessment",
    "## Evidence & Citations",
    "## Recommended Review Areas",
    "## Disclaimer",
]


def _base_state(**overrides) -> dict:
    state = {
        "query": "Review this contract",
        "task_type": "Contract Review",
        "topics": ["liability"],
        "sources": [],
        "clauses": [],
        "obligations": [],
        "deadlines": [],
        "penalties": [],
        "risks": [],
        "overall_risk_level": "Low",
        "document_intelligence": {},
        "compliance_results": {},
        "risk_flags": [],
        "red_flag_severity": "Low",
        "comparison_results": {},
        "workflow_mode": "single",
    }
    state.update(overrides)
    return state


def test_all_required_sections_present_single_mode():
    markdown = render_report_markdown(_base_state(), evidence_references=[])
    for section in EXPECTED_SECTIONS:
        assert section in markdown, f"Missing section: {section}"
    assert "## Contract Comparison" not in markdown


def test_comparison_section_present_in_comparison_mode():
    state = _base_state(
        workflow_mode="comparison",
        comparison_results={
            "added_clauses": [{"clause_title": "Termination", "detail": "New 30-day clause"}],
            "removed_clauses": [],
            "modified_clauses": [],
            "summary": "Contract B adds a termination clause.",
        },
    )
    markdown = render_report_markdown(state, evidence_references=[])
    assert "## Contract Comparison" in markdown
    assert "Termination" in markdown


def test_disclaimer_always_present_regardless_of_risk_level():
    for level in ["Low", "Moderate", "High", "Critical"]:
        markdown = render_report_markdown(_base_state(overall_risk_level=level), evidence_references=[])
        assert "not a substitute for professional" in markdown


def test_evidence_section_deduplicates_entries():
    evidence = [
        {"label": "Clause 8.2", "quote": "unlimited liability", "source": "document_intelligence"},
        {"label": "Clause 8.2", "quote": "unlimited liability", "source": "document_intelligence"},  # dup
        {"label": "Missing section", "quote": None, "source": "compliance_agent"},
    ]
    markdown = render_report_markdown(_base_state(), evidence_references=evidence)
    assert markdown.count("Clause 8.2") == 1
    assert "Missing section" in markdown


def test_high_risk_triggers_attorney_review_recommendation():
    markdown = render_report_markdown(_base_state(overall_risk_level="Critical"), evidence_references=[])
    assert "licensed attorney is strongly suggested" in markdown
