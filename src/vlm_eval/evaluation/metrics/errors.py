"""Error taxonomy: tag every frame with the kinds of mistakes it contains."""

from __future__ import annotations

from collections import Counter

from vlm_eval.domain import MetricResult
from vlm_eval.evaluation.metrics.base import METRICS, EvalPair
from vlm_eval.evaluation.metrics.objects import frame_outcomes
from vlm_eval.evaluation.metrics.robustness import has_repetition_loop
from vlm_eval.taxonomy import Taxonomy


def error_tags(pair: EvalPair, taxonomy: Taxonomy) -> list[str]:
    gt, pred = pair.gt.facts, pair.pred.facts
    tags: list[str] = []
    if not pair.pred.parse_ok:
        tags.append("format:invalid_output")
    if has_repetition_loop(pair.pred.description):
        tags.append("format:repetition_loop")
    for cls, outcome in frame_outcomes(pair, taxonomy.object_classes).items():
        if outcome == "fp":
            tags.append(f"hallucination:{cls}")
        elif outcome == "fn":
            tags.append(f"omission:{cls}")
        elif outcome == "tp":
            diff = abs(
                taxonomy.bucket_index(gt.bucket(cls)) - taxonomy.bucket_index(pred.bucket(cls))
            )
            if diff > 1:
                tags.append(f"count:{cls}")
    for attr in taxonomy.attribute_names:
        g, p = gt.attribute(attr), pred.attribute(attr)
        if g is not None and p is not None and g != p:
            tags.append(f"attribute:{attr}")
    if pair.pred.facts_source in {"json", "vqa"}:
        t = pair.pred.text_facts
        # The prose names a class the JSON says is absent (leaving one out is not a contradiction).
        if any(t.present(c) and not pred.present(c) for c in taxonomy.object_classes):
            tags.append("consistency:text_contradicts_json")
    return tags


@METRICS.register("errors")
class ErrorTaxonomyMetric:
    name = "errors"

    def __init__(self, taxonomy: Taxonomy, n_examples: int = 8) -> None:
        self.taxonomy = taxonomy
        self.n_examples = n_examples

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        tagged = [(p, error_tags(p, self.taxonomy)) for p in pairs]
        by_tag = Counter(t for _, tags in tagged for t in tags)
        by_family = Counter(t.split(":")[0] for _, tags in tagged for t in tags)
        worst = sorted(tagged, key=lambda x: len(x[1]), reverse=True)[: self.n_examples]
        examples = [
            {
                "sample_token": p.gt.sample_token,
                "scene_name": p.gt.scene_name,
                "frame_index": p.frame_index,
                "description": p.pred.description,
                "errors": tags,
                "gt_objects": p.gt.facts.objects,
                "pred_objects": p.pred.facts.objects,
            }
            for p, tags in worst
            if tags
        ]
        return MetricResult(
            name=self.name,
            summary={
                "frames_with_any_error": sum(bool(t) for _, t in tagged) / len(tagged)
                if tagged
                else None
            },
            tables={
                "by_family": dict(by_family.most_common()),
                "by_tag": dict(by_tag.most_common()),
                "worst_examples": examples,
            },
            per_sample={p.gt.sample_token: {"n_errors": float(len(t))} for p, t in tagged},
        )
