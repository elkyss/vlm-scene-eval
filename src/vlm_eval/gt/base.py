from __future__ import annotations

from typing import Protocol

from vlm_eval.domain import GroundTruth, Sample, SceneFactSheet, SceneSample, SceneView
from vlm_eval.registry import Registry


class GTProvider(Protocol):
    """Builds the reference facts a prediction for ``sample`` is checked against."""

    def get(self, sample: Sample) -> GroundTruth: ...


GT_PROVIDERS: Registry[GTProvider] = Registry("ground-truth provider")


class FactSheetBuilder(Protocol):
    """Builds the scene-level reference (fact sheet) for one view of a scene."""

    def build(self, scene: SceneSample, view: SceneView) -> SceneFactSheet: ...


FACT_BUILDERS: Registry[FactSheetBuilder] = Registry("fact-sheet builder")
