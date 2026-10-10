"""Scene-level ground truth ("fact sheet"), generated automatically from the annotations.

For one view of a scene it collects everything the dataset knows that a description could
be checked against:

* objects: classes clearly visible in the view's frames (presence; distinct instances are
  counted with instance tokens), plus any-box presence for lenient hallucination checks;
* object states: annotation attributes (moving / parked / standing ...);
* ego motion: our car's speed and heading change from ``ego_pose`` over the view's span;
* place and conditions: ``scene.description`` keywords and ``log.location``.

It is rendered as plain sentences, which serve as the premise for the NLI judge.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import numpy as np

from vlm_eval.domain import EgoMotion, FactSentence, SceneFactSheet, SceneSample, SceneView
from vlm_eval.gt.base import FACT_BUILDERS
from vlm_eval.gt.nuscenes_gt import NuScenesGTProvider, facts_from_description
from vlm_eval.nuscenes_db import get_nuscenes, scene_sample_tokens
from vlm_eval.taxonomy import Taxonomy, load_taxonomy

STOPPED_MPS = 0.5
SLOW_MPS = 4.0  # ~15 km/h
FAST_MPS = 11.0  # ~40 km/h
TURN_DEG = 30.0

STATE_WORDS = {
    "vehicle.moving": "moving",
    "vehicle.parked": "parked",
    "vehicle.stopped": "stopped",
    "pedestrian.moving": "walking",
    "pedestrian.standing": "standing",
    "pedestrian.sitting_lying_down": "sitting",
    "cycle.with_rider": "ridden",
    "cycle.without_rider": "parked",
}

PLACE_SENTENCES = {
    "intersection": "The drive passes an intersection.",
    "parking_lot": "The scene is in a parking lot.",
}


def ego_motion_from_poses(
    timestamps_us: list[int], positions: list[list[float]], yaws_rad: list[float]
) -> EgoMotion:
    """Classify our car's motion from a time-ordered pose track."""
    t = np.asarray(timestamps_us, dtype=float) / 1e6
    xy = np.asarray(positions, dtype=float)[:, :2]
    dt = np.diff(t)
    speeds = np.linalg.norm(np.diff(xy, axis=0), axis=1) / np.where(dt > 0, dt, np.nan)
    speeds = np.nan_to_num(speeds)
    yaw_change = (
        float(np.degrees(np.sum(np.diff(np.unwrap(yaws_rad))))) if len(yaws_rad) > 1 else 0.0
    )
    mean = float(speeds.mean()) if len(speeds) else 0.0
    if mean < STOPPED_MPS:
        state = "stopped"
    elif mean < SLOW_MPS:
        state = "slow"
    elif mean < FAST_MPS:
        state = "moving"
    else:
        state = "fast"
    turn = "left" if yaw_change > TURN_DEG else "right" if yaw_change < -TURN_DEG else "straight"
    return EgoMotion(
        mean_speed_mps=mean,
        max_speed_mps=float(speeds.max()) if len(speeds) else 0.0,
        stopped_fraction=float((speeds < STOPPED_MPS).mean()) if len(speeds) else 1.0,
        yaw_change_deg=yaw_change,
        state=state,
        turn=turn,
    )


