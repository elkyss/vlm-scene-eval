import pytest

from vlm_eval.evaluation.stats import (
    balanced_accuracy,
    cluster_bootstrap_ci,
    prf,
    sign_flip_p,
    spearman,
)


def test_prf_edge_cases() -> None:
    assert prf(0, 0, 0) == {"precision": None, "recall": None, "f1": None}
    assert prf(0, 1, 1)["f1"] == 0.0
    assert prf(2, 1, 1)["f1"] == pytest.approx(2 / 3)


def test_balanced_accuracy() -> None:
    assert balanced_accuracy(["a", "a", "b"], ["a", "a", "a"]) == 0.5


def test_sign_flip_exact() -> None:
    assert sign_flip_p([1.0] * 10) == pytest.approx(2 / 1024)  # all 10 scenes favour B
    assert sign_flip_p([1.0, -1.0]) == 1.0
    assert sign_flip_p([0.0, 0.0, 0.0]) == 1.0
    assert sign_flip_p([]) is None
    assert sign_flip_p([1.0, None, 1.0]) == pytest.approx(0.5)  # type: ignore[list-item]


def test_spearman_monotonic() -> None:
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)


def test_cluster_bootstrap_contains_true_mean_and_is_deterministic() -> None:
    clusters = [[1.0, 1.0], [0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]
    stat = lambda xs: sum(xs) / len(xs)  # noqa: E731
    lo, hi = cluster_bootstrap_ci(clusters, stat, n_boot=500, seed=1)
    assert lo is not None and hi is not None
    assert lo <= 0.625 <= hi
    assert (lo, hi) == cluster_bootstrap_ci(clusters, stat, n_boot=500, seed=1)


def test_spearman_handles_ties_and_constants() -> None:
    from vlm_eval.evaluation.stats import average_ranks

    assert average_ranks([10, 20, 20, 30]) == [0.0, 1.5, 1.5, 3.0]
    assert spearman([1, 2, 3, 4], [1.0, 1.0, 1.0, 1.0]) is None
