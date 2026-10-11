"""Metric tests on hand-computed examples."""

import pytest

from tests.conftest import TAX, make_gt, make_pred
from vlm_eval.evaluation.metrics import (
    AttributeMetric,
    CountingMetric,
    ErrorTaxonomyMetric,
    EvalPair,
    FormatMetric,
    ObjectPresenceMetric,
    TemporalConsistencyMetric,
    TextFaithfulnessMetric,
    frame_f1,
    frame_outcomes,
)


def pair(gt_objects, pred_objects, loose=None, **pred_kw):  # type: ignore[no-untyped-def]
    return EvalPair(
        gt=make_gt(objects=gt_objects, loose=loose), pred=make_pred(objects=pred_objects, **pred_kw)
    )


def test_frame_outcomes_classifies_tp_fp_fn() -> None:
    # GT {car, pedestrian}; VLM says car + cone. Cone has no box at all -> hallucination.
    gt, pred = {"car": "3-5", "pedestrian": "1-2"}, {"car": "3-5", "traffic_cone": "1-2"}
    out = frame_outcomes(pair(gt, pred), TAX.object_classes)
    assert out["car"] == "tp"
    assert out["pedestrian"] == "fn"
    assert out["traffic_cone"] == "fp"
    assert out["bus"] == "tn"
    assert frame_f1(out) == pytest.approx(2 * 1 / (2 * 1 + 1 + 1))


def test_far_object_is_not_a_hallucination() -> None:
    out = frame_outcomes(
        pair({"car": "1-2"}, {"car": "1-2", "truck": "1-2"}, loose=["truck"]), TAX.object_classes
    )
    assert out["truck"] == "fp_far"
    assert frame_f1(out) == 1.0


def test_empty_frame_with_empty_prediction_is_perfect() -> None:
    assert frame_f1(frame_outcomes(pair({}, {}), TAX.object_classes)) == 1.0


def test_object_presence_micro_and_per_class() -> None:
    pairs = [
        # frame 1: car TP, pedestrian FN
        EvalPair(
            gt=make_gt(token="s1", objects={"car": "3-5", "pedestrian": "1-2"}),
            pred=make_pred(token="s1", objects={"car": "1-2"}),
        ),
        # frame 2: car TP, bus FP (no bus box anywhere -> hallucination)
        EvalPair(
            gt=make_gt(token="s2", objects={"car": "1-2"}),
            pred=make_pred(token="s2", objects={"car": "1-2", "bus": "1-2"}),
        ),
    ]
    r = ObjectPresenceMetric(TAX).compute(pairs)
    assert r.summary["micro_precision"] == pytest.approx(2 / 3)
    assert r.summary["micro_recall"] == pytest.approx(2 / 3)
    assert r.summary["hallucination_rate"] == pytest.approx(1 / 3)
    assert r.summary["omission_rate"] == pytest.approx(1 / 3)
    assert r.tables["per_class"]["car"]["f1"] == 1.0
    assert r.tables["per_class"]["pedestrian"]["recall"] == 0.0
    assert r.tables["per_class"]["bus"]["precision"] == 0.0
    # macro F1 only over classes present in GT (car=1, pedestrian=0)
    assert r.summary["macro_f1"] == pytest.approx(0.5)


def test_counting_only_scores_jointly_present_classes() -> None:
    pairs = [
        pair({"car": "3-5", "pedestrian": "6+", "bus": "1-2"}, {"car": "3-5", "pedestrian": "1-2"})
    ]
    r = CountingMetric(TAX).compute(pairs)
    assert r.summary["n"] == 2  # bus not predicted -> not a counting sample
    assert r.summary["exact_bucket_accuracy"] == 0.5
    assert r.summary["within_one_bucket_accuracy"] == 0.5  # 6+ vs 1-2 is 2 buckets off


def test_attributes_against_majority_baseline() -> None:
    pairs = [
        EvalPair(gt=make_gt(token=f"d{i}"), pred=make_pred(token=f"d{i}", time="day"))
        for i in range(3)
    ] + [EvalPair(gt=make_gt(token="n1", night=True), pred=make_pred(token="n1", time="day"))]
    t = AttributeMetric(TAX).compute(pairs).tables["time_of_day"]
    assert t["accuracy"] == 0.75
    assert t["majority_baseline"] == 0.75
    assert t["balanced_accuracy"] == 0.5  # always "day" = chance level
    assert t["confusion"] == {"day": {"day": 3}, "night": {"day": 1}}


