import json
import re
from contextlib import suppress

import PROMPTS.context_rating_prompt as context_rating_prompt


def _extract_json_payload(text):
    if not text:
        return None

    raw = text.strip()

    # Try direct JSON parse first.
    with suppress(Exception):
        return json.loads(raw)

    # Fallback: extract first {...} JSON object from response.
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return None

    with suppress(Exception):
        return json.loads(match.group(0))

    return None


def get_context_rating(llm, question, context, max_context_chars=12000):
    safe_question = str(question or "").strip()
    safe_context = str(context or "")

    if len(safe_context) > max_context_chars:
        safe_context = safe_context[:max_context_chars]

    rating_prompt_text = context_rating_prompt.context_rating_prompt_template.format(
        question=safe_question,
        context=safe_context,
    )

    rating_llm_response = llm.invoke(rating_prompt_text)
    rating_raw = getattr(rating_llm_response, "content", str(rating_llm_response))
    rating_json = _extract_json_payload(rating_raw)

    if isinstance(rating_json, dict):
        return rating_json

    return {
        "relevance_score": None,
        "relevance_label": "unknown",
        "reason": "Unable to parse relevance rating output",
    }
