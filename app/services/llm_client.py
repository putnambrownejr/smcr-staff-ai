"""Lightweight LLM client for scenario-mode template population.

Calls an OpenAI-compatible chat completion API using httpx (already a
dependency).  Returns populated text or None on any failure so callers
can fall back to the static template.

Configure via environment variables:
    LLM_API_KEY   — required; without it every call returns None
    LLM_BASE_URL  — defaults to https://api.openai.com/v1
    LLM_MODEL     — defaults to gpt-4o-mini
"""

from __future__ import annotations

import logging
from functools import lru_cache

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


@lru_cache
def _llm_settings() -> tuple[str | None, str, str]:
    from app.core.config import get_settings

    s = get_settings()
    return s.llm_api_key, s.llm_base_url, s.llm_model


def generate_scenario_response(
    system_prompt: str,
    template: str,
    user_input: str,
) -> str | None:
    """Call an LLM to populate *template* from *user_input*.

    Returns the populated text, or ``None`` if no API key is configured
    or the call fails for any reason.
    """
    api_key, base_url, model = _llm_settings()
    if not api_key:
        return None

    messages = [
        {
            "role": "system",
            "content": (
                f"{system_prompt}\n\n"
                "OUTPUT FORMAT — populate every field in the template below using "
                "facts from the user's scenario input.  If the scenario does not "
                "contain the information for a field, note the gap explicitly "
                "(e.g. 'Not specified in scenario — requires collection').  "
                "Do NOT return empty brackets or generic placeholder text.\n\n"
                f"TEMPLATE:\n{template}"
            ),
        },
        {"role": "user", "content": user_input},
    ]

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model, "messages": messages, "temperature": 0.3},
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if content and content.strip():
                return content.strip()
    except Exception:
        logger.debug("LLM scenario call failed; falling back to template", exc_info=True)

    return None
