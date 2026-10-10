"""DuckDB results store: every run folder, queryable with SQL across runs.

The run folders (``scenes.jsonl``, ``scene_metrics.json``, ``predictions.jsonl``,
``manifest.json`` ...) remain the source of truth; this store is derived from them and can
be rebuilt at any time. Ingestion is idempotent: a run is replaced as a unit (its rows are
deleted and re-inserted in one transaction), so ingesting the same run twice never
duplicates anything, and a re-scored run simply overwrites its old rows.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR PRIMARY KEY, level VARCHAR, model VARCHAR, prompt_version VARCHAR,
    judge VARCHAR, git_commit VARCHAR, config_sha256 VARCHAR, model_revision VARCHAR,
    created_utc VARCHAR, run_dir VARCHAR
);
CREATE TABLE IF NOT EXISTS run_metrics (
    run_id VARCHAR, metric VARCHAR, key VARCHAR, value DOUBLE
);
CREATE TABLE IF NOT EXISTS scenes (
    run_id VARCHAR, scene_name VARCHAR, description VARCHAR, chosen_view INTEGER,
    view_agreement DOUBLE, consensus_objects VARCHAR[], reference_text VARCHAR
);
CREATE TABLE IF NOT EXISTS views (
    run_id VARCHAR, scene_name VARCHAR, view_id INTEGER, frame_indices INTEGER[],
    description VARCHAR, mentioned_objects VARCHAR[], latency_s DOUBLE
);
CREATE TABLE IF NOT EXISTS scene_metrics (
    run_id VARCHAR, scene_name VARCHAR, view_id INTEGER, is_final BOOLEAN,
    chair_i DOUBLE, object_coverage DOUBLE, claims_supported DOUBLE,
    claims_contradicted DOUBLE, claims_unverifiable DOUBLE, human_coverage DOUBLE,
    hallucinated VARCHAR[], missed VARCHAR[]
);
CREATE TABLE IF NOT EXISTS claims (
    run_id VARCHAR, scene_name VARCHAR, view_id INTEGER, is_final BOOLEAN, claim VARCHAR,
    label VARCHAR, evidence VARCHAR, evidence_source VARCHAR, object_class VARCHAR,
    box_present BOOLEAN
);
CREATE TABLE IF NOT EXISTS frame_predictions (
    run_id VARCHAR, sample_token VARCHAR, scene_name VARCHAR, description VARCHAR,
    facts_source VARCHAR, parse_ok BOOLEAN, latency_s DOUBLE, objects JSON
);
"""
RUN_TABLES = ("run_metrics", "scenes", "views", "scene_metrics", "claims", "frame_predictions")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def connect(db_path: Path) -> Any:
    import duckdb

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(SCHEMA)
    return con


def run_id_for(run_dir: Path, level: str) -> str:
    """Unique id: the same run name can exist at frame and at scene level."""
    return f"{level}:{run_dir.name}"


def _run_row(run_dir: Path, level: str, model: str, prompt: str, judge: str | None) -> tuple:
    manifest_path = run_dir / "manifest.json"
    m = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    return (
        run_id_for(run_dir, level),
        level,
        model,
        prompt,
        judge,
        m.get("git_commit"),
        m.get("config_sha256"),
        m.get("model_revision"),
        m.get("created_utc"),
        str(run_dir),
    )


