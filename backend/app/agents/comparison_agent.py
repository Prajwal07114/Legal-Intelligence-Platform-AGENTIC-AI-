"""
Agent 9 — Contract Comparison Agent (Phase 2)

Compares two contracts (Contract A vs Contract B — e.g. old vs new
agreement, or Vendor A vs Vendor B). Runs Document Intelligence-style
extraction on BOTH documents first, then asks the LLM to diff them into
added / removed / modified clauses.

In comparison_mode, this agent's output for Contract B is also used as
the "document_intelligence" for the rest of the pipeline (Compliance,
Red Flag, Risk agents run against the newer/target contract) — so
comparison mode still yields a full compliance + risk report, per the
Phase 2 workflow spec.
"""
import json
import logging

from app.agents.state import LegalAnalysisState
from app.agents.document_intelligence_agent import (
    _normalize_document_intelligence,
    _to_legacy_clauses,
    MAX_DOCUMENT_CHARS,
)
from app.utils.llm_client import chat_completion_json
from app.utils.prompts import (
    DOCUMENT_INTELLIGENCE_SYSTEM_PROMPT,
    DOCUMENT_INTELLIGENCE_USER_TEMPLATE,
    COMPARISON_SYSTEM_PROMPT,
    COMPARISON_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)


def _extract_intelligence(document_text: str, topics: list[str]) -> dict:
    """Reuses the Document Intelligence Agent's extraction + normalization
    logic for a single contract's text (used for both A and B)."""
    if not document_text:
        return {}
    raw = chat_completion_json(
        system_prompt=DOCUMENT_INTELLIGENCE_SYSTEM_PROMPT,
        user_prompt=DOCUMENT_INTELLIGENCE_USER_TEMPLATE.format(
            document_text=document_text[:MAX_DOCUMENT_CHARS],
            topics=", ".join(topics) or "general review",
        ),
    )
    return _normalize_document_intelligence(raw)


def comparison_node(state: LegalAnalysisState) -> dict:
    text_a = state.get("document_text")
    text_b = state.get("document_text_b")
    topics = state.get("topics", [])
    errors = list(state.get("errors", []))

    if not text_a or not text_b:
        errors.append("Comparison mode requires both document_text and document_text_b.")
        empty = {
            "added_clauses": [],
            "removed_clauses": [],
            "modified_clauses": [],
            "summary": "Comparison could not run — one or both contracts were missing text.",
        }
        return {
            "comparison_results": empty,
            "document_intelligence": {},
            "clauses": [],
            "obligations": [],
            "deadlines": [],
            "penalties": [],
            "errors": errors,
        }

    doc_intel_a = _extract_intelligence(text_a, topics)
    doc_intel_b = _extract_intelligence(text_b, topics)

    raw_result = chat_completion_json(
        system_prompt=COMPARISON_SYSTEM_PROMPT,
        user_prompt=COMPARISON_USER_TEMPLATE.format(
            doc_a_json=json.dumps(doc_intel_a, indent=2)[:4000],
            doc_b_json=json.dumps(doc_intel_b, indent=2)[:4000],
        ),
    )

    if not raw_result:
        errors.append("Contract Comparison Agent returned no structured data.")

    comparison_results = _sanitize_comparison(raw_result)

    # Downstream Compliance/Red Flag/Risk agents run against Contract B
    # (treated as the "current"/"new" contract under review).
    legacy_clauses = _to_legacy_clauses(doc_intel_b)

    return {
        "comparison_results": comparison_results,
        "document_intelligence": doc_intel_b,
        "clauses": legacy_clauses,
        "obligations": doc_intel_b.get("obligations", []),
        "deadlines": doc_intel_b.get("deadlines", []),
        "penalties": doc_intel_b.get("penalties", []),
        "errors": errors,
    }


def _sanitize_diff_list(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if isinstance(item, dict) and item.get("clause_title"):
            out.append({
                "clause_title": str(item["clause_title"]),
                "detail": str(item.get("detail", "")),
            })
        elif isinstance(item, str):
            out.append({"clause_title": item, "detail": ""})
    return out


def _sanitize_comparison(raw: object) -> dict:
    if not isinstance(raw, dict):
        raw = {}
    summary = raw.get("summary")
    return {
        "added_clauses": _sanitize_diff_list(raw.get("added_clauses")),
        "removed_clauses": _sanitize_diff_list(raw.get("removed_clauses")),
        "modified_clauses": _sanitize_diff_list(raw.get("modified_clauses")),
        "summary": str(summary) if summary else "No summary generated.",
    }
