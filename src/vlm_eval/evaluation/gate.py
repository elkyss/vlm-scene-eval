"""Quality gate: pass/fail a run against absolute thresholds and a baseline run.

Meant for CI: before a new model or prompt ships, ``vlm-eval gate`` exits non-zero if
any metric is below its floor, above its ceiling, or regressed past the allowed
margin compared to the current baseline.

Gate file format (keys are ``<metric>.<summary key>`` from metrics.json)::

    thresholds:
      object_presence.micro_f1: {min: 0.5}
      object_presence.hallucination_rate: {max: 0.3}
    regression:            # maximum allowed change in the bad direction vs. baseline
      object_presence.micro_f1: {max_drop: 0.05}
      object_presence.hallucination_rate: {max_rise: 0.05}
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from vlm_eval.domain import MetricResult


@dataclass(frozen=True)
class GateCheck:
    key: str
    rule: str
    value: float | None
    passed: bool


def _lookup(results: list[MetricResult], key: str) -> float | None:
    metric, _, field = key.partition(".")
    for r in results:
        if r.name == metric:
            return r.summary.get(field)
    return None


def evaluate_gate(
    spec: dict[str, Any],
    results: list[MetricResult],
    baseline: list[MetricResult] | None = None,
) -> list[GateCheck]:
    checks = []
    for key, rule in (spec.get("thresholds") or {}).items():
        value = _lookup(results, key)
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
            value, base = _lookup(results, key), _lookup(baseline, key)
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
