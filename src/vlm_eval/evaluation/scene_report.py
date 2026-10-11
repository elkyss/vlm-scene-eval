"""Markdown report for a scene-level run, plus a side-by-side table of several runs."""

from __future__ import annotations

from pathlib import Path

from vlm_eval.evaluation.report import fmt, fmt_ci, md_table
from vlm_eval.evaluation.scene_metrics import SceneEvaluation, SceneRow
from vlm_eval.evaluation.stats import significance
from vlm_eval.judge import CONTRADICTED, SUPPORTED

SCENE_METRICS = "scene_metrics.json"

# (label, key, lower is better)
HEADLINE: tuple[tuple[str, str, bool], ...] = (
    ("CHAIR_i: invented object mentions / all object mentions", "chair_i", True),
    ("CHAIR_s: descriptions with an invented object", "chair_s", True),
    ("Object coverage: clearly visible classes mentioned", "object_coverage", False),
    ("Claims supported by the facts", "claims_supported", False),
    ("Claims that cannot be verified (no annotation covers them)", "claims_unverifiable", False),
    ("Claims supported by annotation-based facts", "claims_supported_by_annotations", False),
    ("Human-sentence items covered", "human_coverage", False),
)
SPECIFIC: tuple[tuple[str, str], ...] = (
    ("Claims supported: own scene minus other scenes", "specific_claims_supported"),
    ("Object coverage: own scene minus other scenes", "specific_object_coverage"),
    ("Human-sentence coverage: own scene minus other scenes", "specific_human_coverage"),
)


def _p(value: float | None) -> str:
    return "–" if value is None else f"{value:.3f}"


def specificity_verdict(s: dict[str, float | None]) -> str:
    """Plain-language conclusion of the shuffled-scene control, with the same decision rule
    as a comparison of two runs (``stats.significance``: CI and exact test must agree)."""
    names = {
        "specific_claims_supported": "claims",
        "specific_object_coverage": "objects",
        "specific_human_coverage": "the human sentence",
    }
    decisions = {
        key: significance(s.get(f"{key}_ci_low"), s.get(f"{key}_ci_high"), s.get(f"{key}_p"))
        for _, key in SPECIFIC
        if s.get(f"{key}_ci_low") is not None
    }
    if not decisions:
        return "**Conclusion:** no shuffled control (fewer than two scenes)."
    by = {
        d: [names[k] for k, v in decisions.items() if v == d]
        for d in ("higher", "lower", "borderline")
    }
    if by["higher"]:
        text = (
            "**Conclusion:** the descriptions are measurably specific to their own scene "
            "on " + ", ".join(by["higher"]) + " (95% CI above 0 and p < 0.05)."
        )
    else:
        text = (
            "**Conclusion:** no clear evidence that the descriptions describe this "
            "particular scene; treat the other scores of this run as reflecting generic "
            "text."
        )
    if by["borderline"]:
        text += " Borderline (CI and exact test disagree) on " + ", ".join(by["borderline"]) + "."
    if by["lower"]:
        text += " They fit other scenes better than their own on " + ", ".join(by["lower"]) + "."
    return text


def _evidence_note(label: str, evidence: str | None) -> str:
    if label == SUPPORTED and evidence:
        return f"  \n  ↳ supporting fact: _{evidence}_"
    if label == CONTRADICTED:
        return "  \n  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)"
    return ""


def _scene_errors(row: SceneRow) -> str:
    parts = []
    if row.final.hallucinated:
        parts.append("invented: " + ", ".join(row.final.hallucinated))
    missed = [c for c in row.final.labelled if c not in row.final.covered]
    if missed:
        parts.append("missed: " + ", ".join(missed))
    n_contra = row.final.count("claims", CONTRADICTED)
    if n_contra:
        parts.append(f"{n_contra} contradicted claim(s), indicative")
    return "; ".join(parts) or "none"


CLAIM_TYPE_LABELS = {
    "motion": ("How vehicles move (our car or others)", ("ego_motion", "turn")),
    "objects": ("Which objects are present", ("objects",)),
    "conditions": ("Time of day, road condition", ("time_of_day",)),
    "place": ("Kind of place, traffic side", ()),
    "other": ("Anything else (buildings, signs, weather...)", ()),
}


def _validation_note(kinds: tuple[str, ...], validation: dict | None) -> str:
    if not kinds:
        return "not validated"
    if validation is None:
        return "no judge validation found (run validate-judge)"
    parts = []
    for kind in kinds:
        v = validation.get(kind)
        if v and v.get("false_supported") is not None:
            parts.append(
                f"{kind.replace('_', ' ')} {fmt(v['false_supported'])} (n={int(v['n_false'] or 0)})"
            )
    return ", ".join(parts) or "–"


def claim_type_table(s: dict[str, float | None], validation: dict | None) -> str:
    rows = [
        [
            label,
            int(s.get(f"claims_n_{kind}") or 0),
            fmt(s.get(f"claims_supported_{kind}")),
            _validation_note(kinds, validation),
        ]
        for kind, (label, kinds) in CLAIM_TYPE_LABELS.items()
    ]
    return md_table(
        ["Claims about", "Claims", "Supported", "Judge validation: false claims wrongly supported"],
        rows,
    )


