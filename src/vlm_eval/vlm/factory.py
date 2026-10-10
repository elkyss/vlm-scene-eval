"""The one place that turns a ``vlm`` config entry into a backend (frame and scene runs)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from vlm_eval.config import ComponentConfig
from vlm_eval.vlm.base import BACKENDS, VLMBackend
from vlm_eval.vlm.cache import CachedBackend
from vlm_eval.vlm.mock import MockBackend

ORACLE = "oracle"


def build_backend(
    cfg: ComponentConfig,
    cache_dir: Path | None,
    oracle_answers: Callable[[], Mapping[str, str]] | None = None,
) -> VLMBackend:
    """``oracle`` = an upper-bound mock that answers from the ground truth (the caller says how
    to render it); real models are wrapped in the response cache, mocks are not (they are free,
    and caching them would hide changes to a mock)."""
    if cfg.name == ORACLE:
        if oracle_answers is None:
            raise ValueError("the oracle backend needs ground-truth answers")
        return MockBackend(mode="table", responses=oracle_answers(), label=ORACLE)
    backend: VLMBackend = BACKENDS.build(cfg.name, **cfg.params)
    if cache_dir is not None and cfg.name != "mock":
        backend = CachedBackend(backend, cache_dir)
    return backend
