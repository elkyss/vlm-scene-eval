# VLM evaluation report: `SmolVLM-500M-Instruct` with prompt `v2b_structured@db8db50a`

50 frames from 10 scenes. Ground truth comes from nuScenes annotations (objects), `scene.description` (time of day, road condition, scene type) and `log.location` (traffic side).

## Headline numbers

| Metric | Value |
|---|---|
| Object presence: micro F1 | 0.0% |
|   ↳ blind baseline (always claims the frequent classes, never looks) | 54.7% |
| Object presence: precision | – |
| Object presence: recall | 0.0% |
| Hallucination rate (claimed class with no box in view) | – |
| Omission rate (clearly visible class not mentioned) | 100.0% |
| Count bucket accuracy (exact) | – |
| Count bucket accuracy within ±1 | – |
| Scene attributes: mean balanced accuracy | 0.0% |
| Free-text claims: micro F1 | 0.0% |
| Prose claims an object the structured answer denies | – |
| Valid structured output | 0.0% |
| Mean latency per frame (s) | 1.49 |

## How far to trust the ground truth

A sample of frames was labelled by eye and compared with the automatic GT. Metrics on a field cannot be trusted beyond its agreement: treat low-agreement fields as indicative only.

| Field | Labels checked | Auto vs. manual agreement |
|---|---|---|
| all | 130 | 86.9% |
| objects | 91 | 89.0% |
| road_condition | 13 | 92.3% |
| scene_type | 13 | 53.8% |
| time_of_day | 13 | 100.0% |

## Objects: hallucination vs. omission

Per frame and class: claimed vs. present (≥40% visible, ≤50 m). `FP` = claimed but no box of that class anywhere in the image (hallucination); `FP far` = a box exists but is far or mostly occluded (excused in *precision*, counted in *precision strict*).

| Class | GT frames | TP | FP | FP far | FN | Precision | Precision strict | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| car | 44 | 0 | 0 | 0 | 44 | – | – | 0.0% | 0.0% |
| truck | 12 | 0 | 0 | 0 | 12 | – | – | 0.0% | 0.0% |
| bus | 7 | 0 | 0 | 0 | 7 | – | – | 0.0% | 0.0% |
| pedestrian | 22 | 0 | 0 | 0 | 22 | – | – | 0.0% | 0.0% |
| two_wheeler | 12 | 0 | 0 | 0 | 12 | – | – | 0.0% | 0.0% |
| traffic_cone | 8 | 0 | 0 | 0 | 8 | – | – | 0.0% | 0.0% |
| barrier | 9 | 0 | 0 | 0 | 9 | – | – | 0.0% | 0.0% |

**Recall by object visibility** (all annotated objects in view)

| Visibility | Objects | Recall |
|---|---|---|
| 0-40% | 165 | 0.0% |
| 40-60% | 69 | 0.0% |
| 60-80% | 63 | 0.0% |
| 80-100% | 322 | 0.0% |

**Recall by distance**

| Distance | Objects | Recall |
|---|---|---|
| 0-15m | 68 | 0.0% |
| 15-30m | 197 | 0.0% |
| 30-50m | 189 | 0.0% |
| 50m+ | 165 | 0.0% |

## Counting

Only frames where GT and prediction both say the class is present (buckets 1-2 / 3-5 / 6+).

| Class | Frames | Exact bucket | Within ±1 bucket |
|---|---|---|---|

## Scene attributes

Accuracy counts unanswered fields as wrong. Compare against the majority-class baseline: with a skewed GT, a model that always says "day" looks good on raw accuracy but gets 50% balanced accuracy.

| Attribute | Accuracy | Balanced acc. | Majority baseline | Answered | GT distribution |
|---|---|---|---|---|---|
| time_of_day | 0.0% | 0.0% | 70.0% | 0.0% | day: 35, night: 15 |
| road_condition | 0.0% | 0.0% | 90.0% | 0.0% | dry: 45, wet: 5 |
| scene_type | 0.0% | 0.0% | 40.0% | 0.0% | intersection: 20, road: 20, parking_lot: 10 |
| traffic_side | 0.0% | 0.0% | 60.0% | 0.0% | left: 30, right: 20 |

Confusion:
- **time_of_day**: GT day → unanswered: 35; GT night → unanswered: 15
- **road_condition**: GT dry → unanswered: 45; GT wet → unanswered: 5
- **scene_type**: GT intersection → unanswered: 20; GT parking_lot → unanswered: 10; GT road → unanswered: 20
- **traffic_side**: GT left → unanswered: 30; GT right → unanswered: 20

## Free-text faithfulness

| Metric | Value |
|---|---|
| Claims in prose: precision | – |
| Claims in prose: recall | 0.0% |
| Claims in prose: hallucination rate | – |
| Prose object claims the structured answer denies | – |
| Prose ↔ structured attribute agreement | – |

Claims are extracted from the description with a rule-based lexicon (see parsing/text_claims.py). Agreement is computed for structured answers (JSON or questionnaire).

## Slices

Headline metrics per ground-truth condition. Slices are defined on ground truth. Small slices have wide uncertainty; check the frame count before drawing conclusions.

**By time_of_day**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| day | 35 | 0.0% | 0.0% | – | 0.0% |
| night | 15 | 0.0% | 0.0% | – | 0.0% |

**By location**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| boston-seaport | 20 | 0.0% | 0.0% | – | 0.0% |
| singapore-hollandvillage | 15 | 0.0% | 0.0% | – | 0.0% |
| singapore-onenorth | 5 | 0.0% | 0.0% | – | 0.0% |
| singapore-queenstown | 10 | 0.0% | 0.0% | – | 0.0% |