def render_scene_report(
    evaluation: SceneEvaluation, run_dir: Path, protocol: str, validation: dict | None = None
) -> Path:
    s = evaluation.summary
    rows = evaluation.rows
    headline = [
        [
            label,
            fmt_ci(s, key),
            fmt(s.get(f"macro_{key}")),
            fmt(s.get(f"view_a_{key}")),
            fmt(s.get(f"views_mean_{key}")),
            fmt(s.get(f"within_scene_spread_{key}")),
            fmt(s.get(f"shuffled_{key}")),
        ]
        for label, key, _ in HEADLINE
    ]
    per_scene = [
        [
            r.scene_name,
            r.reference_text,
            r.description.replace("\n", " ") or "(empty)",
            f"{r.final.count('human_items', SUPPORTED)}/{len(r.final.human_items)}",
            _scene_errors(r),
        ]
        for r in rows
    ]
    details = []
    for r in rows:
        claims = (
            "\n".join(
                f"- **{c.label}**: {c.text}" + _evidence_note(c.label, c.evidence)
                for c in r.final.claims
            )
            or "- (no claims)"
        )
        items = "\n".join(f"- **{c.label}**: {c.text}" for c in r.final.human_items)
        facts = "\n".join(f"- {f}" for f in r.fact_sentences)
        details.append(
            f"<details><summary>{r.scene_name}: view {r.chosen_view} chosen, "
            f"view agreement {fmt(r.view_agreement)}</summary>\n\n"
            f"**Fact sheet (reference)**\n\n{facts}\n\n**Claims of the description**\n\n"
            f"{claims}\n\n**Human sentence items**\n\n{items}\n\n</details>"
        )
    parts = [
        f"# Scene-level evaluation: `{evaluation.model}` with prompt `{evaluation.prompt_version}`",
        f"{int(s.get('n_scenes') or 0)} scenes. {protocol} Claims are judged by "
        f"`{evaluation.judge}` against the fact sheet; objects are checked against the 3D boxes "
        "(CHAIR) without a judge.",
        "## Headline\n\n"
        "**Final** = the chosen view's description (95% CI from a bootstrap over scenes). "
        "**Macro** = mean of per-scene rates. **View A** and **mean of views** show how much "
        "the self-consistency choice changes the result. **Spread** = within-scene max-min "
        "across views. **Shuffled** = each description scored against every other scene "
        "(pooled): a metric that does not get clearly worse there is not measuring content.",
        md_table(
            ["Metric", "Final", "Macro", "View A", "Mean of views", "Spread", "Shuffled"], headline
        ),
        "## Supported claims by type\n\n"
        "The judge is not equally reliable for every kind of claim. Its validation on claims "
        "with known truth (`validate-judge`) shows how often a *false* claim of each type is "
        "wrongly marked supported: read each row's supported rate with that error in mind. "
        "Small validation counts (e.g. 10 turn claims) are weak evidence.\n\n"
        + claim_type_table(s, validation),
        "## Is the description about this scene?\n\n"
        'A generic description ("a car on a street in daylight") is supported in almost any '
        "scene. Each description is therefore also scored against every other scene, and the "
        "gap (own scene minus the other scenes) shows how much of the content is specific to "
        "this scene. The CI comes from a bootstrap over scenes and the p-value from a "
        "sign-flip test on the per-scene gaps, as in a comparison of two runs. A gap whose CI "
        "includes 0 is no evidence of scene-specific content. For reference, the oracle "
        "control (fact sheet as description) scores about +45 points on claims supported.\n\n"
        + md_table(
            ["Metric", "Own − other scenes [95% CI]", "Sign-flip p"],
            [[label, fmt_ci(s, key), _p(s.get(f"{key}_p"))] for label, key in SPECIFIC],
        )
        + "\n\n"
        + specificity_verdict(s),
        "## Contradictions (indicative only)\n\n"
        "A claim counts as contradicted when the NLI judge reads the whole fact sheet as "
        "contradicting it. The automatic check below shows this verdict is much less reliable "
        'than "supported", so contradiction rates are reported but not used for conclusions.\n\n'
        + md_table(
            ["Metric", "Value"],
            [
                [
                    "Claims contradicted",
                    fmt_ci(s, "claims_contradicted"),
                ],
                [
                    "Shuffled control: claims contradicted",
                    fmt(s.get("shuffled_claims_contradicted")),
                ],
            ],
        ),
        "## Output quality\n\n"
        + md_table(
            ["Metric", "Value"],
            [
                [
                    "Agreement between views (facts all views agree on)",
                    fmt(s.get("view_agreement")),
                ],
                ["Empty descriptions", fmt(s.get("empty_rate"))],
                ["Repetition loops", fmt(s.get("repetition_loop_rate"))],
                ["Mean words per description", fmt(s.get("mean_words"), False)],
                ["Mean latency per call (s)", fmt(s.get("mean_latency_s_per_call"), False)],
            ],
        ),
        "## Similarity to the human sentence (secondary)\n\n"
        "Whole-text similarity is reported for completeness. It rewards topical overlap, not "
        "correctness, which is why the claim-level checks above are the main result.\n\n"
        + md_table(
            ["Metric", "Value"],
            [
                [
                    "Mean embedding cosine to scene.description",
                    fmt(s.get("embedding_cosine"), False),
                ],
                [
                    "Description closest to its own scene's sentence (of all scenes)",
                    fmt(s.get("own_scene_rank_1_rate")),
                ],
            ],
        ),
        "## Per scene\n\n"
        + md_table(
            [
                "Scene",
                "Human sentence",
                "Model description (final)",
                "Human items covered",
                "Errors",
            ],
            per_scene,
        ),
        "## Details per scene\n\n" + "\n\n".join(details),
    ]
    path = run_dir / "report.md"
    path.write_text("\n\n".join(parts) + "\n")
    return path
