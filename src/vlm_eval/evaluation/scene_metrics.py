"""Scene-level evaluation of the final (and per-view) descriptions.

Reference = the automatic fact sheet (annotations, ego_pose, log, scene.description keywords)
plus the human ``scene.description``.

* Objects, CHAIR (no judge): CHAIR_i = hallucinated object mentions / all object mentions;
  CHAIR_s = share of descriptions with >= 1 hallucinated object; coverage = clearly visible
  classes that are mentioned. "Hallucinated" = no box of that class anywhere in the frames
  shown. Only the taxonomy's 7 classes can be checked this way.
* Claims (judge): each claim vs each fact sentence -> supported / contradicted / unverifiable,
  keeping the deciding fact and its source. Most scene content (buildings, trees, signs) has
  no annotation, so the unverifiable share is reported as a headline number.
* Human coverage (judge): each item of scene.description vs the description sentences. The
  human sentence lists highlights only, so it is used for coverage, never for hallucinations.
* Robustness: chosen view vs view A vs mean of views (self-consistency can flatter the chosen
  view), within-scene spread across views, and a shuffled-scene control (each description
  scored against another scene) that every metric should clearly fail.
* Similarity (secondary): embedding cosine to scene.description and whether a description is
  closer to its own scene's sentence than to the others'.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from vlm_eval.domain import SceneDescription, SceneFactSheet
from vlm_eval.evaluation.metrics.robustness import has_repetition_loop
from vlm_eval.evaluation.stats import cluster_bootstrap_ci, safe_div
from vlm_eval.judge import CONTRADICTED, NEUTRAL, SUPPORTED, TextJudge, judge_against
from vlm_eval.parsing.claims import (
    reference_hypothesis,
    split_claims,
    split_reference,
    split_sentences,
)
from vlm_eval.parsing.text_claims import extract_objects
from vlm_eval.taxonomy import Taxonomy

log = logging.getLogger(__name__)

KEYS = (
    "chair_i",
    "chair_s",
    "object_coverage",
    "claims_supported",
    "claims_contradicted",
    "claims_unverifiable",
    "claims_supported_by_annotations",
    "human_coverage",
    "human_contradicted",
)
_MAX_OBJECT_CLAIM_WORDS = 6  # "A bus waits at the stop." is about the bus; longer claims mix facts
CI_KEYS = (
    "chair_i",
    "object_coverage",
    "claims_supported",
    "claims_contradicted",
    "human_coverage",
)


class CheckedText(BaseModel):
    text: str
    label: str  # supported | contradicted | neutral
    evidence: str | None = None
    evidence_source: str | None = None
    # For claims naming exactly one object class: is there a box of it in the frames shown?
    # Lets the NLI verdict be cross-checked against the annotations without a human.
    object_class: str | None = None
    box_present: bool | None = None


class DescriptionScore(BaseModel):
    """One description checked against one fact sheet and one human sentence."""

    mentioned: list[str] = Field(default_factory=list)
    hallucinated: list[str] = Field(default_factory=list)
    labelled: list[str] = Field(default_factory=list)
    covered: list[str] = Field(default_factory=list)
    claims: list[CheckedText] = Field(default_factory=list)
    human_items: list[CheckedText] = Field(default_factory=list)

    def count(self, kind: str, label: str) -> int:
        return sum(c.label == label for c in getattr(self, kind))

    def rates(self) -> dict[str, float | None]:
        return aggregate([self])


class SceneRow(BaseModel):
    scene_name: str
    reference_text: str
    description: str
    chosen_view: int
    view_agreement: float
    final: DescriptionScore
    per_view: list[DescriptionScore]
    shuffled: DescriptionScore | None = None
    fact_sentences: list[str]
    words: int
    repetition_loop: bool
    latency_s: float
    embedding_cosine: float | None = None
    own_scene_rank: int | None = None


class SceneEvaluation(BaseModel):
    model: str
    prompt_version: str
    judge: str
    rows: list[SceneRow]
    summary: dict[str, float | None] = Field(default_factory=dict)


def score_description(
    description: str,
    sheet: SceneFactSheet,
    reference_text: str,
    judge: TextJudge,
    taxonomy: Taxonomy,
) -> DescriptionScore:
    mentioned = sorted(extract_objects(description, taxonomy))
    labelled = sorted(sheet.objects)
    sources = {s.text: s.source for s in sheet.sentences}

    claims = split_claims(description)
    claim_verdicts = judge_against(judge, sheet.premise_sentences, claims)
    items = split_reference(reference_text)
    item_verdicts = judge_against(
        judge, split_sentences(description), [reference_hypothesis(i) for i in items]
    )
    return DescriptionScore(
        mentioned=mentioned,
        hallucinated=[c for c in mentioned if c not in sheet.loosely_present],
        labelled=labelled,
        covered=[c for c in labelled if c in mentioned],
        claims=[
            _checked_claim(c, v.label, v.evidence, sources, sheet, taxonomy)
            for c, v in zip(claims, claim_verdicts, strict=True)
        ],
        human_items=[
            CheckedText(text=i, label=v.label, evidence=v.evidence)
            for i, v in zip(items, item_verdicts, strict=True)
        ],
    )


def _checked_claim(
    claim: str,
    label: str,
    evidence: str | None,
    sources: dict[str, str],
    sheet: SceneFactSheet,
    taxonomy: Taxonomy,
) -> CheckedText:
    classes = list(extract_objects(claim, taxonomy))
    cls = classes[0] if len(classes) == 1 else None
    return CheckedText(
        text=claim,
        label=label,
        evidence=evidence,
        evidence_source=sources.get(evidence or ""),
        object_class=cls,
        box_present=None if cls is None else cls in sheet.loosely_present,
    )


def judge_box_check(scores: Sequence[DescriptionScore]) -> dict[str, float | None]:
    """Automatic check of the judge against the boxes, on short claims about one object class
    (at most ``_MAX_OBJECT_CLAIM_WORDS`` words):

    * support precision: when the judge says "supported", is the object really in view?
    * contradiction precision: when it says "contradicted", is the object really absent?
    """
    short = [
        c
        for s in scores
        for c in s.claims
        if c.object_class is not None and len(c.text.split()) <= _MAX_OBJECT_CLAIM_WORDS
    ]
    supported = [c for c in short if c.label == SUPPORTED]
    contradicted = [c for c in short if c.label == CONTRADICTED]
    return {
        "judge_support_precision": safe_div(
            sum(bool(c.box_present) for c in supported), len(supported)
        ),
        "judge_support_n": float(len(supported)),
        "judge_contradiction_precision": safe_div(
            sum(not c.box_present for c in contradicted), len(contradicted)
        ),
        "judge_contradiction_n": float(len(contradicted)),
    }


def aggregate(scores: Sequence[DescriptionScore]) -> dict[str, float | None]:
    """Micro-averaged rates (pooled counts) over a set of descriptions."""
    mentions = sum(len(s.mentioned) for s in scores)
    claims = sum(len(s.claims) for s in scores)
    items = sum(len(s.human_items) for s in scores)
    by_annotations = sum(
        c.label == SUPPORTED and c.evidence_source not in (None, "description")
        for s in scores
        for c in s.claims
    )
    return {
        "chair_i": safe_div(sum(len(s.hallucinated) for s in scores), mentions),
        "chair_s": safe_div(sum(bool(s.hallucinated) for s in scores), len(scores)),
        "object_coverage": safe_div(
            sum(len(s.covered) for s in scores), sum(len(s.labelled) for s in scores)
        ),
        "claims_supported": safe_div(sum(s.count("claims", SUPPORTED) for s in scores), claims),
        "claims_contradicted": safe_div(
            sum(s.count("claims", CONTRADICTED) for s in scores), claims
        ),
        "claims_unverifiable": safe_div(sum(s.count("claims", NEUTRAL) for s in scores), claims),
        "claims_supported_by_annotations": safe_div(by_annotations, claims),
        "human_coverage": safe_div(sum(s.count("human_items", SUPPORTED) for s in scores), items),
        "human_contradicted": safe_div(
            sum(s.count("human_items", CONTRADICTED) for s in scores), items
        ),
    }


def macro(scores: Sequence[DescriptionScore]) -> dict[str, float | None]:
    """Mean of per-scene rates: every scene weighs the same, however long its description."""
    per_scene = [s.rates() for s in scores]
    out: dict[str, float | None] = {}
    for key in KEYS:
        out[key] = _mean([r[key] for r in per_scene])
    return out


def within_scene_spread(rows: Sequence[SceneRow], key: str) -> float | None:
    """Mean over scenes of (max - min) of the per-view rate: how much the frames shown matter."""
    spreads = []
    for row in rows:
        values = [v for s in row.per_view if (v := s.rates()[key]) is not None]
        if len(values) > 1:
            spreads.append(max(values) - min(values))
    return float(np.mean(spreads)) if spreads else None


def embedding_scores(rows: Sequence[SceneRow], model_id: str | None) -> None:
    if not model_id or len(rows) < 2:
        return
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        log.warning("sentence-transformers not installed: embedding similarity skipped")
        return
    model: Any = SentenceTransformer(model_id)
    desc = model.encode(
        [r.description or " " for r in rows], normalize_embeddings=True, show_progress_bar=False
    )
    refs = model.encode(
        [r.reference_text for r in rows], normalize_embeddings=True, show_progress_bar=False
    )
    sims = desc @ refs.T
    for i, row in enumerate(rows):
        row.embedding_cosine = float(sims[i, i])
        row.own_scene_rank = int((sims[i] > sims[i, i]).sum()) + 1


def _mean(values: Sequence[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return float(np.mean(clean)) if clean else None


def evaluate_scenes(
    descriptions: Sequence[SceneDescription],
    sheets: Sequence[SceneFactSheet],
    judge: TextJudge,
    taxonomy: Taxonomy,
    embedding_model: str | None = None,
    seed: int = 0,
) -> SceneEvaluation:
    by_key = {(s.scene_name, s.view_id): s for s in sheets}
    rows = []
    for d in descriptions:
        per_view = [
            score_description(
                v.description,
                by_key[(d.scene_name, v.view_id)],
                by_key[(d.scene_name, v.view_id)].reference_text,
                judge,
                taxonomy,
            )
            for v in d.views
        ]
        sheet = by_key[(d.scene_name, d.chosen_view)]
        rows.append(
            SceneRow(
                scene_name=d.scene_name,
                reference_text=sheet.reference_text,
                description=d.description,
                chosen_view=d.chosen_view,
                view_agreement=d.view_agreement,
                final=per_view[[v.view_id for v in d.views].index(d.chosen_view)],
                per_view=per_view,
                fact_sentences=sheet.premise_sentences,
                words=len(d.description.split()),
                repetition_loop=has_repetition_loop(d.description),
                latency_s=_mean([v.latency_s for v in d.views]) or 0.0,
            )
        )

    # Shuffled-scene control: each description against the next scene's facts and sentence.
    if len(rows) > 1:
        for i, row in enumerate(rows):
            other = descriptions[(i + 1) % len(descriptions)]
            other_sheet = by_key[(other.scene_name, other.chosen_view)]
            row.shuffled = score_description(
                row.description, other_sheet, other_sheet.reference_text, judge, taxonomy
            )
    embedding_scores(rows, embedding_model)
    return SceneEvaluation(
        model=descriptions[0].model if descriptions else "?",
        prompt_version=descriptions[0].prompt_version if descriptions else "?",
        judge=judge.name,
        rows=rows,
        summary=summarize(rows, seed),
    )


def summarize(rows: Sequence[SceneRow], seed: int = 0) -> dict[str, float | None]:
    finals = [r.final for r in rows]
    summary: dict[str, float | None] = dict(aggregate(finals))
    summary.update({f"macro_{k}": v for k, v in macro(finals).items()})

    def micro(key: str) -> Callable[[list[DescriptionScore]], float | None]:
        return lambda scores: aggregate(scores)[key]

    for key in CI_KEYS:
        lo, hi = cluster_bootstrap_ci([[s] for s in finals], micro(key), seed=seed)
        summary[f"{key}_ci_low"], summary[f"{key}_ci_high"] = lo, hi

    n_views = min((len(r.per_view) for r in rows), default=0)
    view_a = aggregate([r.per_view[0] for r in rows]) if n_views else {}
    per_view = [aggregate([r.per_view[v] for r in rows]) for v in range(n_views)]
    for key in KEYS:
        summary[f"view_a_{key}"] = view_a.get(key)
        summary[f"views_mean_{key}"] = _mean([p[key] for p in per_view])
        summary[f"within_scene_spread_{key}"] = within_scene_spread(rows, key)
    shuffled = [r.shuffled for r in rows if r.shuffled is not None]
    if shuffled:
        summary.update({f"shuffled_{k}": v for k, v in aggregate(shuffled).items()})

    summary["view_agreement"] = _mean([r.view_agreement for r in rows])
    summary["empty_rate"] = safe_div(sum(not r.description for r in rows), len(rows))
    summary["repetition_loop_rate"] = safe_div(sum(r.repetition_loop for r in rows), len(rows))
    summary["mean_words"] = _mean([float(r.words) for r in rows])
    summary["mean_latency_s_per_call"] = _mean([r.latency_s for r in rows])
    summary["embedding_cosine"] = _mean([r.embedding_cosine for r in rows])
    ranks = [r.own_scene_rank for r in rows if r.own_scene_rank is not None]
    summary["own_scene_rank_1_rate"] = safe_div(sum(k == 1 for k in ranks), len(ranks))
    summary.update(
        judge_box_check(
            [s for r in rows for s in r.per_view] + [r.shuffled for r in rows if r.shuffled]
        )
    )
    summary["n_scenes"] = float(len(rows))
    return summary
