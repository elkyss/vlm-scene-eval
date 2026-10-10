"""Scene-level loader: each scene becomes a few label-blind "views" (frame subsets).

Protocol (same for every scene and model, never tuned on results):
the scene's keyframes are split into ``n_segments`` equal segments; view ``v`` takes the
frame at relative position ``(v + 0.5) / n_views`` inside every segment. Views are therefore
distinct, non-overlapping, spread over the whole clip and in time order.
"""

from __future__ import annotations

import math
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from vlm_eval.domain import SceneSample, SceneView
from vlm_eval.loaders.base import SCENE_LOADERS
from vlm_eval.nuscenes_db import get_nuscenes, scene_sample_tokens


def view_frame_indices(n_frames: int, n_segments: int, n_views: int) -> list[list[int]]:
    """Frame indices of each view; raises if the scene is too short for distinct views."""
    if n_frames < n_segments * n_views:
        raise ValueError(f"{n_frames} frames cannot give {n_views} distinct views of {n_segments}")
    seg = n_frames / n_segments
    views = []
    for v in range(n_views):
        offset = (v + 0.5) / n_views
        views.append([min(n_frames - 1, math.floor((s + offset) * seg)) for s in range(n_segments)])
    return views


@SCENE_LOADERS.register("nuscenes")
class NuScenesSceneLoader:
    def __init__(
        self,
        dataroot: str,
        version: str = "v1.0-mini",
        camera: str = "CAM_FRONT",
        frames_per_view: int = 6,
        n_views: int = 3,
        scenes: Sequence[str] | None = None,
        nusc: Any | None = None,
    ) -> None:
        self.camera = camera
        self.frames_per_view = frames_per_view
        self.n_views = n_views
        self.scenes = set(scenes) if scenes else None
        self._nusc = nusc or get_nuscenes(dataroot, version)

    def __iter__(self) -> Iterator[SceneSample]:
        nusc = self._nusc
        for scene in sorted(nusc.scene, key=lambda s: s["name"]):
            if self.scenes and scene["name"] not in self.scenes:
                continue
            tokens = scene_sample_tokens(nusc, scene)
            views = []
            for v, indices in enumerate(
                view_frame_indices(len(tokens), self.frames_per_view, self.n_views)
            ):
                samples = [nusc.get("sample", tokens[i]) for i in indices]
                views.append(
                    SceneView(
                        view_id=v,
                        frame_indices=indices,
                        sample_tokens=[s["token"] for s in samples],
                        image_paths=[
                            Path(nusc.get_sample_data_path(s["data"][self.camera])) for s in samples
                        ],
                    )
                )
            yield SceneSample(
                scene_token=scene["token"],
                scene_name=scene["name"],
                n_keyframes=len(tokens),
                views=views,
            )
