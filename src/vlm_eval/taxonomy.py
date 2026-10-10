"""The label vocabulary of an evaluation, loaded from ``taxonomies/<name>.yaml``.

A ``Taxonomy`` answers every domain question the generic code needs: which object
classes and attributes exist, their allowed values, how counts are bucketed, and which
words express each label. Parsers, prompts, metrics and writers receive it by
injection, so none of them hardcode driving-specific labels.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

TAXONOMY_DIR = Path(__file__).parent / "taxonomies"


class CountBucket(BaseModel):
    label: str
    max: int | None  # inclusive upper bound, None = unbounded


class ObjectSpec(BaseModel):
    display: str
    synonyms: list[str]
    singular: str = ""  # natural name used when generating sentences ("traffic cone")
    plural: str = ""

    def name(self, count: int) -> str:
        if count == 1:
            return self.singular or self.synonyms[0]
        return self.plural or (self.synonyms[1] if len(self.synonyms) > 1 else self.synonyms[0])


class AttributeSpec(BaseModel):
    question: str = ""
    values: dict[str, list[str]]  # label -> synonyms in structured / short answers
    text_cues: dict[str, list[str]] = Field(default_factory=dict)  # label -> phrases in prose

    def cues(self) -> dict[str, list[str]]:
        return self.text_cues or self.values


def _phrase(word: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(word.lower())}\b")


def _first_label(text: str, table: dict[str, list[str]]) -> str | None:
    """Label of the earliest-ordered entry with any matching phrase."""
    lowered = text.lower()
    for label, words in table.items():
        if any(_phrase(w).search(lowered) for w in words):
            return label
    return None


class Taxonomy(BaseModel):
    name: str
    count_buckets: list[CountBucket]
    objects: dict[str, ObjectSpec]
    attributes: dict[str, AttributeSpec]
    non_object_phrases: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> Taxonomy:
        if not self.count_buckets or self.count_buckets[0].max != 0:
            raise ValueError("the first count bucket must be the 'absent' bucket (max: 0)")
        if self.count_buckets[-1].max is not None:
            raise ValueError("the last count bucket must be unbounded (max: null)")
        return self

    # --- vocabulary ------------------------------------------------------------------
    @property
    def object_classes(self) -> tuple[str, ...]:
        return tuple(self.objects)

    @property
    def attribute_names(self) -> tuple[str, ...]:
        return tuple(self.attributes)

    @property
    def bucket_labels(self) -> tuple[str, ...]:
        return tuple(b.label for b in self.count_buckets)

    @property
    def absent(self) -> str:
        return self.count_buckets[0].label

    def bucket_index(self, label: str) -> int:
        return self.bucket_labels.index(label)

    def to_bucket(self, count: int) -> str:
        for bucket in self.count_buckets:
            if bucket.max is None or count <= bucket.max:
                return bucket.label
        raise AssertionError("unreachable: last bucket is unbounded")

    def class_for_word(self, word: str) -> str | None:
        word = word.strip().lower()
        if word in self.objects:
            return word
        return next((c for c, s in self.objects.items() if word in s.synonyms), None)

    # --- attribute value matching ----------------------------------------------------
    def normalise_value(self, attribute: str, value: object) -> str | None:
        """Exact match of a structured value ("Night" -> night, "junction" -> intersection)."""
        if not isinstance(value, str):
            return None
        value = value.strip().lower()
        for label, synonyms in self.attributes[attribute].values.items():
            if value == label or value in synonyms:
                return label
        return None

    def value_in_answer(self, attribute: str, answer: str) -> str | None:
        """Value mentioned earliest in a short answer ("It is daytime." -> day)."""
        lowered = answer.lower()
        hits = []
        for label, synonyms in self.attributes[attribute].values.items():
            for word in [label, *synonyms]:
                match = _phrase(word).search(lowered)
                if match:
                    hits.append((match.start(), label))
        return min(hits)[1] if hits else None

    def value_in_text(self, attribute: str, text: str) -> str | None:
        """Value expressed in free prose, using the attribute's text cues."""
        return _first_label(text, self.attributes[attribute].cues())


@lru_cache(maxsize=8)
def load_taxonomy(name_or_path: str = "driving") -> Taxonomy:
    path = Path(name_or_path)
    if not path.suffix:
        path = TAXONOMY_DIR / f"{name_or_path}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in TAXONOMY_DIR.glob("*.yaml"))
        raise KeyError(f"Unknown taxonomy {name_or_path!r}. Available: {available}")
    return Taxonomy.model_validate(yaml.safe_load(path.read_text()))
