"""End-to-end tests with in-memory components and mock VLMs (no dataset, no model)."""

from pathlib import Path

import pytest

from tests.conftest import TAX, FakeGTProvider, FakeLoader
from vlm_eval.config import load_config
from vlm_eval.evaluation import Evaluator
from vlm_eval.evaluation.compare import compare_runs
from vlm_eval.evaluation.report import MarkdownReport
from vlm_eval.pipeline import Pipeline
from vlm_eval.prompting import load_strategy
from vlm_eval.registry import Registry
from vlm_eval.run_store import RunArtifacts
from vlm_eval.vlm import CachedBackend, MockBackend, VLMBackend, facts_to_response
from vlm_eval.writers import CsvWriter, JsonlWriter

FAST_METRICS = [
    "object_presence",
    "counting",
    "attributes",
    "text_faithfulness",
    "consistency",
    "format",
    "errors",
]


def build(loader: FakeLoader, mode: str, backend: VLMBackend | None = None) -> Pipeline:
    gt_provider = FakeGTProvider()
    if mode == "oracle":  # same oracle as the real factory: answers rendered from the GT
        oracle = MockBackend(
            "table",
            responses={s.sample_token: facts_to_response(gt_provider.get(s)) for s in loader},
            label="oracle",
        )
    evaluator = Evaluator.from_config([], TAX)
    evaluator.metrics = [m for m in evaluator.metrics if m.name in FAST_METRICS]
    return Pipeline(
        loader=loader,
        gt_provider=gt_provider,
        backend=backend or (oracle if mode == "oracle" else MockBackend(mode)),
        strategy=load_strategy("v2_structured", TAX),
        writers=[JsonlWriter(), CsvWriter(TAX)],
        evaluator=evaluator,
        report=MarkdownReport(),
    )


def summary(results, metric: str) -> dict:  # type: ignore[no-untyped-def]
    return next(r for r in results if r.name == metric).summary


def test_oracle_scores_perfectly(fake_loader: FakeLoader, tmp_path: Path) -> None:
    run, results = build(fake_loader, "oracle").run(tmp_path / "oracle")
    assert summary(results, "object_presence")["micro_f1"] == 1.0
    assert summary(results, "attributes")["mean_balanced_accuracy"] == 1.0
    assert summary(results, "text_faithfulness")["micro_f1"] == 1.0
    assert summary(results, "format")["parse_success_rate"] == 1.0
    for name in [
        "predictions.jsonl",
        "predictions.csv",
        "ground_truth.jsonl",
        "samples.jsonl",
        "metrics.json",
        "report.md",
    ]:
        assert (run.run_dir / name).exists(), name
    assert len(run.predictions) == 6


def test_empty_model_gets_zero_recall(fake_loader: FakeLoader, tmp_path: Path) -> None:
    _, results = build(fake_loader, "empty").run(tmp_path / "empty")
    assert summary(results, "object_presence")["micro_recall"] == 0.0
    assert summary(results, "format")["parse_success_rate"] == 0.0


def test_always_car_model_is_caught(fake_loader: FakeLoader, tmp_path: Path) -> None:
    _, results = build(fake_loader, "always_car").run(tmp_path / "car")
    obj = next(r for r in results if r.name == "object_presence")
    assert obj.tables["per_class"]["car"]["recall"] == 1.0
    assert obj.tables["per_class"]["pedestrian"]["precision"] == 0.0  # never there
    assert obj.tables["per_class"]["bus"]["recall"] == 0.0  # never mentioned
    attrs = next(r for r in results if r.name == "attributes")
    assert attrs.tables["time_of_day"]["balanced_accuracy"] == 0.5


def test_saved_run_reloads_and_compares(fake_loader: FakeLoader, tmp_path: Path) -> None:
    build(fake_loader, "oracle").run(tmp_path / "a")
    build(fake_loader, "always_car").run(tmp_path / "b")
    reloaded = RunArtifacts.load(tmp_path / "a")
    assert len(reloaded.predictions) == 6
    report = compare_runs(tmp_path / "a", tmp_path / "b", tmp_path / "cmp", TAX)
    text = report.read_text()
    assert "Object micro F1" in text
    assert "sign-flip" in text


