"""
Unit tests — Agent 6: Legal Document Intelligence Agent

Focus: the agent must NEVER crash on malformed LLM output (a hard
requirement from the Phase 2 spec), and must correctly map its rich
output into the Phase 1-compatible legacy fields.
"""
from app.agents import document_intelligence_agent as mod


def test_no_document_text_returns_empty_structures():
    result = mod.document_intelligence_node({"document_text": None, "topics": [], "errors": []})
    assert result["document_intelligence"]["parties"] == []
    assert result["clauses"] == []
    assert result["obligations"] == []
    assert result["deadlines"] == []
    assert result["penalties"] == []


def test_normalizes_well_formed_llm_output(monkeypatch, sample_document_intelligence):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: sample_document_intelligence)

    result = mod.document_intelligence_node({
        "document_text": "some contract text " * 20,
        "topics": ["liability"],
        "errors": [],
    })

    intel = result["document_intelligence"]
    assert intel["liability_clause"]["present"] is True
    assert intel["confidentiality_clause"]["present"] is False
    assert intel["governing_law"] == "State of Delaware"

    # Legacy backward-compat mapping: only "present" clauses become legacy clauses
    legacy_titles = {c["title"] for c in result["clauses"]}
    assert "Liability Clause" in legacy_titles
    assert "Confidentiality Clause" not in legacy_titles  # was present=False
    assert "Termination Clause" not in legacy_titles      # was present=False


def test_never_crashes_on_malformed_llm_output(monkeypatch):
    """The LLM might return wrong types (string instead of dict/list),
    missing keys, or None. None of this should raise."""
    garbage_payloads = [
        {},  # empty
        {"parties": "not-a-list", "payment_terms": "not-a-dict"},
        {"parties": None, "obligations": None, "liability_clause": None},
        {"parties": [{"no_name_key": True}], "termination_clause": {"present": "yes"}},
        "not even a dict",  # top-level wrong type
        None,
    ]

    for payload in garbage_payloads:
        monkeypatch.setattr(mod, "chat_completion_json", lambda p=payload, **kwargs: p)
        result = mod.document_intelligence_node({
            "document_text": "some contract text",
            "topics": [],
            "errors": [],
        })
        # Must always return the expected top-level keys with safe types
        assert isinstance(result["document_intelligence"], dict)
        assert isinstance(result["clauses"], list)
        assert isinstance(result["obligations"], list)
        assert isinstance(result["deadlines"], list)
        assert isinstance(result["penalties"], list)


def test_present_true_but_missing_evidence_key_does_not_crash(monkeypatch):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {
        "liability_clause": {"present": True, "summary": "Uncapped liability"},  # no "evidence" key at all
    })
    result = mod.document_intelligence_node({"document_text": "text", "topics": [], "errors": []})
    detail = result["document_intelligence"]["liability_clause"]
    assert detail["present"] is True
    assert detail["evidence"] == []
