"""DuckDB results store: ingestion is idempotent and frame/scene runs never collide."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.conftest import FakeLoader
from tests.test_pipeline import build
from tests.test_scene import run_fake
from vlm_eval.store import example_queries, ingest, query
from vlm_eval.vlm import MockBackend

pytest.importorskip("duckdb")


def make_runs(tmp_path: Path) -> list[Path]:
    scene_run = run_fake(tmp_path, MockBackend("fixed", fixed_response="There are cars."), "same")
    frame_dir = tmp_path / "frames" / "same"  # same run name at frame level
    build(FakeLoader(tmp_path), "always_car").run(frame_dir)
    return [scene_run, frame_dir]


def test_ingest_is_idempotent_and_ids_are_unique(tmp_path: Path) -> None:
    db = tmp_path / "results.duckdb"
    runs = make_runs(tmp_path)
    first = ingest(runs, db)
    second = ingest(runs, db)  # re-ingesting must not duplicate anything
    assert first == second
    assert first["runs"] == 2  # "same" at scene and frame level are two different runs
    _, rows = query(db, "SELECT run_id, level FROM runs ORDER BY run_id")
    assert rows == [("frame:same", "frame"), ("scene:same", "scene")]
    _, n = query(db, "SELECT count(*) FROM scenes WHERE run_id = 'scene:same'")
    assert n == [(2,)]  # one entry per scene


def test_example_queries_run(tmp_path: Path) -> None:
    db = tmp_path / "results.duckdb"
    ingest(make_runs(tmp_path), db)
    examples = example_queries()
    assert {"leaderboard", "missed_by_every_model", "invented_objects"} <= set(examples)
    for sql in examples.values():
        columns, _ = query(db, sql)
        assert columns
