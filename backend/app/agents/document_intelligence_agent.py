"""
Agent 6 — Legal Document Intelligence Agent (Phase 2)

Replaces the Phase 1 Clause Analysis Agent's role in the default graph
with a much richer structured-extraction layer: parties, dates,
obligations, payment terms, confidentiality/liability/indemnity/
termination clauses, governing law, jurisdiction, deadlines, penalties.

For backward compatibility, this agent ALSO populates the Phase 1
fields (clauses, obligations, deadlines, penalties) so the original
report sections and API response fields keep working unchanged.

Defensive design: this agent must never crash on malformed LLM output.
Every field access uses .get() with safe defaults, and clause-detail
sub-objects are normalized through `_safe_clause_detail`.
"""
import logging

from app.agents.state import LegalAnalysisState
from app.utils.llm_client import chat_completion_json
from app.utils.prompts import (
    DOCUMENT_INTELLIGENCE_SYSTEM_PROMPT,
    DOCUMENT_INTELLIGENCE_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 12000

EMPTY_CLAUSE_DETAIL = {"present": False, "summary": None, "evidence": []}


def document_intelligence_node(state: LegalAnalysisState) -> dict:
    document_text = state.get("document_text")
    errors = list(state.get("errors", []))

    if not document_text:
        logger.info("No document text present — skipping document intelligence extraction.")
        empty = _empty_document_intelligence()
        return {
            "document_intelligence": empty,
            # Phase 1 backward-compat fields
            "clauses": [],
            "obligations": [],
            "deadlines": [],
            "penalties": [],
            "errors": errors,
        }

    truncated = document_text[:MAX_DOCUMENT_CHARS]

    raw_result = chat_completion_json(
        system_prompt=DOCUMENT_INTELLIGENCE_SYSTEM_PROMPT,
        user_prompt=DOCUMENT_INTELLIGENCE_USER_TEMPLATE.format(
            document_text=truncated,
            topics=", ".join(state.get("topics", [])) or "general review",
        ),
    )

    if not raw_result:
        errors.append("Document Intelligence Agent returned no structured data.")

    doc_intel = _normalize_document_intelligence(raw_result)

    # ---- Backward-compat mapping into Phase 1 fields ----
    legacy_clauses = _to_legacy_clauses(doc_intel)

    return {
        "document_intelligence": doc_intel,
        "clauses": legacy_clauses,
        "obligations": doc_intel.get("obligations", []),
        "deadlines": doc_intel.get("deadlines", []),
        "penalties": doc_intel.get("penalties", []),
        "errors": errors,
    }


def _empty_document_intelligence() -> dict:
    return {
        "parties": [],
        "effective_date": None,
        "expiration_date": None,
        "obligations": [],
        "deadlines": [],
        "penalties": [],
        "payment_terms": dict(EMPTY_CLAUSE_DETAIL),
        "confidentiality_clause": dict(EMPTY_CLAUSE_DETAIL),
        "liability_clause": dict(EMPTY_CLAUSE_DETAIL),
        "indemnity_clause": dict(EMPTY_CLAUSE_DETAIL),
        "termination_clause": dict(EMPTY_CLAUSE_DETAIL),
        "governing_law": None,
        "jurisdiction": None,
    }


def _safe_clause_detail(raw: object) -> dict:
    """Defensively coerce whatever the LLM returned for a clause-detail
    field into the expected {present, summary, evidence} shape."""
    if not isinstance(raw, dict):
        return dict(EMPTY_CLAUSE_DETAIL)

    present = bool(raw.get("present", False))
    summary = raw.get("summary")
    if summary is not None and not isinstance(summary, str):
        summary = str(summary)

    evidence_raw = raw.get("evidence", [])
    evidence = []
    if isinstance(evidence_raw, list):
        for item in evidence_raw:
            if isinstance(item, dict):
                evidence.append({
                    "label": str(item.get("label", "Unlabeled evidence")),
                    "quote": item.get("quote") if isinstance(item.get("quote"), str) else None,
                    "source": "document_intelligence",
                })
            elif isinstance(item, str):
                evidence.append({"label": item, "quote": None, "source": "document_intelligence"})

    return {"present": present, "summary": summary, "evidence": evidence}


def _safe_str_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw if x is not None]


def _safe_parties(raw: object) -> list[dict]:
    if not isinstance(raw, list):
        return []
    parties = []
    for item in raw:
        if isinstance(item, dict) and item.get("name"):
            parties.append({"name": str(item["name"]), "role": item.get("role")})
        elif isinstance(item, str):
            parties.append({"name": item, "role": None})
    return parties


def _normalize_document_intelligence(raw: dict) -> dict:
    """Defensive normalization: guarantees every expected key exists
    with a safe type, regardless of what the LLM actually returned."""
    if not isinstance(raw, dict):
        raw = {}

    return {
        "parties": _safe_parties(raw.get("parties")),
        "effective_date": raw.get("effective_date") or None,
        "expiration_date": raw.get("expiration_date") or None,
        "obligations": _safe_str_list(raw.get("obligations")),
        "deadlines": _safe_str_list(raw.get("deadlines")),
        "penalties": _safe_str_list(raw.get("penalties")),
        "payment_terms": _safe_clause_detail(raw.get("payment_terms")),
        "confidentiality_clause": _safe_clause_detail(raw.get("confidentiality_clause")),
        "liability_clause": _safe_clause_detail(raw.get("liability_clause")),
        "indemnity_clause": _safe_clause_detail(raw.get("indemnity_clause")),
        "termination_clause": _safe_clause_detail(raw.get("termination_clause")),
        "governing_law": raw.get("governing_law") or None,
        "jurisdiction": raw.get("jurisdiction") or None,
    }


def _to_legacy_clauses(doc_intel: dict) -> list[dict]:
    """Map the Phase 2 clause-detail objects into the Phase 1
    `ClauseDict` shape ({title, text, category}) so the existing
    report sections / API fields keep working unchanged."""
    mapping = [
        ("payment_terms", "Payment Terms", "financial"),
        ("confidentiality_clause", "Confidentiality Clause", "confidentiality"),
        ("liability_clause", "Liability Clause", "liability"),
        ("indemnity_clause", "Indemnity Clause", "indemnity"),
        ("termination_clause", "Termination Clause", "termination"),
    ]
    legacy = []
    for key, title, category in mapping:
        detail = doc_intel.get(key, {})
        if isinstance(detail, dict) and detail.get("present"):
            legacy.append({
                "title": title,
                "text": detail.get("summary") or "Present in contract (see Document Intelligence section).",
                "category": category,
            })
    return legacy