def test_unanswered_attribute_counts_as_wrong_but_not_in_answered_accuracy() -> None:
    pairs = [
        EvalPair(gt=make_gt(token="a"), pred=make_pred(token="a", time=None)),
        EvalPair(gt=make_gt(token="b"), pred=make_pred(token="b", time="day")),
    ]
    t = AttributeMetric(TAX).compute(pairs).tables["time_of_day"]
    assert t["accuracy"] == 0.5
    assert t["answered_accuracy"] == 1.0
    assert t["coverage"] == 0.5


def test_consistency_detects_attribute_flips() -> None:
    pairs = [
        EvalPair(
            gt=make_gt(token=f"t{i}", frame=i), pred=make_pred(token=f"t{i}", time=t), frame_index=i
        )
        for i, t in enumerate(["day", "night", "day"])
    ]
    r = TemporalConsistencyMetric(TAX).compute(pairs)
    assert r.tables["per_label"]["time_of_day"]["pred_flip_rate"] == 1.0
    assert r.tables["per_label"]["time_of_day"]["gt_flip_rate"] == 0.0


def test_format_metric_counts_failures_and_duplicates() -> None:
    pairs = [
        EvalPair(gt=make_gt(token=t), pred=make_pred(token=t, description=d, parse_ok=ok))
        for t, d, ok in [("a", "same", True), ("b", "same", True), ("c", "", False)]
    ]
    s = FormatMetric().compute(pairs).summary
    assert s["parse_success_rate"] == pytest.approx(2 / 3)
    assert s["duplicate_description_rate"] == pytest.approx(2 / 3)
    assert s["empty_description_rate"] == pytest.approx(1 / 3)


def test_text_json_contradiction() -> None:
    p = pair({"car": "1-2"}, {"car": "1-2"}, text_objects={"car": "1-2", "bus": "1-2"})
    s = TextFaithfulnessMetric(TAX).compute([p]).summary
    assert s["text_json_object_contradiction_rate"] == 0.5  # bus in prose, not in JSON
    assert s["micro_precision"] == 0.5


def test_error_taxonomy_tags() -> None:
    p = pair({"car": "1-2", "pedestrian": "1-2"}, {"car": "6+", "bus": "1-2"}, time="night")
    tables = ErrorTaxonomyMetric(TAX).compute([p]).tables
    assert set(tables["by_tag"]) == {
        "hallucination:bus",
        "omission:pedestrian",
        "count:car",
        "attribute:time_of_day",
    }


def test_slices_split_by_ground_truth() -> None:
    from vlm_eval.evaluation.metrics import SliceMetric

    day = EvalPair(gt=make_gt(token="d"), pred=make_pred(token="d", objects={"car": "3-5"}))
    night = EvalPair(gt=make_gt(token="n", night=True), pred=make_pred(token="n", time="night"))
    r = SliceMetric(TAX, by=["time_of_day"]).compute([day, night])
    assert r.tables["time_of_day"]["day"]["object_recall"] == 0.5  # car found, pedestrian missed
    assert r.tables["time_of_day"]["night"]["object_recall"] == 0.0
    assert r.summary["worst_time_of_day_object_f1"] == 0.0


def test_gate_thresholds_and_regression() -> None:
    from vlm_eval.evaluation.gate import evaluate_gate

    spec = {
        "thresholds": {
            "object_presence.micro_f1": {"min": 0.5},
            "format.parse_success_rate": {"min": 0.9},
        },
        "regression": {"object_presence.micro_f1": {"max_drop": 0.05}},
    }
    run = {"object_presence.micro_f1": 0.6}
    base = {"object_presence.micro_f1": 0.7}
    checks = {(c.key, c.rule.split()[0]): c.passed for c in evaluate_gate(spec, run, base)}
    assert checks[("object_presence.micro_f1", ">=")] is True
    assert checks[("format.parse_success_rate", ">=")] is False  # missing metric fails closed
    assert checks[("object_presence.micro_f1", "drop")] is False  # dropped 0.10 > 0.05


def test_blind_prior_claims_frequent_classes_only() -> None:
    from vlm_eval.evaluation.metrics.objects import blind_prior

    pairs = [
        EvalPair(gt=make_gt(token="a", objects={"car": "1-2", "bus": "1-2"}), pred=make_pred("a")),
        EvalPair(gt=make_gt(token="b", objects={"car": "1-2"}), pred=make_pred("b")),
    ]
    # car is in 2/2 frames -> claimed; bus in 1/2 -> claimed (>= 0.5)
    assert blind_prior(pairs, TAX.object_classes)["blind_prior_micro_recall"] == 1.0
    assert blind_prior(pairs, TAX.object_classes)["blind_prior_micro_precision"] == 0.75
