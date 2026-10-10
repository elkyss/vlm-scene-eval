# Run comparison

- **A**: `Qwen2-VL-2B-Instruct / v2_structured@7f47e762`
- **B**: `Qwen2-VL-2B-Instruct / v2b_structured@db8db50a`
- 50 shared frames, 10 scenes

Δ = B − A. 95% CI from a bootstrap over scenes (frames within a scene are correlated). McNemar p-value on paired per-frame correctness. With only 10 scenes, CIs are wide: treat differences whose CI crosses 0 as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | McNemar p |
|---|---|---|---|---|---|
| Object micro F1 | 59.1% | 35.1% | -24.0% | [-39.9%, -11.7%] | – |
| Mean frame object F1 | 54.8% | 22.9% | -31.9% | [-46.1%, -16.8%] | – |
| Presence accuracy: car | 74.0% | 30.0% | -44.0% | [-62.0%, -24.0%] | 0.000 |
| Presence accuracy: truck | 82.0% | 84.0% | 2.0% | [-6.0%, 10.0%] | 1.000 |
| Presence accuracy: bus | 88.0% | 88.0% | 0.0% | [0.0%, 0.0%] | 1.000 |
| Presence accuracy: pedestrian | 66.0% | 64.0% | -2.0% | [-14.0%, 12.0%] | 1.000 |
| Presence accuracy: two_wheeler | 78.0% | 80.0% | 2.0% | [-4.0%, 8.0%] | 1.000 |
| Presence accuracy: traffic_cone | 88.0% | 86.0% | -2.0% | [-6.0%, 0.0%] | 1.000 |
| Presence accuracy: barrier | 80.0% | 76.0% | -4.0% | [-14.0%, 4.0%] | 0.625 |
| Accuracy: time_of_day | 100.0% | 100.0% | 0.0% | [0.0%, 0.0%] | 1.000 |
| Accuracy: road_condition | 60.0% | 46.0% | -14.0% | [-28.0%, -2.0%] | 0.065 |
| Accuracy: scene_type | 58.0% | 52.0% | -6.0% | [-16.0%, 2.0%] | 0.375 |
| Accuracy: traffic_side | 58.0% | 54.0% | -4.0% | [-28.0%, 16.0%] | 0.815 |
| Valid structured output | 96.0% | 100.0% | 4.0% | [0.0%, 10.0%] | 0.500 |
| Mean latency (s) | 4.12 | 4.72 | 0.60 | [0.39, 0.82] | – |

## Largest disagreements

**scene-0655 / frame 40**. GT objects `{'car': '1-2'}`

- A (F1 1.00): A black SUV is driving down a street with a yellow line in the middle, surrounded by trees and buildings on both sides.
- B (F1 0.00): A black SUV is driving down a two-lane road with a yellow line in the center, surrounded by buildings on both sides. There are no pedestrians or bicycles visible.

**scene-0655 / frame 0**. GT objects `{'car': '6+', 'truck': '1-2'}`

- A (F1 1.00): A street with multiple vehicles, including a truck and a car, parked on the side of the road.
- B (F1 0.00): A busy street with multiple vehicles, including cars, trucks, and buses, parked on both sides. The road is wet, indicating recent rain.

**scene-1077 / frame 0**. GT objects `{'car': '3-5'}`

- A (F1 1.00): A car is driving on a wet road at night.
- B (F1 0.00): The image shows a nighttime scene with a wet road, featuring a car, a truck, a bus, a pedestrian, a two-wheeler, and a traffic cone. The car is on the left side of the road, and the truck is on the right side. The pedestrian is in the middle of the road, and the two-wheeler is on the right side of the road. The traffic cone is on the left side of the road. The scene appears to be an intersection or a parking lot.

**scene-0916 / frame 40**. GT objects `{}`

- A (F1 0.00): A road with trees and buildings on the right side, a wet road with a guardrail on the left.
- B (F1 1.00): A quiet road with trees and buildings on the right side, with a car and a truck visible on the left side.

**scene-0916 / frame 30**. GT objects `{'car': '6+'}`

- A (F1 1.00): The scene shows a parking lot with several cars parked along the edge of a road. The road is wet, and there are trees and buildings in the background.
- B (F1 0.00): The image shows a parking lot with several cars parked along the road. The road is wet, and there are trees and buildings in the background.

**scene-1077 / frame 10**. GT objects `{'car': '3-5'}`

- A (F1 1.00): The scene is a wet road with a car driving on it, surrounded by trees and street lights.
- B (F1 0.00): The image shows a wet road with a car and a truck visible in the distance, and a pedestrian on the sidewalk.
