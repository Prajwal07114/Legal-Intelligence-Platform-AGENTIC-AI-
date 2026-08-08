"""
Unit tests — Agent 9: Contract Comparison Agent

Scenarios: Contract V1 vs V2, Vendor A vs Vendor B — verifies added /
removed / modified clause detection and the defensive fallback when
one contract's text is missing.
"""
from app.agents import comparison_agent as mod


def test_missing_document_text_returns_safe_empty_result():
    result = mod.comparison_node({
        "document_text": "Contract A full text",
        "document_text_b": None,  # missing
        "topics": [],
        "errors": [],
    })
    assert result["comparison_results"]["added_clauses"] == []
    assert result["document_intelligence"] == {}
    assert any("Comparison mode requires" in e for e in result["errors"])


def test_vendor_a_vs_vendor_b_comparison(monkeypatch):
    # Two calls to _extract_intelligence (one per contract) + one call
    # to the comparison diff prompt. Distinguish by system_prompt content.
    def fake_llm(system_prompt, user_prompt, temperature=0.1):
        if "Legal Document Intelligence Agent" in system_prompt:
            if "Vendor A" in user_prompt or "vendor_a_marker" in user_prompt:
                return {"termination_clause": {"present": True, "summary": "30-day notice"}}
            return {"termination_clause": {"present": False}}
        if "Contract Comparison Agent" in system_prompt:
            return {
                "added_clauses": [{"clause_title": "Termination Clause", "detail": "Added 30-day notice provision"}],
                "removed_clauses": [],
                "modified_clauses": [{"clause_title": "Payment Terms", "detail": "Net 30 -> Net 45"}],
                "summary": "Contract B adds termination rights and extends payment terms.",
            }
        return {}

    monkeypatch.setattr(mod, "chat_completion_json", fake_llm)

    result = mod.comparison_node({
        "document_text": "vendor_a_marker contract text",
        "document_text_b": "vendor_b contract text",
        "topics": ["termination"],
        "errors": [],
    })

    comparison = result["comparison_results"]
    assert len(comparison["added_clauses"]) == 1
    assert comparison["added_clauses"][0]["clause_title"] == "Termination Clause"
    assert len(comparison["modified_clauses"]) == 1
    assert "extends payment" in comparison["summary"]

    # document_intelligence in the returned state should reflect Contract B
    # (the target/new contract), per the Phase 2 spec.
    assert result["document_intelligence"]["termination_clause"]["present"] is False


def test_never_crashes_on_malformed_diff_output(monkeypatch):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {
        "added_clauses": "not-a-list",
        "removed_clauses": [None, "just-a-string-title", {"no_clause_title_key": True}],
        "modified_clauses": None,
        "summary": None,
    })

    result = mod.comparison_node({
        "document_text": "Contract A",
        "document_text_b": "Contract B",
        "topics": [],
        "errors": [],
    })
    comparison = result["comparison_results"]
    assert comparison["added_clauses"] == []
    assert len(comparison["removed_clauses"]) == 1  # only the plain string survives
    assert comparison["modified_clauses"] == []
    assert comparison["summary"] == "No summary generated."
