"""Data models shared by every pipeline stage.

Stages only talk to each other through these types, which is what keeps each
component independently reusable and testable. The models are domain-agnostic: the
actual classes, attributes and values come from the ``Taxonomy``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

ABSENT = "0"  # bucket label for "not present"; every taxonomy's first bucket


class Sample(BaseModel):
    """One frame of one scene, as seen by one or more cameras."""

    sample_token: str
    scene_token: str
    scene_name: str
    frame_index: int
    timestamp: int
    image_paths: dict[str, Path]


class SceneFacts(BaseModel):
    """The verifiable claims about a frame.

    Used for both ground truth and predictions so they can be compared field by field.
    ``attributes`` maps attribute -> value; a missing attribute means "not stated".
    ``objects`` maps class -> count bucket; a missing class means "absent / not mentioned".
    """

    attributes: dict[str, str] = Field(default_factory=dict)
    objects: dict[str, str] = Field(default_factory=dict)

    def attribute(self, name: str) -> str | None:
        return self.attributes.get(name)

    def bucket(self, cls: str) -> str:
        return self.objects.get(cls, ABSENT)

    def present(self, cls: str) -> bool:
        return self.bucket(cls) != ABSENT


class AnnotatedObject(BaseModel):
    """A ground-truth object that projects into the camera image."""

    cls: str
    category: str
    visibility: int  # dataset visibility level (nuScenes: 1..4 = 0-40% ... 80-100%)
    distance_m: float
    attribute: str | None = None
    instance_token: str | None = None  # same physical object across frames of a scene


class GroundTruth(BaseModel):
    sample_token: str
    scene_name: str
    frame_index: int = 0
    location: str
    reference_text: str
    facts: SceneFacts
    # Classes with *any* annotation in the image (no visibility / distance filter). Used
    # for lenient precision: mentioning a far-away car is not a hallucination.
    loosely_present: list[str] = Field(default_factory=list)
    objects: list[AnnotatedObject] = Field(default_factory=list)


class Prediction(BaseModel):
    sample_token: str
    scene_name: str
    model: str
    prompt_version: str
    raw_output: str
    description: str
    facts: SceneFacts  # from the structured answer when available, else from the free text
    facts_source: str  # "json" | "vqa" | "text" | "text_fallback"
    text_facts: SceneFacts  # always extracted from the free-text description
    parse_ok: bool
    parse_error: str | None = None
    latency_s: float = 0.0


class MetricResult(BaseModel):
    name: str
    summary: dict[str, float | None] = Field(default_factory=dict)
    tables: dict[str, Any] = Field(default_factory=dict)
    per_sample: dict[str, dict[str, float]] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


# --- scene level --------------------------------------------------------------------------


class SceneView(BaseModel):
    """One label-blind subset of a scene's keyframes, sent to the VLM in a single call."""

    view_id: int
    frame_indices: list[int]
    sample_tokens: list[str]
    image_paths: list[Path]


class SceneSample(BaseModel):
    scene_token: str
    scene_name: str
    n_keyframes: int
    views: list[SceneView]


class EgoMotion(BaseModel):
    mean_speed_mps: float
    max_speed_mps: float
    stopped_fraction: float  # share of keyframe steps with speed < 0.5 m/s
    yaw_change_deg: float  # positive = turned left (counter-clockwise)
    state: str  # "stopped" | "slow" | "moving" | "fast"
    turn: str  # "left" | "right" | "straight"


class SceneFactSheet(BaseModel):
    """Ground truth for one view of a scene, built automatically from the annotations."""

    scene_name: str
    view_id: int
    location: str
    reference_text: str
    attributes: dict[str, str] = Field(default_factory=dict)  # from scene.description + log
    objects: dict[str, int] = Field(
        default_factory=dict
    )  # class -> distinct clearly-visible instances
    loosely_present: list[str] = Field(default_factory=list)  # classes with any box in the frames
    object_states: dict[str, dict[str, int]] = Field(
        default_factory=dict
    )  # class -> attribute counts
    ego: EgoMotion | None = None
    sentences: list[str] = Field(default_factory=list)  # plain-text rendering (NLI premise)


class ViewOutput(BaseModel):
    view_id: int
    frame_indices: list[int]
    raw_output: str
    description: str
    mentioned_objects: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)
    latency_s: float = 0.0


class SceneDescription(BaseModel):
    """The one entry per scene: the final description plus how it was chosen."""

    scene_token: str
    scene_name: str
    model: str
    prompt_version: str
    description: str
    chosen_view: int
    consensus_objects: list[str] = Field(default_factory=list)
    consensus_attributes: dict[str, str] = Field(default_factory=dict)
    view_agreement: float  # share of consensus facts that all views agree on
    views: list[ViewOutput] = Field(default_factory=list)
