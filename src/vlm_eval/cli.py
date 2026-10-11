"""Command line entry point: ``vlm-eval run | evaluate | compare``."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Annotated, Any

import numpy as np
import typer
import yaml

from vlm_eval.config import SceneRunConfig, load_config, load_scene_config
from vlm_eval.evaluation.compare import compare_runs
from vlm_eval.evaluation.gate import evaluate_gate, load_gate, load_summary
from vlm_eval.evaluation.leaderboard import leaderboard as render_leaderboard
from vlm_eval.manifest import save_run_metadata
from vlm_eval.pipeline import build_pipeline, evaluate_run
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


def _start(verbose: bool, seed: int | None = None) -> None:
    """Common start of every command: logging, and fixed seeds for runs."""
    _setup_logging(verbose)
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)


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
    cfg = load_config(config, _parse_overrides(set_))
    _start(verbose, cfg.seed)
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
    _start(verbose)
    typer.echo(f"Report: {evaluate_run(run_dir)}")


@app.command()
def compare(
    run_a: Path,
    run_b: Path,
    out: Annotated[Path, typer.Option(help="Output directory")] = Path("outputs/compare"),
) -> None:
    """Paired comparison of two runs (two VLMs or two prompts) on their shared frames."""
    _start(False)
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
    gates: Annotated[Path, typer.Option(help="Gate YAML (scene runs: configs/gates.yaml)")] = Path(
        "configs/gates.yaml"
    ),
    baseline: Annotated[Path | None, typer.Option(help="Baseline run for regression")] = None,
) -> None:
    """Pass/fail a run against thresholds (and a baseline). Exits 1 on failure (for CI)."""
    checks = evaluate_gate(
        load_gate(gates), load_summary(run_dir), load_summary(baseline) if baseline else None
    )
    for c in checks:
        value = "missing" if c.value is None else f"{c.value:.3f}"
        typer.echo(f"{'PASS' if c.passed else 'FAIL'}  {c.key:45s} {value:>8s}  ({c.rule})")
    failed = sum(not c.passed for c in checks)
    typer.echo(f"{len(checks) - failed}/{len(checks)} checks passed")
    raise typer.Exit(code=1 if failed else 0)


# --- scene level (main deliverable) --------------------------------------------------------


def _describe(cfg: SceneRunConfig, force: bool) -> Path:
    """Shared inference step of describe-scenes and run-scenes."""
    from vlm_eval.scene_pipeline import RunExistsError, describe_scene_run

    try:
        return describe_scene_run(cfg, force=force)
    except RunExistsError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command("describe-scenes")
def describe_scenes(
    config: Annotated[Path, typer.Option("--config", "-c", help="Scene run YAML")],
    set_: Annotated[
        list[str], typer.Option("--set", help="Override, e.g. scenes=[scene-0061]")
    ] = [],  # noqa: B006
    verbose: bool = False,
    force: Annotated[
        bool, typer.Option(help="Overwrite an existing run made with a different config")
    ] = False,
) -> None:
    """Inference only: one description per scene, no scoring (run evaluate-scenes later)."""
    cfg = load_scene_config(config, _parse_overrides(set_))
    _start(verbose, cfg.seed)
    scenes = _describe(cfg, force)
    typer.echo(f"Done. Scenes: {scenes}  Score with: vlm-eval evaluate-scenes {cfg.run_dir}")


@app.command("run-scenes")
def run_scenes(
    config: Annotated[Path, typer.Option("--config", "-c", help="Scene run YAML")],
    set_: Annotated[
        list[str], typer.Option("--set", help="Override, e.g. scenes=[scene-0061]")
    ] = [],  # noqa: B006
    verbose: bool = False,
    force: Annotated[
        bool, typer.Option(help="Overwrite an existing run made with a different config")
    ] = False,
) -> None:
    """describe-scenes followed by evaluate-scenes, in one step."""
    from vlm_eval.scene_pipeline import evaluate_scene_run

    cfg = load_scene_config(config, _parse_overrides(set_))
    _start(verbose, cfg.seed)
    scenes = _describe(cfg, force)
    typer.echo(f"Done. Scenes: {scenes}  Report: {evaluate_scene_run(cfg.run_dir)}")


@app.command("evaluate-model")
def evaluate_model(
    model: Annotated[str, typer.Option("--model", "-m", help="Hugging Face model id")],
    prompt: Annotated[str, typer.Option(help="scene_guided or scene_open")] = "scene_guided",
    baseline: Annotated[
        Path | None, typer.Option(help="Scored run to compare with (same frames)")
    ] = Path("outputs/scenes/qwen2vl_guided"),
    gates: Annotated[Path, typer.Option(help="Gate YAML")] = Path("configs/gates.yaml"),
    run_id: Annotated[str | None, typer.Option(help="Run name (default: from the model)")] = None,
    set_: Annotated[
        list[str], typer.Option("--set", help="Override, e.g. loader.params.scenes=[scene-1094]")
    ] = [],  # noqa: B006
    force: Annotated[
        bool, typer.Option(help="Overwrite an existing run made with a different config")
    ] = False,
    verbose: bool = False,
) -> None:
    """Evaluate a Hugging Face VLM on the dataset: describe, score, compare with the baseline,
    gate. Writes outputs/scenes/<run>/verdict.md; exits 1 if the gate fails."""
    from vlm_eval.model_eval import model_config, model_verdict
    from vlm_eval.scene_pipeline import evaluate_scene_run

    cfg = model_config(model, prompt, run_id=run_id, overrides=_parse_overrides(set_))
    _start(verbose, cfg.seed)
    _describe(cfg, force)
    # Cite the judge validation that sits with the baseline runs, wherever this run is written.
    validation = (
        baseline.parent / "judge_validation" / "judge_validation.json" if baseline else None
    )
    evaluate_scene_run(cfg.run_dir, validation if validation and validation.exists() else None)
    verdict = model_verdict(cfg.run_dir, baseline, gates)
    typer.echo((cfg.run_dir / "verdict.md").read_text())
    raise typer.Exit(code=0 if verdict.passed else 1)


@app.command("evaluate-scenes")
def evaluate_scenes_cmd(
    run_dir: Path,
    judge_validation: Annotated[
        Path | None,
        typer.Option(help="validate-judge output to cite (default: <runs>/judge_validation)"),
    ] = None,
    verbose: bool = False,
) -> None:
    """Re-score a saved scene run (no inference)."""
    from vlm_eval.scene_pipeline import evaluate_scene_run

    _start(verbose)
    typer.echo(f"Report: {evaluate_scene_run(run_dir, judge_validation)}")


@app.command("compare-scenes")
def compare_scenes(
    run_a: Path,
    run_b: Path,
    out: Annotated[Path, typer.Option(help="Output directory")] = Path("outputs/scenes/compare"),
) -> None:
    """Paired comparison of two scene runs on their shared scenes."""
    from vlm_eval.evaluation.scene_compare import compare_scene_runs

    _start(False)
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

    _start(False)
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


if __name__ == "__main__":
    app()
