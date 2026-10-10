"""Caching decorator around any backend: rerunning a config costs no inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from vlm_eval.vlm.base import VLMBackend, VLMRequest, VLMResponse


class CachedBackend:
    """Wraps a ``VLMBackend``; responses are stored per (model, prompt, sample).

    The original latency is stored too, so reports stay meaningful on cached reruns.
    """

    def __init__(self, backend: VLMBackend, root: Path) -> None:
        self.backend = backend
        self.root = root

    @property
    def name(self) -> str:
        return self.backend.name

    def _path(self, request: VLMRequest) -> Path:
        key = f"{request.prompt}\x00{len(request.images)}"
        digest = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.root / self.name / request.sample_token / f"{digest}.json"

    def generate(self, request: VLMRequest) -> VLMResponse:
        path = self._path(request)
        if path.exists():
            data = json.loads(path.read_text())
            return VLMResponse(data["text"], data["latency_s"])
        response = self.backend.generate(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"text": response.text, "latency_s": response.latency_s}))
        return response
