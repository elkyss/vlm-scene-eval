from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from PIL import Image

from vlm_eval.registry import Registry


@dataclass(frozen=True)
class VLMRequest:
    sample_token: str
    images: list[Image.Image]
    prompt: str


@dataclass(frozen=True)
class VLMResponse:
    text: str
    latency_s: float = 0.0


class VLMBackend(Protocol):
    """Anything that turns images + a prompt into text."""

    @property
    def name(self) -> str: ...

    def generate(self, request: VLMRequest) -> VLMResponse: ...


BACKENDS: Registry[VLMBackend] = Registry("VLM backend")
