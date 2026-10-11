"""Evaluate a Hugging Face VLM on the dataset in one step and get a verdict.

``vlm-eval evaluate-model --model <hf id>`` builds a scene-run config from a template (same
loader, frames, ground truth, judge and protocol as the committed runs), describes every scene
with the model, scores the descriptions, compares them with a baseline run on the same frames
and applies the release gate. Everything is written to ``outputs/scenes/<run_id>/``; the
verdict is ``verdict.md`` there.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from vlm_eval.config import SceneRunConfig, load_scene_config
from vlm_eval.evaluation.gate import GateCheck, evaluate_gate, load_gate, load_summary
from vlm_eval.evaluation.report import md_table

DEFAULT_TEMPLATE = Path("configs/scenes/qwen2vl_guided.yaml")
DEFAULT_BASELINE = Path("outputs/scenes/qwen2vl_guided")
DEFAULT_GATES = Path("configs/gates.yaml")
BASELINE_DIR = "vs_baseline"
VERDICT = "verdict.md"
MIN_SCENES = 5  # below this a run is a smoke test: too few scenes for a verdict

# Headline metrics shown in the verdict: (summary key, label, lower is better).
HEADLINE = (
    ("object_coverage", "Visible objects mentioned", False),
    ("chair_i", "Invented objects (CHAIR_i)", True),
    ("human_coverage", "Human sentence covered", False),
    ("claims_supported", "Claims supported (judge; indicative)", False),
    ("specific_object_coverage", "Own scene − other scenes (objects)", False),
    ("repetition_loop_rate", "Repetition loops", True),
)


def run_id_for_model(model_id: str, prompt: str) -> str:
    """``Qwen/Qwen2.5-VL-3B-Instruct`` + ``scene_guided`` -> ``qwen2.5-vl-3b-instruct_guided``."""
    name = re.sub(r"[^a-z0-9.]+", "-", model_id.split("/")[-1].lower()).strip("-")
    return f"{name}_{prompt.removeprefix('scene_')}"


def model_config(
    model_id: str,
    prompt: str = "scene_guided",
    template: Path = DEFAULT_TEMPLATE,
    run_id: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> SceneRunConfig:
    """A scene-run config for ``model_id``: the template's protocol, this model and prompt."""
    return load_scene_config(
        template,
        {
            "vlm.name": "hf",
            "vlm.params.model_id": model_id,
            "prompt": prompt,
            "run_id": run_id or run_id_for_model(model_id, prompt),
            **(overrides or {}),
        },
    )


@dataclass
class ModelVerdict:
    run_dir: Path
    summary: dict[str, float | None]
    comparison: Path | None
    checks: list[GateCheck]

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)


def model_verdict(
    run_dir: Path, baseline: Path | None = DEFAULT_BASELINE, gates: Path = DEFAULT_GATES
) -> ModelVerdict:
    """Compare a scored run with the baseline and apply the gate; writes ``verdict.md``."""
    from vlm_eval.evaluation.scene_compare import compare_scene_runs

    if baseline is not None and not (baseline / "scene_metrics.json").exists():
        baseline = None  # no scored baseline: report the model alone
    comparison = compare_scene_runs(baseline, run_dir, run_dir / BASELINE_DIR) if baseline else None
    summary = load_summary(run_dir)
    checks = evaluate_gate(load_gate(gates), summary, load_summary(baseline) if baseline else None)
    verdict = ModelVerdict(run_dir, summary, comparison, checks)
    (run_dir / VERDICT).write_text(render_verdict(verdict, baseline))
    return verdict


def _pct(v: float | None) -> str:
    return "–" if v is None else f"{100 * v:.1f}%"


def render_verdict(v: ModelVerdict, baseline: Path | None) -> str:
    import json

    rows = [[label, _pct(v.summary.get(key))] for key, label, _ in HEADLINE]
    parts = [
        f"# Verdict: `{v.run_dir.name}`",
        f"**Gate: {'PASS' if v.passed else 'FAIL'}** "
        f"({sum(c.passed for c in v.checks)}/{len(v.checks)} checks). "
        "Full report: `report.md` in this folder.",
        "## Scores\n\n" + md_table(["Metric", "Value"], rows),
    ]
    if v.comparison is not None and baseline is not None:
        data = json.loads((v.comparison.parent / "compare.json").read_text())
        comp = [
            [
                m["metric"],
                _pct(m["a"]),
                _pct(m["b"]),
                "–" if m["diff"] is None else f"{100 * m['diff']:+.1f} pts",
                "–" if m["sign_flip_p"] is None else f"{m['sign_flip_p']:.3f}",
                m["verdict"]
                .replace("B better", "this model better")
                .replace("A better", "baseline better"),
            ]
            for m in data["metrics"]
        ]
        n = data["scenes"]
        if n < MIN_SCENES:
            parts.insert(
                1,
                f"> **Smoke test only: {n} scene{'s' if n != 1 else ''}.** Too few for a "
                "verdict; differences and the specificity checks need the full set of scenes.",
            )
        parts.append(
            f"## Against the baseline (`{baseline.name}`, same frames, "
            f"{n} scene{'s' if n != 1 else ''})\n\n"
            + md_table(["Metric", "Baseline", "This model", "Difference", "p", "Verdict"], comp)
            + "\n\nA difference counts only when the 95% CI excludes 0 and p < 0.05. "
            f"Details: `{BASELINE_DIR}/compare_report.md`."
        )
    else:
        parts.append("## Against the baseline\n\nNo scored baseline run found; skipped.")
    gate_rows = [
        [
            c.key,
            "–" if c.value is None else f"{c.value:.3f}",
            c.rule,
            "PASS" if c.passed else "FAIL",
        ]
        for c in v.checks
    ]
    parts.append("## Release gate\n\n" + md_table(["Check", "Value", "Rule", "Result"], gate_rows))
    return "\n\n".join(parts) + "\n"
