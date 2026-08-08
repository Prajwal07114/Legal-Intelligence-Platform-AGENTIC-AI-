"""
Unit tests — Agent 8: Red Flag Detection Agent
"""
from app.agents import red_flag_agent as mod


def test_no_document_intelligence_returns_low_severity():
    result = mod.red_flag_node({"document_intelligence": {}, "compliance_results": {}, "errors": []})
    assert result["risk_flags"] == []
    assert result["red_flag_severity"] == "Low"


def test_detects_and_sanitizes_flags(monkeypatch, sample_document_intelligence):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {
        "risk_flags": [
            {
                "flag_type": "Unlimited Liability",
                "severity": "Critical",
                "explanation": "No liability cap found",
                "evidence": [{"label": "Clause 8.2", "quote": "unlimited liability"}],
            },
            {
                "flag_type": "One-Sided Termination",
                "severity": "High",
                "explanation": "No termination clause",
                "evidence": [{"label": "Missing section"}],
            },
        ],
        "severity": "Critical",
    })

    result = mod.red_flag_node({
        "document_intelligence": sample_document_intelligence,
        "compliance_results": {"compliance_issues": []},
        "errors": [],
    })

    assert result["red_flag_severity"] == "Critical"
    assert len(result["risk_flags"]) == 2
    assert result["risk_flags"][0]["evidence"][0]["source"] == "red_flag_agent"


def test_derives_severity_when_top_level_missing(monkeypatch, sample_document_intelligence):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {
        "risk_flags": [
            {"flag_type": "Excessive Penalties", "severity": "Moderate", "explanation": "..."},
            {"flag_type": "Broad Indemnification", "severity": "High", "explanation": "..."},
        ],
        # no top-level "severity" key at all
    })
    result = mod.red_flag_node({
        "document_intelligence": sample_document_intelligence,
        "compliance_results": {},
        "errors": [],
    })
    assert result["red_flag_severity"] == "High"  # highest among the two flags


def test_never_crashes_on_malformed_output(monkeypatch, sample_document_intelligence):
    garbage_payloads = [
        {},
        {"risk_flags": "not-a-list"},
        {"risk_flags": [None, "not-a-dict", {"severity": "High"}]},  # missing flag_type entries dropped
        None,
    ]
    for payload in garbage_payloads:
        monkeypatch.setattr(mod, "chat_completion_json", lambda p=payload, **kwargs: p)
        result = mod.red_flag_node({
            "document_intelligence": sample_document_intelligence,
            "compliance_results": {},
            "errors": [],
        })
        assert isinstance(result["risk_flags"], list)
        assert result["red_flag_severity"] in {"Low", "Moderate", "High", "Critical"}
