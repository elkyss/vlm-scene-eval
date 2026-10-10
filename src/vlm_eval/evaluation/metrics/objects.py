"""Object-level metrics: hallucination, omission and counting."""

from __future__ import annotations

from collections import defaultdict

from vlm_eval.domain import MetricResult, SceneFacts
from vlm_eval.evaluation.metrics.base import METRICS, EvalPair
from vlm_eval.evaluation.stats import mean_or_none, prf, safe_div
from vlm_eval.taxonomy import Taxonomy

VISIBILITY_BINS = {1: "0-40%", 2: "40-60%", 3: "60-80%", 4: "80-100%"}
DISTANCE_BINS = ((0, 15, "0-15m"), (15, 30, "15-30m"), (30, 50, "30-50m"), (50, 1e9, "50m+"))


def _facts(pair: EvalPair, source: str) -> SceneFacts:
    facts: SceneFacts = getattr(pair.pred, source)
    return facts


def frame_outcomes(
    pair: EvalPair, classes: tuple[str, ...], source: str = "facts"
) -> dict[str, str]:
    """Per class: 'tp' | 'fn' | 'fp' (no box at all) | 'fp_far' (box exists but filtered) | 'tn'."""
    pred = _facts(pair, source)
    out = {}
    for cls in classes:
        gt_present = pair.gt.facts.present(cls)
        pred_present = pred.present(cls)
        if gt_present and pred_present:
            out[cls] = "tp"
        elif gt_present:
            out[cls] = "fn"
        elif pred_present:
            out[cls] = "fp_far" if cls in pair.gt.loosely_present else "fp"
        else:
            out[cls] = "tn"
    return out


def frame_f1(outcomes: dict[str, str]) -> float:
    tp = sum(o == "tp" for o in outcomes.values())
    fp = sum(o == "fp" for o in outcomes.values())
    fn = sum(o == "fn" for o in outcomes.values())
    if tp + fp + fn == 0:
        return 1.0  # nothing there, nothing claimed
    return 2 * tp / (2 * tp + fp + fn)


def presence_summary(
    pairs: list[EvalPair], classes: tuple[str, ...], source: str = "facts"
) -> MetricResult:
    counts: dict[str, dict[str, int]] = {
        cls: {"tp": 0, "fp": 0, "fp_far": 0, "fn": 0, "tn": 0} for cls in classes
    }
    per_sample = {}
    for pair in pairs:
        outcomes = frame_outcomes(pair, classes, source)
        for cls, outcome in outcomes.items():
            counts[cls][outcome] += 1
        per_sample[pair.gt.sample_token] = {
            "object_f1": frame_f1(outcomes),
            "hallucinations": float(sum(o == "fp" for o in outcomes.values())),
            "omissions": float(sum(o == "fn" for o in outcomes.values())),
        }

    per_class = {}
    for cls, c in counts.items():
        lenient = prf(c["tp"], c["fp"], c["fn"])
        strict = prf(c["tp"], c["fp"] + c["fp_far"], c["fn"])
        per_class[cls] = {
            **c,
            "gt_frames": c["tp"] + c["fn"],
            "precision": lenient["precision"],
            "precision_strict": strict["precision"],
            "recall": lenient["recall"],
            "f1": lenient["f1"],
            "hallucination_rate": safe_div(c["fp"], c["tp"] + c["fp"] + c["fp_far"]),
        }

    tot = {k: sum(c[k] for c in counts.values()) for k in ("tp", "fp", "fp_far", "fn")}
    micro = prf(tot["tp"], tot["fp"], tot["fn"])
    supported = [cls for cls in classes if per_class[cls]["gt_frames"]]
    return MetricResult(
        name="object_presence",
        summary={
            "micro_precision": micro["precision"],
            "micro_recall": micro["recall"],
            "micro_f1": micro["f1"],
            "macro_f1": mean_or_none([per_class[c]["f1"] for c in supported]),
            "hallucination_rate": safe_div(tot["fp"], tot["tp"] + tot["fp"] + tot["fp_far"]),
            "omission_rate": safe_div(tot["fn"], tot["tp"] + tot["fn"]),
            "mean_frame_f1": mean_or_none([s["object_f1"] for s in per_sample.values()]),
        },
        tables={"per_class": per_class},
        per_sample=per_sample,
    )


