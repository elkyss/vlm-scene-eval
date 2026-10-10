from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from vlm_eval.domain import Sample
from vlm_eval.loaders.base import LOADERS
from vlm_eval.nuscenes_db import get_nuscenes, scene_sample_tokens


def evenly_spaced(n_items: int, k: int | None) -> list[int]:
    """Indices of ``k`` evenly spaced items out of ``n_items`` (all items when k is None)."""
    if k is None or k >= n_items:
        return list(range(n_items))
    if k <= 0:
        return []
    return sorted({int(i) for i in np.linspace(0, n_items - 1, k).round()})


@LOADERS.register("nuscenes")
class NuScenesLoader:
    """Selects keyframes from nuScenes scenes.

    Args:
        dataroot: folder containing ``v1.0-mini/``, ``samples/`` ...
        cameras: camera channels to attach to each sample (first one is the primary view).
        frames_per_scene: number of evenly spaced keyframes per scene, or ``None`` for all.
        scenes: optional list of scene names to restrict to.
    """

    def __init__(
        self,
        dataroot: str,
        version: str = "v1.0-mini",
        cameras: Sequence[str] = ("CAM_FRONT",),
        frames_per_scene: int | None = 5,
        scenes: Sequence[str] | None = None,
        nusc: Any | None = None,
    ) -> None:
        self.dataroot = dataroot
        self.cameras = list(cameras)
        self.frames_per_scene = frames_per_scene
        self.scenes = set(scenes) if scenes else None
        self._nusc = nusc or get_nuscenes(dataroot, version)

    def __iter__(self) -> Iterator[Sample]:
        nusc = self._nusc
        for scene in sorted(nusc.scene, key=lambda s: s["name"]):
            if self.scenes and scene["name"] not in self.scenes:
                continue
            tokens = scene_sample_tokens(nusc, scene)
            for idx in evenly_spaced(len(tokens), self.frames_per_scene):
                sample = nusc.get("sample", tokens[idx])
                yield Sample(
                    sample_token=sample["token"],
                    scene_token=scene["token"],
                    scene_name=scene["name"],
                    frame_index=idx,
                    timestamp=sample["timestamp"],
                    image_paths={
                        cam: Path(nusc.get_sample_data_path(sample["data"][cam]))
                        for cam in self.cameras
                    },
                )
