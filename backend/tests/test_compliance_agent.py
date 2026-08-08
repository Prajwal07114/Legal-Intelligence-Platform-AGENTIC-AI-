"""
Unit tests — Agent 7: Compliance Agent

Focus: the compliance_score MUST be computed deterministically in pure
Python (not by the LLM) — these tests verify the score is identical
across repeated calls, regardless of what the (mocked) LLM narrative
call returns, and that missing-clause detection is correct.
"""
from app.agents import compliance_agent as mod


def test_fully_compliant_document_scores_100(monkeypatch, sample_document_intelligence):
    # Make everything present + governing_law/jurisdiction populated
    doc = dict(sample_document_intelligence)
    doc["confidentiality_clause"] = {"present": True, "summary": "Standard NDA", "evidence": []}
    doc["termination_clause"] = {"present": True, "summary": "90-day notice", "evidence": []}
    doc["jurisdiction"] = "Delaware courts"

    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {"compliance_issues": []})

    result = mod.compliance_node({"document_intelligence": doc, "errors": []})
    compliance = result["compliance_results"]

    assert compliance["compliance_score"] == 100
    assert compliance["missing_clauses"] == []


def test_missing_clauses_reduce_score_and_are_listed(monkeypatch, sample_document_intelligence):
    # sample fixture has confidentiality_clause and termination_clause both absent,
    # and jurisdiction is None
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {"compliance_issues": []})

    result = mod.compliance_node({"document_intelligence": sample_document_intelligence, "errors": []})
    compliance = result["compliance_results"]

    assert compliance["compliance_score"] < 100
    assert "Confidentiality Clause" in compliance["missing_clauses"]
    assert "Termination Clause" in compliance["missing_clauses"]
    assert "Dispute Resolution / Jurisdiction Clause" in compliance["missing_clauses"]

    # A deterministic issue must exist for every missing clause, even
    # though the mocked LLM call returned zero issues.
    issue_texts = [i["issue"] for i in compliance["compliance_issues"]]
    assert any("Confidentiality Clause" in t for t in issue_texts)
    assert any("Termination Clause" in t for t in issue_texts)


def test_empty_document_intelligence_scores_zero(empty_document_intelligence, monkeypatch):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {"compliance_issues": []})
    result = mod.compliance_node({"document_intelligence": empty_document_intelligence, "errors": []})
    assert result["compliance_results"]["compliance_score"] == 0
    assert len(result["compliance_results"]["missing_clauses"]) == 7  # all required fields


def test_score_is_deterministic_across_repeated_calls(monkeypatch, sample_document_intelligence):
    """Same input -> same score, every time, regardless of LLM narrative output."""
    call_count = {"n": 0}

    def flaky_llm(**kwargs):
        call_count["n"] += 1
        # Simulate the LLM returning different narrative text each call
        return {"compliance_issues": [{"issue": f"Issue #{call_count['n']}", "severity": "Low", "evidence": []}]}

    monkeypatch.setattr(mod, "chat_completion_json", flaky_llm)

    scores = []
    for _ in range(3):
        result = mod.compliance_node({"document_intelligence": sample_document_intelligence, "errors": []})
        scores.append(result["compliance_results"]["compliance_score"])

    assert len(set(scores)) == 1, "compliance_score must be deterministic regardless of LLM output"


def test_llm_failure_does_not_prevent_deterministic_scoring(monkeypatch, sample_document_intelligence):
    """If the narrative LLM call returns nothing usable, the score and
    missing-clause list (both deterministic) must still be correct."""
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {})

    result = mod.compliance_node({"document_intelligence": sample_document_intelligence, "errors": []})
    compliance = result["compliance_results"]

    assert isinstance(compliance["compliance_score"], int)
    assert "Confidentiality Clause" in compliance["missing_clauses"]
    # Deterministic fallback issues still populate compliance_issues
    assert len(compliance["compliance_issues"]) > 0


def test_malformed_llm_issue_entries_are_dropped_not_crashed(monkeypatch, sample_document_intelligence):
    monkeypatch.setattr(mod, "chat_completion_json", lambda **kwargs: {
        "compliance_issues": [
            "not-a-dict",
            {"severity": "High"},  # missing "issue" key entirely
            {"issue": "Valid issue", "severity": "NOT_A_REAL_SEVERITY", "evidence": "also not a list"},
            None,
        ]
    })
    result = mod.compliance_node({"document_intelligence": sample_document_intelligence, "errors": []})
    issues = result["compliance_results"]["compliance_issues"]
    # Only the "Valid issue" entry (with severity coerced to a valid default) should survive
    valid_entries = [i for i in issues if i["issue"] == "Valid issue"]
    assert len(valid_entries) == 1
    assert valid_entries[0]["severity"] in {"Low", "Moderate", "High", "Critical"}
