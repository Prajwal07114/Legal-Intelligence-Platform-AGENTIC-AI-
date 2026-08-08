"""
Thin wrapper around the Groq client so agents don't each re-implement
retry/error handling. Centralizes the model name and JSON-mode helper.
"""
import json
import logging

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

_client = Groq(api_key=settings.groq_api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def chat_completion(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
    """Single-turn chat completion. Returns raw text content."""
    response = _client.chat.completions.create(
        model=settings.groq_model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def chat_completion_json(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> dict:
    """
    Chat completion constrained to JSON output via Groq's JSON mode.
    The system prompt MUST instruct the model to return JSON (Groq requirement).
    Falls back to best-effort parsing if JSON mode isn't honored.
    """
    response = _client.chat.completions.create(
        model=settings.groq_model,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("LLM did not return valid JSON, raw content: %s", raw[:500])
        return {}
