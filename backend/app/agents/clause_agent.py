"""
Agent 3 — Clause Analysis Agent

Responsibility: extract key clauses, obligations, deadlines, penalties
and important entities from the uploaded contract text. If no document
was uploaded (e.g. a pure Legal Research query), this node is a no-op
and returns empty structures.
"""
import logging

from app.agents.state import LegalAnalysisState
from app.utils.llm_client import chat_completion_json
from app.utils.prompts import CLAUSE_SYSTEM_PROMPT, CLAUSE_USER_TEMPLATE

logger = logging.getLogger(__name__)

# Guard against blowing past the model's context window on very large contracts.
MAX_DOCUMENT_CHARS = 12000


def clause_node(state: LegalAnalysisState) -> dict:
    document_text = state.get("document_text")
    errors = list(state.get("errors", []))

    if not document_text:
        logger.info("No document text present — skipping clause extraction.")
        return {
            "clauses": [],
            "obligations": [],
            "deadlines": [],
            "penalties": [],
            "errors": errors,
        }

    truncated = document_text[:MAX_DOCUMENT_CHARS]

    result = chat_completion_json(
        system_prompt=CLAUSE_SYSTEM_PROMPT,
        user_prompt=CLAUSE_USER_TEMPLATE.format(
            document_text=truncated,
            topics=", ".join(state.get("topics", [])) or "general review",
        ),
    )

    clauses = result.get("clauses") or []
    obligations = result.get("obligations") or []
    deadlines = result.get("deadlines") or []
    penalties = result.get("penalties") or []

    if not result:
        errors.append("Clause analysis returned no structured data.")

    return {
        "clauses": clauses,
        "obligations": obligations,
        "deadlines": deadlines,
        "penalties": penalties,
        "errors": errors,
    }
