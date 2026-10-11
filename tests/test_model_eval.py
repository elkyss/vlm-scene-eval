"""Tests for evaluate-model: config from a Hugging Face id, and the verdict."""

from __future__ import annotations

from pathlib import Path

from tests.test_scene import run_fake
from vlm_eval.model_eval import BASELINE_DIR, VERDICT, model_config, model_verdict, run_id_for_model
from vlm_eval.vlm import MockBackend

ROOT = Path(__file__).resolve().parents[1]


def test_run_id_from_model_and_prompt() -> None:
    assert run_id_for_model("Qwen/Qwen2.5-VL-3B-Instruct", "scene_guided") == (
        "qwen2.5-vl-3b-instruct_guided"
    )
    assert run_id_for_model("HuggingFaceTB/SmolVLM2-2.2B-Instruct", "scene_open") == (
        "smolvlm2-2.2b-instruct_open"
    )


def test_model_config_keeps_the_protocol_and_swaps_the_model() -> None:
    template = ROOT / "configs" / "scenes" / "qwen2vl_guided.yaml"
    cfg = model_config("org/new-vlm", "scene_open", template=template)
    base = model_config("Qwen/Qwen2-VL-2B-Instruct", "scene_guided", template=template)
    assert cfg.vlm.name == "hf" and cfg.vlm.params["model_id"] == "org/new-vlm"
    assert cfg.prompt == "scene_open" and cfg.run_id == "new-vlm_open"
    # same frames, ground truth and judge as the baseline: only the model and prompt differ
    assert cfg.loader == base.loader and cfg.ground_truth == base.ground_truth
    assert cfg.judge == base.judge


def test_verdict_compares_with_baseline_and_applies_gate(tmp_path: Path) -> None:
    base = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "base")
    new = run_fake(tmp_path, MockBackend("fixed", fixed_response="A bus and a truck."), "new")
    verdict = model_verdict(new, base, ROOT / "configs" / "gates.yaml")
    assert verdict.comparison is not None and (new / BASELINE_DIR / "compare.json").exists()
    assert verdict.checks and any("vs" in c.rule for c in verdict.checks)  # regression checks
    text = (new / VERDICT).read_text()
    assert "Against the baseline (`base`" in text and "Release gate" in text
    assert ("PASS" in text) or ("FAIL" in text)
    assert "Smoke test only: 2 scenes" in text  # fake runs have 2 scenes


def test_verdict_without_baseline(tmp_path: Path) -> None:
    run = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "solo")
    verdict = model_verdict(run, tmp_path / "missing", ROOT / "configs" / "gates.yaml")
    assert verdict.comparison is None
    assert "No scored baseline run found" in (run / VERDICT).read_text()
