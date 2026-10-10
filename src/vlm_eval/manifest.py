"""Run manifest: everything needed to know exactly how a run was produced."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

from pydantic import BaseModel

PACKAGES = (
    "vlm-eval",
    "torch",
    "transformers",
    "sentence-transformers",
    "nuscenes-devkit",
    "numpy",
    "pydantic",
)


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def _version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def write_manifest(run_dir: Path, config: BaseModel, extra: dict[str, Any] | None = None) -> Path:
    config_json = config.model_dump_json()
    manifest = {
        "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--untracked-files=no")),
        "config_sha256": hashlib.sha256(config_json.encode()).hexdigest()[:16],
        "config": json.loads(config_json),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {p: _version(p) for p in PACKAGES},
        **(extra or {}),
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str))
    return path
