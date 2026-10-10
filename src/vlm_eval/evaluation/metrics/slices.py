"""Slice metrics: the headline numbers broken down by condition.

An average can hide a model that is fine by day and useless at night. Slices are
taken over ground-truth properties (attributes, location, scene), never over model
output, so every model is cut the same way.
"""

from __future__ import annotations

from collections import defaultdict

from vlm_eval.domain import MetricResult
from vlm_eval.evaluation.metrics.base import METRICS, EvalPair
from vlm_eval.evaluation.metrics.objects import frame_outcomes
from vlm_eval.evaluation.stats import prf, safe_div
from vlm_eval.taxonomy import Taxonomy


def slice_key(pair: EvalPair, by: str) -> str:
    if by == "location":
        return pair.gt.location
    if by == "scene":
        return pair.gt.scene_name
    return pair.gt.facts.attribute(by) or "unknown"


@METRICS.register("slices")
class SliceMetric:
    name = "slices"

    def __init__(self, taxonomy: Taxonomy, by: list[str] | None = None) -> None:
        self.taxonomy = taxonomy
        self.by = by or ["time_of_day", "location", "scene_type"]

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        tables: dict[str, dict[str, dict[str, float | None]]] = {}
        worst: dict[str, float | None] = {}
        for by in self.by:
            groups: dict[str, list[EvalPair]] = defaultdict(list)
            for p in pairs:
                groups[slice_key(p, by)].append(p)
            tables[by] = {k: self._stats(v) for k, v in sorted(groups.items())}
            f1s = [row["object_f1"] for row in tables[by].values() if row["object_f1"] is not None]
            worst[f"worst_{by}_object_f1"] = min(f1s) if f1s else None
        return MetricResult(
            name=self.name,
            summary=worst,
            tables=tables,
            notes=[
                "Slices are defined on ground truth. Small slices have wide uncertainty; "
                "check the frame count before drawing conclusions."
            ],
        )

    def _stats(self, pairs: list[EvalPair]) -> dict[str, float | None]:
        tp = fp = fp_far = fn = 0
        for p in pairs:
            for outcome in frame_outcomes(p, self.taxonomy.object_classes).values():
                tp += outcome == "tp"
                fp += outcome == "fp"
                fp_far += outcome == "fp_far"
                fn += outcome == "fn"
        scores = prf(tp, fp, fn)
        attr_hits = [
            p.pred.facts.attribute(a) == p.gt.facts.attribute(a)
            for p in pairs
            for a in self.taxonomy.attribute_names
            if p.gt.facts.attribute(a) is not None
        ]
        return {
            "frames": float(len(pairs)),
            "object_f1": scores["f1"],
            "object_recall": scores["recall"],
            "hallucination_rate": safe_div(fp, tp + fp + fp_far),
            "attribute_accuracy": safe_div(sum(attr_hits), len(attr_hits)),
        }
