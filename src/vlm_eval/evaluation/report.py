"""Renders metrics into a human-readable markdown report."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from vlm_eval.domain import MetricResult
from vlm_eval.run_artifacts import RunArtifacts

log = logging.getLogger(__name__)


def fmt(value: Any, pct: bool = True) -> str:
    if value is None:
        return "–"
    if isinstance(value, float):
        return f"{value:.1%}" if pct else f"{value:.2f}"
    return str(value)


def fmt_ci(summary: dict[str, float | None], key: str) -> str:
    """``summary[key]`` followed by its ``_ci_low`` / ``_ci_high`` interval, when present."""
    lo, hi = summary.get(f"{key}_ci_low"), summary.get(f"{key}_ci_high")
    ci = "" if lo is None or hi is None else f" [{fmt(lo)}, {fmt(hi)}]"
    return fmt(summary.get(key)) + ci


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


class MarkdownReport:
    def __init__(
        self,
        thumbnails: bool = True,
        thumb_width: int = 480,
    ) -> None:
        self.thumbnails = thumbnails
        self.thumb_width = thumb_width

    def render(self, run: RunArtifacts, results: list[MetricResult]) -> Path:
        r = {m.name: m for m in results}
        preds = run.predictions
        model = preds[0].model if preds else "?"
        prompt = preds[0].prompt_version if preds else "?"
        scenes = sorted({g.scene_name for g in run.ground_truth})

        parts = [
            f"# VLM evaluation report: `{model}` with prompt `{prompt}`",
            f"{len(run.ground_truth)} frames from {len(scenes)} scenes. Ground truth comes from "
            "nuScenes annotations (objects), `scene.description` (time of day, road condition, "
            "scene type) and `log.location` (traffic side).",
        ]
        parts.append(self._headline(r))
        if "object_presence" in r:
            parts.append(self._objects(r["object_presence"]))
        if "counting" in r:
            parts.append(self._counting(r["counting"]))
        if "attributes" in r:
            parts.append(self._attributes(r["attributes"]))
        if "text_faithfulness" in r:
            parts.append(self._text(r["text_faithfulness"]))
        if "slices" in r:
            parts.append(self._slices(r["slices"]))
        if "consistency" in r:
            parts.append(self._consistency(r["consistency"]))
        if "similarity" in r:
            parts.append(self._similarity(r["similarity"]))
        if "errors" in r:
            parts.append(self._errors(r["errors"], run))

        path = run.run_dir / "report.md"
        path.write_text("\n\n".join(parts) + "\n")
        return path

    def _headline(self, r: dict[str, MetricResult]) -> str:
        rows = []

        def add(label: str, metric: str, key: str, pct: bool = True) -> None:
            if metric in r:
                rows.append([label, fmt(r[metric].summary.get(key), pct)])

        add("Object presence: micro F1", "object_presence", "micro_f1")
        add(
            "  ↳ blind baseline (always claims the frequent classes, never looks)",
            "object_presence",
            "blind_prior_micro_f1",
        )
        add("Object presence: precision", "object_presence", "micro_precision")
        add("Object presence: recall", "object_presence", "micro_recall")
        add(
            "Hallucination rate (claimed class with no box in view)",
            "object_presence",
            "hallucination_rate",
        )
        add(
            "Omission rate (clearly visible class not mentioned)",
            "object_presence",
            "omission_rate",
        )
        add("Count bucket accuracy (exact)", "counting", "exact_bucket_accuracy")
        add("Count bucket accuracy within ±1", "counting", "within_one_bucket_accuracy")
        add("Scene attributes: mean balanced accuracy", "attributes", "mean_balanced_accuracy")
        add("Free-text claims: micro F1", "text_faithfulness", "micro_f1")
        add(
            "Prose claims an object the structured answer denies",
            "text_faithfulness",
            "text_json_object_contradiction_rate",
        )
        add("Valid structured output", "format", "parse_success_rate")
        add("Mean latency per frame (s)", "format", "mean_latency_s", pct=False)
        return "## Headline numbers\n\n" + md_table(["Metric", "Value"], rows)

    def _slices(self, m: MetricResult) -> str:
        parts = ["## Slices", "Headline metrics per ground-truth condition. " + " ".join(m.notes)]
        for by, table in m.tables.items():
            rows = [
                [
                    k,
                    int(v["frames"] or 0),
                    fmt(v["object_f1"]),
                    fmt(v["object_recall"]),
                    fmt(v["hallucination_rate"]),
                    fmt(v["attribute_accuracy"]),
                ]
                for k, v in table.items()
            ]
            parts.append(
                f"**By {by}**\n\n"
                + md_table(
                    ["Slice", "Frames", "Object F1", "Recall", "Hallucination", "Attribute acc."],
                    rows,
                )
            )
        return "\n\n".join(parts)

    def _objects(self, m: MetricResult) -> str:
        rows = [
            [
                cls,
                int(v["gt_frames"]),
                v["tp"],
                v["fp"],
                v["fp_far"],
                v["fn"],
                fmt(v["precision"]),
                fmt(v["precision_strict"]),
                fmt(v["recall"]),
                fmt(v["f1"]),
            ]
            for cls, v in m.tables["per_class"].items()
        ]
        vis = [
            [k, int(v["objects"]), fmt(v["recall"])]
            for k, v in m.tables.get("recall_by_visibility", {}).items()
        ]
        dist = [
            [k, int(v["objects"]), fmt(v["recall"])]
            for k, v in m.tables.get("recall_by_distance", {}).items()
        ]
        return "\n\n".join(
            [
                "## Objects: hallucination vs. omission",
                "Per frame and class: claimed vs. present (≥40% visible, ≤50 m). `FP` = claimed "
                "but no box of that class anywhere in the image (hallucination); `FP far` = a box "
                "exists but is far or mostly occluded (excused in *precision*, counted in "
                "*precision strict*).",
                md_table(
                    [
                        "Class",
                        "GT frames",
                        "TP",
                        "FP",
                        "FP far",
                        "FN",
                        "Precision",
                        "Precision strict",
                        "Recall",
                        "F1",
                    ],
                    rows,
                ),
                "**Recall by object visibility** (all annotated objects in view)",
                md_table(["Visibility", "Objects", "Recall"], vis),
                "**Recall by distance**",
                md_table(["Distance", "Objects", "Recall"], dist),
            ]
        )

    def _counting(self, m: MetricResult) -> str:
        rows = [
            [cls, int(v["n"] or 0), fmt(v["exact"]), fmt(v["within_one_bucket"])]
            for cls, v in m.tables["per_class"].items()
            if v["n"]
        ]
        return (
            "## Counting\n\nOnly frames where GT and prediction both say the class is "
            "present (buckets 1-2 / 3-5 / 6+).\n\n"
            + md_table(["Class", "Frames", "Exact bucket", "Within ±1 bucket"], rows)
        )

    def _attributes(self, m: MetricResult) -> str:
        rows = [
            [
                attr,
                fmt(v["accuracy"]),
                fmt(v["balanced_accuracy"]),
                fmt(v["majority_baseline"]),
                fmt(v["coverage"]),
                ", ".join(f"{k}: {n}" for k, n in v["gt_distribution"].items()),
            ]
            for attr, v in m.tables.items()
        ]
        conf = [
            f"- **{attr}**: "
            + "; ".join(
                f"GT {t} → " + ", ".join(f"{p}: {n}" for p, n in preds.items())
                for t, preds in v["confusion"].items()
            )
            for attr, v in m.tables.items()
        ]
        return "\n\n".join(
            [
                "## Scene attributes",
                "Accuracy counts unanswered fields as wrong. Compare against the majority-class "
                'baseline: with a skewed GT, a model that always says "day" looks good on raw '
                "accuracy but gets 50% balanced accuracy.",
                md_table(
                    [
                        "Attribute",
                        "Accuracy",
                        "Balanced acc.",
                        "Majority baseline",
                        "Answered",
                        "GT distribution",
                    ],
                    rows,
                ),
                "Confusion:\n" + "\n".join(conf),
            ]
        )

    def _text(self, m: MetricResult) -> str:
        s = m.summary
        return (
            "## Free-text faithfulness\n\n"
            + md_table(
                ["Metric", "Value"],
                [
                    ["Claims in prose: precision", fmt(s.get("micro_precision"))],
                    ["Claims in prose: recall", fmt(s.get("micro_recall"))],
                    ["Claims in prose: hallucination rate", fmt(s.get("hallucination_rate"))],
                    [
                        "Prose object claims the structured answer denies",
                        fmt(s.get("text_json_object_contradiction_rate")),
                    ],
                    [
                        "Prose ↔ structured attribute agreement",
                        fmt(s.get("text_json_attribute_agreement")),
                    ],
                ],
            )
            + "\n\n"
            + " ".join(m.notes)
        )

    def _consistency(self, m: MetricResult) -> str:
        rows = [
            [k, fmt(v["pred_flip_rate"]), fmt(v["gt_flip_rate"])]
            for k, v in m.tables["per_label"].items()
        ]
        return (
            "## Temporal consistency\n\nHow often a label changes between consecutive "
            "sampled frames of the same scene.\n\n"
            + md_table(["Label", "Model flip rate", "GT flip rate"], rows)
            + "\n\n"
            + " ".join(m.notes)
        )

    def _similarity(self, m: MetricResult) -> str:
        s = m.summary
        rows = [
            [
                "Reference keyword recall (classes in scene.description that are mentioned)",
                fmt(s.get("mean_reference_keyword_recall")),
            ],
            [
                "Mean embedding cosine to scene.description",
                fmt(s.get("mean_embedding_cosine"), False),
            ],
            ["Pearson(cosine, frame object F1)", fmt(s.get("pearson_cosine_vs_object_f1"), False)],
            [
                "Spearman(cosine, frame object F1)",
                fmt(s.get("spearman_cosine_vs_object_f1"), False),
            ],
        ]
        return (
            "## Similarity to the human reference (secondary)\n\n"
            "`scene.description` describes a 20 s scene in keywords, not this frame, so "
            "similarity is a weak proxy. A low correlation with the claim-level F1 shows "
            "that similarity does not track correctness.\n\n"
            + md_table(["Metric", "Value"], rows)
            + ("\n\n" + " ".join(m.notes) if m.notes else "")
        )

    def _errors(self, m: MetricResult, run: RunArtifacts) -> str:
        fam = [[k, v] for k, v in m.tables["by_family"].items()]
        tags = [[k, v] for k, v in list(m.tables["by_tag"].items())[:15]]
        parts = [
            "## Error taxonomy",
            f"Frames with at least one error: {fmt(m.summary.get('frames_with_any_error'))}",
            md_table(["Error family", "Count"], fam),
            md_table(["Most frequent errors", "Count"], tags),
            "### Worst frames",
        ]
        images = {s.sample_token: next(iter(s.image_paths.values())) for s in run.samples}
        for ex in m.tables["worst_examples"]:
            block = [
                f"**{ex['scene_name']} / frame {ex['frame_index']}**: "
                + ", ".join(f"`{e}`" for e in ex["errors"])
            ]
            thumb = self._thumbnail(images.get(ex["sample_token"]), run.run_dir, ex["sample_token"])
            if thumb:
                block.append(f"![{ex['sample_token']}]({thumb})")
            block.append(f"> {ex['description'] or '(empty)'}")
            block.append(f"GT objects: `{ex['gt_objects']}`, predicted: `{ex['pred_objects']}`")
            parts.append("\n\n".join(block))
        return "\n\n".join(parts)

    def _thumbnail(self, image: Path | None, run_dir: Path, token: str) -> str | None:
        if not self.thumbnails or image is None or not Path(image).exists():
            return None
        from PIL import Image

        out = run_dir / "thumbs" / f"{token}.jpg"
        out.parent.mkdir(exist_ok=True)
        with Image.open(image) as img:
            img.thumbnail((self.thumb_width, self.thumb_width))
            img.convert("RGB").save(out, quality=80)
        return f"thumbs/{out.name}"
