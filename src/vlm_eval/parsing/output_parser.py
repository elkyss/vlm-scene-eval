"""Turns a raw VLM answer into description + facts, whatever the prompt style."""

from __future__ import annotations

from dataclasses import dataclass

from vlm_eval.domain import SceneFacts
from vlm_eval.parsing.structured import ParseError, parse_structured
from vlm_eval.parsing.text_claims import extract_facts
from vlm_eval.taxonomy import Taxonomy


@dataclass(frozen=True)
class ParsedOutput:
    description: str
    facts: SceneFacts
    facts_source: str  # "json" | "vqa" | "text" | "text_fallback"
    text_facts: SceneFacts
    parse_ok: bool
    parse_error: str | None = None


class OutputParser:
    """Policy:

    * free-text prompt -> facts come from claim extraction on the text.
    * JSON prompt, valid JSON -> facts from JSON; text facts from its ``description``.
    * JSON prompt, invalid JSON -> counted as a format failure, facts fall back to
      claim extraction on the raw text so the frame is still scored.
    """

    def __init__(self, taxonomy: Taxonomy, expects_json: bool) -> None:
        self.taxonomy = taxonomy
        self.expects_json = expects_json

    def parse(self, raw: str) -> ParsedOutput:
        if not self.expects_json:
            facts = extract_facts(raw, self.taxonomy)
            return ParsedOutput(raw.strip(), facts, "text", facts, parse_ok=bool(raw.strip()))
        try:
            answer = parse_structured(raw, self.taxonomy)
        except ParseError as exc:
            facts = extract_facts(raw, self.taxonomy)
            return ParsedOutput(raw.strip(), facts, "text_fallback", facts, False, str(exc))
        return ParsedOutput(
            description=answer.description,
            facts=answer.facts,
            facts_source="json",
            text_facts=extract_facts(answer.description, self.taxonomy),
            parse_ok=True,
        )
