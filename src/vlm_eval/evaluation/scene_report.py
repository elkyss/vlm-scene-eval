"""Markdown report for a scene-level run, plus a side-by-side table of several runs."""

from __future__ import annotations

from pathlib import Path

from vlm_eval.evaluation.report import fmt, md_table
from vlm_eval.evaluation.scene_metrics import SceneEvaluation, SceneRow
from vlm_eval.judge import CONTRADICTED, SUPPORTED

SCENE_METRICS = "scene_metrics.json"

# (label, key, lower is better)
HEADLINE: tuple[tuple[str, str, bool], ...] = (
    ("CHAIR_i: invented object mentions / all object mentions", "chair_i", True),
    ("CHAIR_s: descriptions with an invented object", "chair_s", True),
    ("Object coverage: clearly visible classes mentioned", "object_coverage", False),
    ("Claims supported by the facts", "claims_supported", False),
    ("Claims contradicted by the facts", "claims_contradicted", True),
    ("Claims that cannot be verified (no annotation covers them)", "claims_unverifiable", False),
    ("Claims supported by annotation-based facts", "claims_supported_by_annotations", False),
    ("Human-sentence items covered", "human_coverage", False),
)


def _ci(summary: dict[str, float | None], key: str) -> str:
    lo, hi = summary.get(f"{key}_ci_low"), summary.get(f"{key}_ci_high")
    return "" if lo is None or hi is None else f" [{fmt(lo)}, {fmt(hi)}]"


def _scene_errors(row: SceneRow) -> str:
    parts = []
    if row.final.hallucinated:
        parts.append("invented: " + ", ".join(row.final.hallucinated))
    missed = [c for c in row.final.labelled if c not in row.final.covered]
    if missed:
        parts.append("missed: " + ", ".join(missed))
    n_contra = row.final.count("claims", CONTRADICTED)
    if n_contra:
        parts.append(f"{n_contra} contradicted claim(s)")
    return "; ".join(parts) or "none"


def render_scene_report(evaluation: SceneEvaluation, run_dir: Path, protocol: str) -> Path:
    s = evaluation.summary
    rows = evaluation.rows
    headline = [
        [
            label,
            fmt(s.get(key)) + _ci(s, key),
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
                f"- **{c.label}**: {c.text}"
                + (f"  \n  ↳ fact: _{c.evidence}_" if c.evidence else "")
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
        "across views. **Shuffled** = each description scored against another scene: a "
        "metric that does not get clearly worse there is not measuring content.",
        md_table(
            ["Metric", "Final", "Macro", "View A", "Mean of views", "Spread", "Shuffled"], headline
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
                [
                    "Judge check: 'supported' object claims whose object is in view "
                    f"(n={int(s.get('judge_support_n') or 0)})",
                    fmt(s.get("judge_support_precision")),
                ],
                [
                    "Judge check: 'contradicted' object claims whose object is absent "
                    f"(n={int(s.get('judge_contradiction_n') or 0)})",
                    fmt(s.get("judge_contradiction_precision")),
                ],
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


def scene_leaderboard(run_dirs: list[Path]) -> str:
    rows = []
    for run_dir in run_dirs:
        path = run_dir / SCENE_METRICS
        if not path.exists():
            continue
        ev = SceneEvaluation.model_validate_json(path.read_text())
        s = ev.summary
        rows.append(
            [
                run_dir.name,
                ev.model,
                ev.prompt_version.split("@")[0],
                *(fmt(s.get(k)) for _, k, _ in HEADLINE if k != "claims_supported_by_annotations"),
                fmt(s.get("shuffled_claims_supported")),
                fmt(s.get("view_agreement")),
                fmt(s.get("mean_latency_s_per_call"), False),
            ]
        )
    headers = [
        "Run",
        "Model",
        "Prompt",
        "CHAIR_i",
        "CHAIR_s",
        "Obj. coverage",
        "Supported",
        "Contradicted",
        "Unverifiable",
        "Human coverage",
        "Shuffled: supported",
        "View agreement",
        "s / call",
    ]
    return md_table(headers, rows)
