"""Language-level (domain-independent) words used by the parsers.

Domain vocabulary (object synonyms, attribute values) lives in the taxonomy; this
module only knows how English expresses quantity and negation.
"""

from __future__ import annotations

# Count words mapped to a representative number; the taxonomy turns it into a bucket.
COUNT_WORDS: dict[str, int] = {
    "a": 1,
    "an": 1,
    "one": 1,
    "single": 1,
    "lone": 1,
    "two": 2,
    "couple": 2,
    "pair": 2,
    "few": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "several": 4,
    "some": 3,
    "multiple": 4,
    "various": 4,
    "number": 4,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "many": 8,
    "lots": 8,
    "lot": 8,
    "numerous": 8,
    "dozen": 12,
    "dozens": 24,
    "crowd": 8,
    "busy": 8,
    "heavy": 8,
}

NEGATION_WORDS: frozenset[str] = frozenset({"no", "without", "not", "zero", "none", "nor"})

# Plural nouns that do not end in "s".
IRREGULAR_PLURALS: frozenset[str] = frozenset(
    {"people", "men", "women", "children", "crowd", "peds"}
)
