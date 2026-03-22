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


def _coerce_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    if isinstance(value, str):
        # Accept common model outputs like "72", "72%", "score: 72"
        m = re.search(r"-?\d+", value)
        if m:
            with suppress(Exception):
                return int(m.group(0))
    return None


def _normalize_rating_payload(payload):
    if not isinstance(payload, dict):
        return None

    raw_score = payload.get("relevance_score")
    score = _coerce_int(raw_score)
    if score is None:
        return None

    score = max(0, min(100, score))

    raw_label = str(payload.get("relevance_label", "")).strip().lower()
    if raw_label not in {"low", "medium", "high"}:
        if score <= 40:
            raw_label = "low"
        elif score <= 70:
            raw_label = "medium"
        else:
            raw_label = "high"

    reason = str(payload.get("reason", "")).strip()
    if not reason:
        reason = "Model did not provide a reason"

    return {
        "relevance_score": score,
        "relevance_label": raw_label,
        "reason": reason,
    }


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

    normalized = _normalize_rating_payload(rating_json)
    if normalized is not None:
        return normalized

    return {
        "relevance_score": 0,
        "relevance_label": "low",
        "reason": "Unable to parse relevance rating output",
    }
