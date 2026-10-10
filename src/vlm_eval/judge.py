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
    """Check hypotheses against a set of premise sentences.

    supported    if one sentence, or the whole premise read together, entails the hypothesis
                 (evidence: the best single sentence);
    contradicted if the whole premise contradicts it (evidence: the sentence with the highest
                 contradiction score, indicative only);
    neutral      otherwise.

    Why: small NLI models flag unrelated sentence pairs as contradictions ("There are cars."
    vs "There are no buses."), so contradiction is only taken from the whole premise. A
    compound claim ("turns left, passing cones") needs several facts at once, so whole-premise
    entailment also counts as support. Measured on the controls: oracle 100% supported / 0%
    contradicted; without whole-premise support, detailed Qwen descriptions scored 0%.
    """
    if not hypotheses:
        return []
    if not premises:
        return [Verdict(NEUTRAL, {NEUTRAL: 1.0}) for _ in hypotheses]
    whole = " ".join(premises)
    per = judge.judge_pairs([(p, h) for h in hypotheses for p in premises])
    together = judge.judge_pairs([(whole, h) for h in hypotheses])
    verdicts = []
    for i, _ in enumerate(hypotheses):
        rows = per[i * len(premises) : (i + 1) * len(premises)]
        best_s = max(range(len(premises)), key=lambda j: rows[j].get(SUPPORTED, 0.0))
        best_c = max(range(len(premises)), key=lambda j: rows[j].get(CONTRADICTED, 0.0))
        if (
            rows[best_s].get(SUPPORTED, 0.0) >= threshold
            or together[i].get(SUPPORTED, 0.0) >= threshold
        ):
            verdicts.append(Verdict(SUPPORTED, rows[best_s], premises[best_s]))
        elif together[i].get(CONTRADICTED, 0.0) >= threshold:
            verdicts.append(Verdict(CONTRADICTED, together[i], premises[best_c]))
        else:
            verdicts.append(Verdict(NEUTRAL, together[i]))
    return verdicts


@JUDGES.register("nli")
class NLIJudge:
    """Cross-encoder NLI model; the label order is read from the model config."""

    def __init__(
        self, model_id: str = "cross-encoder/nli-deberta-v3-base", batch_size: int = 32
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
