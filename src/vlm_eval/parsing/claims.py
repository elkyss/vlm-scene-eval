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
# Participle / "with" phrases add a separate fact ("..., passing a construction site").
# They are split off and wrapped like reference items, because they have no subject.
_PHRASE = re.compile(
    r",\s+(?=(?:passing|with|adding|showing|creating|leading|indicating|suggesting|"
    r"followed)\b)"
)
_MIN_WORDS = 2  # "Pedestrians cross." is a real claim


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text.strip()) if s.strip()]


def split_claims(text: str) -> list[str]:
    """Model description -> short claims.

    Sentences are split at clause boundaries (", and the ...", ";") and at participle or
    "with" phrases; a subject-less phrase becomes "The scene shows: <phrase>." so the judge
    can read it as a statement. Short claims are what NLI can check: a compound sentence is
    almost never entailed by any single fact, which would penalise detailed descriptions.
    """
    claims: list[str] = []
    for sentence in split_sentences(text):
        for clause in _CLAUSE.split(sentence):
            head, *phrases = _PHRASE.split(clause.strip(" ,.;"))
            head = head.strip(" ,.;")
            if len(head.split()) >= _MIN_WORDS:
                claims.append(head[0].upper() + head[1:] + ".")
            claims += [
                reference_hypothesis(p.strip(" ,.;"))
                for p in phrases
                if len(p.split()) >= _MIN_WORDS
            ]
    return claims


def split_reference(text: str) -> list[str]:
    """Human scene.description (a keyword list) -> items."""
    return [item.strip() for item in re.split(r"[,;]", text) if item.strip()]


def reference_hypothesis(item: str) -> str:
    """Generic wrapper so a bare keyword ("Night", "many peds") reads as a statement."""
    return f"The scene shows: {item}."
