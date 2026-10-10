from __future__ import annotations

from typing import Protocol

from vlm_eval.domain import GroundTruth, Sample
from vlm_eval.registry import Registry


class GTProvider(Protocol):
    """Builds the reference facts a prediction for ``sample`` is checked against."""

    def get(self, sample: Sample) -> GroundTruth: ...


GT_PROVIDERS: Registry[GTProvider] = Registry("ground-truth provider")
