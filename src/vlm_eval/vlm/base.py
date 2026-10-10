from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from PIL import Image

from vlm_eval.registry import Registry


@dataclass(frozen=True)
class ImageSet:
    """The images of one request: stable identities plus lazily loaded pixels.

    ``ids`` identify the exact frames (e.g. ``<sample_token>:CAM_FRONT``) and are part of the
    cache key, so changing which frames are sent can never return a stale answer. Pixels are
    only decoded when a backend actually needs them (not on a cache hit).
    """

    ids: tuple[str, ...]
    paths: tuple[Path, ...]
    _loaded: list[Image.Image] = field(default_factory=list, compare=False, repr=False)

    @classmethod
    def from_paths(cls, ids: Sequence[str], paths: Sequence[Path]) -> ImageSet:
        if len(ids) != len(paths):
            raise ValueError("ids and paths must have the same length")
        return cls(tuple(ids), tuple(Path(p) for p in paths))

    def load(self) -> list[Image.Image]:
        if not self._loaded:
            self._loaded.extend(Image.open(p).convert("RGB") for p in self.paths)
        return list(self._loaded)

    def __len__(self) -> int:
        return len(self.ids)


@dataclass(frozen=True)
class VLMRequest:
    sample_token: str
    images: ImageSet
    prompt: str


@dataclass(frozen=True)
class VLMResponse:
    text: str
    latency_s: float = 0.0


class VLMBackend(Protocol):
    """Anything that turns images + a prompt into text."""

    @property
    def name(self) -> str: ...

    @property
    def signature(self) -> str:
        """Everything that changes the output for the same input (model, revision, settings)."""
        ...

    def generate(self, request: VLMRequest) -> VLMResponse: ...


BACKENDS: Registry[VLMBackend] = Registry("VLM backend")
