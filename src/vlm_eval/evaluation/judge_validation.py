"""Automatic validation of the claim judge on paraphrased claims with known truth.

The oracle control only shows the judge can match a fact sentence to itself. Here every
scene's fact sheet is used to generate claims in *different wording* whose truth is known
from the annotations (true: objects in view, the real time of day, our car's real motion;
false: classes with no box in view, the opposite time of day or motion). The judge's
answers on them estimate how far "supported" can be trusted, without human labelling.

Limitation: the paraphrases are template sentences written by us, cleaner than real model
output, so these numbers are an optimistic bound on the judge's accuracy.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from vlm_eval.domain import SceneFactSheet
from vlm_eval.evaluation.report import fmt, md_table
from vlm_eval.evaluation.stats import safe_div
from vlm_eval.judge import CONTRADICTED, SUPPORTED, TextJudge, judge_against
from vlm_eval.taxonomy import Taxonomy

OPPOSITE_TIME = {"night": "day", "day": "night"}
TIME_CLAIM = {
    "night": "The drive takes place at night.",
    "day": "The drive takes place in daylight.",
}
EGO_CLAIM = {
    True: "The vehicle carrying the camera is not moving.",
    False: "The vehicle carrying the camera is moving.",
}
TURN_CLAIM = {
    "left": "The vehicle carrying the camera makes a left turn.",
    "right": "The vehicle carrying the camera makes a right turn.",
}


class ProbeClaim(BaseModel):
    scene_name: str
    kind: str  # objects | time_of_day | ego_motion | turn | ambiguous_car
    claim: str
    truth: bool | None  # None = genuinely ambiguous (reported, not scored)
    verdict: str = ""


def probe_claims(sheet: SceneFactSheet, taxonomy: Taxonomy) -> list[ProbeClaim]:
    """Paraphrased claims with known truth for one fact sheet."""
    claims: list[ProbeClaim] = []

    def add(kind: str, text: str, truth: bool | None) -> None:
        claims.append(ProbeClaim(scene_name=sheet.scene_name, kind=kind, claim=text, truth=truth))

    for cls, spec in taxonomy.objects.items():
        if sheet.objects.get(cls):
            add("objects", f"Some {spec.name(2)} can be seen in the scene.", True)
        elif cls not in sheet.loosely_present:
            add("objects", f"A {spec.name(1)} is clearly visible in the scene.", False)
    time = sheet.attributes.get("time_of_day")
    if time in TIME_CLAIM:
        add("time_of_day", TIME_CLAIM[time], True)
        add("time_of_day", TIME_CLAIM[OPPOSITE_TIME[time]], False)
    if sheet.ego is not None:
        stopped = sheet.ego.state == "stopped"
        add("ego_motion", EGO_CLAIM[stopped], True)
        add("ego_motion", EGO_CLAIM[not stopped], False)
        if sheet.ego.turn in TURN_CLAIM:
            other = "right" if sheet.ego.turn == "left" else "left"
            add("turn", TURN_CLAIM[sheet.ego.turn], True)
            add("turn", TURN_CLAIM[other], False)
        if not stopped and "car" in sheet.objects:
            # "The car" may mean our car (moving) or another car (which may well be stopped):
            # the truth is unknown, so only the verdict distribution is reported.
            add("ambiguous_car", "The car is stopped.", None)
    return claims


def validate_judge(
    sheets: Sequence[SceneFactSheet], judge: TextJudge, taxonomy: Taxonomy
) -> list[ProbeClaim]:
    probes = []
    for sheet in sheets:
        claims = probe_claims(sheet, taxonomy)
        verdicts = judge_against(judge, sheet.premise_sentences, [c.claim for c in claims])
        for c, v in zip(claims, verdicts, strict=True):
            c.verdict = v.label
        probes += claims
    return probes


def summarize_probes(probes: Sequence[ProbeClaim]) -> dict[str, dict[str, float | None]]:
    """Per claim kind: how often true claims are supported, false claims are supported (an
    error) and false claims are contradicted."""
    groups: dict[str, list[ProbeClaim]] = defaultdict(list)
    for p in probes:
        if p.truth is None:
            continue
        groups[p.kind].append(p)
        groups["all"].append(p)
    out = {}
    for kind, items in groups.items():
        true = [p for p in items if p.truth]
        false = [p for p in items if not p.truth]
        out[kind] = {
            "n_true": float(len(true)),
            "n_false": float(len(false)),
            "true_supported": safe_div(sum(p.verdict == SUPPORTED for p in true), len(true)),
            "false_supported": safe_div(sum(p.verdict == SUPPORTED for p in false), len(false)),
            "false_contradicted": safe_div(
                sum(p.verdict == CONTRADICTED for p in false), len(false)
            ),
            "true_contradicted": safe_div(sum(p.verdict == CONTRADICTED for p in true), len(true)),
        }
    return out


def write_judge_validation(probes: Sequence[ProbeClaim], judge_name: str, out_dir: Path) -> Path:
    summary = summarize_probes(probes)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "judge_validation.json").write_text(
        json.dumps(
            {"judge": judge_name, "summary": summary, "probes": [p.model_dump() for p in probes]},
            indent=2,
        )
    )
    order = ["all", "objects", "time_of_day", "ego_motion", "turn"]
    rows = [
        [
            kind,
            int(v["n_true"] or 0),
            int(v["n_false"] or 0),
            fmt(v["true_supported"]),
            fmt(v["false_supported"]),
            fmt(v["false_contradicted"]),
            fmt(v["true_contradicted"]),
        ]
        for kind in order
        if (v := summary.get(kind))
    ]
    errors = [p for p in probes if p.truth is not None and (p.verdict == SUPPORTED) != p.truth][:15]
    ambiguous = [p for p in probes if p.truth is None]
    amb = {v: sum(p.verdict == v for p in ambiguous) for v in (SUPPORTED, CONTRADICTED, "neutral")}
    report = "\n\n".join(
        [
            f"# Judge validation: `{judge_name}`",
            "Claims are generated from each scene's fact sheet in different wording, with known "
            "truth (true: objects in view, the real time of day and motion of our car; false: "
            "classes with no box in view, the opposite time of day or motion). They are cleaner "
            "than real model text, so these are optimistic estimates of the judge's accuracy.",
            md_table(
                [
                    "Claim kind",
                    "True claims",
                    "False claims",
                    "True → supported",
                    "False → supported (error)",
                    "False → contradicted",
                    "True → contradicted (error)",
                ],
                rows,
            ),
            '**How to read it.** "True → supported" is how often a correct claim gets credit; '
            '"False → supported" is how often a wrong claim is wrongly credited.',
            f'**"The car" ambiguity.** "The car is stopped." was judged on {len(ambiguous)} '
            "views where our car is moving and other cars are present (truth unknown: "
            f'"the car" may be another car): supported {amb[SUPPORTED]}, contradicted '
            f"{amb[CONTRADICTED]}, neutral {amb['neutral']}. A contradiction means the judge "
            'read "the car" as our car; one reason contradiction rates are indicative only.',
            "**Disagreements (first 15)**\n\n"
            + "\n".join(
                f"- {p.scene_name} ({p.kind}, {'true' if p.truth else 'false'}): {p.claim} → "
                f"**{p.verdict}**"
                for p in errors
            )
            if errors
            else "No disagreements.",
        ]
    )
    path = out_dir / "judge_validation.md"
    path.write_text(report + "\n")
    return path
