"""Split texts into short, independently checkable pieces (rule-based, no model)."""

from __future__ import annotations

import re

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
# Only split where a new clause with its own subject usually starts. Phrases like
# ", with cars parked" are kept attached: on their own they have no subject.
_CLAUSE = re.compile(
    r";\s*|,\s+(?:and|while|but|whereas)\s+"
    r"(?=(?:the|a|an|there|it|our|we|they|[a-z]+s)\b)"
)
_MIN_WORDS = 2  # "Pedestrians cross." is a real claim


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text.strip()) if s.strip()]


def split_claims(text: str) -> list[str]:
    """Model description -> claims: sentences, further split at clause boundaries."""
    claims: list[str] = []
    for sentence in split_sentences(text):
        for clause in _CLAUSE.split(sentence):
            clause = clause.strip(" ,.;")
            if len(clause.split()) >= _MIN_WORDS:
                claims.append(clause[0].upper() + clause[1:] + ".")
    return claims


def split_reference(text: str) -> list[str]:
    """Human scene.description (a keyword list) -> items."""
    return [item.strip() for item in re.split(r"[,;]", text) if item.strip()]


def reference_hypothesis(item: str) -> str:
    """Generic wrapper so a bare keyword ("Night", "many peds") reads as a statement."""
    return f"The scene shows: {item}."
