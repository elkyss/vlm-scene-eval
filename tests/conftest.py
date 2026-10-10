from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image

from vlm_eval.domain import AnnotatedObject, GroundTruth, Prediction, Sample, SceneFacts
from vlm_eval.taxonomy import Taxonomy, load_taxonomy

TAX: Taxonomy = load_taxonomy("driving")

DATAROOT = Path(__file__).resolve().parents[1] / "data" / "nuscenes"


def make_gt(
    token: str = "s1",
    scene: str = "scene-a",
    frame: int = 0,
    objects: dict[str, str] | None = None,
    loose: list[str] | None = None,
    night: bool = False,
    reference: str = "cars, peds",
) -> GroundTruth:
    objects = {"car": "3-5", "pedestrian": "1-2"} if objects is None else objects
    return GroundTruth(
        sample_token=token,
        scene_name=scene,
        frame_index=frame,
        location="singapore-onenorth",
        reference_text=reference,
        facts=SceneFacts(
            attributes={
                "time_of_day": "night" if night else "day",
                "road_condition": "dry",
                "scene_type": "intersection",
                "traffic_side": "left",
            },
            objects=objects,
        ),
        loosely_present=sorted(set(objects) | set(loose or [])),
        objects=[
            AnnotatedObject(cls=c, category=c, visibility=4, distance_m=10.0) for c in objects
        ],
    )


def make_pred(
    token: str = "s1",
    scene: str = "scene-a",
    objects: dict[str, str] | None = None,
    time: str | None = "day",
    description: str = "",
    parse_ok: bool = True,
    text_objects: dict[str, str] | None = None,
) -> Prediction:
    attributes = {"road_condition": "dry", "scene_type": "intersection", "traffic_side": "left"}
    if time:
        attributes["time_of_day"] = time
    facts = SceneFacts(attributes=attributes, objects=objects or {})
    return Prediction(
        sample_token=token,
        scene_name=scene,
        model="m",
        prompt_version="p",
        raw_output="",
        description=description,
        facts=facts,
        facts_source="json",
        text_facts=SceneFacts(objects=text_objects or {}),
        parse_ok=parse_ok,
    )


class FakeLoader:
    """In-memory SceneLoader: 2 scenes x 3 frames with tiny generated images."""

    def __init__(self, tmp: Path) -> None:
        self.samples = []
        for s in range(2):
            for f in range(3):
                path = tmp / f"img_{s}_{f}.jpg"
                Image.new("RGB", (32, 18), (s * 100, f * 50, 0)).save(path)
                self.samples.append(
                    Sample(
                        sample_token=f"tok-{s}-{f}",
                        scene_token=f"scene-{s}",
                        scene_name=f"scene-{s}",
                        frame_index=f,
                        timestamp=f,
                        image_paths={"CAM_FRONT": path},
                    )
                )

    def __iter__(self) -> Iterator[Sample]:
        return iter(self.samples)


class FakeGTProvider:
    def get(self, sample: Sample) -> GroundTruth:
        night = sample.scene_name == "scene-1"
        objects = {"car": "3-5"} if sample.frame_index % 2 else {"car": "1-2", "bus": "1-2"}
        return make_gt(
            sample.sample_token,
            sample.scene_name,
            sample.frame_index,
            objects,
            loose=["truck"],
            night=night,
        )


@pytest.fixture
def fake_loader(tmp_path: Path) -> FakeLoader:
    return FakeLoader(tmp_path)


@pytest.fixture
def nusc():  # type: ignore[no-untyped-def]
    if not (DATAROOT / "v1.0-mini").exists():
        pytest.skip("nuScenes mini not available under data/nuscenes")
    from vlm_eval.nuscenes_db import get_nuscenes

    return get_nuscenes(str(DATAROOT), "v1.0-mini")
