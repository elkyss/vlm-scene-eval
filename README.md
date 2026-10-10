# VLM scene-description evaluation on nuScenes

A small pipeline that describes nuScenes driving frames with a vision-language model (VLM)
and, more importantly, **measures how good those descriptions are**. It is written as a
small version of a model-evaluation system: any model, prompt or dataset plugs in, every
run is reproducible from a config file, and runs can be compared with statistics and
checked by a pass/fail quality gate.

```
frames ──► VLM ──► description + facts ──► check each fact against GT ──► report / compare / gate
 (loader)  (backend +   (parser)            (annotation-derived ground truth)
            prompt strategy)
```

**Results at a glance** are in [Results](#results). Each run's full report is in
`outputs/<run>/report.md`, and the results are committed so they can be read without
running anything.

> nuScenes data and the image thumbnails in `outputs/*/thumbs/` are © Motional, used under
> [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) for non-commercial evaluation.

---

## Quick start

### Docker (recommended)

1. Download **nuScenes v1.0-mini** (free account): <https://www.nuscenes.org/nuscenes#download>,
   under *Full dataset (v1.0) → Mini*, file `v1.0-mini.tgz` (about 4 GB).
2. Extract it so that the folder `data/nuscenes/v1.0-mini` exists:

```bash
mkdir -p data/nuscenes && tar -xzf v1.0-mini.tgz -C data/nuscenes
```

3. Build the image and run the tests:

```bash
docker compose build
```

```bash
docker compose run --rm --entrypoint make app test
```

4. Run the pipeline. The oracle mock needs no model download and every metric should come
   out at about 100%:

```bash
docker compose run --rm app run -c configs/mock_oracle.yaml
```

5. Run a real VLM. It downloads SmolVLM-500M (about 1 GB) on first use, then takes a few
   seconds per model call on CPU:

```bash
docker compose run --rm app run -c configs/smolvlm_v1.yaml
```

Outputs go to `outputs/<run_id>/`. Model weights are cached in a Docker volume, and raw VLM
answers are cached in `.cache/`, so rerunning a config does not run inference again. The
image (Python 3.12, CPU-only torch) installs the exact library versions the results were
produced with (`constraints.txt`).

### Local (Python ≥ 3.11)

```bash
python -m venv .venv && source .venv/bin/activate && pip install -e ".[vlm,similarity,dev]"
```

```bash
make test && make run CONFIG=configs/smolvlm_v3.yaml
```

On Apple Silicon or with CUDA the backend uses the GPU automatically.

### Commands

| Command | What it does |
|---|---|
| `vlm-eval run -c CONFIG [--set key=value]` | Load frames, call the VLM, write `predictions.jsonl/.csv`, evaluate, write `report.md` |
| `vlm-eval evaluate RUN_DIR` | Recompute metrics and the report from saved predictions (no inference) |
| `vlm-eval compare RUN_A RUN_B` | Paired comparison of two VLMs or two prompts on the same frames |
| `vlm-eval gate RUN_DIR [--baseline RUN]` | Pass/fail against `configs/gates.yaml`; exits 1 on failure (for CI) |
| `vlm-eval leaderboard RUN_DIR...` | Headline metrics of many runs side by side (`outputs/leaderboard.md`) |
| `vlm-eval gt-export RUN_DIR` / `gt-agreement` | Export a sheet for checking the ground truth by eye, then score agreement |
| `./scripts/run_all.sh` | Reproduce every run and comparison in this README |

---

## The pipeline (the four steps of the assignment)

1. **Load a scene.** `NuScenesLoader` takes *K* evenly spaced keyframes per scene
   (default 5, so 50 frames over the 10 mini scenes; `frames_per_scene: null` uses all
   404) from **`CAM_FRONT`**. Why the front camera: it is where a driver looks and what a
   scene description is about, and a single 1600×900 image suits small VLMs. Other cameras
   are a config option (`cameras: [...]`), and the backend accepts several images.
2. **Run a VLM.** `HFVisionChatBackend` runs any Hugging Face image-text-to-text model.
   I used **SmolVLM-500M-Instruct** (main, runs on CPU) and **Qwen2-VL-2B-Instruct**
   (second model, for comparison). Decoding is greedy, so runs are deterministic.
   *How* the VLM is asked is a separate, swappable **prompt strategy**:
   - `v1_open`: "describe the scene" in free text. Facts are extracted from the prose.
   - `v2_structured`: one prompt asking for a JSON object with every fact.
   - `v3_questionnaire`: an open description plus one short question per fact (VQA style).
3. **Output the results.** `predictions.jsonl` has one entry per frame: the raw output,
   description, parsed facts, model, prompt version (with a content hash) and latency.
   `predictions.csv` is a flat version of the same. The ground truth used is saved next to
   it (`ground_truth.jsonl`), so a run directory is self-contained.
4. **Evaluate.** Nine pluggable metric families produce `metrics.json` and `report.md`, which
   also includes thumbnails of the worst frames.

---

## How the evaluation works

### What the outputs are compared against

Text-to-text similarity with a reference sentence is **not** the main metric. It rewards
sounding like the reference, not being right: *"no pedestrians at night"* and *"many
pedestrians at night"* are very similar sentences, yet one is wrong. And the only human
text in nuScenes, `scene.description`, describes a whole 20-second scene in keywords
("Night, after rain, many peds, PMD, jaywalker…"), not the frame the VLM sees.

Instead, each description is turned into **checkable facts**, and every fact is checked
against **ground truth derived from the nuScenes annotations**:

| Fact | Ground truth source | Rule |
|---|---|---|
| Which object classes are present (car, truck, bus, pedestrian, two-wheeler, traffic cone, barrier) | 3D boxes projected into `CAM_FRONT` (`get_sample_data(..., BoxVisibility.ANY)`) | **Strict** set: box ≥ 40% visible (nuScenes visibility level ≥ 2) and ≤ 50 m away. **Loose** set: any box in the image |
| How many (bucketed: 0 / 1-2 / 3-5 / 6+) | Same boxes, counted | Exact counts are unrealistic for a VLM and noisy in the GT, so buckets are used |
| Time of day | `scene.description` contains "night" | Scene-level label |
| Road condition | `scene.description` contains "rain" | Scene-level label |
| Scene type (road / intersection / parking lot) | `scene.description` keywords | Scene-level label |
| Traffic side (left / right) | `log.location` (Singapore drives on the left, Boston on the right) | |

The VLM's facts come from its JSON or questionnaire answers when the prompt asks for them,
and from a rule-based **claim extractor** run on the free text otherwise. The extractor
uses taxonomy synonyms ("people" → pedestrian), count words ("several" → 3-5) and handles
negation ("no pedestrians" is not a pedestrian claim). It is unit-tested on its own.

### Metrics

| Metric | Question it answers |
|---|---|
| **Object presence**: precision, recall, F1 per class, micro and macro | Does it **invent** objects (precision; hallucination rate = claimed class with *no* box in view) or **miss** clearly visible ones (recall; omission rate)? Precision is lenient: naming a car that is in view but far or occluded is not a hallucination (the strict version is also reported) |
| Recall by visibility and distance bin | *Which* objects does it miss: small, far, occluded? |
| **Counting**: exact and ±1-bucket accuracy | Given it saw the class, does it get the quantity right? |
| **Scene attributes**: accuracy, **balanced accuracy**, confusion matrix, **majority baseline** | 70% of frames are daytime, so "always day" scores 70% raw accuracy. Balanced accuracy and the baseline expose that |
| **Free-text faithfulness** | Are the claims in the prose true? Does the prose contradict the model's own structured answer? |
| **Slices** by time of day, city and scene type | Is the model fine by day but failing at night? (An average would hide that) |
| **Temporal consistency** | Do answers flip between neighbouring frames of one scene more often than the GT does? |
| **Format** | Valid structured output, empty or duplicate descriptions, **repetition loops**, latency |
| **Error taxonomy** | Counts of each mistake type, plus the worst frames with thumbnails |
| **Similarity** (secondary) | Embedding cosine and keyword recall against `scene.description`, plus their **correlation with the claim-level F1**, to show whether similarity tracks correctness |

### Mistakes a VLM makes, and how each is caught

| Mistake | Caught by |
|---|---|
| Hallucinated object ("a bus" on an empty street) | Object precision; `hallucination:<class>` tags |
| Missed object, especially small, far or occluded | Recall; recall by visibility and distance |
| Wrong count | Counting accuracy; `count:<class>` tags |
| Wrong scene property (day vs night, wet road, traffic side) | Attribute accuracy against a majority baseline; confusion matrices |
| Generic boilerplate ("The road is empty" for every frame) | Duplicate-description rate; low recall |
| Repetition loops ("There are two people…" ×5) | Repetition-loop rate |
| Ignoring the output format, or copying the prompt template | Parse-success rate; template-echo detection |
| Prose that contradicts its own structured answer | Text vs. structured contradiction rate |
| Prompt-induced hallucination (listing classes in the prompt makes the model repeat them) | Comparing prompts on the same frames (`vlm-eval compare`) |
| Unstable answers across neighbouring frames | Temporal consistency vs. GT flip rate |

### Is the ground truth itself right?

Metrics are only as good as their reference, so I checked it. `vlm-eval gt-export`
samples frames (13 frames × 10 labels = 130 labels). I labelled them by looking at the
images, and `vlm-eval gt-agreement` scores how often the automatic GT matches
(`annotations/gt_audit.csv`, with a comment for each disagreement):

| Field | Labels checked | Agreement |
|---|---|---|
| Objects (presence per class) | 91 | 89.0% |
| Time of day | 13 | 100.0% |
| Road condition | 13 | 92.3% |
| Scene type | 13 | **53.8%** |
| All | 130 | 86.9% |

**Scene type is unreliable as frame-level GT.** `scene.description` labels the whole
20-second scene ("Wait at intersection…"), but many individual frames show a plain road.
Its metric is reported, but flagged as indicative only. Object disagreements are mostly
borderline cases: far objects and barriers on the median.

### Sanity checks of the evaluation itself

- An **oracle** mock VLM that answers the GT gets 100% on every claim-based metric. That
  shows the metric code is correct.
- An **always-"car"** mock and an **empty** mock produce exactly the expected failure
  pattern (tested).
- The oracle is also evidence against similarity metrics: a *perfect* answer only reaches
  **0.48 cosine similarity and 46% keyword recall** against
  `scene.description`.

### Comparing two VLMs, or two prompts

`vlm-eval compare RUN_A RUN_B` pairs the runs frame by frame and reports, for each metric:
A, B, Δ, a **95% bootstrap CI that resamples whole scenes** (frames from the same 20 s
scene are correlated, so resampling frames would overstate confidence), and **McNemar's
exact test** on paired per-frame correctness. With 10 scenes the CIs are wide. A
difference whose CI crosses 0 is reported as inconclusive rather than as a win. The report
also lists the frames where the two runs disagree most, for qualitative review. Latency is
compared too, since a prompt that is 12× more expensive needs to earn it.

---

## Results

All runs use the same 50 `CAM_FRONT` frames (5 per scene, 10 scenes), greedy decoding
and the configs in `configs/`. Reproduce everything with `./scripts/run_all.sh`
(`outputs/leaderboard.md`, per-run `report.md`, `compare_*/compare_report.md`).

| Run | Object F1 | Precision | Recall | Halluc. rate | Count exact | Day/night bal. acc. | Valid output | s / frame | Gate |
|---|---|---|---|---|---|---|---|---|---|
| *blind baseline (claims "car" everywhere)* | *54.7%* | | | | | | | | |
| *mock: always "car + pedestrian, day"* | *64.1%* | *71.7%* | *57.9%* | *26.0%* | | *50.0%* | | | |
| SmolVLM-500M · v1 open text | 67.8% | **89.9%** | 54.4% | **9.6%** | 53.2% | 3.3%¹ | 100% | **1.7** | fail |
| SmolVLM-500M · v2 JSON | 0.0% | – | 0.0% | – | – | 20.0% | 48% | 2.1 | fail |
| SmolVLM-500M · v2b JSON (placeholders) | 0.0% | – | 0.0% | – | – | 0.0% | 0% | 1.5 | fail |
| SmolVLM-500M · v3 questionnaire | 63.4% | 50.3% | **86.0%** | 46.0% | 68.4% | **100%** | 100% | 17.4 | fail |
| Qwen2-VL-2B · v2 JSON | 59.1% | 83.9% | 45.6% | 15.2% | 51.9% | **100%** | 96% | 4.1 | pass |
| Qwen2-VL-2B · v2b JSON (placeholders) | 35.1% | 76.5% | 22.8% | 21.1% | **80.8%** | **100%** | 100% | 4.7 | fail |
| **Qwen2-VL-2B · v3 questionnaire** | **73.4%** | 70.7% | 76.3% | 27.9% | 67.8% | **100%** | 100% | 18.1 | pass |

¹ SmolVLM's free text almost never says whether it is day or night (2% coverage). When it
does, it is right. "Unanswered" counts as wrong, and the report shows coverage separately.

### Summary: how well did the VLMs do?

**SmolVLM-500M (the main, CPU-friendly model) is only marginally useful as a scene
describer.** Its free-text descriptions are *precise but thin*. 90% of the object classes
it names are really there, but it misses about half of what is visible, rarely states
time of day or road condition, and reuses stock phrases ("The road is empty") even on busy
frames. Its object F1 (68%) is only 13 points above a blind baseline that never looks at
the image (55%), and it is statistically indistinguishable from a mock that always says
"car and pedestrian" (64%; Δ +3.7 pts, 95% CI [−3.9, +11.9]). It **cannot produce structured output**: with a JSON prompt it
copies the template (48% valid, F1 0), and with a schema of placeholders it answers "3."
to every frame. Asked one question at a time (v3) it becomes *recall-heavy*: it finds 86%
of visible classes and gets day/night 100% right, but it says "yes" to leading questions.
46% of the classes it claims are not there, mostly barriers, trucks and cones.

**Qwen2-VL-2B with the questionnaire is the best configuration tested**: object F1 73% vs.
SmolVLM's 63% on the same prompt (**+10 pts, 95% CI [+6, +14]**). It hallucinates far fewer
trucks (+42 pts presence accuracy, McNemar p < 0.001) and barriers (+20, p = 0.01). It
still claims a class that is not in view 28% of the time and misses 24% of visible
classes. That is good enough to *search or triage* scenes, not to *label* them without
verification.

### What the evaluation revealed

1. **Prompt design matters as much as model choice.** For Qwen, the questionnaire beats
   JSON by +14 pts F1 (CI [+6, +22]). But it costs 4× the latency (12 calls per frame),
   and it makes barrier answers worse (−38 pts, p < 0.001) because of leading-question bias.
2. **A hypothesis tested, and rejected.** Qwen's JSON answers often contradicted its own
   description (23% of prose object claims denied by the JSON). I suspected the template's
   example values (`"car": "0"`) anchored the model, so v2b replaced them with neutral
   `<0|1-2|3-5|6+>` placeholders. **It made things worse**: F1 −24 pts (CI [−40, −12]),
   car presence −44 pts, contradictions up to 74%. The model now picks the first option,
   "0". The quality gate blocks this change against the v2 baseline. Without paired
   statistics it would have been easy to ship a plausible-sounding "fix".
3. **Baselines change the story.** Raw numbers look decent until put next to the blind
   baseline (55% F1, because 88% of frames contain cars) and the majority baseline for
   attributes (70% of frames are daytime).
4. **Errors depend on conditions.** SmolVLM v3 drops from 68% F1 by day to 51% at night.
   But all night frames come from one location (Holland Village), so night and location
   are **confounded** in mini. The slice is a lead to investigate, not a conclusion.
5. **Recall falls with distance** (Qwen v3: 91% for objects within 15 m, 73% beyond
   50 m), **but hardly with visibility level** (81% at 0-40% visible vs. 85% at 80-100%).
   That is a limit of my metric, not good occlusion handling: recall is measured per
   class, and an occluded car is usually in a frame that also has a clearly visible car.
   Measuring occlusion robustness needs instance-level (localised) claims.
6. **Text similarity does not measure correctness.** Across the real models, Spearman
   correlation between embedding similarity to `scene.description` and per-frame object F1
   is between 0.01 and 0.22. Even the perfect oracle only reaches 0.48 cosine.

---

## Assumptions

- **Unit of evaluation = one CAM_FRONT keyframe.** "One entry per scene" in the
  assignment is met by aggregating frames per scene. Per-frame evaluation is needed
  because the visible content changes within a 20 s scene.
- **5 evenly spaced keyframes per scene (50 frames)** by default, to keep CPU runtime
  reasonable. Statistical power is limited by the **10 scenes**, not the frame count.
- **A box counts as "visible"** if nuScenes visibility ≥ 40% and the box is within 50 m.
  A VLM is not penalised for naming a class whose box is in the image but outside that
  filter (lenient precision).
- **Classes are coarse** (7 classes). Fine nuScenes categories are mapped, e.g. vans are
  cars, construction vehicles are trucks, scooters and bicycles are two-wheelers.
  Rare categories (debris, animals) are ignored.
- **Scene-level labels** (time of day, road condition, scene type) come from keywords in
  `scene.description` and are applied to every frame of the scene. The audit shows where
  this breaks (scene type).
- **Mini has no rain** (one "after rain" scene, which is counted as wet) and only 3 night
  scenes, so weather and night results rest on very few scenes.
- **Unanswered fields count as wrong** in accuracy. Answered-only accuracy and coverage
  are reported separately.
- **Small, local, open models only.** Nothing needs an API key, and everything runs in
  Docker on CPU. Greedy decoding gives determinism.

## Limitations and next steps

- **The claim extractor is rule-based.** It is transparent and tested, but it will miss
  paraphrases and complex negation. Next step: an LLM-based claim extractor or judge,
  **calibrated against human labels** before being trusted. The `Metric` interface makes
  it a drop-in addition.
- **Spatial claims are not checked** ("a pedestrian on the left"). The projected 2D box
  centres are available, so left/centre/right claims could be scored the same way.
- **Object state** ("parked" vs "moving") is available in the annotation attributes but
  not scored yet.
- **10 scenes** means wide confidence intervals. The full nuScenes trainval (850 scenes)
  would work unchanged: point `version` at it.
- The ground-truth audit was done by one person (me) on 13 frames. A real audit would use
  two annotators and report inter-annotator agreement.
- **Prompt biases are not fully explored.** The v2b result suggests first-option bias. The
  next experiment is to reverse the option order and see whether answers follow it.

## From this take-home to an evaluation system

This is deliberately a small version of what a team evaluating models across many drives
would run. The pieces that carry over:

- **Generic core, thin adapters.** Datasets plug in through `SceneLoader` and
  `GTProvider`, models through `VLMBackend`, prompting through `PromptStrategy`, and the
  label vocabulary through a **taxonomy YAML** (`taxonomies/driving.yaml`). Metrics,
  parsers, reports and gates never mention nuScenes or specific classes.
- **Reproducibility.** Every run is a config, and every prediction records model, prompt
  version (content hash) and latency. A run directory contains its own GT and config, and
  raw answers are cached, so re-evaluating with a new metric costs no inference.
- **Regression gates in CI** (`vlm-eval gate`). Absolute floors plus max regression vs.
  the current production baseline, so a model or prompt change cannot silently get worse.
- **Slices as first-class results.** Release decisions should look at the worst slice
  (night, a new city, rain), not only the mean.
- **Trust the reference before trusting the metric.** GT audits, agreement per field, and
  marking low-trust fields.
- **What I would add next at scale:** a proper run registry (today: run folders plus
  `vlm-eval leaderboard`); dataset
  and GT versioning; scenario mining (find the frames where a model fails and add them to
  a regression set); a calibrated LLM judge for open-ended claims; drift monitoring on
  production logs; cost and latency budgets per frame.

---

## Code structure

```
src/vlm_eval/
  domain.py            data models shared by all stages (Sample, GroundTruth, Prediction, ...)
  taxonomy.py          label vocabulary loader; taxonomies/driving.yaml holds classes, values, synonyms
  config.py            typed YAML run config (pydantic)
  registry.py          name -> class registries; components are chosen from config
  pipeline.py          orchestrator: load -> describe -> write -> evaluate (dependency-injected)
  loaders/             SceneLoader protocol + NuScenesLoader
  gt/                  GTProvider protocol + NuScenesGTProvider (the only nuScenes-aware code)
  vlm/                 VLMBackend protocol, HF backend, mock backends, CachedBackend decorator
  prompting.py         PromptStrategy: single prompt (free text / JSON) or questionnaire
  prompts/             versioned prompt templates (rendered from the taxonomy)
  parsing/             JSON repair + normalisation, free-text claim extraction, short answers
  writers.py           JSONL / CSV writers
  evaluation/
    metrics/           one module per metric family, each a registered Metric
    evaluator.py       runs the configured metrics
    report.py          markdown report
    compare.py         paired comparison (scene bootstrap, McNemar)
    leaderboard.py     headline metrics across runs
    gate.py            CI quality gate
    gt_audit.py        manual GT audit export / agreement
    stats.py           dependency-free statistics helpers
  cli.py               Typer CLI
configs/               one YAML per run + gates.yaml
tests/                 unit tests per component, end-to-end with mock VLMs, real-data tests
```

**Extending it**

| To add… | Do this |
|---|---|
| A model | Use the `hf` backend with a new `model_id`, or implement `generate(VLMRequest) -> VLMResponse` and `@BACKENDS.register("name")` |
| A prompt | Add `prompts/<name>.txt` (or a `.yaml` questionnaire) and set `prompt: <name>` |
| A metric | Implement `compute(pairs) -> MetricResult`, `@METRICS.register("name")`, then list it under `metrics:` |
| A dataset | Implement a `SceneLoader` and a `GTProvider`, and register them |
| A label set | Write a new taxonomy YAML and set `taxonomy: <name or path>` |

## How the code was tested

- **113 tests** (`make test`) covering:
  - Unit tests per component: the claim extractor (counts, negation, clause boundaries,
    "bus stop" ≠ bus, ego-vehicle phrases), JSON repair (fences, quotes, truncation,
    template echo), short-answer parsing, every metric on **hand-computed examples**,
    statistics helpers, the registry, config overrides and the gate.
  - **End-to-end tests with mock VLMs** on in-memory fake data: oracle → 100%, empty →
    0 recall, always-car → the expected precision and recall pattern. They also check
    saving, reloading, comparing and caching.
  - **Real-data tests** (skipped if `data/` is missing): the loader on mini, GT invariants
    (strict ⊆ loose; stricter filters never add objects), and a known night frame.
- Testing found real bugs, several of which would have silently distorted results:
  - A class present in the GT but never predicted got an undefined F1 and dropped out of
    macro-F1, which inflated scores. F1 is now 2TP/(2TP+FP+FN).
  - When a model echoed the JSON template, the claim extractor read `"car": "0"` as a car
    claim. SmolVLM v2 scored 11.6% F1 instead of the correct 0%.
  - "The image is taken from the front of a car" (the ego vehicle) counted as a car.
  - Spearman correlation mishandled ties and constant inputs.
  - Running a real model inside Docker (not only the mock) exposed a torch/transformers
    version mismatch. The image now installs pinned versions (`constraints.txt`).
- `ruff` (lint and format) and `mypy` run clean. Pre-commit config is included.
