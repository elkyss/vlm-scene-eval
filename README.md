# VLM scene-description evaluation on nuScenes

This project describes each nuScenes driving **scene** with a small vision-language model
(VLM), writes **one description per scene**, and **measures how good those descriptions
are**. Every claim in a description is checked against the dataset's annotations, and each
score is compared with controls that show what the score would be without the model
actually seeing the scene.

> nuScenes data and the thumbnails in `outputs/` are © Motional,
> [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). All results are
> committed under `outputs/`, so they can be read without running anything.

## Summary

**Pipeline.** 10 scenes (all of nuScenes v1.0-mini). Each scene is passed to the VLM as
3 views of 6 front-camera frames, one call per view. The view that agrees most with the
other two becomes the scene's description: one entry per scene in
`outputs/scenes/<run>/scenes.jsonl`.

**Main results** (`outputs/scenes/leaderboard.md`):

| Run | Invented objects (CHAIRᵢ) | Visible objects mentioned | Claims supported | Own scene − shuffled scene | Human sentence covered |
|---|---|---|---|---|---|
| *Oracle (answers with the facts)* | *0%* | *100%* | *100%* | *+41 pts* | *63% (ceiling)* |
| *Always "a car and a pedestrian"* | *10%* | *42%* | *20%* | *0 pts* | *17%* |
| **Qwen2-VL-2B, guided prompt** | 4% | **56%** [44, 68] | **38%** [32, 45] | +8 pts | **44%** |
| Qwen2-VL-2B, open prompt | 4% | 51% [36, 65] | 21% [11, 31] | +9 pts | 36% |
| SmolVLM-500M, guided prompt | 7% | 30% [25, 35] | 32% [19, 46] | +5 pts | 22% |
| SmolVLM-500M, open prompt | 0% | 24% [20, 29] | 27% [7, 51] | −7 pts | 12% |

Brackets are 95% confidence intervals from a bootstrap over the 10 scenes.

**Three findings:**
1. **Qwen2-VL-2B is the better describer.** On the same frames it mentions about 26 more points
   of the visible object types than SmolVLM (CI [+15, +36], scene-level p = 0.004, guided
   prompt). It also covers 22 more points of what the human annotator wrote.
2. **The prompt matters.** Asking Qwen to cover place, conditions, road users and what our
   car does raises supported claims by 17 points (CI [+7, +27], p = 0.02).
