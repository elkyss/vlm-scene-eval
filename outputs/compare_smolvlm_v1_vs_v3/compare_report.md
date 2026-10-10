# Run comparison

- **A**: `SmolVLM-500M-Instruct / v1_open@14073038`
- **B**: `SmolVLM-500M-Instruct / v3_questionnaire@14414ec5`
- 50 shared frames, 10 scenes

Δ = B − A. 95% CI from a bootstrap over scenes (frames within a scene are correlated). McNemar p-value on paired per-frame correctness. With only 10 scenes, CIs are wide: treat differences whose CI crosses 0 as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | McNemar p |
|---|---|---|---|---|---|
| Object micro F1 | 67.8% | 63.4% | -4.3% | [-14.9%, 4.9%] | – |
| Mean frame object F1 | 68.2% | 59.9% | -8.4% | [-17.8%, 0.9%] | – |
| Presence accuracy: car | 94.0% | 98.0% | 4.0% | [0.0%, 12.0%] | 0.500 |
| Presence accuracy: truck | 78.0% | 42.0% | -36.0% | [-62.0%, -12.0%] | 0.005 |
| Presence accuracy: bus | 88.0% | 88.0% | 0.0% | [-14.0%, 14.0%] | 1.000 |
| Presence accuracy: pedestrian | 74.0% | 80.0% | 6.0% | [-4.0%, 16.0%] | 0.375 |
| Presence accuracy: two_wheeler | 76.0% | 82.0% | 6.0% | [-4.0%, 16.0%] | 0.581 |
| Presence accuracy: traffic_cone | 88.0% | 62.0% | -26.0% | [-52.0%, -4.0%] | 0.015 |
| Presence accuracy: barrier | 84.0% | 22.0% | -62.0% | [-88.0%, -30.0%] | 0.000 |
| Accuracy: time_of_day | 2.0% | 100.0% | 98.0% | [94.0%, 100.0%] | 0.000 |
| Accuracy: road_condition | 0.0% | 60.0% | 60.0% | [36.0%, 80.0%] | 0.000 |
| Accuracy: scene_type | 56.0% | 52.0% | -4.0% | [-36.0%, 30.0%] | 0.832 |
| Accuracy: traffic_side | 6.0% | 40.0% | 34.0% | [10.0%, 58.0%] | 0.000 |
| Valid structured output | 100.0% | 100.0% | 0.0% | [0.0%, 0.0%] | 1.000 |
| Mean latency (s) | 1.74 | 17.42 | 15.68 | [15.60, 15.75] | – |

## Largest disagreements

**scene-0103 / frame 39**. GT objects `{'car': '6+'}`

- A (F1 1.00): A car is parked on the road. The road is empty. There are cars parked on both sides of the road.
- B (F1 0.40): A car is parked on the road. The road is empty. There are cars parked on both sides of the road.

**scene-1100 / frame 0**. GT objects `{'car': '3-5'}`

- A (F1 1.00): A car is parked on the road. The car is black and the road is wet. There are traffic lights and street lights in the background.
- B (F1 0.40): A car is parked on the road. The car is black and the road is wet. There are traffic lights and street lights in the background.

**scene-0757 / frame 0**. GT objects `{'traffic_cone': '1-2', 'bus': '1-2', 'truck': '1-2'}`

- A (F1 0.00): A car is parked on the road. The road is empty. The road is surrounded by a fence.
- B (F1 0.57): A car is parked on the road. The road is empty. The road is surrounded by a fence.

**scene-0796 / frame 29**. GT objects `{'truck': '1-2'}`

- A (F1 0.00): A car is on the road. There are trees on both sides of the road.
- B (F1 0.50): A car is on the road. There are trees on both sides of the road.

**scene-0655 / frame 40**. GT objects `{'car': '1-2'}`

- A (F1 1.00): A black Jeep is parked on the road in front of a yellow sign with a pedestrian crossing.
- B (F1 0.50): A black Jeep is parked on the road in front of a yellow sign with a pedestrian crossing.

**scene-0796 / frame 20**. GT objects `{'car': '1-2'}`

- A (F1 1.00): A car is on the road. The road is wide. There are trees on both sides of the road. There are cars on the road.
- B (F1 0.50): A car is on the road. The road is wide. There are trees on both sides of the road. There are cars on the road.
