"""Typed run configuration loaded from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ComponentConfig(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class RunConfig(BaseModel):
    run_id: str
    loader: ComponentConfig
    ground_truth: ComponentConfig
    vlm: ComponentConfig
    taxonomy: str = "driving"  # name in taxonomies/ or a path to a YAML file
    prompt: str = "v2_structured"
    writers: list[str] = Field(default_factory=lambda: ["jsonl", "csv"])
    metrics: list[ComponentConfig] = Field(default_factory=list)
    output_dir: Path = Path("outputs")
    cache_dir: Path | None = Path(".cache/vlm")
    seed: int = 0

    @property
    def run_dir(self) -> Path:
        return self.output_dir / self.run_id


class SceneRunConfig(BaseModel):
    """Scene-level run: N frames per view, K views per scene, one description per scene."""

    run_id: str
    dataroot: str = "data/nuscenes"
    version: str = "v1.0-mini"
    camera: str = "CAM_FRONT"
    frames_per_view: int = 6
    n_views: int = 3
    scenes: list[str] | None = None
    min_visibility: int = 2  # nuScenes level 2 = 40-60% visible
    max_distance_m: float = 50.0
    taxonomy: str = "driving"
    vlm: ComponentConfig
    prompt: str = "scene_open"
    judge: ComponentConfig = Field(default_factory=lambda: ComponentConfig(name="nli"))
    embedding_model: str | None = "sentence-transformers/all-MiniLM-L6-v2"
    output_dir: Path = Path("outputs/scenes")
    cache_dir: Path | None = Path(".cache/vlm")
    seed: int = 0

    @property
    def run_dir(self) -> Path:
        return self.output_dir / self.run_id


def _load_raw(path: str | Path, overrides: dict[str, Any] | None) -> dict[str, Any]:
    with open(path) as fh:
        raw: dict[str, Any] = yaml.safe_load(fh)
    for dotted, value in (overrides or {}).items():
        _set_dotted(raw, dotted, value)
    return raw


def load_config(path: str | Path, overrides: dict[str, Any] | None = None) -> RunConfig:
    return RunConfig.model_validate(_load_raw(path, overrides))


def load_scene_config(path: str | Path, overrides: dict[str, Any] | None = None) -> SceneRunConfig:
    return SceneRunConfig.model_validate(_load_raw(path, overrides))


def _set_dotted(tree: dict[str, Any], dotted: str, value: Any) -> None:
    keys = dotted.split(".")
    node = tree
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value
