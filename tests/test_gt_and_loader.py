import pytest

from tests.conftest import DATAROOT
from vlm_eval.gt import NuScenesGTProvider, category_to_class, facts_from_description
from vlm_eval.loaders import NuScenesLoader
from vlm_eval.loaders.nuscenes_loader import evenly_spaced


@pytest.mark.parametrize(
    ("category", "cls"),
    [
        ("vehicle.car", "car"),
        ("vehicle.bus.bendy", "bus"),
        ("vehicle.construction", "truck"),
        ("human.pedestrian.adult", "pedestrian"),
        ("human.pedestrian.personal_mobility", "pedestrian"),
        ("vehicle.motorcycle", "two_wheeler"),
        ("movable_object.trafficcone", "traffic_cone"),
        ("movable_object.debris", None),
        ("animal", None),
    ],
)
def test_category_mapping(category: str, cls: str | None) -> None:
    assert category_to_class(category) == cls


def test_facts_from_description() -> None:
    f = facts_from_description("Night, after rain, many peds, PMD", "singapore-hollandvillage")
    assert f.attribute("time_of_day") == "night"
    assert f.attribute("road_condition") == "wet"
    assert f.attribute("scene_type") == "road"
    assert f.attribute("traffic_side") == "left"
    f = facts_from_description("Parking lot, parked cars, intersection", "boston-seaport")
    assert f.attribute("scene_type") == "parking_lot"  # parking lot wins over intersection
    assert f.attribute("traffic_side") == "right"
    assert f.attribute("time_of_day") == "day"


@pytest.mark.parametrize(
    ("n", "k", "expected"),
    [(40, 5, [0, 10, 20, 29, 39]), (3, 5, [0, 1, 2]), (10, None, list(range(10))), (10, 0, [])],
)
def test_evenly_spaced(n: int, k: int | None, expected: list[int]) -> None:
    assert evenly_spaced(n, k) == expected


# --- real data (skipped when the dataset is not present) -----------------------------


def test_loader_on_mini(nusc) -> None:  # type: ignore[no-untyped-def]
    samples = list(NuScenesLoader(str(DATAROOT), frames_per_scene=5, nusc=nusc))
    assert len(samples) == 50
    assert len({s.scene_name for s in samples}) == 10
    assert all(s.image_paths["CAM_FRONT"].exists() for s in samples)
    only = list(
        NuScenesLoader(str(DATAROOT), frames_per_scene=None, scenes=["scene-0061"], nusc=nusc)
    )
    assert len(only) == 39


def test_gt_on_known_frame(nusc) -> None:  # type: ignore[no-untyped-def]
    sample = next(
        iter(NuScenesLoader(str(DATAROOT), frames_per_scene=1, scenes=["scene-1094"], nusc=nusc))
    )
    gt = NuScenesGTProvider(str(DATAROOT), nusc=nusc).get(sample)
    assert gt.facts.attribute("time_of_day") == "night"
    assert gt.facts.attribute("traffic_side") == "left"
    # strict set is a subset of the loose set, and every object is in front of the camera
    assert set(gt.facts.objects) <= set(gt.loosely_present)
    assert all(o.distance_m > 0 for o in gt.objects)


def test_stricter_visibility_never_adds_objects(nusc) -> None:  # type: ignore[no-untyped-def]
    samples = list(NuScenesLoader(str(DATAROOT), frames_per_scene=2, nusc=nusc))
    lenient = NuScenesGTProvider(str(DATAROOT), min_visibility=1, max_distance_m=1e9, nusc=nusc)
    strict = NuScenesGTProvider(str(DATAROOT), min_visibility=4, max_distance_m=20, nusc=nusc)
    for s in samples:
        assert set(strict.get(s).facts.objects) <= set(lenient.get(s).facts.objects)
