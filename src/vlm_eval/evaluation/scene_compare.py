"""Paired comparison of two scene-level runs (two VLMs or two prompts) on the same scenes.

With ~10 scenes, intervals are wide: the report gives a bootstrap CI over scenes, paired
per-scene win counts and an exact paired sign-flip test over scenes, and says a
difference is inconclusive when the interval crosses zero.
"""

from __future__ import annotations

import json
from pathlib import Path

from vlm_eval.evaluation.report import fmt, md_table
from vlm_eval.evaluation.scene_metrics import DescriptionScore, SceneEvaluation, aggregate
from vlm_eval.evaluation.scene_report import SCENE_METRICS
from vlm_eval.evaluation.stats import cluster_bootstrap_ci, sign_flip_p

Pair = tuple[DescriptionScore, DescriptionScore]
METRICS = (  # (label, key, lower is better)
    ("CHAIR_i", "chair_i", True),
    ("Object coverage", "object_coverage", False),
    ("Claims supported", "claims_supported", False),
    ("Claims contradicted", "claims_contradicted", True),
    ("Human-sentence coverage", "human_coverage", False),
)


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
        va = aggregate([x for x, _ in pairs])[key]
        vb = aggregate([y for _, y in pairs])[key]

        def diff(items: list[Pair], k: str = key) -> float | None:
            sa, sb = aggregate([x for x, _ in items])[k], aggregate([y for _, y in items])[k]
            return None if sa is None or sb is None else sb - sa

        lo, hi = cluster_bootstrap_ci([[p] for p in pairs], diff, seed=seed)
        wins = losses = 0
        scene_diffs = []
        for x, y in pairs:
            rx, ry = x.rates()[key], y.rates()[key]
            if rx is None or ry is None:
                continue
            scene_diffs.append(ry - rx)
            if rx == ry:
                continue
            better = ry < rx if lower_better else ry > rx
            wins, losses = wins + better, losses + (not better)
        p_value = sign_flip_p(scene_diffs)
        verdict = (
            "inconclusive"
            if lo is None or hi is None or lo <= 0 <= hi
            else "B better"
            if (hi < 0) == lower_better
            else "A better"
        )
        record = {
            "metric": label,
            "a": va,
            "b": vb,
            "diff": None if va is None or vb is None else vb - va,
            "ci_low": lo,
            "ci_high": hi,
            "b_wins": wins,
            "b_losses": losses,
            "sign_flip_p": p_value,
            "verdict": verdict,
        }
        records.append(record)
        table.append(
            [
                label,
                fmt(va),
                fmt(vb),
                fmt(record["diff"]),
                f"[{fmt(lo)}, {fmt(hi)}]",
                f"{wins} / {losses}",
                "–" if p_value is None else f"{p_value:.3f}",
                verdict,
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
            "where B is better/worse on that scene's own rate. The p-value is an exact paired "
            "sign-flip test on the per-scene differences (items within a scene are not "
            f"independent, so nothing is tested at item level). With {len(pairs)} scenes, a "
            "difference whose CI crosses 0 is reported as inconclusive.",
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
