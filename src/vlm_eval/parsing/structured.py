"""Parse and normalise the structured (JSON) answer of a VLM.

Small VLMs often wrap JSON in prose or markdown fences, use single quotes, trailing
commas, integers instead of buckets or synonyms instead of our labels. We repair the
common cases; anything we cannot repair is reported as a format failure.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from vlm_eval.domain import SceneFacts
from vlm_eval.parsing.answers import count_from_answer
from vlm_eval.taxonomy import Taxonomy


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class StructuredAnswer:
    description: str
    facts: SceneFacts


def _extract_json_block(raw: str) -> str:
    text = re.sub(r"```(?:json)?", "", raw)
    start = text.find("{")
    if start == -1:
        raise ParseError("no JSON object found")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    # Truncated output (ran out of tokens): close the open braces.
    return text[start:] + "}" * depth


def _loads_lenient(block: str) -> dict[str, Any]:
    attempts = [
        block,
        re.sub(r",\s*([}\]])", r"\1", block),  # trailing commas
        re.sub(r",\s*([}\]])", r"\1", block.replace("'", '"')),  # single quotes
    ]
    for attempt in attempts:
        try:
            data = json.loads(attempt)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    raise ParseError("invalid JSON")


def normalise_bucket(value: Any, taxonomy: Taxonomy) -> str | None:
    """Accept a bucket label, a number, a range ("2-4") or a count word."""
    if isinstance(value, bool):
        return taxonomy.to_bucket(int(value))
    if isinstance(value, int | float):
        return taxonomy.to_bucket(int(value))
    if not isinstance(value, str):
        return None
    text = value.strip().lower().replace(" ", "")
    if text in taxonomy.bucket_labels:
        return text
    if text in {"yes", "true", "present"}:
        return taxonomy.to_bucket(1)
    if re.fullmatch(r"\d+-\d+", text):  # a range: use its upper end
        return taxonomy.to_bucket(int(text.split("-")[1]))
    count = count_from_answer(text.rstrip("+"))
    return None if count is None else taxonomy.to_bucket(count)


_PLACEHOLDER = re.compile(r"^\s*<.*>\s*$")


def _echoed_placeholders(data: dict[str, Any]) -> bool:
    values = list(data.values())
    if isinstance(data.get("objects"), dict):
        values += list(data["objects"].values())
    return any(isinstance(v, str) and _PLACEHOLDER.match(v) for v in values)


def parse_structured(raw: str, taxonomy: Taxonomy) -> StructuredAnswer:
    """Parse a raw VLM answer into a description and ``SceneFacts``; raises ParseError."""
    data = _loads_lenient(_extract_json_block(raw))
    if _echoed_placeholders(data):
        raise ParseError("template echoed: a <placeholder> from the prompt was copied")

    raw_objects = data.get("objects", {})
    if isinstance(raw_objects, list):  # e.g. ["car", "pedestrian"]
        raw_objects = {str(name): 1 for name in raw_objects}
    if not isinstance(raw_objects, dict):
        raise ParseError("'objects' is not a mapping")
    objects: dict[str, str] = {}
    for key, value in raw_objects.items():
        cls = taxonomy.class_for_word(str(key))
        bucket = normalise_bucket(value, taxonomy)
        if cls is None or bucket is None or bucket == taxonomy.absent:
            continue
        current = objects.get(cls, taxonomy.absent)
        objects[cls] = max(current, bucket, key=taxonomy.bucket_index)

    attributes = {}
    for name in taxonomy.attribute_names:
        value = taxonomy.normalise_value(name, data.get(name))
        if value is not None:
            attributes[name] = value

    description = data.get("description")
    return StructuredAnswer(
        description=description if isinstance(description, str) else "",
        facts=SceneFacts(attributes=attributes, objects=objects),
    )
