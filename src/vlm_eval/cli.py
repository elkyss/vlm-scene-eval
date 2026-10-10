"""Command line entry point: ``vlm-eval run | evaluate | compare``."""

from __future__ import annotations

import logging
import random
import shutil
from pathlib import Path
from typing import Annotated, Any

import numpy as np
import typer
import yaml

from vlm_eval.config import load_config
from vlm_eval.evaluation.compare import compare_runs
from vlm_eval.evaluation.evaluator import Evaluator
from vlm_eval.evaluation.gate import evaluate_gate, load_gate
from vlm_eval.evaluation.gt_audit import agreement, export_sheet
from vlm_eval.evaluation.leaderboard import leaderboard as render_leaderboard
from vlm_eval.evaluation.report import MarkdownReport
from vlm_eval.manifest import write_manifest
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
    cfg.run_dir.mkdir(parents=True, exist_ok=True)
    (cfg.run_dir / "config.yaml").write_text(yaml.safe_dump(cfg.model_dump(mode="json")))
    pipeline = build_pipeline(cfg)
    _, results = pipeline.run(cfg.run_dir)
    inner = getattr(pipeline.backend, "backend", pipeline.backend)
    write_manifest(
        cfg.run_dir,
        cfg,
        {
            "model_signature": pipeline.backend.signature,
            "model_revision": getattr(inner, "resolved_revision", None),
        },
    )
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
    if out.exists():
        shutil.rmtree(out)
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
