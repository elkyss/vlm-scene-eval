# VLM evaluation report: `SmolVLM-500M-Instruct` with prompt `v1_open@14073038`

50 frames from 10 scenes. Ground truth comes from nuScenes annotations (objects), `scene.description` (time of day, road condition, scene type) and `log.location` (traffic side).

## Headline numbers

| Metric | Value |
|---|---|
| Object presence: micro F1 | 67.8% |
|   ↳ blind baseline (always claims the frequent classes, never looks) | 54.7% |
| Object presence: precision | 89.9% |
| Object presence: recall | 54.4% |
| Hallucination rate (claimed class with no box in view) | 9.6% |
| Omission rate (clearly visible class not mentioned) | 45.6% |
| Count bucket accuracy (exact) | 53.2% |
| Count bucket accuracy within ±1 | 88.7% |
| Scene attributes: mean balanced accuracy | 14.2% |
| Free-text claims: micro F1 | 67.8% |
| Prose claims an object the structured answer denies | – |
| Valid structured output | 100.0% |
| Mean latency per frame (s) | 1.74 |

## Objects: hallucination vs. omission

Per frame and class: claimed vs. present (≥40% visible, ≤50 m). `FP` = claimed but no box of that class anywhere in the image (hallucination); `FP far` = a box exists but is far or mostly occluded (excused in *precision*, counted in *precision strict*).

| Class | GT frames | TP | FP | FP far | FN | Precision | Precision strict | Recall | F1 |
|---|---|---|---|---|---|---|---|---|---|
| car | 44 | 44 | 3 | 3 | 0 | 93.6% | 88.0% | 100.0% | 96.7% |
| truck | 12 | 2 | 1 | 0 | 10 | 66.7% | 66.7% | 16.7% | 26.7% |
| bus | 7 | 2 | 1 | 0 | 5 | 66.7% | 66.7% | 28.6% | 40.0% |
| pedestrian | 22 | 10 | 1 | 1 | 12 | 90.9% | 83.3% | 45.5% | 60.6% |
| two_wheeler | 12 | 1 | 1 | 0 | 11 | 50.0% | 50.0% | 8.3% | 14.3% |
| traffic_cone | 8 | 2 | 0 | 0 | 6 | 100.0% | 100.0% | 25.0% | 40.0% |
| barrier | 9 | 1 | 0 | 0 | 8 | 100.0% | 100.0% | 11.1% | 20.0% |

**Recall by object visibility** (all annotated objects in view)

| Visibility | Objects | Recall |
|---|---|---|
| 0-40% | 165 | 64.8% |
| 40-60% | 69 | 73.9% |
| 60-80% | 63 | 60.3% |
| 80-100% | 322 | 68.3% |

**Recall by distance**

| Distance | Objects | Recall |
|---|---|---|
| 0-15m | 68 | 75.0% |
| 15-30m | 197 | 74.1% |
| 30-50m | 189 | 64.6% |
| 50m+ | 165 | 58.8% |

## Counting

Only frames where GT and prediction both say the class is present (buckets 1-2 / 3-5 / 6+).

| Class | Frames | Exact bucket | Within ±1 bucket |
|---|---|---|---|
| car | 44 | 54.5% | 93.2% |
| truck | 2 | 50.0% | 100.0% |
| bus | 2 | 100.0% | 100.0% |
| pedestrian | 10 | 50.0% | 80.0% |
| two_wheeler | 1 | 100.0% | 100.0% |
| traffic_cone | 2 | 0.0% | 50.0% |
| barrier | 1 | 0.0% | 0.0% |

## Scene attributes

Accuracy counts unanswered fields as wrong. Compare against the majority-class baseline: with a skewed GT, a model that always says "day" looks good on raw accuracy but gets 50% balanced accuracy.

| Attribute | Accuracy | Balanced acc. | Majority baseline | Answered | GT distribution |
|---|---|---|---|---|---|
| time_of_day | 2.0% | 3.3% | 70.0% | 2.0% | day: 35, night: 15 |
| road_condition | 0.0% | 0.0% | 90.0% | 6.0% | dry: 45, wet: 5 |
| scene_type | 56.0% | 46.7% | 40.0% | 100.0% | intersection: 20, road: 20, parking_lot: 10 |
| traffic_side | 6.0% | 6.7% | 60.0% | 10.0% | left: 30, right: 20 |

