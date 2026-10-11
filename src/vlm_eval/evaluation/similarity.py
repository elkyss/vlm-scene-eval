"""Text-embedding similarity (secondary metric), shared by frame and scene evaluation."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from functools import lru_cache
from typing import Any

import numpy as np

log = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def _model(model_id: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_id)


def similarity_matrix(
    texts: Sequence[str], references: Sequence[str], model_id: str | None
) -> np.ndarray | None:
    """Cosine similarity of every text to every reference, or None if unavailable."""
    if not model_id or not texts:
        return None
    try:
        model = _model(model_id)
    except ImportError:
        log.warning("sentence-transformers not installed: embedding similarity skipped")
        return None
    a = model.encode([t or " " for t in texts], normalize_embeddings=True, show_progress_bar=False)
    b = model.encode(list(references), normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(a @ b.T)
