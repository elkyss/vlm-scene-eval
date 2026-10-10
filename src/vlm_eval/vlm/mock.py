"""Deterministic fake backends used to test the pipeline and sanity-check the metrics."""

from __future__ import annotations

import json
from collections.abc import Mapping

from vlm_eval.domain import GroundTruth
from vlm_eval.vlm.base import BACKENDS, VLMRequest, VLMResponse

_PLURALS = {
    "car": "cars",
    "truck": "trucks",
    "bus": "buses",
    "pedestrian": "pedestrians",
    "two_wheeler": "bicycles",
    "traffic_cone": "traffic cones",
    "barrier": "barriers",
}
_COUNT_WORD = {"1-2": "two", "3-5": "four", "6+": "many"}


def facts_to_response(gt: GroundTruth) -> str:
    """Render ground truth as a perfect structured answer (the 'oracle').

    The description names each class by its key (e.g. "four car"), which the text
    claim extractor maps back through the taxonomy synonyms.
    """
    facts = gt.facts
    objects = ", ".join(f"{_COUNT_WORD.get(b, b)} {c}" for c, b in facts.objects.items())
    attrs = ", ".join(v.replace("_", " ") for v in facts.attributes.values())
    payload = {
        "description": f"{attrs}. Visible: {objects or 'nothing notable'}.",
        **facts.attributes,
        "objects": dict(facts.objects),
    }
    return json.dumps(payload)


@BACKENDS.register("mock")
class MockBackend:
    """Modes:

    * ``empty``: answers nothing (recall must be 0, format failures 100%).
    * ``always_car``: always claims a car and a pedestrian on a sunny road.
    * ``fixed``: returns ``fixed_response`` for every frame.
    * ``table``: returns ``responses[request.sample_token]`` (e.g. a scene oracle).
    """

    def __init__(
        self,
        mode: str = "always_car",
        fixed_response: str = "",
        responses: Mapping[str, str] | None = None,
        label: str | None = None,
    ) -> None:
        if mode == "table" and responses is None:
            raise ValueError("table mode needs responses")
        self.mode = mode
        self.fixed_response = fixed_response
        self.label = label or mode
        self._responses = responses or {}

    @property
    def name(self) -> str:
        return f"mock-{self.label}"

    @property
    def signature(self) -> str:
        return f"{self.name}|{self.fixed_response}"

    def generate(self, request: VLMRequest) -> VLMResponse:
        return VLMResponse(self._answer(request))

    def _answer(self, request: VLMRequest) -> str:
        if self.mode == "empty":
            return ""
        if self.mode == "always_car":
            return json.dumps(
                {
                    "description": "A car and a pedestrian on a sunny road.",
                    "time_of_day": "day",
                    "road_condition": "dry",
                    "scene_type": "road",
                    "traffic_side": "right",
                    "objects": {"car": "1-2", "pedestrian": "1-2"},
                }
            )
        if self.mode == "fixed":
            return self.fixed_response
        if self.mode == "table":
            return self._responses[request.sample_token]
        raise ValueError(f"unknown mock mode {self.mode!r}")
