"""Quality gate: pass/fail a run against absolute thresholds and a baseline run.

Meant for CI: before a new model or prompt ships, ``vlm-eval gate`` exits non-zero if
any metric is below its floor, above its ceiling, or regressed past the allowed
margin compared to the current baseline.

Gate file format (keys are summary keys: ``object_coverage`` for scene runs,
``<metric>.<summary key>`` for frame runs)::

    thresholds:
      object_presence.micro_f1: {min: 0.5}
      object_presence.hallucination_rate: {max: 0.3}
    regression:            # maximum allowed change in the bad direction vs. baseline
      object_presence.micro_f1: {max_drop: 0.05}
      object_presence.hallucination_rate: {max_rise: 0.05}
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GateCheck:
    key: str
    rule: str
    value: float | None
    passed: bool


def load_summary(run_dir: Path) -> dict[str, float | None]:
    """Flat metric summary of a run: scene runs use their summary keys as they are
    (``object_coverage``), frame runs prefix the metric name (``object_presence.micro_f1``)."""
    scene = run_dir / "scene_metrics.json"
    if scene.exists():
        summary: dict[str, float | None] = json.loads(scene.read_text())["summary"]
        return summary
    data = json.loads((run_dir / "metrics.json").read_text())
    return {f"{name}.{k}": v for name, m in data.items() for k, v in m["summary"].items()}


def evaluate_gate(
    spec: dict[str, Any],
    results: Mapping[str, float | None],
    baseline: Mapping[str, float | None] | None = None,
) -> list[GateCheck]:
    checks = []
    for key, rule in (spec.get("thresholds") or {}).items():
        value = results.get(key)
        if "min" in rule:
            checks.append(
                GateCheck(
                    key, f">= {rule['min']}", value, value is not None and value >= rule["min"]
                )
            )
        if "max" in rule:
            checks.append(
                GateCheck(
                    key, f"<= {rule['max']}", value, value is not None and value <= rule["max"]
                )
            )
    if baseline is not None:
        for key, rule in (spec.get("regression") or {}).items():
            value, base = results.get(key), baseline.get(key)
            if value is None or base is None:
                checks.append(GateCheck(key, "regression (missing value)", value, False))
                continue
            if "max_drop" in rule:
                checks.append(
                    GateCheck(
                        key,
                        f"drop <= {rule['max_drop']} vs {base:.3f}",
                        value,
                        base - value <= rule["max_drop"],
                    )
                )
            if "max_rise" in rule:
                checks.append(
                    GateCheck(
                        key,
                        f"rise <= {rule['max_rise']} vs {base:.3f}",
                        value,
                        value - base <= rule["max_rise"],
                    )
                )
    return checks


def load_gate(path: Path) -> dict[str, Any]:
    spec: dict[str, Any] = yaml.safe_load(path.read_text())
    return spec