def _scene_rows(run_dir: Path) -> dict[str, list[tuple]]:
    from vlm_eval.evaluation.scene_metrics import SceneEvaluation

    evaluation = SceneEvaluation.model_validate_json((run_dir / "scene_metrics.json").read_text())
    scenes = {d["scene_name"]: d for d in _read_jsonl(run_dir / "scenes.jsonl")}
    run_id = run_id_for(run_dir, "scene")
    rows: dict[str, list[tuple]] = {t: [] for t in RUN_TABLES}
    rows["runs"] = [
        _run_row(run_dir, "scene", evaluation.model, evaluation.prompt_version, evaluation.judge)
    ]
    rows["run_metrics"] = [
        (run_id, "scene", k, v) for k, v in evaluation.summary.items() if v is not None
    ]
    for row in evaluation.rows:
        d = scenes.get(row.scene_name, {})
        rows["scenes"].append(
            (
                run_id,
                row.scene_name,
                row.description,
                row.chosen_view,
                row.view_agreement,
                d.get("consensus_objects", []),
                row.reference_text,
            )
        )
        for v in d.get("views", []):
            rows["views"].append(
                (
                    run_id,
                    row.scene_name,
                    v["view_id"],
                    v["frame_indices"],
                    v["description"],
                    v["mentioned_objects"],
                    v["latency_s"],
                )
            )
        view_ids = [v["view_id"] for v in d.get("views", [])] or list(range(len(row.per_view)))
        for view_id, score in zip(view_ids, row.per_view, strict=False):
            final = view_id == row.chosen_view
            r = score.rates()
            rows["scene_metrics"].append(
                (
                    run_id,
                    row.scene_name,
                    view_id,
                    final,
                    r["chair_i"],
                    r["object_coverage"],
                    r["claims_supported"],
                    r["claims_contradicted"],
                    r["claims_unverifiable"],
                    r["human_coverage"],
                    score.hallucinated,
                    [c for c in score.labelled if c not in score.covered],
                )
            )
            for c in score.claims:
                rows["claims"].append(
                    (
                        run_id,
                        row.scene_name,
                        view_id,
                        final,
                        c.text,
                        c.label,
                        c.evidence,
                        c.evidence_source,
                        c.object_class,
                        c.box_present,
                    )
                )
    return rows


def _frame_rows(run_dir: Path) -> dict[str, list[tuple]]:
    predictions = _read_jsonl(run_dir / "predictions.jsonl")
    metrics = json.loads((run_dir / "metrics.json").read_text())
    run_id = run_id_for(run_dir, "frame")
    first = predictions[0] if predictions else {}
    rows: dict[str, list[tuple]] = {t: [] for t in RUN_TABLES}
    rows["runs"] = [
        _run_row(run_dir, "frame", first.get("model", "?"), first.get("prompt_version", "?"), None)
    ]
    rows["run_metrics"] = [
        (run_id, name, k, v)
        for name, m in metrics.items()
        for k, v in m["summary"].items()
        if v is not None
    ]
    rows["frame_predictions"] = [
        (
            run_id,
            p["sample_token"],
            p["scene_name"],
            p["description"],
            p["facts_source"],
            p["parse_ok"],
            p["latency_s"],
            json.dumps(p["facts"]["objects"]),
        )
        for p in predictions
    ]
    return rows


def ingest(run_dirs: Sequence[Path], db_path: Path) -> dict[str, int]:
    """Load (or reload) run folders into the store. Returns rows per table after ingestion."""
    con = connect(db_path)
    for run_dir in run_dirs:
        if (run_dir / "scene_metrics.json").exists():
            rows, run_id = _scene_rows(run_dir), run_id_for(run_dir, "scene")
        elif (run_dir / "metrics.json").exists():
            rows, run_id = _frame_rows(run_dir), run_id_for(run_dir, "frame")
        else:
            continue
        con.execute("BEGIN TRANSACTION")
        try:
            for table in (*RUN_TABLES, "runs"):
                con.execute(f"DELETE FROM {table} WHERE run_id = ?", [run_id])
            for table, table_rows in rows.items():
                if table_rows:
                    marks = ", ".join("?" * len(table_rows[0]))
                    con.executemany(f"INSERT INTO {table} VALUES ({marks})", table_rows)
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise
    counts = {
        t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in ("runs", *RUN_TABLES)
    }
    con.close()
    return counts


def query(db_path: Path, sql: str) -> tuple[list[str], list[tuple]]:
    con = connect(db_path)
    try:
        result = con.execute(sql)
        columns = [d[0] for d in result.description]
        return columns, result.fetchall()
    finally:
        con.close()


EXAMPLES = Path(__file__).parent / "sql" / "examples.sql"


def example_queries() -> dict[str, str]:
    """Named queries from sql/examples.sql (blocks starting with ``-- name: <name>``)."""
    queries: dict[str, list[str]] = {}
    current: str | None = None
    for line in EXAMPLES.read_text().splitlines():
        if line.startswith("-- name:"):
            current = line.split(":", 1)[1].strip()
            queries[current] = []
        elif current is not None and not line.startswith("--"):
            queries[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in queries.items()}
