"""Scene-level orchestrator: views -> VLM -> one description per scene.

For every scene, each view (N frames, time-ordered) is sent to the VLM in one call. The
views' descriptions are combined by self-consistency: facts stated by a majority of views
form the consensus, and the view that agrees most with it becomes the scene's description.
The final description is therefore real model text, and disagreement between views measures
how much the model's answer depends on which frames it happened to see.
"""

from __future__ import annotations

import csv
import logging
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from vlm_eval.config import SceneRunConfig
from vlm_eval.domain import SceneDescription, SceneFactSheet, SceneSample, ViewOutput
from vlm_eval.gt import FACT_BUILDERS, FactSheetBuilder
from vlm_eval.judge import JUDGES, TextJudge
from vlm_eval.loaders import SCENE_LOADERS
from vlm_eval.parsing.text_claims import extract_objects
from vlm_eval.prompting import ScenePrompt, load_scene_prompt
from vlm_eval.taxonomy import Taxonomy, load_taxonomy
from vlm_eval.vlm import ImageSet, VLMBackend, VLMRequest, build_backend
from vlm_eval.writers import write_jsonl

log = logging.getLogger(__name__)

SCENES = "scenes.jsonl"
SCENES_CSV = "scenes.csv"
FACT_SHEETS = "fact_sheets.jsonl"
KEYFRAME_SECONDS = 0.5  # nuScenes keyframes are annotated at 2 Hz


def view_output(
    view_id: int, frames: list[int], raw: str, latency: float, taxonomy: Taxonomy
) -> ViewOutput:
    description = raw.strip()
    attributes = {
        a: v
        for a in taxonomy.attribute_names
        if (v := taxonomy.value_in_text(a, description)) is not None
    }
    return ViewOutput(
        view_id=view_id,
        frame_indices=frames,
        raw_output=raw,
        description=description,
        mentioned_objects=sorted(extract_objects(description, taxonomy)),
        attributes=attributes,
        latency_s=latency,
    )


def combine_views(views: Sequence[ViewOutput]) -> tuple[int, list[str], dict[str, str], float]:
    """Self-consistency: (chosen view id, consensus objects, consensus attributes, agreement).

    A fact is in the consensus when more than half of the views state it. The chosen view is
    the one agreeing with the consensus on the most facts (ties -> lowest view id). Agreement
    is the share of facts mentioned by any view on which all views agree.
    """
    n = len(views)
    object_votes = Counter(cls for v in views for cls in v.mentioned_objects)
    consensus_objects = sorted(c for c, k in object_votes.items() if k > n / 2)
    attr_names = sorted({a for v in views for a in v.attributes})
    consensus_attrs: dict[str, str] = {}
    for attr in attr_names:
        value, k = Counter(v.attributes.get(attr) for v in views).most_common(1)[0]
        if value is not None and k > n / 2:
            consensus_attrs[attr] = value

    def score(v: ViewOutput) -> int:
        objs = sum((c in v.mentioned_objects) == (c in consensus_objects) for c in object_votes)
        attrs = sum(v.attributes.get(a) == consensus_attrs.get(a) for a in attr_names)
        return objs + attrs

    chosen = max(views, key=lambda v: (score(v), -v.view_id))
    facts = len(object_votes) + len(attr_names)
    unanimous = sum(k == n for k in object_votes.values()) + sum(
        len({v.attributes.get(a) for v in views}) == 1 for a in attr_names
    )
    return chosen.view_id, consensus_objects, consensus_attrs, unanimous / facts if facts else 1.0


class ScenePipeline:
    def __init__(
        self,
        scenes: Sequence[SceneSample],
        facts: FactSheetBuilder,
        backend: VLMBackend,
        prompt: ScenePrompt,
        taxonomy: Taxonomy,
    ) -> None:
        self.scenes = scenes
        self.facts = facts
        self.backend = backend
        self.prompt = prompt
        self.taxonomy = taxonomy

    def describe(self, scene: SceneSample) -> SceneDescription:
        outputs = []
        for view in scene.views:
            span_s = (max(view.frame_indices) - min(view.frame_indices)) * KEYFRAME_SECONDS
            images = ImageSet.from_paths(view.image_ids, view.image_paths)
            request = VLMRequest(
                f"{scene.scene_token}-v{view.view_id}",
                images,
                self.prompt.render(len(view.frame_indices), span_s, view.cameras),
            )
            response = self.backend.generate(request)
            outputs.append(
                view_output(
                    view.view_id,
                    view.frame_indices,
                    response.text,
                    response.latency_s,
                    self.taxonomy,
                )
            )
        chosen, objects, attrs, agreement = combine_views(outputs)
        return SceneDescription(
            scene_token=scene.scene_token,
            scene_name=scene.scene_name,
            model=self.backend.name,
            prompt_version=self.prompt.version,
            description=next(o.description for o in outputs if o.view_id == chosen),
            chosen_view=chosen,
            consensus_objects=objects,
            consensus_attributes=attrs,
            view_agreement=agreement,
            views=outputs,
        )

    def run(self, run_dir: Path) -> tuple[list[SceneDescription], list[SceneFactSheet]]:
        descriptions, sheets = [], []
        for i, scene in enumerate(self.scenes, 1):
            sheets += [self.facts.build(scene, view) for view in scene.views]
            descriptions.append(self.describe(scene))
            log.info(
                "[%d/%d] %s -> view %d",
                i,
                len(self.scenes),
                scene.scene_name,
                descriptions[-1].chosen_view,
            )
        write_scene_outputs(run_dir, descriptions, sheets)
        return descriptions, sheets


