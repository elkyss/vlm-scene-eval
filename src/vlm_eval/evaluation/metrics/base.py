from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from vlm_eval.domain import GroundTruth, MetricResult, Prediction
from vlm_eval.registry import Registry


@dataclass(frozen=True)
class EvalPair:
    gt: GroundTruth
    pred: Prediction
    frame_index: int = 0


class Metric(Protocol):
    name: str

    def compute(self, pairs: list[EvalPair]) -> MetricResult: ...


METRICS: Registry[Metric] = Registry("metric")
