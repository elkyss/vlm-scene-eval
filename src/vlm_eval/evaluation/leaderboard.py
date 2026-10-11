"""Side-by-side headline metrics for many runs, frame level and scene level."""

from __future__ import annotations

from pathlib import Path

from vlm_eval.evaluation.report import fmt, fmt_ci, md_table
from vlm_eval.evaluation.scene_metrics import SceneEvaluation
from vlm_eval.evaluation.scene_report import SCENE_METRICS
from vlm_eval.run_artifacts import RunArtifacts, load_metrics

# (column label, metric, summary key, is_percentage)
COLUMNS: tuple[tuple[str, str, str, bool], ...] = (
    ("Object F1", "object_presence", "micro_f1", True),
    ("Blind baseline F1", "object_presence", "blind_prior_micro_f1", True),
    ("Precision", "object_presence", "micro_precision", True),
    ("Recall", "object_presence", "micro_recall", True),
    ("Hallucination", "object_presence", "hallucination_rate", True),
    ("Count exact", "counting", "exact_bucket_accuracy", True),
    ("Day/night bal. acc.", "attributes", "time_of_day_balanced_accuracy", True),
    ("Attr. mean bal. acc.", "attributes", "mean_balanced_accuracy", True),
    ("Valid output", "format", "parse_success_rate", True),
    ("Latency/frame (s)", "format", "mean_latency_s", False),
)


def leaderboard(run_dirs: list[Path]) -> str:
    rows = []
    for run_dir in run_dirs:
        if not (run_dir / "metrics.json").exists():
            continue
        results = {r.name: r for r in load_metrics(run_dir)}
        pred = RunArtifacts.load(run_dir).predictions[0]
        row: list[str] = [run_dir.name, pred.model, pred.prompt_version.split("@")[0]]
        for _, metric, key, pct in COLUMNS:
            value = results[metric].summary.get(key) if metric in results else None
            row.append(fmt(value, pct))
        rows.append(row)
    headers = ["Run", "Model", "Prompt", *(c[0] for c in COLUMNS)]
    return md_table(headers, rows)


def scene_leaderboard(run_dirs: list[Path]) -> str:
    columns = (  # (header, summary key, format): "pct", "ci" (pct with its 95% CI) or "num"
        ("CHAIR_i", "chair_i", "pct"),
        ("CHAIR_s", "chair_s", "pct"),
        ("Obj. coverage", "object_coverage", "pct"),
        ("Supported", "claims_supported", "pct"),
        ("Specific support (own − other scenes) [95% CI]", "specific_claims_supported", "ci"),
        ("Specific objects (own − other scenes) [95% CI]", "specific_object_coverage", "ci"),
        ("Unverifiable", "claims_unverifiable", "pct"),
        ("Human coverage", "human_coverage", "pct"),
        ("Repetition loops", "repetition_loop_rate", "pct"),
        ("View agreement", "view_agreement", "pct"),
        ("s / call", "mean_latency_s_per_call", "num"),
    )
    rows = []
    for run_dir in run_dirs:
        path = run_dir / SCENE_METRICS
        if not path.exists():
            continue
        ev = SceneEvaluation.model_validate_json(path.read_text())
        rows.append(
            [run_dir.name, ev.model, ev.prompt_version.split("@")[0]]
            + [
                fmt_ci(ev.summary, key) if kind == "ci" else fmt(ev.summary.get(key), kind == "pct")
                for _, key, kind in columns
            ]
        )
    return md_table(["Run", "Model", "Prompt", *(c[0] for c in columns)], rows)
