"""CI smoke test of the quality gate without the dataset or a model.

Builds two tiny runs with mock VLMs on synthetic frames (oracle vs. always-"car"),
then checks that the gate passes the oracle and blocks the regression.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.conftest import TAX, FakeGTProvider, FakeLoader  # noqa: E402
from vlm_eval.evaluation import Evaluator  # noqa: E402
from vlm_eval.pipeline import Pipeline  # noqa: E402
from vlm_eval.prompting import load_strategy  # noqa: E402
from vlm_eval.vlm import MockBackend  # noqa: E402
from vlm_eval.writers import JsonlWriter  # noqa: E402


def make_run(tmp: Path, mode: str) -> Path:
    loader, gt = FakeLoader(tmp), FakeGTProvider()
    truth = {s.sample_token: gt.get(s) for s in loader} if mode == "oracle" else None
    evaluator = Evaluator.from_config([], TAX)
    evaluator.metrics = [m for m in evaluator.metrics if m.name != "similarity"]
    pipeline = Pipeline(loader, gt, MockBackend(mode, ground_truth=truth),
                        load_strategy("v2_structured", TAX), [JsonlWriter()], evaluator)
    pipeline.run(tmp / mode)
    return tmp / mode


def gate(run: Path, baseline: Path | None = None) -> int:
    cmd = ["vlm-eval", "gate", str(run), "--gates", str(ROOT / "configs/gates.yaml")]
    if baseline:
        cmd += ["--baseline", str(baseline)]
    return subprocess.run(cmd, check=False).returncode


with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    good, bad = make_run(tmp, "oracle"), make_run(tmp, "always_car")
    assert gate(good) == 0, "oracle run should pass the gate"
    assert gate(bad, baseline=good) == 1, "regressed run should be blocked"
    print("gate demo OK: oracle passes, regression is blocked")
