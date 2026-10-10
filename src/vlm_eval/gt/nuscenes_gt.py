"""Ground truth derived from nuScenes annotations and metadata.

* Objects: 3D boxes that project into the camera image (``BoxVisibility.ANY``).
  The *strict* set (used for recall and counts) keeps boxes that are at least
  ``min_visibility`` visible and within ``max_distance_m``. The *loose* set (any box
  in the image) is used for lenient precision.
* Time of day / road condition / scene type: keywords in the human-written
  ``scene.description``. These are scene-level labels applied to every frame.
* Traffic side: from ``log.location`` (Singapore drives on the left, Boston on the right).

This adapter is the only place that knows nuScenes; it emits labels of the configured
taxonomy (the defaults below target ``taxonomies/driving.yaml``).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

import numpy as np

from vlm_eval.domain import AnnotatedObject, GroundTruth, Sample, SceneFacts
from vlm_eval.gt.base import GT_PROVIDERS
from vlm_eval.nuscenes_db import get_nuscenes
from vlm_eval.taxonomy import Taxonomy, load_taxonomy

# Ordered: first matching prefix wins.
_CATEGORY_PREFIXES: tuple[tuple[str, str], ...] = (
    ("vehicle.car", "car"),
    ("vehicle.emergency.police", "car"),
    ("vehicle.bus", "bus"),
    ("vehicle.truck", "truck"),
    ("vehicle.trailer", "truck"),
    ("vehicle.construction", "truck"),
    ("vehicle.emergency.ambulance", "truck"),
    ("vehicle.bicycle", "two_wheeler"),
    ("vehicle.motorcycle", "two_wheeler"),
    ("human.pedestrian", "pedestrian"),
    ("movable_object.trafficcone", "traffic_cone"),
    ("movable_object.barrier", "barrier"),
)


def category_to_class(category: str) -> str | None:
    """Map a fine nuScenes category to one of our coarse classes (None = ignored)."""
    for prefix, cls in _CATEGORY_PREFIXES:
        if category.startswith(prefix):
            return cls
    return None


def facts_from_description(description: str, location: str) -> SceneFacts:
    """Scene-level attributes from the free-text ``scene.description`` and log location."""
    text = description.lower()
    scene_type = "road"
    if "parking lot" in text:
        scene_type = "parking_lot"
    elif "intersection" in text:
        scene_type = "intersection"
    return SceneFacts(
        attributes={
            "time_of_day": "night" if re.search(r"\bnight\b", text) else "day",
            "road_condition": "wet" if "rain" in text else "dry",
            "scene_type": scene_type,
            "traffic_side": "left" if location.startswith("singapore") else "right",
        }
    )


@GT_PROVIDERS.register("nuscenes")
class NuScenesGTProvider:
    def __init__(
        self,
        dataroot: str,
        version: str = "v1.0-mini",
        camera: str = "CAM_FRONT",
        min_visibility: int = 2,
        max_distance_m: float = 50.0,
        taxonomy: Taxonomy | None = None,
        nusc: Any | None = None,
    ) -> None:
        self.taxonomy = taxonomy or load_taxonomy("driving")
        self.camera = camera
        self.min_visibility = min_visibility
        self.max_distance_m = max_distance_m
        self._nusc = nusc or get_nuscenes(dataroot, version)

    def get(self, sample: Sample) -> GroundTruth:
        nusc = self._nusc
        scene = nusc.get("scene", sample.scene_token)
        location = nusc.get("log", scene["log_token"])["location"]
        objects = self.objects_in_view(sample.sample_token)

        strict = Counter(
            o.cls
            for o in objects
            if o.visibility >= self.min_visibility and o.distance_m <= self.max_distance_m
        )
        facts = facts_from_description(scene["description"], location)
        facts.objects = {cls: self.taxonomy.to_bucket(n) for cls, n in strict.items()}

        return GroundTruth(
            sample_token=sample.sample_token,
            scene_name=sample.scene_name,
            frame_index=sample.frame_index,
            location=location,
            reference_text=scene["description"],
            facts=facts,
            loosely_present=sorted({o.cls for o in objects}),
            objects=objects,
        )

    def objects_in_view(self, sample_token: str) -> list[AnnotatedObject]:
        from nuscenes.utils.geometry_utils import BoxVisibility

        nusc = self._nusc
        sample = nusc.get("sample", sample_token)
        _, boxes, _ = nusc.get_sample_data(
            sample["data"][self.camera], box_vis_level=BoxVisibility.ANY
        )
        objects = []
        for box in boxes:  # boxes are already in the camera frame
            cls = category_to_class(box.name)
            if cls is None:
                continue
            ann = nusc.get("sample_annotation", box.token)
            attribute = (
                nusc.get("attribute", ann["attribute_tokens"][0])["name"]
                if ann["attribute_tokens"]
                else None
            )
            objects.append(
                AnnotatedObject(
                    cls=cls,
                    category=box.name,
                    visibility=int(ann["visibility_token"]),
                    distance_m=float(np.linalg.norm(box.center)),
                    attribute=attribute,
                    instance_token=ann["instance_token"],
                )
            )
        return objects
