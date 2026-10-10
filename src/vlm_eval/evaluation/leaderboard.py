"""Side-by-side headline metrics for many runs (a minimal run registry view)."""

from __future__ import annotations

from pathlib import Path

from vlm_eval.evaluation.report import fmt, md_table
from vlm_eval.run_store import RunArtifacts, load_metrics

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
