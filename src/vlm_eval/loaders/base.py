from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from vlm_eval.domain import Sample, SceneSample
from vlm_eval.registry import Registry


class SceneLoader(Protocol):
    """Yields the frames (with their camera images) that should be described."""

    def __iter__(self) -> Iterator[Sample]: ...


LOADERS: Registry[SceneLoader] = Registry("loader")


class SceneSource(Protocol):
    """Yields whole scenes, each as a few label-blind views (frame subsets)."""

    def __iter__(self) -> Iterator[SceneSample]: ...


SCENE_LOADERS: Registry[SceneSource] = Registry("scene loader")
