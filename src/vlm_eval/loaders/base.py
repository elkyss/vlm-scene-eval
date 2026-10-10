from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from vlm_eval.domain import Sample
from vlm_eval.registry import Registry


class SceneLoader(Protocol):
    """Yields the frames (with their camera images) that should be described."""

    def __iter__(self) -> Iterator[Sample]: ...


LOADERS: Registry[SceneLoader] = Registry("loader")
