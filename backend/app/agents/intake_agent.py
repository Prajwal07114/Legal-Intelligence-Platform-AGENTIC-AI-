"""
Agent 1 — Legal Intake Agent

Responsibility: understand the user's query and classify the task type
so downstream agents know what to focus on.
"""
import logging

from app.agents.state import LegalAnalysisState
from app.utils.llm_client import chat_completion_json
from app.utils.prompts import INTAKE_SYSTEM_PROMPT, INTAKE_USER_TEMPLATE

logger = logging.getLogger(__name__)

VALID_TASK_TYPES = {"Contract Review", "Legal Research", "Clause Explanation", "Risk Analysis"}
DEFAULT_TASK_TYPE = "Legal Research"


def intake_node(state: LegalAnalysisState) -> dict:
    query = state.get("query", "")
    has_document = bool(state.get("document_id") or state.get("document_text"))

    result = chat_completion_json(
        system_prompt=INTAKE_SYSTEM_PROMPT,
        user_prompt=INTAKE_USER_TEMPLATE.format(query=query, has_document=has_document),
    )

    task_type = result.get("task_type", DEFAULT_TASK_TYPE)
    if task_type not in VALID_TASK_TYPES:
        logger.warning("Intake agent returned invalid task_type '%s', defaulting.", task_type)
        task_type = DEFAULT_TASK_TYPE if not has_document else "Contract Review"

    topics = result.get("topics") or []
    if not isinstance(topics, list):
        topics = [str(topics)]

    return {
        "task_type": task_type,
        "topics": topics[:6],
        "errors": state.get("errors", []),
    }
