import pytest

from tests.conftest import TAX
from vlm_eval.parsing import OutputParser, ParseError, normalise_bucket, parse_structured

VALID = (
    '{"description": "Two cars at night.", "time_of_day": "night", "road_condition": "dry", '
    '"scene_type": "road", "traffic_side": "left", '
    '"objects": {"car": "1-2", "truck": "0", "bus": 0}}'
)


def test_parses_valid_json() -> None:
    answer = parse_structured(VALID, TAX)
    assert answer.description == "Two cars at night."
    assert answer.facts.objects == {"car": "1-2"}
    assert answer.facts.attribute("time_of_day") == "night"
    assert answer.facts.attribute("traffic_side") == "left"


def test_parses_json_wrapped_in_fences_and_prose() -> None:
    raw = "Sure! Here is the JSON:\n```json\n" + VALID + "\n```\nHope this helps."
    assert parse_structured(raw, TAX).facts.objects == {"car": "1-2"}


def test_repairs_single_quotes_and_trailing_commas() -> None:
    raw = "{'description': 'x', 'objects': {'car': 3,},}"
    assert parse_structured(raw, TAX).facts.objects == {"car": "3-5"}


def test_repairs_truncated_output() -> None:
    raw = '{"description": "x", "objects": {"pedestrian": "6+"'
    assert parse_structured(raw, TAX).facts.objects == {"pedestrian": "6+"}


def test_maps_synonym_keys_and_values() -> None:
    raw = '{"time_of_day": "evening", "scene_type": "junction", "objects": {"bicycles": "two"}}'
    facts = parse_structured(raw, TAX).facts
    assert facts.objects == {"two_wheeler": "1-2"}
    assert facts.attribute("time_of_day") == "night"
    assert facts.attribute("scene_type") == "intersection"


def test_unknown_enum_value_becomes_none() -> None:
    assert parse_structured('{"time_of_day": "foggy"}', TAX).facts.attribute("time_of_day") is None


@pytest.mark.parametrize("raw", ["", "A car on the road.", "{not json at all"])
def test_invalid_output_raises(raw: str) -> None:
    with pytest.raises(ParseError):
        parse_structured(raw, TAX)


@pytest.mark.parametrize(
    ("value", "bucket"),
    [
        (0, "0"),
        (1, "1-2"),
        (4, "3-5"),
        (12, "6+"),
        ("3-5", "3-5"),
        ("3 - 5", "3-5"),
        ("none", "0"),
        ("many", "6+"),
        ("10+", "6+"),
        (True, "1-2"),
        ("2-4", "3-5"),
        ("?", None),
    ],
)
def test_normalise_bucket(value: object, bucket: str | None) -> None:
    assert normalise_bucket(value, TAX) == bucket


def test_parser_falls_back_to_text_on_invalid_json() -> None:
    parsed = OutputParser(TAX, expects_json=True).parse("I see a bus and two pedestrians.")
    assert not parsed.parse_ok
    assert parsed.facts_source == "text_fallback"
    assert parsed.facts.objects == {"bus": "1-2", "pedestrian": "1-2"}


def test_parser_free_text_prompt() -> None:
    parsed = OutputParser(TAX, expects_json=False).parse("A truck at night.")
    assert parsed.parse_ok
    assert parsed.facts_source == "text"
    assert parsed.facts.objects == {"truck": "1-2"}


def test_parser_json_extracts_text_facts_from_description() -> None:
    parsed = OutputParser(TAX, expects_json=True).parse(VALID)
    assert parsed.facts_source == "json"
    assert parsed.text_facts.objects == {"car": "1-2"}


def test_template_echo_is_a_format_failure() -> None:
    raw = '{"description": "<2-3 sentence description of the scene>", "objects": {}}'
    with pytest.raises(ParseError, match="template"):
        parse_structured(raw, TAX)


def test_echoed_value_placeholder_is_a_format_failure() -> None:
    raw = '{"description": "A road.", "objects": {"car": "<0|1-2|3-5|6+>"}}'
    with pytest.raises(ParseError, match="template"):
        parse_structured(raw, TAX)
