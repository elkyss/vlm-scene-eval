"""Scene-level orchestrator: views -> VLM -> one description per scene.

For every scene, each view (N frames, time-ordered) is sent to the VLM in one call. The
views' descriptions are combined by self-consistency: facts stated by a majority of views
form the consensus, and the view that agrees most with it becomes the scene's description.
The final description is therefore real model text, and disagreement between views measures
how much the model's answer depends on which frames it happened to see.
"""

from __future__ import annotations

import csv
import hashlib
import logging
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from vlm_eval.config import SceneRunConfig
from vlm_eval.domain import SceneDescription, SceneFactSheet, SceneSample, ViewOutput
from vlm_eval.gt.scene_facts import SceneFactBuilder
from vlm_eval.judge import JUDGES, TextJudge
from vlm_eval.loaders.scene_loader import NuScenesSceneLoader
from vlm_eval.manifest import write_manifest
from vlm_eval.parsing.text_claims import extract_objects
from vlm_eval.prompting import PROMPT_DIR
from vlm_eval.taxonomy import Taxonomy, load_taxonomy
from vlm_eval.vlm import BACKENDS, CachedBackend, ImageSet, MockBackend, VLMBackend, VLMRequest
from vlm_eval.writers import write_jsonl

log = logging.getLogger(__name__)

SCENES = "scenes.jsonl"
SCENES_CSV = "scenes.csv"
FACT_SHEETS = "fact_sheets.jsonl"
KEYFRAME_SECONDS = 0.5  # nuScenes keyframes are annotated at 2 Hz


@dataclass(frozen=True)
class ScenePrompt:
    name: str
    template: str

    def render(self, n_frames: int, span_s: float) -> str:
        spacing = max(1, round(span_s / max(1, n_frames - 1)))
        return self.template.format(n_frames=n_frames, spacing=spacing)

    @property
    def version(self) -> str:
        return f"{self.name}@{hashlib.sha256(self.template.encode()).hexdigest()[:8]}"


def load_scene_prompt(name: str) -> ScenePrompt:
    path = PROMPT_DIR / f"{name}.txt"
    if not path.exists():
        available = sorted(p.stem for p in PROMPT_DIR.glob("scene_*.txt"))
        raise KeyError(f"Unknown scene prompt {name!r}. Available: {available}")
    return ScenePrompt(name, path.read_text().strip())


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
        facts: SceneFactBuilder,
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
            images = ImageSet.from_paths(view.sample_tokens, view.image_paths)
            request = VLMRequest(
                f"{scene.scene_token}-v{view.view_id}",
                images,
                self.prompt.render(len(view.frame_indices), span_s),
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
            description=outputs[[o.view_id for o in outputs].index(chosen)].description,
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


def oracle_backend(scenes: Sequence[SceneSample], facts: SceneFactBuilder) -> VLMBackend:
    """Upper-bound 'model' that answers with each view's own fact sheet."""
    responses = {
        f"{s.scene_token}-v{v.view_id}": " ".join(facts.build(s, v).premise_sentences)
        for s in scenes
        for v in s.views
    }
    return MockBackend(mode="table", responses=responses)


def build_scene_pipeline(cfg: SceneRunConfig) -> ScenePipeline:
    taxonomy = load_taxonomy(cfg.taxonomy)
    loader = NuScenesSceneLoader(
        cfg.dataroot, cfg.version, cfg.camera, cfg.frames_per_view, cfg.n_views, cfg.scenes
    )
    facts = SceneFactBuilder(
        cfg.dataroot, cfg.version, cfg.camera, cfg.min_visibility, cfg.max_distance_m, taxonomy
    )
    scenes = list(loader)
    if cfg.vlm.name == "oracle":
        backend = oracle_backend(scenes, facts)
    else:
        backend = BACKENDS.build(cfg.vlm.name, **cfg.vlm.params)
        if cfg.cache_dir is not None and cfg.vlm.name != "mock":
            backend = CachedBackend(backend, cfg.cache_dir)
    return ScenePipeline(scenes, facts, backend, load_scene_prompt(cfg.prompt), taxonomy)


def build_judge(cfg: SceneRunConfig) -> TextJudge:
    return JUDGES.build(cfg.judge.name, **cfg.judge.params)


def save_run_metadata(cfg: SceneRunConfig, backend: VLMBackend, judge: TextJudge) -> None:
    cfg.run_dir.mkdir(parents=True, exist_ok=True)
    (cfg.run_dir / "config.yaml").write_text(yaml.safe_dump(cfg.model_dump(mode="json")))
    inner = getattr(backend, "backend", backend)
    write_manifest(
        cfg.run_dir,
        cfg,
        {
            "model_signature": backend.signature,
            "model_revision": getattr(inner, "resolved_revision", None),
            "judge": judge.name,
        },
    )