**By scene_type**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| intersection | 20 | 0.0% | 0.0% | – | 0.0% |
| parking_lot | 10 | 0.0% | 0.0% | – | 0.0% |
| road | 20 | 0.0% | 0.0% | – | 0.0% |

## Temporal consistency

How often a label changes between consecutive sampled frames of the same scene.

| Label | Model flip rate | GT flip rate |
|---|---|---|
| time_of_day | 0.0% | 0.0% |
| road_condition | 0.0% | 0.0% |
| scene_type | 0.0% | 0.0% |
| traffic_side | 0.0% | 0.0% |
| obj:car | 0.0% | 20.0% |
| obj:truck | 0.0% | 37.5% |
| obj:bus | 0.0% | 15.0% |
| obj:pedestrian | 0.0% | 22.5% |
| obj:two_wheeler | 0.0% | 32.5% |
| obj:traffic_cone | 0.0% | 15.0% |
| obj:barrier | 0.0% | 10.0% |

Scene-level GT attributes never change within a scene, so any attribute flip by the model is an inconsistency.

## Similarity to the human reference (secondary)

`scene.description` describes a 20 s scene in keywords, not this frame, so similarity is a weak proxy. A low correlation with the claim-level F1 shows that similarity does not track correctness.

| Metric | Value |
|---|---|
| Reference keyword recall (classes in scene.description that are mentioned) | 0.0% |
| Mean embedding cosine to scene.description | 0.15 |
| Pearson(cosine, frame object F1) | 0.10 |
| Spearman(cosine, frame object F1) | 0.08 |

## Error taxonomy

Frames with at least one error: 100.0%

| Error family | Count |
|---|---|
| omission | 114 |
| format | 50 |

| Most frequent errors | Count |
|---|---|
| format:invalid_output | 50 |
| omission:car | 44 |
| omission:pedestrian | 22 |
| omission:truck | 12 |
| omission:two_wheeler | 12 |
| omission:barrier | 9 |
| omission:traffic_cone | 8 |
| omission:bus | 7 |

### Worst frames

**scene-0061 / frame 10**: `format:invalid_output`, `omission:car`, `omission:truck`, `omission:pedestrian`, `omission:traffic_cone`, `omission:barrier`

![023c4df2d451409881d8e6ea82f14704](thumbs/023c4df2d451409881d8e6ea82f14704.jpg)

> 3.

GT objects: `{'pedestrian': '6+', 'car': '3-5', 'barrier': '3-5', 'truck': '1-2', 'traffic_cone': '3-5'}`, predicted: `{}`

**scene-0061 / frame 19**: `format:invalid_output`, `omission:car`, `omission:truck`, `omission:pedestrian`, `omission:traffic_cone`, `omission:barrier`

![b26e791522294bec90f86fd72226e35c](thumbs/b26e791522294bec90f86fd72226e35c.jpg)

> 3.

GT objects: `{'truck': '3-5', 'traffic_cone': '6+', 'pedestrian': '1-2', 'barrier': '3-5', 'car': '1-2'}`, predicted: `{}`

**scene-0553 / frame 10**: `format:invalid_output`, `omission:car`, `omission:truck`, `omission:bus`, `omission:pedestrian`, `omission:barrier`

![8bf071b1b92c4ff1bd5016bfb30de3f7](thumbs/8bf071b1b92c4ff1bd5016bfb30de3f7.jpg)

> 3.

GT objects: `{'pedestrian': '1-2', 'barrier': '1-2', 'bus': '1-2', 'car': '1-2', 'truck': '1-2'}`, predicted: `{}`

**scene-0061 / frame 0**: `format:invalid_output`, `omission:car`, `omission:truck`, `omission:pedestrian`, `omission:barrier`

![ca9a282c9e77460f8360f564131a8af5](thumbs/ca9a282c9e77460f8360f564131a8af5.jpg)

> 3.

GT objects: `{'pedestrian': '3-5', 'barrier': '6+', 'car': '3-5', 'truck': '1-2'}`, predicted: `{}`

**scene-0103 / frame 29**: `format:invalid_output`, `omission:car`, `omission:truck`, `omission:pedestrian`, `omission:two_wheeler`

![6d9984d09d52479e837da2fd09e192cc](thumbs/6d9984d09d52479e837da2fd09e192cc.jpg)

> 3.

GT objects: `{'car': '6+', 'two_wheeler': '1-2', 'pedestrian': '1-2', 'truck': '1-2'}`, predicted: `{}`

**scene-0655 / frame 20**: `format:invalid_output`, `omission:car`, `omission:truck`, `omission:bus`, `omission:traffic_cone`

![0d7263a5b8264cad996582d6219ef1f2](thumbs/0d7263a5b8264cad996582d6219ef1f2.jpg)

> 3.

GT objects: `{'car': '1-2', 'bus': '1-2', 'traffic_cone': '1-2', 'truck': '1-2'}`, predicted: `{}`

**scene-0655 / frame 30**: `format:invalid_output`, `omission:truck`, `omission:bus`, `omission:pedestrian`, `omission:traffic_cone`

![b2e2ffeabf91451cb31a79649bfd95df](thumbs/b2e2ffeabf91451cb31a79649bfd95df.jpg)

> 3.

GT objects: `{'truck': '1-2', 'pedestrian': '1-2', 'traffic_cone': '3-5', 'bus': '1-2'}`, predicted: `{}`

**scene-0061 / frame 28**: `format:invalid_output`, `omission:car`, `omission:two_wheeler`, `omission:traffic_cone`

![0cd661df01aa40c3bb3a773ba86f753a](thumbs/0cd661df01aa40c3bb3a773ba86f753a.jpg)

> 3.

GT objects: `{'traffic_cone': '6+', 'two_wheeler': '1-2', 'car': '1-2'}`, predicted: `{}`
