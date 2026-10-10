"""Shared, lazily-loaded nuScenes handle (loading the tables takes a few seconds)."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nuscenes.nuscenes import NuScenes

log = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def get_nuscenes(dataroot: str, version: str = "v1.0-mini") -> NuScenes:
    from nuscenes.nuscenes import NuScenes

    log.info("Loading nuScenes %s from %s", version, dataroot)
    return NuScenes(version=version, dataroot=dataroot, verbose=False)


def scene_sample_tokens(nusc: NuScenes, scene: dict[str, Any]) -> list[str]:
    """All keyframe (sample) tokens of a scene, in time order."""
    tokens = []
    token = scene["first_sample_token"]
    while token:
        tokens.append(token)
        token = nusc.get("sample", token)["next"]
    return tokens