3. **Generic text looks good on paper, and the controls expose it.** SmolVLM's descriptions
   fit *other* scenes as well as their own (−7 pts). 60% of them loop ("The first image
   shows a car… The second image shows a car…"). A fixed sentence that never looks at the
   image still gets 20% of its claims supported.

---

## The four steps of the assignment

| Step | What it does | Where |
|---|---|---|
| 1. Load a scene | A scene is one 20 s clip of about 40 keyframes. **CAM_FRONT** frames only: it is where a driver looks, and one camera keeps the input small enough for small VLMs. The keyframes are split into 6 segments. View *v* takes the frame at position (v + 0.5)/3 in each segment, which gives 3 non-overlapping, time-ordered views of 6 frames. The rule is fixed and never looks at the labels. | `loaders/scene_loader.py` |
| 2. Run a VLM | One call per view: 6 images plus a prompt saying they are consecutive snapshots of one drive. The final description is the view that agrees most with the facts the majority of views state (self-consistency). Disagreement between views measures the model's variance. | `scene_pipeline.py`, `prompts/scene_*.txt` |
| 3. Output | **One entry per scene**: `scenes.jsonl` and `scenes.csv` hold the final description, the chosen view, view agreement, model and prompt version, with every view's text attached. | `outputs/scenes/<run>/` |
| 4. Evaluate | `report.md` and `scene_metrics.json` per run, plus comparisons, a leaderboard and a validation of the judge. | `evaluation/scene_*.py` |

---

## How do you know the VLM is giving good results?

A good description says true things about **this** scene, covers what matters in it, and
says the same thing whichever frames it was shown. Each of those is measured, and none of
them is trusted until it beats a control:

- **True things:** every claim is checked against facts taken from the annotations, not
  against wording (next section). CHAIRᵢ catches invented objects, and "claims supported"
  catches everything else that can be checked.
- **About this scene:** the same description is also scored against a *different* scene.
  A description that scores as well there is generic. The oracle gains 41 points on its
  own scene; SmolVLM's open prompt loses 7.
- **What matters:** coverage of the visible object types, and of the items in the human
  annotator's sentence.
- **Stable:** three views per scene. The report shows the chosen view next to view A and
  the mean of all views, plus the spread within each scene.
- **The measurement itself is checked:**
  - controls: an oracle, a fixed "always car" sentence, and shuffled scenes;
  - an automatic validation of the judge (see "How did you test the code?");
  - scene-level statistics that don't treat frames of one clip as independent.

## What do you compare the outputs against?

**The annotations first, the human sentence second.** For each view, a fact sheet is
generated automatically (`gt/scene_facts.py`) and written as plain sentences:

| Fact | Source | Rule |
|---|---|---|
| Object types in view (car, truck, bus, pedestrian, two-wheeler, cone, barrier) | 3D boxes in the 6 frames shown | Visible if at least 40% visible and within 50 m. **Presence only**: counting the same car across frames is ambiguous, and "There are 23 cars" would contradict a reasonable "a few cars" |
| Object types *not* in view | Same | "There are no buses" is stated only if no box of that type appears anywhere in the frames |
| What objects are doing | Annotation attributes (moving / parked / standing) | Majority state per type |
| What our car does | `ego_pose` over the view's time span | Stopped (< 0.5 m/s), slow (< 4 m/s), driving, fast (> 11 m/s); turning if the heading changes by more than 30° |
| City and traffic side | `log.location` | Singapore drives on the left, Boston on the right |
| Night, rain, intersection, parking lot | Keywords in `scene.description` | Same text cues as the taxonomy |

This works: without any human input, the fact sheet recovers the annotator's "turn left"
(scene-0061, a heading change of 86°) and "wait at intersection" (scene-0553, 0.0 m/s).

The human `scene.description` (e.g. "Night, after rain, many peds, PMD, jaywalker") is used
**only for coverage**. It lists highlights, so a missing item there does not make a model's
claim false. It also describes all ~40 keyframes while the model saw 6, so even the oracle
covers only 63% of it. That is the ceiling for this metric.

**Why not text similarity?** It rewards topical overlap, not truth. The report still shows
it: real descriptions score 0.27–0.41 cosine to the human sentence, and are closest to
their own scene's sentence in at most 2 of 10 scenes. That is near chance.

## What kinds of mistakes can the VLM make, and how would you catch them?

| Mistake | Caught by | Seen in |
|---|---|---|
| Invented objects | CHAIRᵢ / CHAIRₛ against the boxes | Up to 7% of object mentions (SmolVLM guided) |
| Missed objects | Object coverage | SmolVLM mentions 24–30% of visible types |
| Wrong conditions or wrong motion of our car | Claims contradicted by the fact sheet (indicative only, see "How did you test the code?") | Reported per scene |
| Generic text that would fit any scene | Own scene − shuffled scene | SmolVLM open −7 pts |
| Describing each image instead of the drive, or repetition loops ("The first image shows… The second image shows…") | Repetition detector that ignores ordinals and numbers | 60% of SmolVLM open descriptions |
| Answers that depend on which frames were shown | Agreement between views, and spread within each scene | View agreement 43–70% for real models |
| Leaving out what the annotator found important | Human-sentence coverage | 12–44% |
| Claims nobody can check (buildings, trees, signs) | Share of unverifiable claims, reported as its own number | 44–53% of claims |
| Ambiguous references ("the car": ours or another?) | Ambiguity probe in the judge validation | The judge splits 13 / 11 on it |

## How would you compare two VLMs, or two prompts?

Run both on the **same views** and use `vlm-eval compare-scenes A B`. For each metric it
reports A, B, the difference, a 95% CI from a bootstrap over scenes, per-scene wins and
losses, and an exact sign-flip test on per-scene differences. The verdict is
"inconclusive" whenever the CI includes 0. Testing happens at scene level because frames
and claims within a scene are not independent.

| Comparison | Clear differences | Inconclusive |
|---|---|---|
| Qwen2-VL vs SmolVLM, guided prompt | Objects mentioned +26 pts [+15, +36], p = 0.004; human sentence +22 pts [+15, +30], p = 0.004 | Claims supported, CHAIRᵢ |
| Qwen2-VL vs SmolVLM, open prompt | Objects mentioned +27 pts [+10, +43], p = 0.04; human sentence +24 pts [+7, +40], p = 0.03 | Claims supported, CHAIRᵢ |
| Qwen2-VL, guided vs open prompt | Claims supported +17 pts [+7, +27], p = 0.02 | Objects, human sentence |
| SmolVLM, guided vs open prompt | None | Everything |

With 10 scenes, small differences cannot be resolved. The reports say so instead of
picking a winner.

## How did you test the code?

- **139 tests** (`make test`, also run inside Docker and in CI):
  - Unit tests per component: frame sampling, ego motion on synthetic tracks, fact
    sentences, view combination, claim splitting, the judge rule, CHAIR and coverage
    against hand-computed examples, the sign-flip test, the cache key and the run
    manifest.
  - End-to-end runs on fake scenes with mock models.
  - Real-data tests that are skipped if `data/` is missing. One of them checks that the
    fact sheet recovers "turn left" and "wait at intersection".
- **Controls:**
  - The oracle has to score 100% supported and 0% contradicted.
  - The fixed-sentence model and the shuffled scenes have to score clearly lower.
- **Validation of the judge** (`vlm-eval validate-judge`, `outputs/scenes/judge_validation/`):
  - **Method:** claims with known truth are generated from each fact sheet, worded
    differently from it.
  - **Correct claims** are supported 100% of the time and never contradicted.
  - **Wrong claims** are wrongly supported 15.6% of the time: 18.5% for objects, 30% for
    our car's motion, 0% for time of day and turns.
  - **How it was used:** the validation chose the judge rule. Supporting a claim from the
    whole fact sheet is needed: without it, paraphrased day/night claims get 0%, and it
    adds no false support.
  - **Verdict:** "contradicted" is much less reliable ("the car" is read as our car about
    half the time), so it is reported but not used for conclusions.
- **Bugs found by testing** that would have changed results:
  - A class that is present but never predicted dropped out of macro F1.
  - Echoed JSON templates were read as object claims.
  - The ego camera car ("taken from the front of a car") was counted as a car.
  - Rank correlation was wrong with tied values.
  - Long, correct claims were scored neutral, which penalised detailed descriptions.
  - The repetition detector missed "first image… second image…" loops.
  - A torch/transformers version mismatch only appeared when running inside Docker.
- `ruff` and `mypy` pass cleanly. Every run writes `manifest.json` with the git commit,
  model revision, library versions and config hash.

---

## How well did the chosen VLM do?

**Qwen2-VL-2B** (local, about 10 s per 6-image call on a laptop GPU) is a usable but
shallow scene describer. With the guided prompt:
- **Objects:** it mentions 56% of the visible object types and rarely invents one (4% of
  mentions).
- **Claims:** 38% of its claims are confirmed by the annotations, about 18% contradict
  them, and 44% are about things nobody annotated.
- **Human sentence:** it covers 44% of what the annotator wrote, against a ceiling of 63%.
- **Scene-specific:** its descriptions are measurably about their own scene, but only
  modestly (+8 pts over a shuffled scene).

It is good enough to search or triage drives, not to replace annotation.

**SmolVLM-500M**, the comparison model, mostly describes images one by one, loops, and
writes text that fits any scene equally well.

## Assumptions

- **Scene and camera:** a scene is one nuScenes clip. CAM_FRONT only.
- **Sampling protocol:** 6 frames per call (SmolVLM's context fits about 8 images) and 3
  views per scene. This is a fixed rule, not something tuned on results.
- **Final description:** the view most consistent with the others, so it is real model
  text. The report also shows view A and the mean of all views.
- **Ground truth scope:** objects are judged on the frames shown. Visible means at least
  40% visible and within 50 m. Presence only, 7 object types.
- **Text-derived facts:** night, rain, intersection and parking lot come from the scene
  sentence and hold for the whole clip. An intersection mentioned there may not be in
  every view.
- **Ego motion:** thresholds of 0.5 / 4 / 11 m/s and a 30° turn, computed over the view's
  time span.
- **Judge:** `cross-encoder/nli-deberta-v3-base` with a 0.5 threshold. Supported if one
  fact sentence or the whole fact sheet entails the claim; contradicted only if the whole
  fact sheet contradicts it.
- **Statistics:** only 10 scenes, so every comparison gives a CI and a scene-level test.
- **Models:** small local models only, greedy decoding, model revisions recorded
  in each run's manifest.

## Limitations

- **"Claims supported" depends on how claims are split.** Splitting is rule-based, and
  long compound claims are hard to verify. CHAIR and coverage do not have this problem.
- **The judge validation is optimistic:** the claims it uses are cleaner than real model
  text.
- **About half of what the models say cannot be checked**, because nuScenes has no labels
  for buildings, trees, signs or weather beyond the scene sentence.
- **Night and location are confounded:** all night scenes are in Holland Village.
- **10 scenes** is the whole mini split. Full trainval (850 scenes) needs only a config
  change.

---

## Frame-level diagnostic (why scene descriptions fail)

Before the scene pipeline, single frames were scored (5 per scene, one call per frame) to
find out what the models get right and wrong frame by frame (`outputs/<run>/`,
`outputs/leaderboard.md`). The main points:

- **Small models cannot follow a JSON schema.** SmolVLM copied the template (48% valid
  output) or answered "3." to every frame.
- **Asking one question at a time works best for objects.** Qwen2-VL reaches 73% object F1
  this way, against 55% for a blind baseline that never looks at the image. It beats JSON
  by 14 pts [+6, +22] (p = 0.02), but costs 4× the latency and invites "yes" to leading
  questions (barrier accuracy −38 pts [−66, −10]).
- **A tested hypothesis that failed.** Replacing the JSON template's example values with
  `<0|1-2|3-5|6+>` placeholders made Qwen worse: object F1 −24 pts [−40, −12], p = 0.002.
  The model picked the first option. The quality gate (`vlm-eval gate`) blocks this change
  against the previous version.
- **SmolVLM's free text cannot be told apart from the fixed sentence** (+3.7 pts
  [−3.9, +11.9], p = 0.31).

---

## Setup and run

```bash
mkdir -p data/nuscenes && tar -xzf v1.0-mini.tgz -C data/nuscenes
```

Download `v1.0-mini.tgz` from <https://www.nuscenes.org/nuscenes#download> (*Full dataset
(v1.0) → Mini*). This needs a free account.

