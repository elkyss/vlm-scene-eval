# Run comparison

- **A**: `SmolVLM-500M-Instruct / v2_structured@7f47e762`
- **B**: `SmolVLM-500M-Instruct / v3_questionnaire@14414ec5`
- 50 shared frames, 10 scenes

Δ = B − A. 95% CI from a bootstrap over scenes (frames within a scene are correlated). The p-value is an exact paired sign-flip test on per-scene differences (frames of a scene are not independent, so testing happens at scene level). With only 10 scenes, CIs are wide: treat differences whose CI crosses 0 as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | Scene sign-flip p | Verdict |
|---|---|---|---|---|---|---|
| Object micro F1 | 0.0% | 63.4% | 63.4% | [55.7%, 70.8%] | 0.002 | B better |
| Mean frame object F1 | 2.0% | 59.9% | 57.9% | [48.8%, 66.4%] | 0.002 | B better |
| Presence accuracy: car | 12.0% | 98.0% | 86.0% | [76.0%, 94.0%] | 0.002 | B better |
| Presence accuracy: truck | 76.0% | 42.0% | -34.0% | [-62.0%, -6.0%] | 0.086 | A better |
| Presence accuracy: bus | 86.0% | 88.0% | 2.0% | [-16.0%, 18.0%] | 1.000 | inconclusive |
| Presence accuracy: pedestrian | 56.0% | 80.0% | 24.0% | [4.0%, 42.0%] | 0.078 | B better |
| Presence accuracy: two_wheeler | 76.0% | 82.0% | 6.0% | [-6.0%, 18.0%] | 0.562 | inconclusive |
| Presence accuracy: traffic_cone | 84.0% | 62.0% | -22.0% | [-50.0%, 6.0%] | 0.211 | inconclusive |
| Presence accuracy: barrier | 82.0% | 22.0% | -60.0% | [-88.0%, -26.0%] | 0.014 | A better |
| Accuracy: time_of_day | 12.0% | 100.0% | 88.0% | [68.0%, 100.0%] | 0.002 | B better |
| Accuracy: road_condition | 4.0% | 60.0% | 56.0% | [34.0%, 74.0%] | 0.008 | B better |
| Accuracy: scene_type | 2.0% | 52.0% | 50.0% | [22.0%, 78.0%] | 0.031 | B better |
| Accuracy: traffic_side | 0.0% | 40.0% | 40.0% | [16.0%, 64.0%] | 0.031 | B better |
| Valid structured output | 48.0% | 100.0% | 52.0% | [32.0%, 72.0%] | 0.004 | B better |
| Mean latency (s) | 2.06 | 17.42 | 15.36 | [15.17, 15.59] | 0.002 | A better |

## Largest disagreements

**scene-0061 / frame 10**. GT objects `{'pedestrian': '6+', 'car': '3-5', 'barrier': '3-5', 'truck': '1-2', 'traffic_cone': '3-5'}`

- A (F1 0.00): left or right
- B (F1 1.00): A car is on the road. The road is on the left side of the image. There are people on the right side of the image. There are trees and buildings on the right side of the image. There are traffic lights on the right side of the image.

**scene-0655 / frame 0**. GT objects `{'car': '6+', 'truck': '1-2'}`

- A (F1 0.00): wet or dry
- B (F1 1.00): A car is parked on the left side of the road. There are many cars parked on the right side of the road. There are trees and buildings on both sides of the road.

**scene-0916 / frame 40**. GT objects `{}`

- A (F1 1.00): 0.
- B (F1 0.00): A car is parked on the road. The road is surrounded by greenery and there are buildings and trees in the background.

**scene-0655 / frame 20**. GT objects `{'car': '1-2', 'bus': '1-2', 'traffic_cone': '1-2', 'truck': '1-2'}`

- A (F1 0.00): parking lot or intersection or road
- B (F1 0.89): A car is parked on the road in front of a building. The road has a crosswalk. There are cars parked on the side of the road.

**scene-0103 / frame 29**. GT objects `{'car': '6+', 'two_wheeler': '1-2', 'pedestrian': '1-2', 'truck': '1-2'}`

- A (F1 0.00): wet or dry
- B (F1 0.89): A car is parked on the road. The road is empty. There are cars parked on both sides of the road. There are trees on both sides of the road.

**scene-0061 / frame 0**. GT objects `{'pedestrian': '3-5', 'barrier': '6+', 'car': '3-5', 'truck': '1-2'}`

- A (F1 0.00): wet or dry
- B (F1 0.89): The image is taken from the front of a car. The road is empty, with a few vehicles passing by. The road is surrounded by a white and red colored barrier. There are trees and buildings on both sides of the road. The sky is cloudy.
