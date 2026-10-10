# Run comparison

- **A**: `mock-always_car / v2_structured@7f47e762`
- **B**: `SmolVLM-500M-Instruct / v1_open@14073038`
- 50 shared frames, 10 scenes

Δ = B − A. 95% CI from a bootstrap over scenes (frames within a scene are correlated). The p-value is an exact paired sign-flip test on per-scene differences (frames of a scene are not independent, so testing happens at scene level). With only 10 scenes, CIs are wide: treat differences whose CI crosses 0 as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | Scene sign-flip p | Verdict |
|---|---|---|---|---|---|---|
| Object micro F1 | 64.1% | 67.8% | 3.7% | [-3.9%, 11.9%] | 0.311 | inconclusive |
| Mean frame object F1 | 64.0% | 68.2% | 4.2% | [-4.7%, 13.0%] | 0.406 | inconclusive |
| Presence accuracy: car | 94.0% | 94.0% | 0.0% | [0.0%, 0.0%] | 1.000 | inconclusive |
| Presence accuracy: truck | 76.0% | 78.0% | 2.0% | [-4.0%, 8.0%] | 1.000 | inconclusive |
| Presence accuracy: bus | 86.0% | 88.0% | 2.0% | [-4.0%, 8.0%] | 1.000 | inconclusive |
| Presence accuracy: pedestrian | 54.0% | 74.0% | 20.0% | [-12.0%, 50.0%] | 0.324 | inconclusive |
| Presence accuracy: two_wheeler | 76.0% | 76.0% | 0.0% | [-6.0%, 6.0%] | 1.000 | inconclusive |
| Presence accuracy: traffic_cone | 84.0% | 88.0% | 4.0% | [0.0%, 12.0%] | 1.000 | inconclusive |
| Presence accuracy: barrier | 82.0% | 84.0% | 2.0% | [0.0%, 6.0%] | 1.000 | inconclusive |
| Accuracy: time_of_day | 70.0% | 2.0% | -68.0% | [-90.0%, -36.0%] | 0.016 | A better |
| Accuracy: road_condition | 90.0% | 0.0% | -90.0% | [-100.0%, -70.0%] | 0.004 | A better |
| Accuracy: scene_type | 40.0% | 56.0% | 16.0% | [-4.0%, 38.0%] | 0.312 | inconclusive |
| Accuracy: traffic_side | 40.0% | 6.0% | -34.0% | [-62.0%, -6.0%] | 0.125 | A better |
| Valid structured output | 100.0% | 100.0% | 0.0% | [0.0%, 0.0%] | 1.000 | inconclusive |
| Mean latency (s) | 0.00 | 1.74 | 1.74 | [1.70, 1.80] | 0.002 | A better |

## Largest disagreements

**scene-0553 / frame 0**. GT objects `{'two_wheeler': '1-2', 'pedestrian': '1-2'}`

- A (F1 0.67): A car and a pedestrian on a sunny road.
- B (F1 0.00): A car is parked on the road. The road is empty. The road has white lines.

**scene-0061 / frame 38**. GT objects `{'traffic_cone': '6+', 'two_wheeler': '1-2', 'car': '1-2'}`

- A (F1 0.50): A car and a pedestrian on a sunny road.
- B (F1 1.00): The car is white and parked on the side of the road. There are two orange traffic cones on the road. There is a bicycle on the sidewalk. There are trees and buildings in the background.

**scene-0061 / frame 28**. GT objects `{'traffic_cone': '6+', 'two_wheeler': '1-2', 'car': '1-2'}`

- A (F1 0.40): A car and a pedestrian on a sunny road.
- B (F1 0.80): A white car is on the road. There are traffic cones on the road. There are buildings and trees on the sides of the road.

**scene-1094 / frame 20**. GT objects `{'car': '3-5', 'pedestrian': '1-2'}`

- A (F1 1.00): A car and a pedestrian on a sunny road.
- B (F1 0.67): A car is on the road. The road is empty. The road is surrounded by plants and trees.

**scene-0103 / frame 39**. GT objects `{'car': '6+'}`

- A (F1 0.67): A car and a pedestrian on a sunny road.
- B (F1 1.00): A car is parked on the road. The road is empty. There are cars parked on both sides of the road.

**scene-0655 / frame 40**. GT objects `{'car': '1-2'}`

- A (F1 0.67): A car and a pedestrian on a sunny road.
- B (F1 1.00): A black Jeep is parked on the road in front of a yellow sign with a pedestrian crossing.
