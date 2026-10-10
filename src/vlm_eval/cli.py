"""Command line entry point: ``vlm-eval run | evaluate | compare``."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Annotated, Any

import numpy as np
import typer
import yaml

from vlm_eval.config import load_config, load_scene_config
from vlm_eval.evaluation.compare import compare_runs
from vlm_eval.evaluation.evaluator import Evaluator
from vlm_eval.evaluation.gate import evaluate_gate, load_gate
from vlm_eval.evaluation.gt_audit import agreement, export_sheet
from vlm_eval.evaluation.leaderboard import leaderboard as render_leaderboard
from vlm_eval.evaluation.report import MarkdownReport
from vlm_eval.manifest import save_run_metadata
from vlm_eval.pipeline import build_pipeline
from vlm_eval.run_store import RunArtifacts, load_metrics, save_metrics
from vlm_eval.taxonomy import load_taxonomy

app = typer.Typer(add_completion=False, help=__doc__)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    for noisy in ("httpx", "httpcore", "urllib3", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _parse_overrides(items: list[str]) -> dict[str, Any]:
    overrides = {}
    for item in items:
        key, _, value = item.partition("=")
        overrides[key] = yaml.safe_load(value)
    return overrides


@app.command()
def run(
    config: Annotated[Path, typer.Option("--config", "-c", help="YAML run config")],
    set_: Annotated[
        list[str], typer.Option("--set", help="Override, e.g. loader.params.scenes=[scene-0061]")
    ] = [],  # noqa: B006
    verbose: bool = False,
) -> None:
    """Describe every selected frame with the VLM, write results and evaluate them."""
    _setup_logging(verbose)
    cfg = load_config(config, _parse_overrides(set_))
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    pipeline = build_pipeline(cfg)
    save_run_metadata(cfg.run_dir, cfg, pipeline.backend)
    _, results = pipeline.run(cfg.run_dir)
    typer.echo(f"Done. Report: {cfg.run_dir / 'report.md'}")
    headline = next((r for r in results if r.name == "object_presence"), None)
    if headline:
        typer.echo(f"Object micro F1: {headline.summary.get('micro_f1')}")


@app.command()
def evaluate(
    run_dir: Annotated[Path, typer.Argument(help="An existing outputs/<run_id> directory")],
    verbose: bool = False,
) -> None:
    """Recompute metrics and the report from saved predictions (no inference)."""
    _setup_logging(verbose)
    cfg = load_config(run_dir / "config.yaml")
    artifacts = RunArtifacts.load(run_dir)
    results = Evaluator.from_config(cfg.metrics, load_taxonomy(cfg.taxonomy)).evaluate(
        artifacts.ground_truth, artifacts.predictions
    )
    save_metrics(results, run_dir)
    typer.echo(f"Report: {MarkdownReport().render(artifacts, results)}")


@app.command()
def compare(
    run_a: Path,
    run_b: Path,
    out: Annotated[Path, typer.Option(help="Output directory")] = Path("outputs/compare"),
) -> None:
    """Paired comparison of two runs (two VLMs or two prompts) on their shared frames."""
    _setup_logging(False)
    taxonomy = load_taxonomy(load_config(run_a / "config.yaml").taxonomy)
    typer.echo(f"Comparison: {compare_runs(run_a, run_b, out, taxonomy)}")


@app.command()
def leaderboard(
    run_dirs: list[Path],
    out: Annotated[Path, typer.Option(help="Markdown output")] = Path("outputs/leaderboard.md"),
) -> None:
    """Headline metrics of several runs side by side."""
    table = render_leaderboard(run_dirs)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# Leaderboard\n\n" + table + "\n")
    typer.echo(table)


@app.command()
def gate(
    run_dir: Path,
    gates: Annotated[Path, typer.Option(help="Gate YAML")] = Path("configs/gates.yaml"),
    baseline: Annotated[Path | None, typer.Option(help="Baseline run for regression")] = None,
) -> None:
    """Pass/fail a run against thresholds (and a baseline). Exits 1 on failure (for CI)."""
    checks = evaluate_gate(
        load_gate(gates), load_metrics(run_dir), load_metrics(baseline) if baseline else None
    )
    for c in checks:
        value = "missing" if c.value is None else f"{c.value:.3f}"
        typer.echo(f"{'PASS' if c.passed else 'FAIL'}  {c.key:45s} {value:>8s}  ({c.rule})")
    failed = sum(not c.passed for c in checks)
    typer.echo(f"{len(checks) - failed}/{len(checks)} checks passed")
    raise typer.Exit(code=1 if failed else 0)


# --- scene level (main deliverable) --------------------------------------------------------


def _evaluate_scene_run(run_dir: Path) -> Path:
    from vlm_eval.domain import SceneDescription, SceneFactSheet
    from vlm_eval.evaluation.scene_metrics import evaluate_scenes
    from vlm_eval.evaluation.scene_report import SCENE_METRICS, render_scene_report
    from vlm_eval.scene_pipeline import FACT_SHEETS, SCENES, build_judge
    from vlm_eval.writers import read_jsonl

    cfg = load_scene_config(run_dir / "config.yaml")
    descriptions = read_jsonl(run_dir / SCENES, SceneDescription)
    evaluation = evaluate_scenes(
        descriptions,
        read_jsonl(run_dir / FACT_SHEETS, SceneFactSheet),
        build_judge(cfg),
        load_taxonomy(cfg.taxonomy),
        cfg.embedding_model,
        cfg.seed,
    )
    (run_dir / SCENE_METRICS).write_text(evaluation.model_dump_json(indent=2))
    views = descriptions[0].views if descriptions else []
    protocol = (
        f"Each scene is shown as {len(views)} views of "
        f"{len(views[0].frame_indices) if views else 0} frames (one VLM call per view); "
        "the final description is the view most consistent with the others."
    )
    return render_scene_report(evaluation, run_dir, protocol)


@app.command("run-scenes")
def run_scenes(
    config: Annotated[Path, typer.Option("--config", "-c", help="Scene run YAML")],
    set_: Annotated[
        list[str], typer.Option("--set", help="Override, e.g. scenes=[scene-0061]")
    ] = [],  # noqa: B006
    verbose: bool = False,
) -> None:
    """One description per scene (N frames x K views per scene), then evaluate it."""
    from vlm_eval.scene_pipeline import build_judge, build_scene_pipeline

    _setup_logging(verbose)
    cfg = load_scene_config(config, _parse_overrides(set_))
    pipeline = build_scene_pipeline(cfg)
    save_run_metadata(cfg.run_dir, cfg, pipeline.backend, {"judge": build_judge(cfg).name})
    pipeline.run(cfg.run_dir)
    typer.echo(
        f"Done. Scenes: {cfg.run_dir / 'scenes.jsonl'}  Report: {_evaluate_scene_run(cfg.run_dir)}"
    )


@app.command("evaluate-scenes")
def evaluate_scenes_cmd(run_dir: Path, verbose: bool = False) -> None:
    """Re-score a saved scene run (no inference)."""
    _setup_logging(verbose)
    typer.echo(f"Report: {_evaluate_scene_run(run_dir)}")


@app.command("compare-scenes")
def compare_scenes(
    run_a: Path,
    run_b: Path,
    out: Annotated[Path, typer.Option(help="Output directory")] = Path("outputs/scenes/compare"),
) -> None:
    """Paired comparison of two scene runs on their shared scenes."""
    from vlm_eval.evaluation.scene_compare import compare_scene_runs

    _setup_logging(False)
    typer.echo(f"Comparison: {compare_scene_runs(run_a, run_b, out)}")


@app.command("validate-judge")
def validate_judge_cmd(
    run_dir: Annotated[Path, typer.Argument(help="A scene run (its fact sheets are used)")],
    out: Annotated[Path, typer.Option(help="Output directory")] = Path(
        "outputs/scenes/judge_validation"
    ),
) -> None:
    """Check the claim judge on paraphrased claims with known truth (no human labels)."""
    from vlm_eval.domain import SceneFactSheet
    from vlm_eval.evaluation.judge_validation import validate_judge, write_judge_validation
    from vlm_eval.scene_pipeline import FACT_SHEETS, build_judge
    from vlm_eval.writers import read_jsonl

    _setup_logging(False)
    cfg = load_scene_config(run_dir / "config.yaml")
    judge = build_judge(cfg)
    probes = validate_judge(
        read_jsonl(run_dir / FACT_SHEETS, SceneFactSheet), judge, load_taxonomy(cfg.taxonomy)
    )
    typer.echo(f"Judge validation: {write_judge_validation(probes, judge.name, out)}")


@app.command("scene-leaderboard")
def scene_leaderboard_cmd(
    run_dirs: list[Path],
    out: Annotated[Path, typer.Option(help="Markdown output")] = Path(
        "outputs/scenes/leaderboard.md"
    ),
) -> None:
    """Headline scene-level metrics of several runs side by side."""
    from vlm_eval.evaluation.leaderboard import scene_leaderboard

    table = scene_leaderboard(run_dirs)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# Scene-level leaderboard\n\n" + table + "\n")
    typer.echo(table)


@app.command()
def ingest(
    run_dirs: list[Path],
    db: Annotated[Path, typer.Option(help="DuckDB file")] = Path("outputs/results.duckdb"),
) -> None:
    """Load run folders into the DuckDB results store (idempotent: a run is replaced)."""
    from vlm_eval.store import ingest as ingest_runs

    counts = ingest_runs(run_dirs, db)
    typer.echo(f"{db}: " + ", ".join(f"{t}={n}" for t, n in counts.items()))


@app.command()
def query(
    sql: Annotated[str | None, typer.Argument(help="SQL to run")] = None,
    example: Annotated[str | None, typer.Option(help="Named query from sql/examples.sql")] = None,
    db: Annotated[Path, typer.Option(help="DuckDB file")] = Path("outputs/results.duckdb"),
) -> None:
    """Run SQL (or a named example) against the results store."""
    from vlm_eval.evaluation.report import md_table
    from vlm_eval.store import example_queries
    from vlm_eval.store import query as run_query

    examples = example_queries()
    if example is not None:
        if example not in examples:
            raise typer.BadParameter(f"unknown example; available: {sorted(examples)}")
        sql = examples[example]
    if not sql:
        raise typer.BadParameter(f"give SQL or --example (one of {sorted(examples)})")
    columns, rows = run_query(db, sql)
    typer.echo(md_table(columns, [list(r) for r in rows]))


@app.command("gt-export")
def gt_export(
    run_dir: Annotated[Path, typer.Argument(help="Run whose frames to audit")],
    out: Path = Path("internal/gt_audit.csv"),
    every: Annotated[int, typer.Option(help="Keep every n-th frame")] = 4,
) -> None:
    """Write a sheet of automatic GT labels for manual checking."""
    run = RunArtifacts.load(run_dir)
    gts = run.ground_truth[::every]
    taxonomy = load_taxonomy(load_config(run_dir / "config.yaml").taxonomy)
    typer.echo(f"{len(gts)} frames -> {export_sheet(run.samples, gts, out, taxonomy)}")


@app.command("gt-agreement")
def gt_agreement(sheet: Path = Path("internal/gt_audit.csv")) -> None:
    """Agreement between the automatic GT and the manually filled sheet."""
    for family, row in agreement(sheet).items():
        value = row["agreement"]
        typer.echo(
            f"{family:16s} n={int(row['n'] or 0):3d}  agreement="
            f"{'-' if value is None else f'{value:.1%}'}"
        )


if __name__ == "__main__":
    app()
