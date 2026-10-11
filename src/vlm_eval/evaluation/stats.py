"""Small, dependency-free statistics helpers."""

from __future__ import annotations

import itertools
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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


def sign_flip_p(diffs: Sequence[float], n_mc: int = 20000, seed: int = 0) -> float | None:
    """Two-sided paired permutation (sign-flip) test on per-cluster differences.

    Under "no difference between A and B" each scene's difference is equally likely to have
    either sign. Testing at the scene level respects that frames/items of one scene are
    correlated (an item-level McNemar test would treat them as independent and overstate
    confidence). Exact for <= 16 clusters, Monte Carlo above.
    """
    d = np.asarray([x for x in diffs if x is not None], dtype=float)
    if len(d) == 0:
        return None
    observed = abs(d.mean())
    if len(d) <= 16:
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=len(d))))
    else:
        signs = np.random.default_rng(seed).choice((1.0, -1.0), size=(n_mc, len(d)))
    means = np.abs((signs * d).mean(axis=1))
    return float((means >= observed - 1e-12).mean())


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


ALPHA = 0.05


def min_clusters(alpha: float = ALPHA) -> int:
    """Fewest clusters (scenes) for which the exact two-sided sign-flip test can reach
    p < alpha: its smallest possible p is 2 / 2**n (all differences share one sign), so
    n = 6 for alpha = 0.05. With fewer, no difference can be significant."""
    n = 1
    while 2 / 2**n >= alpha:
        n += 1
    return n


def significance(
    ci_low: float | None,
    ci_high: float | None,
    p_value: float | None,
    alpha: float = ALPHA,
    n_clusters: int | None = None,
) -> str:
    """One decision rule for every difference reported (two runs, or own vs other scenes).

    "higher" / "lower": the 95% CI excludes 0 AND the exact sign-flip test gives p < alpha.
    "borderline": only one of the two says so (with ~10 scenes a bootstrap CI is often too
    narrow, so the exact test is required too). "inconclusive": neither, or fewer clusters
    than ``min_clusters`` (the test cannot reach p < alpha, and a bootstrap over 1-2
    clusters collapses to a point that trivially "excludes 0").
    """
    if ci_low is None or ci_high is None:
        return "inconclusive"
    if n_clusters is not None and n_clusters < min_clusters(alpha):
        return "inconclusive"
    ci_says = ci_low > 0 or ci_high < 0
    p_says = p_value is not None and p_value < alpha
    if ci_says and p_says:
        return "higher" if ci_low > 0 else "lower"
    if ci_says or p_says:
        return "borderline"
    return "inconclusive"


@dataclass(frozen=True)
class PairedComparison:
    a: float | None
    b: float | None
    diff: float | None  # b - a
    ci_low: float | None
    ci_high: float | None
    p_value: float | None  # exact sign-flip test on per-cluster differences
    verdict: str  # "A better" | "B better" | "borderline" | "inconclusive"


def paired_comparison(
    clusters: Sequence[Sequence[tuple[T, T]]],
    stat: Callable[[list[T]], float | None],
    lower_is_better: bool = False,
    seed: int = 0,
) -> PairedComparison:
    """Compare paired runs A and B on a statistic, respecting clusters (scenes).

    CI of B - A from a bootstrap over clusters, p-value from a sign-flip test on per-cluster
    differences; the verdict follows ``significance`` (CI and p must agree).
    """
    items = [pair for cluster in clusters for pair in cluster]
    va, vb = stat([x for x, _ in items]), stat([y for _, y in items])

    def diff(pairs: list[tuple[T, T]]) -> float | None:
        sa, sb = stat([x for x, _ in pairs]), stat([y for _, y in pairs])
        return None if sa is None or sb is None else sb - sa

    lo, hi = cluster_bootstrap_ci(clusters, diff, seed=seed)
    diffs = [d for c in clusters if (d := diff(list(c))) is not None]
    p = sign_flip_p(diffs)
    decision = significance(lo, hi, p, n_clusters=len(diffs))
    if decision in ("higher", "lower"):
        b_better = (decision == "higher") != lower_is_better
        verdict = "B better" if b_better else "A better"
    else:
        verdict = decision
    return PairedComparison(
        va, vb, None if va is None or vb is None else vb - va, lo, hi, p, verdict
    )
