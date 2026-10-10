"""Result writers: one row per frame, in a simple structured format."""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TypeVar

from pydantic import BaseModel

from vlm_eval.domain import Prediction
from vlm_eval.registry import Registry
from vlm_eval.taxonomy import Taxonomy

M = TypeVar("M", bound=BaseModel)


class ResultWriter(Protocol):
    def write(self, predictions: Sequence[Prediction], out_dir: Path) -> Path: ...


WRITERS: Registry[ResultWriter] = Registry("writer")


def write_jsonl(items: Sequence[BaseModel], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for item in items:
            fh.write(item.model_dump_json() + "\n")
    return path


def read_jsonl(path: Path, model: type[M]) -> list[M]:
    with path.open() as fh:
        return [model.model_validate(json.loads(line)) for line in fh if line.strip()]


@WRITERS.register("jsonl")
class JsonlWriter:
    filename = "predictions.jsonl"

    def __init__(self, taxonomy: Taxonomy | None = None) -> None:
        pass  # writes the full models; no vocabulary needed

    def write(self, predictions: Sequence[Prediction], out_dir: Path) -> Path:
        return write_jsonl(predictions, out_dir / self.filename)


@WRITERS.register("csv")
class CsvWriter:
    """Flat, spreadsheet-friendly table (one column per attribute / object class)."""

    filename = "predictions.csv"

    def __init__(self, taxonomy: Taxonomy) -> None:
        self.taxonomy = taxonomy

    def write(self, predictions: Sequence[Prediction], out_dir: Path) -> Path:
        path = out_dir / self.filename
        path.parent.mkdir(parents=True, exist_ok=True)
        columns = [
            "scene_name",
            "sample_token",
            "model",
            "prompt_version",
            "parse_ok",
            "facts_source",
            *self.taxonomy.attribute_names,
            *self.taxonomy.object_classes,
            "description",
        ]
        with path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            for p in predictions:
                row: dict[str, object] = {
                    "scene_name": p.scene_name,
                    "sample_token": p.sample_token,
                    "model": p.model,
                    "prompt_version": p.prompt_version,
                    "parse_ok": p.parse_ok,
                    "facts_source": p.facts_source,
                    "description": p.description,
                }
                row.update({a: p.facts.attribute(a) for a in self.taxonomy.attribute_names})
                row.update({c: p.facts.bucket(c) for c in self.taxonomy.object_classes})
                writer.writerow(row)
        return path
