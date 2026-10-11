import json

import pytest

from tests.conftest import TAX
from vlm_eval.parsing.answers import bucket_from_answer
from vlm_eval.prompting import QuestionnaireStrategy, SinglePromptStrategy, load_strategy
from vlm_eval.vlm import ImageSet, VLMRequest, VLMResponse


@pytest.mark.parametrize(
    ("answer", "bucket"),
    [
        ("3", "3-5"),
        ("There are two cars.", "1-2"),
        ("None.", "0"),
        ("No buses.", "0"),
        ("a few", "1-2"),
        ("A lot of people", "6+"),
        ("There is a truck", "1-2"),
        ("Many pedestrians", "6+"),
        ("I am not sure", "0"),
        ("unclear", None),
    ],
)
def test_bucket_from_answer(answer: str, bucket: str | None) -> None:
    assert bucket_from_answer(answer, TAX) == bucket


@pytest.mark.parametrize(
    ("field", "answer", "label"),
    [
        ("time_of_day", "Night.", "night"),
        ("time_of_day", "It is daytime", "day"),
        ("scene_type", "The car is in a parking lot.", "parking_lot"),
        ("scene_type", "intersection", "intersection"),
        ("road_condition", "Wet", "wet"),
        ("traffic_side", "Vehicles drive on the left.", "left"),
        ("road_condition", "maybe", None),
    ],
)
def test_value_in_answer(field: str, answer: str, label: str | None) -> None:
    assert TAX.value_in_answer(field, answer) == label


class ScriptedBackend:
    """Answers each question from a lookup on a keyword of the prompt."""

    name = "scripted"
    signature = "scripted"

    def __init__(self, script: dict[str, str]) -> None:
        self.script = script
        self.prompts: list[str] = []

    def generate(self, request: VLMRequest) -> VLMResponse:
        self.prompts.append(request.prompt)
        for keyword, answer in self.script.items():
            if keyword in request.prompt:
                return VLMResponse(answer, 0.5)
        return VLMResponse("0", 0.5)


def test_questionnaire_builds_facts_from_answers() -> None:
    strategy = QuestionnaireStrategy(
        "q",
        "Describe.",
        TAX,
        {
            "time_of_day": "day or night?",
            "count:car": "How many cars?",
            "count:bus": "How many buses?",
            "scene_type": "road or parking lot?",
        },
    )
    backend = ScriptedBackend(
        {
            "Describe": "Two cars on a street.",
            "day or night": "Night",
            "cars": "4",
            "buses": "none",
            "parking": "hmm",
        }
    )
    out = strategy.run(backend, "tok", ImageSet.from_paths(["img"], ["unused.jpg"]))
    facts = out.parsed.facts
    assert facts.objects == {"car": "3-5"}
    assert facts.attribute("time_of_day") == "night"
    assert facts.attribute("scene_type") is None
    assert out.parsed.parse_ok is False and "scene_type" in (out.parsed.parse_error or "")
    assert out.parsed.text_facts.objects == {"car": "1-2"}
    assert out.latency_s == pytest.approx(2.5)  # 1 description + 4 questions
    assert json.loads(out.raw_output)["answers"]["count:car"] == "4"


def test_load_strategy_by_file_type() -> None:
    assert isinstance(load_strategy("v1_open", TAX), SinglePromptStrategy)
    v2 = load_strategy("v2_structured", TAX)
    assert v2.expects_json  # type: ignore[attr-defined]
    assert '"two_wheeler": "0"' in v2.text  # type: ignore[attr-defined]  # rendered template
    q = load_strategy("v3_questionnaire", TAX)
    assert isinstance(q, QuestionnaireStrategy)
    assert len(q.questions) == 11
    with pytest.raises(KeyError, match="Available"):
        load_strategy("nope", TAX)


def test_version_changes_with_prompt_text() -> None:
    a, b = SinglePromptStrategy("a", "x", TAX), SinglePromptStrategy("a", "y", TAX)
    assert a.version != b.version