**Docker** (Python 3.12, CPU torch, pinned versions in `constraints.txt`):

```bash
docker compose build
```

```bash
docker compose run --rm --entrypoint make app test
```

```bash
docker compose run --rm app run-scenes -c configs/scenes/qwen2vl_guided.yaml --set 'loader.params.scenes=[scene-1094]'
```

**Local** (Python ≥ 3.11): `pip install -e ".[vlm,similarity,dev]"`, then the same commands
without `docker compose run --rm app`.

| Command | What it does |
|---|---|
| `vlm-eval run-scenes -c configs/scenes/<run>.yaml` | Describe every scene (N frames × K views), write `scenes.jsonl`, evaluate, write `report.md` |
| `vlm-eval evaluate-scenes RUN_DIR` | Re-score a saved run (no inference) |
| `vlm-eval compare-scenes A B --out DIR` | Paired comparison of two models or prompts |
| `vlm-eval validate-judge RUN_DIR` | Check the claim judge on claims with known truth |
| `vlm-eval scene-leaderboard RUN_DIR...` | All runs side by side |
| `vlm-eval run` / `evaluate` / `compare` / `leaderboard` / `gate` | Frame-level equivalents and the quality gate |
| `./scripts/run_all.sh` | Reproduce every result in this README |

**Runtime.** About 10–13 s per 6-image call on an Apple M1 GPU, so 5–7 minutes per scene
run (30 calls). On CPU in Docker, expect several times longer. Use
`--set 'loader.params.scenes=[scene-1094]'` (3 calls) for a quick check. VLM answers are
cached under a key built from the model, its settings, the prompt and the exact frames, so
re-running a config only re-scores.