Confusion:
- **time_of_day**: GT day → unanswered: 35; GT night → unanswered: 14, night: 1
- **road_condition**: GT dry → unanswered: 42, wet: 3; GT wet → unanswered: 5
- **scene_type**: GT intersection → road: 10, intersection: 10; GT parking_lot → road: 10; GT road → road: 18, intersection: 2
- **traffic_side**: GT left → unanswered: 29, left: 1; GT right → unanswered: 16, left: 2, right: 2

## Free-text faithfulness

| Metric | Value |
|---|---|
| Claims in prose: precision | 89.9% |
| Claims in prose: recall | 54.4% |
| Claims in prose: hallucination rate | 9.6% |
| Prose object claims the structured answer denies | – |
| Prose ↔ structured attribute agreement | – |

Claims are extracted from the description with a rule-based lexicon (see parsing/text_claims.py). Agreement is computed for structured answers (JSON or questionnaire).

## Slices

Headline metrics per ground-truth condition. Slices are defined on ground truth. Small slices have wide uncertainty; check the frame count before drawing conclusions.

**By time_of_day**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| day | 35 | 64.2% | 51.2% | 12.7% | 12.9% |
| night | 15 | 78.3% | 64.3% | 0.0% | 23.3% |

**By location**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| boston-seaport | 20 | 59.7% | 45.1% | 10.3% | 18.8% |
| singapore-hollandvillage | 15 | 78.3% | 64.3% | 0.0% | 23.3% |
| singapore-onenorth | 5 | 68.8% | 55.0% | 8.3% | 10.0% |
| singapore-queenstown | 10 | 71.4% | 66.7% | 21.4% | 2.5% |

**By scene_type**

| Slice | Frames | Object F1 | Recall | Hallucination | Attribute acc. |
|---|---|---|---|---|---|
| intersection | 20 | 62.8% | 49.1% | 12.1% | 16.2% |
| parking_lot | 10 | 66.7% | 57.9% | 20.0% | 0.0% |
| road | 20 | 75.0% | 60.0% | 0.0% | 23.8% |

## Temporal consistency

How often a label changes between consecutive sampled frames of the same scene.

| Label | Model flip rate | GT flip rate |
|---|---|---|
| time_of_day | 5.0% | 0.0% |
| road_condition | 12.5% | 0.0% |
| scene_type | 15.0% | 0.0% |
| traffic_side | 15.0% | 0.0% |
| obj:car | 0.0% | 20.0% |
| obj:truck | 15.0% | 37.5% |
| obj:bus | 15.0% | 15.0% |
| obj:pedestrian | 32.5% | 22.5% |
| obj:two_wheeler | 5.0% | 32.5% |
| obj:traffic_cone | 2.5% | 15.0% |
| obj:barrier | 2.5% | 10.0% |

Scene-level GT attributes never change within a scene, so any attribute flip by the model is an inconsistency.

## Similarity to the human reference (secondary)

`scene.description` describes a 20 s scene in keywords, not this frame, so similarity is a weak proxy. A low correlation with the claim-level F1 shows that similarity does not track correctness.

| Metric | Value |
|---|---|
| Reference keyword recall (classes in scene.description that are mentioned) | 28.7% |
| Mean embedding cosine to scene.description | 0.31 |
| Pearson(cosine, frame object F1) | 0.14 |
| Spearman(cosine, frame object F1) | 0.06 |

## Error taxonomy

Frames with at least one error: 88.0%

| Error family | Count |
|---|---|
| omission | 52 |
| attribute | 27 |
| count | 7 |
| hallucination | 7 |
| format | 1 |

| Most frequent errors | Count |
|---|---|
| attribute:scene_type | 22 |
| omission:pedestrian | 12 |
| omission:two_wheeler | 11 |
| omission:truck | 10 |
| omission:barrier | 8 |
| omission:traffic_cone | 6 |
| omission:bus | 5 |
| count:car | 3 |
| hallucination:car | 3 |
| attribute:road_condition | 3 |
| attribute:traffic_side | 2 |
| count:pedestrian | 2 |
| count:barrier | 1 |
| hallucination:bus | 1 |
| count:traffic_cone | 1 |

### Worst frames

**scene-0757 / frame 0**: `hallucination:car`, `omission:truck`, `omission:bus`, `omission:traffic_cone`, `attribute:scene_type`

![cd9964f8c3d34383b16e9c2997de1ed0](thumbs/cd9964f8c3d34383b16e9c2997de1ed0.jpg)