class ExplodingBackend(MockBackend):
    """Same name as the cached backend, but fails if it is ever actually called."""

    def generate(self, request):  # type: ignore[no-untyped-def]
        raise AssertionError("inference should have been served from the cache")


def test_cache_avoids_second_inference(fake_loader: FakeLoader, tmp_path: Path) -> None:
    pipeline = build(fake_loader, "always_car", CachedBackend(MockBackend(), tmp_path / "cache"))
    first, _ = pipeline.run(tmp_path / "r1")
    pipeline.backend = CachedBackend(ExplodingBackend("always_car"), tmp_path / "cache")
    second, _ = pipeline.run(tmp_path / "r2")
    assert [p.raw_output for p in first.predictions] == [p.raw_output for p in second.predictions]
    assert len(list((tmp_path / "cache").rglob("*.json"))) == 6


def test_registry_rejects_unknown_and_duplicates() -> None:
    reg: Registry[object] = Registry("thing")
    reg.register("a")(object)
    with pytest.raises(ValueError):
        reg.register("a")(object)
    with pytest.raises(KeyError, match="Available"):
        reg.build("b")


def test_config_overrides(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    cfg = load_config(
        root / "configs" / "smolvlm_v2.yaml",
        {"loader.params.scenes": ["scene-0061"], "run_id": "x"},
    )
    assert cfg.loader.params["scenes"] == ["scene-0061"]
    assert cfg.run_dir == Path("outputs/x")


def test_leaderboard_lists_runs(fake_loader: FakeLoader, tmp_path: Path) -> None:
    from vlm_eval.evaluation.leaderboard import leaderboard

    build(fake_loader, "oracle").run(tmp_path / "a")
    build(fake_loader, "always_car").run(tmp_path / "b")
    table = leaderboard([tmp_path / "a", tmp_path / "b", tmp_path / "missing"])
    assert "mock-oracle" in table and "mock-always_car" in table
    assert table.count("\n") == 3  # header, separator, 2 rows


def test_cache_key_depends_on_frames_prompt_and_settings(tmp_path: Path) -> None:
    from vlm_eval.vlm import ImageSet, VLMRequest

    cached = CachedBackend(MockBackend("always_car"), tmp_path)
    a = VLMRequest("tok", ImageSet.from_paths(["f1", "f2"], ["a.jpg", "b.jpg"]), "p")
    b = VLMRequest("tok", ImageSet.from_paths(["f1", "f3"], ["a.jpg", "c.jpg"]), "p")
    c = VLMRequest("tok", ImageSet.from_paths(["f1", "f2"], ["a.jpg", "b.jpg"]), "q")
    assert len({cached.path_for(a), cached.path_for(b), cached.path_for(c)}) == 3
    other = CachedBackend(MockBackend("fixed", fixed_response="x"), tmp_path)
    assert other.path_for(a) != cached.path_for(a)  # backend settings are part of the key


def test_images_are_not_decoded_on_cache_hit(tmp_path: Path) -> None:
    from vlm_eval.vlm import ImageSet, VLMRequest

    cached = CachedBackend(MockBackend("always_car"), tmp_path)
    request = VLMRequest("tok", ImageSet.from_paths(["f1"], [tmp_path / "missing.jpg"]), "p")
    cached.generate(request)  # mock never opens images
    assert cached.generate(request).text  # served from disk; the missing file is never read


def test_manifest_records_config_and_versions(tmp_path: Path) -> None:
    import json

    from vlm_eval.manifest import write_manifest

    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / "configs" / "mock_oracle.yaml")
    data = json.loads(write_manifest(tmp_path, cfg, {"model_revision": "abc"}).read_text())
    assert data["config"]["run_id"] == "mock_oracle"
    assert data["model_revision"] == "abc"
    assert len(data["config_sha256"]) == 16
    assert "transformers" in data["packages"]


def test_compare_never_deletes_existing_files(fake_loader: FakeLoader, tmp_path: Path) -> None:
    build(fake_loader, "oracle").run(tmp_path / "a")
    build(fake_loader, "always_car").run(tmp_path / "b")
    out = tmp_path / "shared"
    out.mkdir()
    (out / "keep.txt").write_text("not ours")
    compare_runs(tmp_path / "a", tmp_path / "b", out, TAX)
    assert (out / "keep.txt").exists()  # only compare.json / compare_report.md are written
