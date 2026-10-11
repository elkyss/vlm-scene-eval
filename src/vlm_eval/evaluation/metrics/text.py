"""Metrics on the free-text description itself."""

from __future__ import annotations

import logging

from vlm_eval.domain import MetricResult
from vlm_eval.evaluation.metrics.base import METRICS, EvalPair
from vlm_eval.evaluation.metrics.objects import frame_f1, frame_outcomes, presence_summary
from vlm_eval.evaluation.similarity import similarity_matrix
from vlm_eval.evaluation.stats import mean_or_none, pearson, safe_div, spearman
from vlm_eval.parsing.text_claims import extract_objects
from vlm_eval.taxonomy import Taxonomy

log = logging.getLogger(__name__)


@METRICS.register("text_faithfulness")
class TextFaithfulnessMetric:
    """Scores the claims made in the prose, and whether the prose agrees with the JSON."""

    name = "text_faithfulness"

    def __init__(self, taxonomy: Taxonomy) -> None:
        self.taxonomy = taxonomy

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        tax = self.taxonomy
        result = presence_summary(pairs, tax.object_classes, source="text_facts")
        result.name = self.name

        # Contradiction = the prose claims something the JSON denies. Leaving an object
        # out of a 2-sentence description is not a contradiction.
        json_pairs = [p for p in pairs if p.pred.facts_source in {"json", "vqa"}]
        obj_contra, attr_agree = [], []
        for p in json_pairs:
            j, t = p.pred.facts, p.pred.text_facts
            obj_contra += [int(not j.present(c)) for c in tax.object_classes if t.present(c)]
            for a in tax.attribute_names:
                if j.attribute(a) is not None and t.attribute(a) is not None:
                    attr_agree.append(int(j.attribute(a) == t.attribute(a)))
        result.summary["text_json_object_contradiction_rate"] = safe_div(
            sum(obj_contra), len(obj_contra)
        )
        result.summary["text_json_attribute_agreement"] = safe_div(sum(attr_agree), len(attr_agree))
        result.notes.append(
            "Claims are extracted from the description with a rule-based lexicon "
            "(see parsing/text_claims.py). Agreement is computed for structured answers "
            "(JSON or questionnaire)."
        )
        return result


@METRICS.register("similarity")
class ReferenceSimilarityMetric:
    """Secondary signal: how close the description is to the human ``scene.description``.

    Reported mainly to show its limits: the reference is per *scene* (20 s), terse, and
    similarity rewards topical overlap rather than correctness. We report its correlation
    with the claim-level frame F1 to make that point quantitatively.
    """

    name = "similarity"

    def __init__(
        self,
        taxonomy: Taxonomy,
        embedding_model: str | None = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.taxonomy = taxonomy
        self.embedding_model = embedding_model

    def compute(self, pairs: list[EvalPair]) -> MetricResult:
        per_sample: dict[str, dict[str, float]] = {}
        for p in pairs:
            ref_classes = set(extract_objects(p.gt.reference_text, self.taxonomy))
            mentioned = set(p.pred.facts.objects) | set(p.pred.text_facts.objects)
            recall = safe_div(len(ref_classes & mentioned), len(ref_classes))
            per_sample[p.gt.sample_token] = {
                "object_f1": frame_f1(frame_outcomes(p, self.taxonomy.object_classes)),
                **({"reference_keyword_recall": recall} if recall is not None else {}),
            }
        notes: list[str] = []
        cosines = self._cosines(pairs, notes)
        if cosines is not None:
            for p, c in zip(pairs, cosines, strict=True):
                per_sample[p.gt.sample_token]["embedding_cosine"] = c

        summary: dict[str, float | None] = {
            "mean_reference_keyword_recall": mean_or_none(
                [s.get("reference_keyword_recall") for s in per_sample.values()]
            ),
        }
        if cosines is not None:
            f1 = [per_sample[p.gt.sample_token]["object_f1"] for p in pairs]
            summary["mean_embedding_cosine"] = mean_or_none(list(cosines))
            summary["pearson_cosine_vs_object_f1"] = pearson(cosines, f1)
            summary["spearman_cosine_vs_object_f1"] = spearman(cosines, f1)
        return MetricResult(name=self.name, summary=summary, per_sample=per_sample, notes=notes)

    def _cosines(self, pairs: list[EvalPair], notes: list[str]) -> list[float] | None:
        sims = similarity_matrix(
            [p.pred.description for p in pairs],
            [p.gt.reference_text for p in pairs],
            self.embedding_model,
        )
        if sims is None:
            notes.append("Embedding similarity skipped (no model or sentence-transformers).")
            return None
        return [float(sims[i, i]) for i in range(len(pairs))]