def write_scene_outputs(
    run_dir: Path, descriptions: Sequence[SceneDescription], sheets: Sequence[SceneFactSheet]
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(descriptions, run_dir / SCENES)
    write_jsonl(sheets, run_dir / FACT_SHEETS)
    with (run_dir / SCENES_CSV).open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "scene_name",
                "model",
                "prompt_version",
                "chosen_view",
                "view_agreement",
                "consensus_objects",
                "description",
            ]
        )
        for d in descriptions:
            writer.writerow(
                [
                    d.scene_name,
                    d.model,
                    d.prompt_version,
                    d.chosen_view,
                    f"{d.view_agreement:.2f}",
                    " ".join(d.consensus_objects),
                    d.description,
                ]
            )


def build_scene_pipeline(cfg: SceneRunConfig) -> ScenePipeline:
    taxonomy = load_taxonomy(cfg.taxonomy)
    loader = SCENE_LOADERS.build(cfg.loader.name, **cfg.loader.params)
    facts = FACT_BUILDERS.build(cfg.ground_truth.name, taxonomy=taxonomy, **cfg.ground_truth.params)
    scenes = list(loader)
    backend = build_backend(
        cfg.vlm,
        cfg.cache_dir,
        # Scene oracle: answers each view with its own fact sheet (upper bound).
        lambda: {
            f"{s.scene_token}-v{v.view_id}": " ".join(facts.build(s, v).premise_sentences)
            for s in scenes
            for v in s.views
        },
    )
    return ScenePipeline(scenes, facts, backend, load_scene_prompt(cfg.prompt), taxonomy)


def build_judge(cfg: SceneRunConfig) -> TextJudge:
    return JUDGES.build(cfg.judge.name, **cfg.judge.params)


class RunExistsError(RuntimeError):
    """The run folder already holds a run made with a different config."""


def check_run_dir(cfg: SceneRunConfig, force: bool = False) -> None:
    """Refuse to overwrite an existing run made with a different config (e.g. a committed
    full run re-used for a one-scene check). Re-running the same config is allowed: the
    cached answers make it a re-score."""
    from vlm_eval.config import load_scene_config

    existing = cfg.run_dir / "config.yaml"
    if force or not (cfg.run_dir / SCENES).exists() or not existing.exists():
        return
    if load_scene_config(existing).model_dump(mode="json") != cfg.model_dump(mode="json"):
        raise RunExistsError(
            f"{cfg.run_dir} already holds a run with a different config. Use another run id "
            "(--set run_id=NAME) or pass --force to overwrite it."
        )


def describe_scene_run(
    cfg: SceneRunConfig, pipeline: ScenePipeline | None = None, force: bool = False
) -> Path:
    """Inference only: describe every scene and write the run folder (scenes, fact sheets,
    config, manifest), with no judge or scoring. Returns the ``scenes.jsonl`` path.

    This is the step that needs the VLM (and ideally a GPU); ``evaluate_scene_run`` then
    scores the folder anywhere."""
    from vlm_eval.manifest import save_run_metadata

    check_run_dir(cfg, force)
    pipeline = pipeline or build_scene_pipeline(cfg)
    # The judge is only named here (its model loads lazily on first use).
    save_run_metadata(cfg.run_dir, cfg, pipeline.backend, {"judge": build_judge(cfg).name})
    pipeline.run(cfg.run_dir)
    return cfg.run_dir / SCENES


def default_validation_path(run_dir: Path) -> Path:
    """Where validate-judge writes by default: outputs/scenes/judge_validation."""
    return run_dir.parent / "judge_validation" / "judge_validation.json"


def evaluate_scene_run(run_dir: Path, validation_path: Path | None = None) -> Path:
    """Score a saved scene run from its own config (no inference); returns the report path.

    ``validation_path`` is the judge validation whose error rates are shown next to each
    claim type (default: ``default_validation_path``). Without it the report says so."""
    import json

    from vlm_eval.config import load_scene_config
    from vlm_eval.evaluation.scene_metrics import evaluate_scenes
    from vlm_eval.evaluation.scene_report import SCENE_METRICS, render_scene_report
    from vlm_eval.writers import read_jsonl

    cfg = load_scene_config(run_dir / "config.yaml")
    descriptions = read_jsonl(run_dir / SCENES, SceneDescription)
    evaluation = evaluate_scenes(
        descriptions,
        read_jsonl(run_dir / FACT_SHEETS, SceneFactSheet),
        build_judge(cfg),
        load_taxonomy(cfg.taxonomy),
        cfg.embedding_model,
        cfg.seed,
    )
    (run_dir / SCENE_METRICS).write_text(evaluation.model_dump_json(indent=2))
    views = descriptions[0].views if descriptions else []
    protocol = (
        f"Each scene is shown as {len(views)} views of "
        f"{len(views[0].frame_indices) if views else 0} frames (one VLM call per view); "
        "the final description is the view most consistent with the others."
    )
    validation_path = validation_path or default_validation_path(run_dir)
    validation = None
    if validation_path.exists():
        validation = json.loads(validation_path.read_text())["summary"]
    else:
        log.warning(
            "No judge validation at %s; the report shows no judge error rates", validation_path
        )
    return render_scene_report(evaluation, run_dir, protocol, validation)
