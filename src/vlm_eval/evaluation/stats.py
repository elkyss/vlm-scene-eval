"""Small, dependency-free statistics helpers."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable, Sequence
from typing import TypeVar

import numpy as np

T = TypeVar("T")


def safe_div(num: float, den: float) -> float | None:
    return None if den == 0 else num / den


def prf(tp: int, fp: int, fn: int) -> dict[str, float | None]:
    # F1 = 2TP / (2TP + FP + FN): a class that is present but never predicted gets F1 = 0
    # (precision alone would be undefined and the class would silently drop out of macro F1).
    return {
        "precision": safe_div(tp, tp + fp),
        "recall": safe_div(tp, tp + fn),
        "f1": safe_div(2 * tp, 2 * tp + fp + fn),
    }


def mean_or_none(values: Sequence[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return float(np.mean(vals)) if vals else None


def balanced_accuracy(y_true: Sequence[str], y_pred: Sequence[str | None]) -> float | None:
    """Mean per-class recall; robust to the heavy class imbalance (e.g. mostly 'day')."""
    recalls = []
    for label in sorted(set(y_true)):
        idx = [i for i, t in enumerate(y_true) if t == label]
        recalls.append(sum(y_pred[i] == label for i in idx) / len(idx))
    return float(np.mean(recalls)) if recalls else None


def confusion(y_true: Sequence[str], y_pred: Sequence[str | None]) -> dict[str, dict[str, int]]:
    table: dict[str, Counter[str]] = {}
    for t, p in zip(y_true, y_pred, strict=True):
        table.setdefault(t, Counter())[p or "unanswered"] += 1
    return {t: dict(c) for t, c in sorted(table.items())}


def pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def average_ranks(values: Sequence[float]) -> list[float]:
    """Ranks with ties sharing their average rank (as in scipy.stats.rankdata)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    """Rank correlation; None when either input is constant (correlation undefined)."""
    return pearson(average_ranks(x), average_ranks(y)) if len(x) >= 3 else None


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts b (A right, B wrong), c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * p)


def cluster_bootstrap_ci(
    clusters: Sequence[Sequence[T]],
    statistic: Callable[[list[T]], float | None],
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float | None, float | None]:
    """Percentile CI, resampling whole clusters (scenes): frames of a scene are correlated."""
    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(n_boot):
        picks = rng.integers(0, len(clusters), len(clusters))
        items = [item for i in picks for item in clusters[i]]
        value = statistic(items)
        if value is not None:
            stats.append(value)
    if not stats:
        return None, None
    return float(np.quantile(stats, alpha / 2)), float(np.quantile(stats, 1 - alpha / 2))
