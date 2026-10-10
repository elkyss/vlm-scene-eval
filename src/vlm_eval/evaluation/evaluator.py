from __future__ import annotations

import logging
from collections.abc import Sequence

from vlm_eval.config import ComponentConfig
from vlm_eval.domain import GroundTruth, MetricResult, Prediction
from vlm_eval.evaluation.metrics import METRICS, EvalPair, Metric
from vlm_eval.taxonomy import Taxonomy

log = logging.getLogger(__name__)

DEFAULT_METRICS = (
    "object_presence",
    "counting",
    "attributes",
    "text_faithfulness",
    "consistency",
    "format",
    "errors",
    "slices",
    "similarity",
)


def join(gts: Sequence[GroundTruth], preds: Sequence[Prediction]) -> list[EvalPair]:
    """Pair predictions with ground truth by sample token (missing predictions are an error)."""
    by_token = {p.sample_token: p for p in preds}
    missing = [g.sample_token for g in gts if g.sample_token not in by_token]
    if missing:
        raise ValueError(f"{len(missing)} frames have no prediction, e.g. {missing[:3]}")
    return [EvalPair(gt=g, pred=by_token[g.sample_token], frame_index=g.frame_index) for g in gts]


class Evaluator:
    def __init__(self, metrics: Sequence[Metric]) -> None:
        self.metrics = list(metrics)

    @classmethod
    def from_config(cls, configs: Sequence[ComponentConfig], taxonomy: Taxonomy) -> Evaluator:
        configs = configs or [ComponentConfig(name=n) for n in DEFAULT_METRICS]
        return cls([METRICS.build(c.name, taxonomy=taxonomy, **c.params) for c in configs])

    def evaluate(
        self, gts: Sequence[GroundTruth], preds: Sequence[Prediction]
    ) -> list[MetricResult]:
        pairs = join(gts, preds)
        results = []
        for metric in self.metrics:
            log.info("Computing metric %s", metric.name)
            results.append(metric.compute(pairs))
        return results
