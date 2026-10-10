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
from vlm_eval.gt.nuscenes_gt import (
    STATE_WORDS,
    NuScenesGTProvider,
    city_and_side,
    facts_from_description,
)
from vlm_eval.nuscenes_db import get_nuscenes, scene_sample_tokens
from vlm_eval.taxonomy import Taxonomy, load_taxonomy

# Default ego-motion thresholds (stated as assumptions; configurable on the builder).
STOPPED_MPS = 0.5
SLOW_MPS = 4.0  # ~15 km/h
FAST_MPS = 11.0  # ~40 km/h
TURN_DEG = 30.0


def ego_motion_from_poses(
    timestamps_us: list[int],
    positions: list[list[float]],
    yaws_rad: list[float],
    stopped_mps: float = STOPPED_MPS,
    slow_mps: float = SLOW_MPS,
    fast_mps: float = FAST_MPS,
    turn_deg: float = TURN_DEG,
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
    if mean < stopped_mps:
        state = "stopped"
    elif mean < slow_mps:
        state = "slow"
    elif mean < fast_mps:
        state = "moving"
    else:
        state = "fast"
    turn = "left" if yaw_change > turn_deg else "right" if yaw_change < -turn_deg else "straight"
    return EgoMotion(
        mean_speed_mps=mean,
        max_speed_mps=float(speeds.max()) if len(speeds) else 0.0,
        stopped_fraction=float((speeds < stopped_mps).mean()) if len(speeds) else 1.0,
        yaw_change_deg=yaw_change,
        state=state,
        turn=turn,
    )


def render_sentences(
    sheet: SceneFactSheet, taxonomy: Taxonomy, city: str | None = None
) -> list[FactSentence]:
    """Plain-text rendering of a fact sheet, one fact per sentence, worded by the taxonomy.

    Objects are stated as presence only; absence only when no box of the class is anywhere
    in the frames; nothing is stated for attribute values the taxonomy gives no sentence.
    """
    out: list[FactSentence] = []

    def add(text: str | None, source: str) -> None:
        if text:
            out.append(FactSentence(text=text, source=source))

    for name, value in sheet.attributes.items():
        source = "log" if name == "traffic_side" else "description"
        add(taxonomy.fact_sentences.get(name, {}).get(value), source)
    if city and taxonomy.location_sentence:
        add(taxonomy.location_sentence.format(city=city), "log")
    if sheet.ego is not None:
        ego = taxonomy.ego_sentences
        add(ego.state.get(sheet.ego.state), "ego_pose")
        if sheet.ego.state != "stopped":
            if 0.2 <= sheet.ego.stopped_fraction <= 0.8:
                add(ego.partly_stopped, "ego_pose")
            add(ego.turn.get(sheet.ego.turn), "ego_pose")
    templates = taxonomy.object_sentences
    for cls, spec in taxonomy.objects.items():
        n = sheet.objects.get(cls, 0)
        plural = spec.name(2)
        if n:
            add(templates.get("present", "").format(plural=plural), "annotations")
            states = sheet.object_states.get(cls, {})
            if states:
                state, k = max(states.items(), key=lambda kv: kv[1])
                if k > n / 2:
                    add(
                        templates.get("state", "").format(plural=plural, state=state), "annotations"
                    )
        elif cls not in sheet.loosely_present:
            add(templates.get("absent", "").format(plural=plural), "annotations")
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
        stopped_mps: float = STOPPED_MPS,
        slow_mps: float = SLOW_MPS,
        fast_mps: float = FAST_MPS,
        turn_deg: float = TURN_DEG,
    ) -> None:
        self.taxonomy = taxonomy or load_taxonomy("driving")
        self.thresholds = {
            "stopped_mps": stopped_mps,
            "slow_mps": slow_mps,
            "fast_mps": fast_mps,
            "turn_deg": turn_deg,
        }
        self._scene_tokens: dict[str, list[str]] = {}
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
        attributes = facts_from_description(
            record["description"], location, self.taxonomy
        ).attributes

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
        sheet.sentences = render_sentences(sheet, self.taxonomy, city_and_side(location)[0])
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
        if scene.scene_token not in self._scene_tokens:
            self._scene_tokens[scene.scene_token] = scene_sample_tokens(nusc, record)
        tokens = self._scene_tokens[scene.scene_token]
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
        return ego_motion_from_poses(times, positions, yaws, **self.thresholds)
