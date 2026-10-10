"""Text judges: does a premise support, contradict or say nothing about a hypothesis?

Used in two places of the scene evaluation:
* claim check: each claim of the model's description vs the fact-sheet sentences;
* human coverage: each item of ``scene.description`` vs the model's description.

Hypotheses are checked against each premise sentence separately (short, clean pairs are what
NLI models handle best) and the result is aggregated, keeping the sentence that decided it,
so every verdict is traceable. ``NLIJudge`` uses a small local cross-encoder; the interface is
tiny so an LLM-based judge can replace it without touching the metrics.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from vlm_eval.registry import Registry

SUPPORTED, CONTRADICTED, NEUTRAL = "supported", "contradicted", "neutral"
LABELS = (SUPPORTED, CONTRADICTED, NEUTRAL)


@dataclass(frozen=True)
class Verdict:
    label: str  # supported | contradicted | neutral
    probs: dict[str, float]  # probability per label
    evidence: str | None = None  # the premise sentence that decided the label


class TextJudge(Protocol):
    @property
    def name(self) -> str: ...

    def judge_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[dict[str, float]]:
        """Label probabilities for each (premise, hypothesis) pair."""
        ...


JUDGES: Registry[TextJudge] = Registry("judge")


def judge_against(
    judge: TextJudge, premises: Sequence[str], hypotheses: Sequence[str], threshold: float = 0.5
) -> list[Verdict]:
    """Check every hypothesis against every premise sentence and aggregate.

    supported   if the best entailment >= threshold and beats the best contradiction;
    contradicted if the best contradiction >= threshold and beats the best entailment;
    neutral     otherwise (nothing in the premise speaks to it).
    """
    if not hypotheses:
        return []
    if not premises:
        return [Verdict(NEUTRAL, {NEUTRAL: 1.0}) for _ in hypotheses]
    pairs = [(p, h) for h in hypotheses for p in premises]
    probs = judge.judge_pairs(pairs)
    verdicts = []
    for i, _ in enumerate(hypotheses):
        rows = probs[i * len(premises) : (i + 1) * len(premises)]
        best_s = max(range(len(premises)), key=lambda j: rows[j].get(SUPPORTED, 0.0))
        best_c = max(range(len(premises)), key=lambda j: rows[j].get(CONTRADICTED, 0.0))
        s, c = rows[best_s].get(SUPPORTED, 0.0), rows[best_c].get(CONTRADICTED, 0.0)
        if s >= threshold and s >= c:
            verdicts.append(Verdict(SUPPORTED, rows[best_s], premises[best_s]))
        elif c >= threshold:
            verdicts.append(Verdict(CONTRADICTED, rows[best_c], premises[best_c]))
        else:
            verdicts.append(Verdict(NEUTRAL, rows[best_s]))
    return verdicts


@JUDGES.register("nli")
class NLIJudge:
    """Cross-encoder NLI model; the label order is read from the model config."""

    def __init__(
        self, model_id: str = "cross-encoder/nli-deberta-v3-small", batch_size: int = 64
    ) -> None:
        self.model_id = model_id
        self.batch_size = batch_size
        self._model: Any = None
        self._labels: list[str] = []

    @property
    def name(self) -> str:
        return self.model_id.split("/")[-1]

    def _load(self) -> None:
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(self.model_id)
        id2label = self._model.model.config.id2label
        mapping = {"entailment": SUPPORTED, "contradiction": CONTRADICTED, "neutral": NEUTRAL}
        self._labels = [mapping[id2label[i].lower()] for i in range(len(id2label))]

    def judge_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[dict[str, float]]:
        if not pairs:
            return []
        if self._model is None:
            self._load()
        probs = self._model.predict(
            list(pairs), apply_softmax=True, batch_size=self.batch_size, show_progress_bar=False
        )
        return [{label: float(p[i]) for i, label in enumerate(self._labels)} for p in probs]


@JUDGES.register("fake")
class FakeJudge:
    """Deterministic judge for tests: ``rule(premise, hypothesis)`` returns the label."""

    def __init__(self, rule: Callable[[str, str], str] | None = None) -> None:
        self.rule = rule or _substring_rule

    @property
    def name(self) -> str:
        return "fake"

    def judge_pairs(self, pairs: Sequence[tuple[str, str]]) -> list[dict[str, float]]:
        return [{label: float(label == self.rule(p, h)) for label in LABELS} for p, h in pairs]


def _substring_rule(premise: str, hypothesis: str) -> str:
    return SUPPORTED if hypothesis.lower().rstrip(".") in premise.lower() else NEUTRAL