def render_sentences(sheet: SceneFactSheet, taxonomy: Taxonomy) -> list[FactSentence]:
    """Plain-text rendering of a fact sheet, one fact per sentence.

    Objects are stated as presence only ("There are cars."): instance counts over a whole
    view would contradict reasonable answers such as "a few cars" seen in six stills.
    Absence is stated only when no box of the class is anywhere in the frames.
    """
    out: list[FactSentence] = []

    def add(text: str, source: str) -> None:
        out.append(FactSentence(text=text, source=source))

    attrs = sheet.attributes
    if attrs.get("time_of_day") == "night":
        add("It is night.", "description")
    elif attrs.get("time_of_day") == "day":
        add("It is daytime.", "description")
    if attrs.get("road_condition") == "wet":
        add("The road is wet.", "description")
    if attrs.get("scene_type") in PLACE_SENTENCES:
        add(PLACE_SENTENCES[attrs["scene_type"]], "description")
    if attrs.get("traffic_side"):
        city = "Singapore" if sheet.location.startswith("singapore") else "Boston"
        add(f"The drive is in {city}, where vehicles drive on the {attrs['traffic_side']}.", "log")
    if sheet.ego is not None:
        add(
            {
                "stopped": "Our car is stopped.",
                "slow": "Our car is moving slowly.",
                "moving": "Our car is driving.",
                "fast": "Our car is driving fast.",
            }[sheet.ego.state],
            "ego_pose",
        )
        if sheet.ego.state != "stopped" and 0.2 <= sheet.ego.stopped_fraction <= 0.8:
            add("Our car stops for part of the drive.", "ego_pose")
        if sheet.ego.state != "stopped":
            add(
                "Our car drives straight ahead."
                if sheet.ego.turn == "straight"
                else f"Our car turns {sheet.ego.turn}.",
                "ego_pose",
            )
    for cls, spec in taxonomy.objects.items():
        n = sheet.objects.get(cls, 0)
        plural = spec.name(2)
        if n:
            add(f"There are {plural}.", "annotations")
            states = sheet.object_states.get(cls, {})
            if states:
                state, k = max(states.items(), key=lambda kv: kv[1])
                if k > n / 2:
                    add(f"Most {plural} are {state}.", "annotations")
        elif cls not in sheet.loosely_present:
            add(f"There are no {plural}.", "annotations")
    return out


@FACT_BUILDERS.register("nuscenes")
class SceneFactBuilder:
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
        self._built: dict[tuple[str, int], SceneFactSheet] = {}
        self._frames = NuScenesGTProvider(
            dataroot, version, camera, min_visibility, max_distance_m, self.taxonomy, self._nusc
        )

    def build(self, scene: SceneSample, view: SceneView) -> SceneFactSheet:
        """Fact sheet of one view (memoised: the oracle and the pipeline both ask for it)."""
        key = (scene.scene_token, view.view_id)
        if key not in self._built:
            self._built[key] = self._build(scene, view)
        return self._built[key]

    def _build(self, scene: SceneSample, view: SceneView) -> SceneFactSheet:
        nusc = self._nusc
        record = nusc.get("scene", scene.scene_token)
        location = nusc.get("log", record["log_token"])["location"]
        attributes = facts_from_description(record["description"], location).attributes

        instances: dict[str, set[str]] = defaultdict(set)
        states: dict[str, Counter[str]] = defaultdict(Counter)
        loose: set[str] = set()
        for token in view.sample_tokens:
            for obj in self._frames.objects_in_view(token):
                loose.add(obj.cls)
                if obj.visibility < self.min_visibility or obj.distance_m > self.max_distance_m:
                    continue
                key = obj.instance_token or f"{token}:{len(instances[obj.cls])}"
                if key not in instances[obj.cls]:
                    instances[obj.cls].add(key)
                    if obj.attribute in STATE_WORDS:
                        states[obj.cls][STATE_WORDS[obj.attribute]] += 1

        sheet = SceneFactSheet(
            scene_name=scene.scene_name,
            view_id=view.view_id,
            location=location,
            reference_text=record["description"],
            attributes=attributes,
            objects={cls: len(ids) for cls, ids in instances.items()},
            loosely_present=sorted(loose),
            object_states={cls: dict(c) for cls, c in states.items()},
            ego=self._ego_motion(scene, view),
        )
        sheet.sentences = render_sentences(sheet, self.taxonomy)
        return sheet

    def _ego_motion(self, scene: SceneSample, view: SceneView) -> EgoMotion:
        """Our car's motion over the view's time span.

        Uses every keyframe between the first and last frame shown (motion is continuous, and
        the gaps between shown frames are where speed and turning happen), while objects use
        only the frames that were actually shown to the model.
        """
        from pyquaternion import Quaternion

        nusc = self._nusc
        record = nusc.get("scene", scene.scene_token)
        tokens = scene_sample_tokens(nusc, record)
        first, last = min(view.frame_indices), max(view.frame_indices)
        times, positions, yaws = [], [], []
        for token in tokens[first : last + 1]:
            sample = nusc.get("sample", token)
            pose = nusc.get(
                "ego_pose", nusc.get("sample_data", sample["data"][self.camera])["ego_pose_token"]
            )
            times.append(pose["timestamp"])
            positions.append(pose["translation"])
            yaws.append(Quaternion(pose["rotation"]).yaw_pitch_roll[0])
        return ego_motion_from_poses(times, positions, yaws)
