"""Output-quality and stability metrics that need no ground truth about content."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from itertools import pairwise

import numpy as np

from vlm_eval.domain import MetricResult, SceneFacts
from vlm_eval.evaluation.metrics.base import METRICS, EvalPair
from vlm_eval.evaluation.stats import safe_div
from vlm_eval.taxonomy import Taxonomy


def has_repetition_loop(text: str, min_repeats: int = 3) -> bool:
    """A sentence repeated ``min_repeats`` times: the decoder got stuck in a loop."""
    sentences = [s.strip().lower() for s in re.split(r"[.!?]\s*", text) if len(s.strip()) > 10]
    return any(n >= min_repeats for n in Counter(sentences).values())


@METRICS.register("format")
class FormatMetric:
    """Did the model follow the output contract, and is it saying anything specific?"""

    name = "format"

    def __init__(self, taxonomy: Taxonomy | None = None) -> None:
        pass  # taxonomy-independent

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        preds = [p.pred for p in pairs]
        descriptions = [p.description.strip().lower() for p in preds]
        dupes = Counter(descriptions)
        latencies = [p.latency_s for p in preds]
        return MetricResult(
            name=self.name,
            summary={
                "parse_success_rate": safe_div(sum(p.parse_ok for p in preds), len(preds)),
                "empty_description_rate": safe_div(sum(not d for d in descriptions), len(preds)),
                "repetition_loop_rate": safe_div(
                    sum(has_repetition_loop(d) for d in descriptions), len(preds)
                ),
                "duplicate_description_rate": safe_div(
                    sum(1 for d in descriptions if d and dupes[d] > 1), len(preds)
                ),
                "mean_description_words": float(np.mean([len(d.split()) for d in descriptions]))
                if preds
                else None,
                "mean_latency_s": float(np.mean(latencies)) if latencies else None,
                "p95_latency_s": float(np.quantile(latencies, 0.95)) if latencies else None,
            },
            tables={"facts_source": dict(Counter(p.facts_source for p in preds))},
        )


def _labels(facts: SceneFacts, taxonomy: Taxonomy) -> dict[str, str | None]:
    labels: dict[str, str | None] = {a: facts.attribute(a) for a in taxonomy.attribute_names}
    labels.update({f"obj:{c}": str(facts.present(c)) for c in taxonomy.object_classes})
    return labels


@METRICS.register("consistency")
class TemporalConsistencyMetric:
    """How often answers flip between consecutive sampled frames of the same scene.

    The GT flip rate is reported next to it: objects really do enter/leave view, so
    the model should flip about as often as the GT, not more.
    """

    name = "consistency"

    def __init__(self, taxonomy: Taxonomy, source: str = "facts") -> None:
        self.taxonomy = taxonomy
        self.source = source

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        by_scene: dict[str, list[EvalPair]] = defaultdict(list)
        for p in pairs:
            by_scene[p.gt.scene_name].append(p)

        pred_flips: dict[str, list[int]] = defaultdict(list)
        gt_flips: dict[str, list[int]] = defaultdict(list)
        for scene_pairs in by_scene.values():
            scene_pairs.sort(key=lambda p: p.frame_index)
            for a, b in pairwise(scene_pairs):
                pa, pb = (
                    _labels(getattr(a.pred, self.source), self.taxonomy),
                    _labels(getattr(b.pred, self.source), self.taxonomy),
                )
                ga, gb = _labels(a.gt.facts, self.taxonomy), _labels(b.gt.facts, self.taxonomy)
                for key in pa:
                    pred_flips[key].append(int(pa[key] != pb[key]))
                    gt_flips[key].append(int(ga[key] != gb[key]))

        table = {
            key: {
                "pred_flip_rate": safe_div(sum(pred_flips[key]), len(pred_flips[key])),
                "gt_flip_rate": safe_div(sum(gt_flips[key]), len(gt_flips[key])),
            }
            for key in pred_flips
        }
        attr_keys = list(self.taxonomy.attribute_names)
        return MetricResult(
            name=self.name,
            summary={
                "attribute_flip_rate": safe_div(
                    sum(sum(pred_flips[k]) for k in attr_keys),
                    sum(len(pred_flips[k]) for k in attr_keys),
                ),
                "gt_attribute_flip_rate": safe_div(
                    sum(sum(gt_flips[k]) for k in attr_keys),
                    sum(len(gt_flips[k]) for k in attr_keys),
                ),
            },
            tables={"per_label": table},
            notes=[
                "Scene-level GT attributes never change within a scene, so any "
                "attribute flip by the model is an inconsistency."
            ],
        )