## Code structure

```
src/vlm_eval/
  loaders/          scene_loader.py (views), nuscenes_loader.py (frames)
  gt/               scene_facts.py (fact sheet), nuscenes_gt.py (the only nuScenes-specific code)
  vlm/              hf_backend.py, mock.py, cache.py (content-keyed), factory.py
  prompting.py      prompt strategies; prompts/ holds versioned templates
  scene_pipeline.py load -> describe views -> combine -> write
  judge.py          NLI judge behind a swappable TextJudge interface
  parsing/          claim splitting, claim extraction, JSON repair
  evaluation/       scene_metrics, scene_report, scene_compare, judge_validation,
                    frame metrics/, compare, leaderboard, gate, stats
  taxonomies/       driving.yaml: object types, values, synonyms, fact-sentence wording
  manifest.py       run manifest
configs/scenes/     one YAML per scene run (configs/ for frame runs)
tests/              139 tests
```

**Extending.** Datasets, models, judges and metrics are chosen by name in the config
through small registries. A new dataset needs a scene loader and a fact-sheet builder. A
new label set needs a taxonomy YAML. A new model is usually just a different `model_id`.

**At scale** (not built here):
- Evaluation would run on a fixed, labelled set of a few hundred to a few thousand scenes.
  Production data has no labels, so it would be monitored with label-free signals such as
  agreement between views.
- Model answers would go in the same content-keyed cache, moved to an object store.
- Results would be ingested into a queryable store for analysis across runs.
- A model or prompt change would be gated in CI against the current baseline.
