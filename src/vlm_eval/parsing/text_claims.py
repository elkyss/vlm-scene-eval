"""Rule-based claim extraction from a free-text scene description.

Deliberately simple and transparent: the taxonomy's synonyms, a count-word window
before each mention and negation handling ("no pedestrians", "without trucks").
Its own accuracy is covered by unit tests; known limitations are listed in the README.
"""

from __future__ import annotations

import re

from vlm_eval.domain import SceneFacts
from vlm_eval.parsing.claims import split_sentences
from vlm_eval.parsing.lexicon import COUNT_WORDS, IRREGULAR_PLURALS, NEGATION_WORDS
from vlm_eval.taxonomy import Taxonomy

_WINDOW = 4  # words before a mention that may carry a count or a negation
# Negation scope ends at a clause break inside a sentence (sentences are split first with the
# shared splitter in parsing/claims.py).
_CLAUSE_BREAK = re.compile(r"[;:]|,\s*(?:but|while|and there)\b|\bbut\b")
_POSTFIX_COUNT = re.compile(r"[\"']?\s*[:=]\s*[\"']?(\d+)")  # "car: 0", "car = 2", "car": "3"


def _count_from_window(words: list[str], is_plural: bool) -> int:
    for word in reversed(words):
        if word.isdigit():
            return int(word)
        if word in COUNT_WORDS:
            return COUNT_WORDS[word]
    return 3 if is_plural else 1


def extract_objects(text: str, taxonomy: Taxonomy) -> dict[str, str]:
    text = text.lower()
    for phrase in taxonomy.non_object_phrases:
        text = re.sub(rf"\b{re.escape(phrase)}\b", " ", text)

    result: dict[str, str] = {}
    sentences = split_sentences(text) or [text]
    for cls, spec in taxonomy.objects.items():
        counts: list[int] = []
        # Longest synonyms first so "traffic cones" is matched before "cones".
        words = sorted(spec.synonyms, key=len, reverse=True)
        pattern = "|".join(re.escape(w) for w in words)
        matches = [(m, s) for s in sentences for m in re.finditer(rf"\b({pattern})\b", s)]
        for match, sentence in matches:
            postfix = _POSTFIX_COUNT.match(sentence, match.end())
            if postfix:  # key-value style, e.g. from malformed JSON: "car: 0"
                counts.append(int(postfix.group(1)))
                continue
            before = sentence[: match.start()]
            breaks = list(_CLAUSE_BREAK.finditer(before))
            clause = before[breaks[-1].end() :] if breaks else before
            window = re.findall(r"[a-z0-9]+", clause)[-_WINDOW:]
            if any(w in NEGATION_WORDS for w in window):
                continue  # "no pedestrians", "without trucks" -> not a positive claim
            word = match.group(1)
            is_plural = word.endswith("s") or word in IRREGULAR_PLURALS
            counts.append(_count_from_window(window, is_plural))
        bucket = taxonomy.to_bucket(max(counts)) if counts else taxonomy.absent
        if bucket != taxonomy.absent:  # "car: 0" is not a car claim
            result[cls] = bucket
    return result


def extract_facts(text: str, taxonomy: Taxonomy) -> SceneFacts:
    """Turn a free-text description into checkable ``SceneFacts``."""
    attributes = {}
    for name in taxonomy.attribute_names:
        value = taxonomy.value_in_text(name, text)
        if value is not None:
            attributes[name] = value
    return SceneFacts(attributes=attributes, objects=extract_objects(text, taxonomy))