> A car is parked on the road. The road is empty. The road is surrounded by a fence.

GT objects: `{'traffic_cone': '1-2', 'bus': '1-2', 'truck': '1-2'}`, predicted: `{'car': '1-2'}`

**scene-0916 / frame 0**: `format:repetition_loop`, `hallucination:car`, `count:pedestrian`, `hallucination:two_wheeler`, `attribute:scene_type`

![b5989651183643369174912bc5641d3b](thumbs/b5989651183643369174912bc5641d3b.jpg)

> The image is taken from the front of a car. The car is parked on the road. The road is empty. There are two people riding bicycles on the road. There are two people walking on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk.

GT objects: `{'pedestrian': '6+'}`, predicted: `{'car': '1-2', 'pedestrian': '1-2', 'two_wheeler': '1-2'}`

**scene-0061 / frame 0**: `omission:truck`, `omission:pedestrian`, `count:barrier`, `attribute:scene_type`

![ca9a282c9e77460f8360f564131a8af5](thumbs/ca9a282c9e77460f8360f564131a8af5.jpg)

> The image is taken from the front of a car. The road is empty, with a few vehicles passing by. The road is surrounded by a white and red colored barrier. There are trees and buildings on both sides of the road. The sky is cloudy.

GT objects: `{'pedestrian': '3-5', 'barrier': '6+', 'car': '3-5', 'truck': '1-2'}`, predicted: `{'car': '1-2', 'barrier': '1-2'}`

**scene-0061 / frame 19**: `hallucination:bus`, `omission:pedestrian`, `omission:traffic_cone`, `omission:barrier`

![b26e791522294bec90f86fd72226e35c](thumbs/b26e791522294bec90f86fd72226e35c.jpg)

> A car is stopped at a traffic light. There is a truck and a bus on the road. There are trees and buildings in the background.

GT objects: `{'truck': '3-5', 'traffic_cone': '6+', 'pedestrian': '1-2', 'barrier': '3-5', 'car': '1-2'}`, predicted: `{'car': '1-2', 'truck': '1-2', 'bus': '1-2'}`

**scene-0103 / frame 10**: `count:car`, `omission:pedestrian`, `omission:traffic_cone`, `attribute:traffic_side`

![b6b0d9f2f2e14a3aaa2c8aedeb1edb69](thumbs/b6b0d9f2f2e14a3aaa2c8aedeb1edb69.jpg)

> A car is parked on the road. The road is empty. There are trees on the left side of the road.

GT objects: `{'car': '6+', 'traffic_cone': '1-2', 'pedestrian': '3-5'}`, predicted: `{'car': '1-2'}`

**scene-0655 / frame 20**: `omission:truck`, `omission:bus`, `omission:traffic_cone`, `attribute:scene_type`

![0d7263a5b8264cad996582d6219ef1f2](thumbs/0d7263a5b8264cad996582d6219ef1f2.jpg)

> A car is parked on the road in front of a building. The road has a crosswalk. There are cars parked on the side of the road.

GT objects: `{'car': '1-2', 'bus': '1-2', 'traffic_cone': '1-2', 'truck': '1-2'}`, predicted: `{'car': '3-5'}`

**scene-0061 / frame 10**: `omission:truck`, `omission:traffic_cone`, `omission:barrier`

![023c4df2d451409881d8e6ea82f14704](thumbs/023c4df2d451409881d8e6ea82f14704.jpg)

> A car is on the road. The road is on the left side of the image. There are people on the right side of the image. There are trees and buildings on the right side of the image. There are traffic lights on the right side of the image.

GT objects: `{'pedestrian': '6+', 'car': '3-5', 'barrier': '3-5', 'truck': '1-2', 'traffic_cone': '3-5'}`, predicted: `{'car': '1-2', 'pedestrian': '3-5'}`

**scene-0103 / frame 29**: `omission:truck`, `omission:pedestrian`, `omission:two_wheeler`

![6d9984d09d52479e837da2fd09e192cc](thumbs/6d9984d09d52479e837da2fd09e192cc.jpg)

> A car is parked on the road. The road is empty. There are cars parked on both sides of the road. There are trees on both sides of the road.

GT objects: `{'car': '6+', 'two_wheeler': '1-2', 'pedestrian': '1-2', 'truck': '1-2'}`, predicted: `{'car': '3-5'}`