def blind_prior(pairs: list[EvalPair], classes: tuple[str, ...]) -> dict[str, float | None]:
    """Scores of a model that never looks at the image.

    It always claims every class that is present in at least half of the frames (here:
    "car"). This is an optimistic blind baseline (it knows the test-set frequencies); a
    VLM that does not beat it clearly is not using the image for object claims.
    """
    if not pairs:
        return {}
    freq = {c: sum(p.gt.facts.present(c) for p in pairs) / len(pairs) for c in classes}
    claimed = {c for c, f in freq.items() if f >= 0.5}
    tp = fp = fp_far = fn = 0
    for p in pairs:
        for c in classes:
            present = p.gt.facts.present(c)
            if c in claimed:
                tp += present
                fp += not present and c not in p.gt.loosely_present
                fp_far += not present and c in p.gt.loosely_present
            else:
                fn += present
    scores = prf(tp, fp, fn)
    return {
        "blind_prior_micro_f1": scores["f1"],
        "blind_prior_micro_precision": scores["precision"],
        "blind_prior_micro_recall": scores["recall"],
    }


@METRICS.register("object_presence")
class ObjectPresenceMetric:
    """Which object classes are claimed vs. really in view.

    * Recall/omission uses the strict GT (>= 40% visible, <= 50 m).
    * Precision is lenient: claiming a class that has *some* box in the image (far away
      or mostly occluded) is not counted as a hallucination; ``precision_strict`` is
      reported too.
    * Recall is also broken down by the visibility and distance of each annotated object.
    """

    name = "object_presence"

    def __init__(self, taxonomy: Taxonomy, source: str = "facts") -> None:
        self.taxonomy = taxonomy
        self.source = source

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        result = presence_summary(pairs, self.taxonomy.object_classes, self.source)
        result.summary.update(blind_prior(pairs, self.taxonomy.object_classes))
        result.tables["recall_by_visibility"] = self._recall_by(pairs, "visibility")
        result.tables["recall_by_distance"] = self._recall_by(pairs, "distance")
        result.notes.append(
            "Recall by bin = share of annotated objects whose class the VLM mentioned "
            "(a class-level proxy: the VLM does not localise objects)."
        )
        return result

    def _recall_by(self, pairs: list[EvalPair], key: str) -> dict[str, dict[str, float | None]]:
        hits: dict[str, list[int]] = defaultdict(list)
        for pair in pairs:
            pred = _facts(pair, self.source)
            for obj in pair.gt.objects:
                if key == "visibility":
                    label = VISIBILITY_BINS.get(obj.visibility, "?")
                else:
                    label = next(lbl for lo, hi, lbl in DISTANCE_BINS if lo <= obj.distance_m < hi)
                hits[label].append(int(pred.present(obj.cls)))
        order = (
            list(VISIBILITY_BINS.values())
            if key == "visibility"
            else [lbl for *_, lbl in DISTANCE_BINS]
        )
        return {
            lbl: {
                "objects": float(len(hits[lbl])),
                "recall": safe_div(sum(hits[lbl]), len(hits[lbl])),
            }
            for lbl in order
            if hits[lbl]
        }


@METRICS.register("counting")
class CountingMetric:
    """Count-bucket accuracy, only where both GT and prediction say the class is present.

    This isolates counting skill from detection (which object_presence already scores).
    """

    name = "counting"

    def __init__(self, taxonomy: Taxonomy, source: str = "facts") -> None:
        self.taxonomy = taxonomy
        self.source = source

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        tax = self.taxonomy
        per_class: dict[str, dict[str, float | None]] = {}
        all_exact, all_within = [], []
        for cls in tax.object_classes:
            exact, within = [], []
            for pair in pairs:
                gt_b, pred_b = pair.gt.facts.bucket(cls), _facts(pair, self.source).bucket(cls)
                if gt_b == tax.absent or pred_b == tax.absent:
                    continue
                diff = abs(tax.bucket_index(gt_b) - tax.bucket_index(pred_b))
                exact.append(int(diff == 0))
                within.append(int(diff <= 1))
            all_exact += exact
            all_within += within
            per_class[cls] = {
                "n": float(len(exact)),
                "exact": safe_div(sum(exact), len(exact)),
                "within_one_bucket": safe_div(sum(within), len(within)),
            }
        return MetricResult(
            name=self.name,
            summary={
                "exact_bucket_accuracy": safe_div(sum(all_exact), len(all_exact)),
                "within_one_bucket_accuracy": safe_div(sum(all_within), len(all_within)),
                "n": float(len(all_exact)),
            },
            tables={"per_class": per_class},
        )
