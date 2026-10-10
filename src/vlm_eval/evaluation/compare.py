"""Paired comparison of two runs (two VLMs, or two prompts) on the same frames.

Frames of one scene are strongly correlated, so confidence intervals come from a
bootstrap that resamples whole scenes, and binary per-frame outcomes are compared
with an exact paired sign-flip test over scenes.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Callable
from functools import partial
from pathlib import Path

import numpy as np

from vlm_eval.evaluation.evaluator import join
from vlm_eval.evaluation.metrics import EvalPair, frame_f1, frame_outcomes
from vlm_eval.evaluation.report import fmt, md_table
from vlm_eval.evaluation.stats import cluster_bootstrap_ci, prf, sign_flip_p
from vlm_eval.run_store import RunArtifacts
from vlm_eval.taxonomy import Taxonomy

Paired = tuple[EvalPair, EvalPair]


def _micro_f1(pairs: list[EvalPair], classes: tuple[str, ...]) -> float | None:
    tp = fp = fn = 0
    for p in pairs:
        for o in frame_outcomes(p, classes).values():
            tp += o == "tp"
            fp += o == "fp"
            fn += o == "fn"
    return prf(tp, fp, fn)["f1"]


def _attr_correct(p: EvalPair, attr: str) -> bool:
    return p.pred.facts.attribute(attr) == p.gt.facts.attribute(attr)


def _presence_correct(p: EvalPair, cls: str) -> bool:
    return frame_outcomes(p, (cls,))[cls] in {"tp", "tn", "fp_far"}


def _parse_ok(p: EvalPair) -> bool:
    return p.pred.parse_ok


def _mean_of(value: Callable[[EvalPair], float]) -> Callable[[list[EvalPair]], float | None]:
    def stat(pairs: list[EvalPair]) -> float | None:
        return float(np.mean([value(p) for p in pairs])) if pairs else None

    return stat


def compare_runs(
    run_a: Path, run_b: Path, out_dir: Path, taxonomy: Taxonomy, seed: int = 0
) -> Path:
    classes = taxonomy.object_classes

    def f1(p: EvalPair) -> float:
        return frame_f1(frame_outcomes(p, classes))

    a, b = RunArtifacts.load(run_a), RunArtifacts.load(run_b)
    pairs_a = {p.gt.sample_token: p for p in join(a.ground_truth, a.predictions)}
    pairs_b = {p.gt.sample_token: p for p in join(b.ground_truth, b.predictions)}
    common = sorted(set(pairs_a) & set(pairs_b))
    if not common:
        raise ValueError("The two runs share no frames")
    paired: list[Paired] = [(pairs_a[t], pairs_b[t]) for t in common]
    by_scene: dict[str, list[Paired]] = defaultdict(list)
    for pa, pb in paired:
        by_scene[pa.gt.scene_name].append((pa, pb))
    clusters = list(by_scene.values())

    name_a = f"{a.predictions[0].model} / {a.predictions[0].prompt_version}"
    name_b = f"{b.predictions[0].model} / {b.predictions[0].prompt_version}"

    def diff(
        stat: Callable[[list[EvalPair]], float | None],
    ) -> Callable[[list[Paired]], float | None]:
        def inner(items: list[Paired]) -> float | None:
            sa, sb = stat([x for x, _ in items]), stat([y for _, y in items])
            return None if sa is None or sb is None else sb - sa

        return inner

    rows: list[dict[str, object]] = []

    def add_row(
        label: str,
        stat: Callable[[list[EvalPair]], float | None],
    ) -> None:
        va, vb = stat([x for x, _ in paired]), stat([y for _, y in paired])
        lo, hi = cluster_bootstrap_ci(clusters, diff(stat), seed=seed)
        row: dict[str, object] = {
            "metric": label,
            "a": va,
            "b": vb,
            "diff": None if va is None or vb is None else vb - va,
            "ci_low": lo,
            "ci_high": hi,
            "sign_flip_p": sign_flip_p([d for c in clusters if (d := diff(stat)(c)) is not None]),
        }
        rows.append(row)

    add_row("Object micro F1", partial(_micro_f1, classes=classes))
    add_row("Mean frame object F1", _mean_of(f1))
    for cls in classes:
        correct = partial(_presence_correct, cls=cls)
        add_row(f"Presence accuracy: {cls}", _mean_of(correct))
    for attr in taxonomy.attribute_names:
        correct = partial(_attr_correct, attr=attr)
        add_row(f"Accuracy: {attr}", _mean_of(correct))
    add_row("Valid structured output", _mean_of(_parse_ok))
    add_row("Mean latency (s)", _mean_of(lambda p: p.pred.latency_s))

    disagreements = sorted(
        paired,
        key=lambda xy: abs(f1(xy[0]) - f1(xy[1])),
        reverse=True,
    )[:6]

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "compare.json").write_text(
        json.dumps(
            {
                "a": name_a,
                "b": name_b,
                "frames": len(paired),
                "scenes": len(clusters),
                "rows": rows,
            },
            indent=2,
            default=str,
        )
    )

    table = [
        [
            r["metric"],
            fmt(r["a"]),
            fmt(r["b"]),
            fmt(r["diff"]),
            f"[{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]",
            "–" if r["sign_flip_p"] is None else f"{r['sign_flip_p']:.3f}",
        ]
        for r in rows
    ]
    for r, t in zip(rows, table, strict=True):
        if r["metric"] == "Mean latency (s)":
            t[1:4] = [fmt(r["a"], False), fmt(r["b"], False), fmt(r["diff"], False)]
            t[4] = f"[{fmt(r['ci_low'], False)}, {fmt(r['ci_high'], False)}]"
    examples = []
    for x, y in disagreements:
        examples.append(
            f"**{x.gt.scene_name} / frame {x.frame_index}**. GT objects `{x.gt.facts.objects}`\n\n"
            f"- A (F1 {f1(x):.2f}): {x.pred.description or '(empty)'}\n"
            f"- B (F1 {f1(y):.2f}): {y.pred.description or '(empty)'}"
        )
    report = "\n\n".join(
        [
            "# Run comparison",
            f"- **A**: `{name_a}`\n- **B**: `{name_b}`\n- {len(paired)} shared frames, "
            f"{len(clusters)} scenes",
            "Δ = B − A. 95% CI from a bootstrap over scenes "
            "(frames within a scene are correlated). "
            "The p-value is an exact paired sign-flip test on per-scene differences "
            "(frames of a scene are not independent, so testing happens at scene level). "
            "With only 10 scenes, CIs are wide: treat differences whose CI crosses 0 as "
            "inconclusive.",
            md_table(["Metric", "A", "B", "Δ", "95% CI of Δ", "Scene sign-flip p"], table),
            "## Largest disagreements",
            *examples,
        ]
    )
    path = out_dir / "compare_report.md"
    path.write_text(report + "\n")
    return path
