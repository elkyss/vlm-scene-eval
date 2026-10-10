"""Prompting strategies: how a frame is turned into VLM calls and then into facts.

* ``SinglePromptStrategy``: one prompt (free text or JSON) -> ``OutputParser``.
* ``QuestionnaireStrategy``: one open description + one short question per fact
  (VQA style). Costs more calls, but small VLMs answer single questions far more
  reliably than they fill a JSON schema.

Prompts are templates rendered from the taxonomy (``{json_template}``,
``{json_schema}``, ``{bucket_list}``, ``{object_list}``; questions per class and
attribute), so changing the label set does not mean rewriting prompts.

Strategies are loaded by name from ``prompts/<name>.txt`` (single prompt) or
``prompts/<name>.yaml`` (questionnaire). The version includes a content hash, so
editing a prompt file changes the version recorded with every prediction.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import yaml

from vlm_eval.domain import SceneFacts
from vlm_eval.parsing import OutputParser, ParsedOutput, bucket_from_answer, extract_facts
from vlm_eval.taxonomy import Taxonomy
from vlm_eval.vlm.base import ImageSet, VLMBackend, VLMRequest

PROMPT_DIR = Path(__file__).parent / "prompts"


@dataclass(frozen=True)
class StrategyOutput:
    raw_output: str
    parsed: ParsedOutput
    latency_s: float


class PromptStrategy(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def run(self, backend: VLMBackend, sample_token: str, images: ImageSet) -> StrategyOutput: ...


def content_version(name: str, text: str) -> str:
    """Prompt name plus a content hash: editing a prompt file changes its recorded version."""
    return f"{name}@{hashlib.sha256(text.encode()).hexdigest()[:8]}"


def render_template(template: str, taxonomy: Taxonomy) -> str:
    example = {
        "description": "<2-3 sentence description of the scene>",
        **{a: " or ".join(spec.values) for a, spec in taxonomy.attributes.items()},
        "objects": {c: taxonomy.absent for c in taxonomy.object_classes},
    }
    # Same schema but with neutral placeholders: concrete example values ("0") anchor
    # small models, which then copy them instead of looking at the image.
    schema = {
        "description": "<2-3 sentence description of the scene>",
        **{a: f"<{'|'.join(spec.values)}>" for a, spec in taxonomy.attributes.items()},
        "objects": {c: f"<{'|'.join(taxonomy.bucket_labels)}>" for c in taxonomy.object_classes},
    }
    fields = {
        "json_template": json.dumps(example),
        "json_schema": json.dumps(schema),
        "bucket_list": ", ".join(f'"{b}"' for b in taxonomy.bucket_labels),
        "object_list": ", ".join(spec.display for spec in taxonomy.objects.values()),
    }
    return template.format_map(fields) if "{" in template else template


@dataclass(frozen=True)
class SinglePromptStrategy:
    name: str
    text: str
    taxonomy: Taxonomy

    @property
    def version(self) -> str:
        return content_version(self.name, self.text)

    @property
    def expects_json(self) -> bool:
        return "JSON" in self.text

    def run(self, backend: VLMBackend, sample_token: str, images: ImageSet) -> StrategyOutput:
        response = backend.generate(VLMRequest(sample_token, images, self.text))
        parsed = OutputParser(self.taxonomy, self.expects_json).parse(response.text)
        return StrategyOutput(response.text, parsed, response.latency_s)


@dataclass(frozen=True)
class QuestionnaireStrategy:
    """``questions`` maps ``<attribute>`` or ``count:<class>`` to the question text."""

    name: str
    description_prompt: str
    taxonomy: Taxonomy
    questions: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_spec(
        cls, name: str, spec: dict[str, str], taxonomy: Taxonomy
    ) -> QuestionnaireStrategy:
        questions = {a: s.question for a, s in taxonomy.attributes.items() if s.question}
        questions |= {
            f"count:{c}": spec["count_question"].format(display=o.display)
            for c, o in taxonomy.objects.items()
        }
        return cls(name, spec["description"].strip(), taxonomy, questions)

    @property
    def version(self) -> str:
        return content_version(self.name, self.description_prompt + json.dumps(self.questions))

    def run(self, backend: VLMBackend, sample_token: str, images: ImageSet) -> StrategyOutput:
        desc = backend.generate(VLMRequest(sample_token, images, self.description_prompt))
        latency = desc.latency_s
        answers: dict[str, str] = {}
        for key, question in self.questions.items():
            response = backend.generate(VLMRequest(sample_token, images, question))
            answers[key] = response.text
            latency += response.latency_s

        facts, unparsed = self._facts(answers)
        description = desc.text.strip()
        parsed = ParsedOutput(
            description=description,
            facts=facts,
            facts_source="vqa",
            text_facts=extract_facts(description, self.taxonomy),
            parse_ok=not unparsed,
            parse_error=f"unparseable answers: {unparsed}" if unparsed else None,
        )
        raw = json.dumps({"description": description, "answers": answers})
        return StrategyOutput(raw, parsed, latency)

    def _facts(self, answers: dict[str, str]) -> tuple[SceneFacts, list[str]]:
        attributes: dict[str, str] = {}
        objects: dict[str, str] = {}
        unparsed = []
        for key, answer in answers.items():
            if key.startswith("count:"):
                bucket = bucket_from_answer(answer, self.taxonomy)
                if bucket is None:
                    unparsed.append(key)
                elif bucket != self.taxonomy.absent:
                    objects[key.split(":", 1)[1]] = bucket
            else:
                value = self.taxonomy.value_in_answer(key, answer)
                if value is None:
                    unparsed.append(key)
                else:
                    attributes[key] = value
        return SceneFacts(attributes=attributes, objects=objects), unparsed


def load_strategy(name: str, taxonomy: Taxonomy) -> PromptStrategy:
    txt, yml = PROMPT_DIR / f"{name}.txt", PROMPT_DIR / f"{name}.yaml"
    if txt.exists():
        return SinglePromptStrategy(
            name, render_template(txt.read_text().strip(), taxonomy), taxonomy
        )
    if yml.exists():
        return QuestionnaireStrategy.from_spec(name, yaml.safe_load(yml.read_text()), taxonomy)
    available = sorted(p.stem for p in PROMPT_DIR.glob("*.*") if p.suffix in {".txt", ".yaml"})
    raise KeyError(f"Unknown prompt {name!r}. Available: {available}")


@dataclass(frozen=True)
class ScenePrompt:
    """Prompt for one multi-frame scene call; ``{n_frames}`` and ``{spacing}`` are filled in."""

    name: str
    template: str

    def render(self, n_frames: int, span_s: float) -> str:
        spacing = max(1, round(span_s / max(1, n_frames - 1)))
        return self.template.format(n_frames=n_frames, spacing=spacing)

    @property
    def version(self) -> str:
        return content_version(self.name, self.template)


def load_scene_prompt(name: str) -> ScenePrompt:
    path = PROMPT_DIR / f"{name}.txt"
    if not path.exists():
        available = sorted(p.stem for p in PROMPT_DIR.glob("scene_*.txt"))
        raise KeyError(f"Unknown scene prompt {name!r}. Available: {available}")
    return ScenePrompt(name, path.read_text().strip())
