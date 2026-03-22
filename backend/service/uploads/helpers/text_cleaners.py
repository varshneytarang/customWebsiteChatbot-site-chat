import re
import json
from contextlib import suppress
def _clip_text(value, max_chars):
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def _sanitize_extracted_text(value):
    raw = str(value or "")
    if not raw:
        return ""

    # Keep readable whitespace and printable characters; drop control/binary noise.
    cleaned_chars = []
    for ch in raw:
        code = ord(ch)
        if ch in {"\n", "\t", "\r"}:
            cleaned_chars.append(ch)
        elif 32 <= code <= 126:
            cleaned_chars.append(ch)
        elif ch.isprintable():
            cleaned_chars.append(ch)

    cleaned = "".join(cleaned_chars)
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _looks_like_gibberish(text):
    sample = str(text or "")[:6000]
    if not sample:
        return True

    total_len = len(sample)
    if total_len < 20:
        return True

    alnum_count = sum(ch.isalnum() for ch in sample)
    alpha_count = sum(ch.isalpha() for ch in sample)
    punctuation_count = sum((not ch.isalnum()) and (not ch.isspace()) for ch in sample)
    tokens = [tok for tok in re.split(r"\s+", sample) if tok]
    token_count = len(tokens)
    long_token_count = sum(1 for tok in tokens if len(tok) > 30)

    alnum_ratio = alnum_count / total_len
    alpha_ratio = (alpha_count / alnum_count) if alnum_count else 0.0
    punctuation_ratio = punctuation_count / total_len
    long_token_ratio = (long_token_count / token_count) if token_count else 1.0

    if total_len > 300 and alpha_count < 40:
        return True
    if punctuation_ratio > 0.35 and alpha_ratio < 0.45:
        return True
    if token_count >= 12 and long_token_ratio > 0.35:
        return True
    if alnum_ratio < 0.25:
        return True

    return False