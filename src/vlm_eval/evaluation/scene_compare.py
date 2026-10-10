"""Paired comparison of two scene-level runs (two VLMs or two prompts) on the same scenes.

With ~10 scenes, intervals are wide: the report gives a bootstrap CI over scenes, paired
per-scene win counts and an exact paired sign-flip test over scenes, and says a
difference is inconclusive when the interval crosses zero.
"""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path

from vlm_eval.evaluation.report import fmt, md_table
from vlm_eval.evaluation.scene_metrics import DescriptionScore, SceneEvaluation, aggregate
from vlm_eval.evaluation.scene_report import SCENE_METRICS
from vlm_eval.evaluation.stats import paired_comparison

Pair = tuple[DescriptionScore, DescriptionScore]
METRICS = (  # (label, key, lower is better)
    ("CHAIR_i", "chair_i", True),
    ("Object coverage", "object_coverage", False),
    ("Claims supported", "claims_supported", False),
    ("Claims contradicted", "claims_contradicted", True),
    ("Human-sentence coverage", "human_coverage", False),
)


def _rate(scores: list[DescriptionScore], key: str) -> float | None:
    return aggregate(scores)[key]


def _load(run_dir: Path) -> SceneEvaluation:
    return SceneEvaluation.model_validate_json((run_dir / SCENE_METRICS).read_text())


def compare_scene_runs(run_a: Path, run_b: Path, out_dir: Path, seed: int = 0) -> Path:
    a, b = _load(run_a), _load(run_b)
    rows_b = {r.scene_name: r for r in b.rows}
    pairs: list[Pair] = [
        (r.final, rows_b[r.scene_name].final) for r in a.rows if r.scene_name in rows_b
    ]
    if not pairs:
        raise ValueError("The two runs share no scenes")

    table, records = [], []
    for label, key, lower_better in METRICS:
        c = paired_comparison([[p] for p in pairs], partial(_rate, key=key), lower_better, seed)
        wins = losses = 0
        for x, y in pairs:
            rx, ry = x.rates()[key], y.rates()[key]
            if rx is None or ry is None or rx == ry:
                continue
            better = ry < rx if lower_better else ry > rx
            wins, losses = wins + better, losses + (not better)
        records.append(
            {
                "metric": label,
                "a": c.a,
                "b": c.b,
                "diff": c.diff,
                "ci_low": c.ci_low,
                "ci_high": c.ci_high,
                "b_wins": wins,
                "b_losses": losses,
                "sign_flip_p": c.p_value,
                "verdict": c.verdict,
            }
        )
        table.append(
            [
                label,
                fmt(c.a),
                fmt(c.b),
                fmt(c.diff),
                f"[{fmt(c.ci_low)}, {fmt(c.ci_high)}]",
                f"{wins} / {losses}",
                "–" if c.p_value is None else f"{c.p_value:.3f}",
                c.verdict,
            ]
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "compare.json").write_text(
        json.dumps(
            {
                "a": f"{a.model} / {a.prompt_version}",
                "b": f"{b.model} / {b.prompt_version}",
                "scenes": len(pairs),
                "metrics": records,
            },
            indent=2,
        )
    )
    report = "\n\n".join(
        [
            "# Scene-level comparison",
            f"- **A**: `{a.model} / {a.prompt_version}`\n"
            f"- **B**: `{b.model} / {b.prompt_version}`\n"
            f"- {len(pairs)} shared scenes",
            "Δ = B − A. The 95% CI comes from a bootstrap over scenes. Wins/losses count scenes "
            "where B is better/worse on that scene's own rate (a metric undefined for a "
            "scene, e.g. CHAIR_i with no object mentions, is skipped). The p-value is an exact "
            "paired "
            "sign-flip test on the per-scene differences (items within a scene are not "
            "independent, so nothing is tested at item level); when only one scene or none "
            "differs, p = 1 by construction. With "
            f"{len(pairs)} scenes, a difference whose CI crosses 0 is reported as inconclusive.",
            md_table(
                [
                    "Metric",
                    "A",
                    "B",
                    "Δ",
                    "95% CI of Δ",
                    "B wins / losses",
                    "Sign-flip p",
                    "Verdict",
                ],
                table,
            ),
        ]
    )
    path = out_dir / "compare_report.md"
    path.write_text(report + "\n")
    return path
