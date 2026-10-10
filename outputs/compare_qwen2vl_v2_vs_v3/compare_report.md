# Run comparison

- **A**: `Qwen2-VL-2B-Instruct / v2_structured@7f47e762`
- **B**: `Qwen2-VL-2B-Instruct / v3_questionnaire@14414ec5`
- 50 shared frames, 10 scenes

Δ = B − A. 95% CI from a bootstrap over scenes (frames within a scene are correlated). The p-value is an exact paired sign-flip test on per-scene differences (frames of a scene are not independent, so testing happens at scene level). With only 10 scenes, CIs are wide: treat differences whose CI crosses 0 as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | Scene sign-flip p | Verdict |
|---|---|---|---|---|---|---|
| Object micro F1 | 59.1% | 73.4% | 14.3% | [5.9%, 22.2%] | 0.023 | B better |
| Mean frame object F1 | 54.8% | 70.6% | 15.8% | [5.8%, 25.6%] | 0.029 | B better |
| Presence accuracy: car | 74.0% | 100.0% | 26.0% | [16.0%, 38.0%] | 0.008 | B better |
| Presence accuracy: truck | 82.0% | 84.0% | 2.0% | [-16.0%, 18.0%] | 1.000 | inconclusive |
| Presence accuracy: bus | 88.0% | 94.0% | 6.0% | [-2.0%, 16.0%] | 0.500 | inconclusive |
| Presence accuracy: pedestrian | 66.0% | 82.0% | 16.0% | [8.0%, 26.0%] | 0.031 | B better |
| Presence accuracy: two_wheeler | 78.0% | 78.0% | 0.0% | [-8.0%, 8.0%] | 1.000 | inconclusive |
| Presence accuracy: traffic_cone | 88.0% | 94.0% | 6.0% | [-4.0%, 16.0%] | 0.500 | inconclusive |
| Presence accuracy: barrier | 80.0% | 42.0% | -38.0% | [-66.0%, -10.0%] | 0.051 | A better |
| Accuracy: time_of_day | 100.0% | 100.0% | 0.0% | [0.0%, 0.0%] | 1.000 | inconclusive |
| Accuracy: road_condition | 60.0% | 78.0% | 18.0% | [6.0%, 32.0%] | 0.055 | B better |
| Accuracy: scene_type | 58.0% | 62.0% | 4.0% | [-10.0%, 24.0%] | 0.938 | inconclusive |
| Accuracy: traffic_side | 58.0% | 38.0% | -20.0% | [-46.0%, 6.0%] | 0.188 | inconclusive |
| Valid structured output | 96.0% | 100.0% | 4.0% | [0.0%, 10.0%] | 0.500 | inconclusive |
| Mean latency (s) | 4.12 | 18.14 | 14.02 | [13.74, 14.33] | 0.002 | A better |

## Largest disagreements

**scene-0103 / frame 39**. GT objects `{'car': '6+'}`

- A (F1 0.00): A street with parked cars and buildings on both sides, with a pedestrian crossing sign visible on the right.
- B (F1 1.00): The image depicts a city street with a mix of old and new buildings. The street is lined with parked cars on both sides, and there are no visible pedestrians or cyclists. The lighting is natural, suggesting it is daytime. The road appears to be in good condition, with no visible potholes or debris. The buildings on either side are of different architectural styles, indicating a diverse urban landscape.

**scene-0757 / frame 40**. GT objects `{'car': '1-2'}`

- A (F1 0.00): A white van with the word 'Aetna' on the side is parked at an intersection with a pedestrian crossing in the foreground.
- B (F1 1.00): The image depicts an urban street scene with a focus on a white van labeled "Aetna" parked at an intersection. The street is marked with pedestrian crosswalks and traffic lights, indicating a busy area. The sky is overcast, suggesting a cloudy day. There are construction barriers and scaffolding visible on the left side of the image, indicating ongoing development or renovation work. The road conditions appear to be clear, with no visible traffic or pedestrians in the immediate vicinity.

**scene-0916 / frame 0**. GT objects `{'pedestrian': '6+'}`

- A (F1 0.00): {"description": "A car is parked in a parking lot with palm trees and a building in the background.", "time_of_day": "day", "road_condition": "dry", "scene_type": "parking_lot", "traffic_side": "left", "objects": "0"}
- B (F1 1.00): The image depicts the front view of a large, multi-story building with a modern architectural style. The building has a light-colored facade with multiple levels, and there are several windows visible. The ground level of the building appears to be a parking area or a courtyard, with a paved area and some greenery. There are a few people visible in the background, including a few individuals walking on the sidewalk and a few standing near the building. The lighting in the image is natural, suggesting it is daytime. The road conditions appear to be clear, with no visible traffic or pedestrians.

**scene-0655 / frame 20**. GT objects `{'car': '1-2', 'bus': '1-2', 'traffic_cone': '1-2', 'truck': '1-2'}`

- A (F1 0.00): The scene shows a street with a large building on the right and a smaller building on the left. There are no cars or trucks visible, and no pedestrians are present. The road is wet, and there are no traffic cones or barriers. The scene type is an intersection.
- B (F1 0.89): The image depicts a street scene in an urban area. The road is wide and appears to be a main thoroughfare, possibly a business district or a commercial area. The lighting is bright, suggesting it is daytime. There are several vehicles on the road, including cars and a bus, indicating moderate traffic. The road is marked with white lines, and there are construction cones placed on the left side, suggesting ongoing work or maintenance. The buildings on either side of the road have large windows and appear to be commercial or office buildings. The overall atmosphere is busy yet orderly.

**scene-0916 / frame 10**. GT objects `{'car': '3-5', 'two_wheeler': '3-5', 'pedestrian': '1-2'}`

- A (F1 0.00): A parking lot with motorcycles and cars, trees in the background, and a pedestrian standing in the middle of the lot.
- B (F1 0.75): The image shows a parking lot with several parked cars and motorcycles. The lighting is natural, suggesting it might be daytime. The road conditions appear to be clear, with no visible signs of rain or snow. There are trees and a building in the background, indicating that the parking lot is located in a suburban or urban area. The road users visible in the image include parked cars and motorcycles.

**scene-0655 / frame 30**. GT objects `{'truck': '1-2', 'pedestrian': '1-2', 'traffic_cone': '3-5', 'bus': '1-2'}`

- A (F1 0.00): A road with a truck and a bus, with traffic cones and a construction zone in the middle. The sky is clear.
- B (F1 0.75): The image depicts a street scene with a construction zone in the foreground. A white utility truck is parked on the left side of the road, with a crane attached to its back. The road is marked with yellow double lines, and there are orange traffic cones placed on the left side of the road. In the background, there are tall buildings with large windows, suggesting an urban setting. The sky is clear, indicating good weather. There are also a few cars and a bus visible on the right side of the road, indicating that the street is busy. The overall lighting is bright, suggesting it is daytime.
