"""Typed run configuration loaded from YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ComponentConfig(BaseModel):
    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class BaseRunConfig(BaseModel):
    """Fields every run has, frame level or scene level."""

    run_id: str
    loader: ComponentConfig  # which frames/scenes and cameras (registry name + params)
    ground_truth: ComponentConfig  # how the reference is built (registry name + params)
    vlm: ComponentConfig
    taxonomy: str = "driving"  # name in taxonomies/ or a path to a YAML file
    prompt: str
    output_dir: Path
    cache_dir: Path | None = Path(".cache/vlm")
    seed: int = 0

    @property
    def run_dir(self) -> Path:
        return self.output_dir / self.run_id


class RunConfig(BaseRunConfig):
    """Frame-level run (diagnostic): every selected frame described on its own."""

    prompt: str = "v2_structured"
    output_dir: Path = Path("outputs")
    writers: list[str] = Field(default_factory=lambda: ["jsonl", "csv"])
    metrics: list[ComponentConfig] = Field(default_factory=list)


class SceneRunConfig(BaseRunConfig):
    """Scene-level run: N frames per view, K views per scene, one description per scene."""

    prompt: str = "scene_open"
    output_dir: Path = Path("outputs/scenes")
    judge: ComponentConfig = Field(default_factory=lambda: ComponentConfig(name="nli"))
    embedding_model: str | None = "sentence-transformers/all-MiniLM-L6-v2"


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
