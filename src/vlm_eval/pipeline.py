"""The orchestrator: load -> describe -> write -> evaluate.

``Pipeline`` receives fully built components (dependency injection) and is the only
place that knows the order of the stages. ``build_pipeline`` wires components from a
``RunConfig`` via the registries.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from vlm_eval.config import RunConfig
from vlm_eval.domain import GroundTruth, MetricResult, Prediction, Sample
from vlm_eval.evaluation.evaluator import Evaluator
from vlm_eval.evaluation.report import MarkdownReport
from vlm_eval.gt import GT_PROVIDERS, GTProvider
from vlm_eval.loaders import LOADERS, SceneLoader
from vlm_eval.prompting import PromptStrategy, load_strategy
from vlm_eval.run_artifacts import RunArtifacts, save_metrics
from vlm_eval.taxonomy import load_taxonomy
from vlm_eval.vlm import ImageSet, VLMBackend, build_backend, facts_to_response
from vlm_eval.writers import WRITERS, ResultWriter

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        loader: SceneLoader,
        gt_provider: GTProvider,
        backend: VLMBackend,
        strategy: PromptStrategy,
        writers: Sequence[ResultWriter],
        evaluator: Evaluator,
        report: MarkdownReport | None = None,
    ) -> None:
        self.loader = loader
        self.gt_provider = gt_provider
        self.backend = backend
        self.strategy = strategy
        self.writers = list(writers)
        self.evaluator = evaluator
        self.report = report

    # --- stages -----------------------------------------------------------------------
    def load(self) -> tuple[list[Sample], list[GroundTruth]]:
        samples = list(self.loader)
        log.info(
            "Loaded %d frames from %d scenes", len(samples), len({s.scene_name for s in samples})
        )
        return samples, [self.gt_provider.get(s) for s in samples]

    def describe(self, sample: Sample) -> Prediction:
        images = ImageSet.from_paths(
            [f"{sample.sample_token}:{cam}" for cam in sample.image_paths],
            list(sample.image_paths.values()),
        )
        out = self.strategy.run(self.backend, sample.sample_token, images)
        parsed = out.parsed
        return Prediction(
            sample_token=sample.sample_token,
            scene_name=sample.scene_name,
            model=self.backend.name,
            prompt_version=self.strategy.version,
            raw_output=out.raw_output,
            description=parsed.description,
            facts=parsed.facts,
            facts_source=parsed.facts_source,
            text_facts=parsed.text_facts,
            parse_ok=parsed.parse_ok,
            parse_error=parsed.parse_error,
            latency_s=out.latency_s,
        )

    def evaluate(self, run: RunArtifacts) -> list[MetricResult]:
        results = self.evaluator.evaluate(run.ground_truth, run.predictions)
        save_metrics(results, run.run_dir)
        if self.report:
            self.report.render(run, results)
        return results

    # --- end to end -------------------------------------------------------------------
    def run(self, run_dir: Path) -> tuple[RunArtifacts, list[MetricResult]]:
        samples, gts = self.load()
        predictions = []
        for i, sample in enumerate(samples, 1):
            predictions.append(self.describe(sample))
            log.info("[%d/%d] %s frame %d", i, len(samples), sample.scene_name, sample.frame_index)
        run = RunArtifacts(run_dir, samples, gts, predictions)
        run_dir.mkdir(parents=True, exist_ok=True)
        run.save_inputs()
        for writer in self.writers:
            writer.write(predictions, run_dir)
        return run, self.evaluate(run)


def build_pipeline(cfg: RunConfig) -> Pipeline:
    taxonomy = load_taxonomy(cfg.taxonomy)
    loader = LOADERS.build(cfg.loader.name, **cfg.loader.params)
    gt_provider = GT_PROVIDERS.build(
        cfg.ground_truth.name, taxonomy=taxonomy, **cfg.ground_truth.params
    )
    backend = build_backend(
        cfg.vlm,
        cfg.cache_dir,
        lambda: {s.sample_token: facts_to_response(gt_provider.get(s)) for s in loader},
    )
    return Pipeline(
        loader=loader,
        gt_provider=gt_provider,
        backend=backend,
        strategy=load_strategy(cfg.prompt, taxonomy),
        writers=[WRITERS.build(name, taxonomy=taxonomy) for name in cfg.writers],
        evaluator=Evaluator.from_config(cfg.metrics, taxonomy),
        report=MarkdownReport(),
    )


def evaluate_run(run_dir: Path) -> Path:
    """Re-score a saved frame-level run from its own config (no inference); returns the report."""
    from vlm_eval.config import load_config

    cfg = load_config(run_dir / "config.yaml")
    artifacts = RunArtifacts.load(run_dir)
    results = Evaluator.from_config(cfg.metrics, load_taxonomy(cfg.taxonomy)).evaluate(
        artifacts.ground_truth, artifacts.predictions
    )
    save_metrics(results, run_dir)
    return MarkdownReport().render(artifacts, results)
