"""Caching decorator around any backend: rerunning a config costs no inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from vlm_eval.vlm.base import VLMBackend, VLMRequest, VLMResponse


def cache_key(signature: str, prompt: str, image_ids: tuple[str, ...]) -> str:
    """Content key: model + generation settings + prompt + the exact frames sent."""
    payload = json.dumps({"backend": signature, "prompt": prompt, "images": list(image_ids)})
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


class CachedBackend:
    """Wraps a ``VLMBackend``; responses are stored under a content key.

    The original latency is stored too, so reports stay meaningful on cached reruns.
    """

    def __init__(self, backend: VLMBackend, root: Path) -> None:
        self.backend = backend
        self.root = root

    @property
    def name(self) -> str:
        return self.backend.name

    @property
    def signature(self) -> str:
        return self.backend.signature

    def path_for(self, request: VLMRequest) -> Path:
        key = cache_key(self.signature, request.prompt, request.images.ids)
        return self.root / self.name / request.sample_token / f"{key}.json"

    def generate(self, request: VLMRequest) -> VLMResponse:
        path = self.path_for(request)
        if path.exists():
            data = json.loads(path.read_text())
            return VLMResponse(data["text"], data["latency_s"])
        response = self.backend.generate(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"text": response.text, "latency_s": response.latency_s}))
        return response
