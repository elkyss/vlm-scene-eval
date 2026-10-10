"""Parsers for short answers to single questions (the questionnaire / VQA strategy)."""

from __future__ import annotations

import re

from vlm_eval.parsing.lexicon import COUNT_WORDS, NEGATION_WORDS
from vlm_eval.taxonomy import Taxonomy

_ARTICLES = {"a", "an"}


def count_from_answer(answer: str) -> int | None:
    """Count in a short answer ("3", "There are two cars.", "None") or None if unclear."""
    tokens = re.findall(r"[a-z]+|\d+", answer.lower())
    for i, token in enumerate(tokens):
        if token.isdigit():
            return int(token)
        if token in NEGATION_WORDS:
            return 0
        if token in _ARTICLES:  # "a few" / "a lot" -> look at the next word
            nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
            return COUNT_WORDS.get(nxt, 1)
        if token in COUNT_WORDS:
            return COUNT_WORDS[token]
    return None


def bucket_from_answer(answer: str, taxonomy: Taxonomy) -> str | None:
    count = count_from_answer(answer)
    return None if count is None else taxonomy.to_bucket(count)
