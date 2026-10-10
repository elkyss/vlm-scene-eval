"""Reads and writes the artifacts of a run directory (``outputs/<run_id>/``)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from vlm_eval.domain import GroundTruth, MetricResult, Prediction, Sample
from vlm_eval.writers import read_jsonl, write_jsonl

SAMPLES = "samples.jsonl"
GROUND_TRUTH = "ground_truth.jsonl"
PREDICTIONS = "predictions.jsonl"
METRICS = "metrics.json"


@dataclass
class RunArtifacts:
    run_dir: Path
    samples: list[Sample]
    ground_truth: list[GroundTruth]
    predictions: list[Prediction]

    @classmethod
    def load(cls, run_dir: Path) -> RunArtifacts:
        return cls(
            run_dir=run_dir,
            samples=read_jsonl(run_dir / SAMPLES, Sample),
            ground_truth=read_jsonl(run_dir / GROUND_TRUTH, GroundTruth),
            predictions=read_jsonl(run_dir / PREDICTIONS, Prediction),
        )

    def save_inputs(self) -> None:
        write_jsonl(self.samples, self.run_dir / SAMPLES)
        write_jsonl(self.ground_truth, self.run_dir / GROUND_TRUTH)


def save_metrics(results: list[MetricResult], run_dir: Path) -> Path:
    path = run_dir / METRICS
    path.write_text(json.dumps({r.name: r.model_dump() for r in results}, indent=2))
    return path


def load_metrics(run_dir: Path) -> list[MetricResult]:
    data = json.loads((run_dir / METRICS).read_text())
    return [MetricResult.model_validate(v) for v in data.values()]
