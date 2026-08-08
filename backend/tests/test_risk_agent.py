"""
Unit tests — Agent 4: Legal Risk Assessment Agent (Phase 2 aggregator)

Focus: overall_risk_level must be the single highest severity across
Agent 4's own risks, Agent 8's risk_flags, and Agent 7's
compliance_issues — computed deterministically in Python.
"""
from app.agents import risk_agent as mod


def test_no_clauses_returns_low_with_no_llm_call(monkeypatch):
    def fail_if_called(**kwargs):
        raise AssertionError("LLM should not be called when there are no clauses")

    monkeypatch.setattr(mod, "chat_completion_json", fail_if_called)

    result = mod.risk_node({"clauses": [], "obligations": [], "penalties": [], "errors": []})
    assert result["overall_risk_level"] == "Low"
    assert result["risks"] == []


def test_aggregates_highest_severity_across_all_sources(monkeypatch):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {
        "risks": [{"risk_level": "Moderate", "reason": "..."}]
    })

    result = mod.risk_node({
        "clauses": [{"title": "Liability", "text": "...", "category": "liability"}],
        "obligations": [],
        "penalties": [],
        "risk_flags": [{"severity": "Critical"}],  # Agent 8 found something worse
        "red_flag_severity": "Critical",
        "compliance_results": {"compliance_issues": [{"severity": "Low"}]},
        "errors": [],
    })

    assert result["overall_risk_level"] == "Critical"


def test_ignores_invalid_severity_values(monkeypatch):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {
        "risks": [{"risk_level": "NOT_VALID", "reason": "..."}]
    })

    result = mod.risk_node({
        "clauses": [{"title": "X", "text": "Y", "category": None}],
        "obligations": [], "penalties": [],
        "risk_flags": [{"severity": "also-not-valid"}],
        "red_flag_severity": None,
        "compliance_results": {},
        "errors": [],
    })
    # Nothing valid anywhere -> defaults to Low
    assert result["overall_risk_level"] == "Low"


def test_compliance_issues_alone_can_drive_overall_risk(monkeypatch):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {"risks": []})

    result = mod.risk_node({
        "clauses": [{"title": "X", "text": "Y", "category": None}],
        "obligations": [], "penalties": [],
        "risk_flags": [],
        "red_flag_severity": "Low",
        "compliance_results": {"compliance_issues": [{"severity": "High"}]},
        "errors": [],
    })
    assert result["overall_risk_level"] == "High"
