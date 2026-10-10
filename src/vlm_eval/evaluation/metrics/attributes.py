"""Scene-level attribute accuracy (time of day, road condition, scene type, traffic side)."""

from __future__ import annotations

from collections import Counter

from vlm_eval.domain import MetricResult
from vlm_eval.evaluation.metrics.base import METRICS, EvalPair
from vlm_eval.evaluation.stats import balanced_accuracy, confusion, mean_or_none, safe_div
from vlm_eval.taxonomy import Taxonomy


@METRICS.register("attributes")
class AttributeMetric:
    """Accuracy per attribute, always next to a majority-class baseline.

    An unanswered field counts as wrong for ``accuracy``; ``answered_accuracy`` only
    looks at frames where the model gave a value.
    """

    name = "attributes"

    def __init__(
        self, taxonomy: Taxonomy, source: str = "facts", attributes: list[str] | None = None
    ) -> None:
        self.source = source
        self.attributes = tuple(attributes or taxonomy.attribute_names)

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        tables: dict[str, dict[str, object]] = {}
        summary: dict[str, float | None] = {}
        per_sample: dict[str, dict[str, float]] = {p.gt.sample_token: {} for p in pairs}
        for attr in self.attributes:
            y_true = [p.gt.facts.attribute(attr) for p in pairs]
            y_pred = [getattr(p.pred, self.source).attribute(attr) for p in pairs]
            idx = [i for i, t in enumerate(y_true) if t is not None]
            if not idx:
                continue
            t = [y_true[i] for i in idx]
            pr = [y_pred[i] for i in idx]
            t_str = [str(v) for v in t]
            correct = [a == b for a, b in zip(t_str, pr, strict=True)]
            answered = [i for i, v in enumerate(pr) if v is not None]
            majority_label, majority_n = Counter(t_str).most_common(1)[0]
            tables[attr] = {
                "accuracy": safe_div(sum(correct), len(correct)),
                "answered_accuracy": safe_div(sum(correct[i] for i in answered), len(answered)),
                "coverage": safe_div(len(answered), len(pr)),
                "balanced_accuracy": balanced_accuracy(t_str, pr),
                "majority_baseline": majority_n / len(t_str),
                "majority_label": majority_label,
                "gt_distribution": dict(Counter(t_str)),
                "confusion": confusion(t_str, pr),
            }
            summary[f"{attr}_accuracy"] = tables[attr]["accuracy"]  # type: ignore[assignment]
            summary[f"{attr}_balanced_accuracy"] = tables[attr]["balanced_accuracy"]  # type: ignore[assignment]
            for i, ok in zip(idx, correct, strict=True):
                per_sample[pairs[i].gt.sample_token][f"{attr}_correct"] = float(ok)
        summary["mean_balanced_accuracy"] = mean_or_none(
            [summary.get(f"{a}_balanced_accuracy") for a in self.attributes]
        )
        return MetricResult(name=self.name, summary=summary, tables=tables, per_sample=per_sample)
