import pytest

from tests.conftest import TAX
from vlm_eval.parsing import extract_facts, extract_objects


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("A red car is parked on the street.", {"car": "1-2"}),
        ("Several cars and two pedestrians at a crossing.", {"car": "3-5", "pedestrian": "1-2"}),
        ("Many people are walking.", {"pedestrian": "6+"}),
        ("There are 7 vehicles in the queue.", {"car": "6+"}),
        ("A cyclist rides past a bus.", {"two_wheeler": "1-2", "bus": "1-2"}),
        ("Orange traffic cones block the lane.", {"traffic_cone": "3-5"}),
        ("", {}),
    ],
)
def test_extract_objects_counts(text: str, expected: dict[str, str]) -> None:
    assert extract_objects(text, TAX) == expected


@pytest.mark.parametrize(
    "text",
    [
        "There are no pedestrians.",
        "An empty road without any pedestrians or cyclists.",
        "No people, no bikes.",
    ],
)
def test_negated_mentions_are_not_claims(text: str) -> None:
    objects = extract_objects(text, TAX)
    assert "pedestrian" not in objects


def test_negation_does_not_leak_across_clauses() -> None:
    assert extract_objects("No trucks. A pedestrian waits.", TAX) == {"pedestrian": "1-2"}


@pytest.mark.parametrize(
    "text",
    [
        "Cars wait at the bus stop.",
        "A bike lane runs along the street.",
        "People cross at the pedestrian crossing.",
    ],
)
def test_non_object_phrases_are_ignored(text: str) -> None:
    objects = extract_objects(text, TAX)
    assert "bus" not in objects
    assert "two_wheeler" not in objects


def test_car_park_is_scene_not_car() -> None:
    facts = extract_facts("A quiet car park at night.", TAX)
    assert facts.objects == {}
    assert facts.attribute("scene_type") == "parking_lot"
    assert facts.attribute("time_of_day") == "night"


def test_attributes_unstated_are_none() -> None:
    facts = extract_facts("A truck.", TAX)
    assert facts.attributes == {}


def test_wet_road_and_intersection() -> None:
    facts = extract_facts("A wet intersection after rain during the day.", TAX)
    assert facts.attribute("road_condition") == "wet"
    assert facts.attribute("scene_type") == "intersection"
    assert facts.attribute("time_of_day") == "day"


def test_dark_car_is_not_night() -> None:
    assert extract_facts("A dark car in the daylight.", TAX).attribute("time_of_day") == "day"


def test_ego_vehicle_is_not_a_car_claim() -> None:
    assert extract_objects("The image is taken from the front of a car. A bus.", TAX) == {
        "bus": "1-2"
    }


def test_repetition_loop_detector() -> None:
    from vlm_eval.evaluation.metrics.robustness import has_repetition_loop

    loop = "There are two people on the sidewalk. " * 3
    assert has_repetition_loop(loop)
    assert not has_repetition_loop("A car. A bus. A truck on the road.")
    per_image = (
        "The first image shows a car on the road. The second image shows a car on the "
        "road. The third image shows a car on the road."
    )
    assert has_repetition_loop(per_image)  # only the ordinal changes
    assert not has_repetition_loop("The first image shows a car. The second shows a bus stop.")


def test_explicit_zero_count_is_not_a_claim() -> None:
    assert extract_objects("car: 0, truck: 2", TAX) == {"truck": "1-2"}
