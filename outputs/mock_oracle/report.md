# VLM evaluation report: `mock-oracle` with prompt `v2_structured@7f47e762`

50 frames from 10 scenes. Ground truth comes from nuScenes annotations (objects), `scene.description` (time of day, road condition, scene type) and `log.location` (traffic side).

## Headline numbers

| Metric | Value |
|---|---|
| Object presence: micro F1 | 100.0% |
|   ↳ blind baseline (always claims the frequent classes, never looks) | 54.7% |
| Object presence: precision | 100.0% |
| Object presence: recall | 100.0% |
| Hallucination rate (claimed class with no box in view) | 0.0% |
| Omission rate (clearly visible class not mentioned) | 0.0% |
| Count bucket accuracy (exact) | 100.0% |
| Count bucket accuracy within ±1 | 100.0% |
| Scene attributes: mean balanced accuracy | 100.0% |
| Free-text claims: micro F1 | 100.0% |
| Prose claims an object the structured answer denies | 0.0% |
| Valid structured output | 100.0% |
| Mean latency per frame (s) | 0.00 |

## Objects: hallucination vs. omission

Per frame and class: claimed vs. present (≥40% visible, ≤50 m). `FP` = claimed but no box of that class anywhere in the image (hallucination); `FP far` = a box exists but is far or mostly occluded (excused in *precision*, counted in *precision strict*).

| Class | GT frames | TP | FP | FP far | FN | Precision | Precision strict | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| car | 44 | 44 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| truck | 12 | 12 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| bus | 7 | 7 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| pedestrian | 22 | 22 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| two_wheeler | 12 | 12 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| traffic_cone | 8 | 8 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| barrier | 9 | 9 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |

**Recall by object visibility** (all annotated objects in view)

| Visibility | Objects | Recall |
|---|---|---|
| 0-40% | 165 | 87.9% |
| 40-60% | 69 | 92.8% |
| 60-80% | 63 | 100.0% |
| 80-100% | 322 | 93.8% |

**Recall by distance**

| Distance | Objects | Recall |
|---|---|---|
| 0-15m | 68 | 100.0% |
| 15-30m | 197 | 95.4% |
| 30-50m | 189 | 97.9% |
| 50m+ | 165 | 80.6% |

## Counting

Only frames where GT and prediction both say the class is present (buckets 1-2 / 3-5 / 6+).

| Class | Frames | Exact bucket | Within ±1 bucket |
|---|---|---|---|
| car | 44 | 100.0% | 100.0% |
| truck | 12 | 100.0% | 100.0% |
| bus | 7 | 100.0% | 100.0% |
| pedestrian | 22 | 100.0% | 100.0% |
| two_wheeler | 12 | 100.0% | 100.0% |
| traffic_cone | 8 | 100.0% | 100.0% |
| barrier | 9 | 100.0% | 100.0% |

## Scene attributes

Accuracy counts unanswered fields as wrong. Compare against the majority-class baseline: with a skewed GT, a model that always says "day" looks good on raw accuracy but gets 50% balanced accuracy.

| Attribute | Accuracy | Balanced acc. | Majority baseline | Answered | GT distribution |
|---|---|---|---|---|---|
| time_of_day | 100.0% | 100.0% | 70.0% | 100.0% | day: 35, night: 15 |
| road_condition | 100.0% | 100.0% | 90.0% | 100.0% | dry: 45, wet: 5 |
| scene_type | 100.0% | 100.0% | 40.0% | 100.0% | intersection: 20, road: 20, parking_lot: 10 |
| traffic_side | 100.0% | 100.0% | 60.0% | 100.0% | left: 30, right: 20 |

Confusion:
- **time_of_day**: GT day → day: 35; GT night → night: 15
- **road_condition**: GT dry → dry: 45; GT wet → wet: 5
- **scene_type**: GT intersection → intersection: 20; GT parking_lot → parking_lot: 10; GT road → road: 20
- **traffic_side**: GT left → left: 30; GT right → right: 20

## Free-text faithfulness

| Metric | Value |
|---|---|
| Claims in prose: precision | 100.0% |
| Claims in prose: recall | 100.0% |
| Claims in prose: hallucination rate | 0.0% |
| Prose object claims the structured answer denies | 0.0% |
| Prose ↔ structured attribute agreement | 100.0% |

Claims are extracted from the description with a rule-based lexicon (see parsing/text_claims.py). Agreement is computed for structured answers (JSON or questionnaire).

## Slices

Headline metrics per ground-truth condition. Slices are defined on ground truth. Small slices have wide uncertainty; check the frame count before drawing conclusions.

**By time_of_day**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| day | 35 | 100.0% | 100.0% | 0.0% | 100.0% |
| night | 15 | 100.0% | 100.0% | 0.0% | 100.0% |

**By location**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| boston-seaport | 20 | 100.0% | 100.0% | 0.0% | 100.0% |
| singapore-hollandvillage | 15 | 100.0% | 100.0% | 0.0% | 100.0% |
| singapore-onenorth | 5 | 100.0% | 100.0% | 0.0% | 100.0% |
| singapore-queenstown | 10 | 100.0% | 100.0% | 0.0% | 100.0% |

**By scene_type**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| intersection | 20 | 100.0% | 100.0% | 0.0% | 100.0% |
| parking_lot | 10 | 100.0% | 100.0% | 0.0% | 100.0% |
| road | 20 | 100.0% | 100.0% | 0.0% | 100.0% |

## Temporal consistency

How often a label changes between consecutive sampled frames of the same scene.

| Label | Model flip rate | GT flip rate |
|---|---|---|
| time_of_day | 0.0% | 0.0% |
| road_condition | 0.0% | 0.0% |
| scene_type | 0.0% | 0.0% |
| traffic_side | 0.0% | 0.0% |
| obj:car | 20.0% | 20.0% |
| obj:truck | 37.5% | 37.5% |
| obj:bus | 15.0% | 15.0% |
| obj:pedestrian | 22.5% | 22.5% |
| obj:two_wheeler | 32.5% | 32.5% |
| obj:traffic_cone | 15.0% | 15.0% |
| obj:barrier | 10.0% | 10.0% |

Scene-level GT attributes never change within a scene, so any attribute flip by the model is an inconsistency.

## Similarity to the human reference (secondary)

`scene.description` describes a 20 s scene in keywords, not this frame, so similarity is a weak proxy. A low correlation with the claim-level F1 shows that similarity does not track correctness.

| Metric | Value |
|---|---|
| Reference keyword recall (classes in scene.description that are mentioned) | 45.5% |
| Mean embedding cosine to scene.description | 0.48 |
| Pearson(cosine, frame object F1) | – |
| Spearman(cosine, frame object F1) | – |

## Error taxonomy

Frames with at least one error: 0.0%

| Error family | Count |
|---|---|

| Most frequent errors | Count |
|---|---|

### Worst frames
