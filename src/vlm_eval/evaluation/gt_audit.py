"""Manual audit of the automatically derived ground truth.

``export_sheet`` writes one row per (frame, field) with the automatic value and an
empty ``manual_value`` column. A person looks at the image and fills it in;
``agreement`` then reports how often the automatic GT matches the human label.
Disagreements bound how much the metrics can be trusted.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from vlm_eval.domain import GroundTruth, Sample
from vlm_eval.evaluation.stats import safe_div
from vlm_eval.taxonomy import Taxonomy

COLUMNS = [
    "sample_token",
    "scene_name",
    "frame_index",
    "image",
    "field",
    "auto_value",
    "manual_value",
    "comment",
]


def _auto_values(gt: GroundTruth, taxonomy: Taxonomy) -> dict[str, str]:
    values = {f: str(gt.facts.attribute(f)) for f in taxonomy.attribute_names}
    values.update(
        {f"present:{c}": "yes" if gt.facts.present(c) else "no" for c in taxonomy.object_classes}
    )
    return values


def export_sheet(
    samples: list[Sample], gts: list[GroundTruth], path: Path, taxonomy: Taxonomy
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    images = {s.sample_token: next(iter(s.image_paths.values())) for s in samples}
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for gt in gts:
            for field, value in _auto_values(gt, taxonomy).items():
                writer.writerow(
                    {
                        "sample_token": gt.sample_token,
                        "scene_name": gt.scene_name,
                        "frame_index": gt.frame_index,
                        "image": images.get(gt.sample_token, ""),
                        "field": field,
                        "auto_value": value,
                        "manual_value": "",
                        "comment": "",
                    }
                )
    return path


def agreement(path: Path) -> dict[str, dict[str, float | None]]:
    """Per field family: number of checked labels and share where auto == manual."""
    checked: dict[str, list[int]] = defaultdict(list)
    with path.open() as fh:
        for row in csv.DictReader(fh):
            manual = row["manual_value"].strip().lower()
            if not manual:
                continue
            family = "objects" if row["field"].startswith("present:") else row["field"]
            ok = int(manual == row["auto_value"].strip().lower())
            checked[family].append(ok)
            checked["all"].append(ok)
    return {
        family: {"n": float(len(v)), "agreement": safe_div(sum(v), len(v))}
        for family, v in sorted(checked.items())
    }
