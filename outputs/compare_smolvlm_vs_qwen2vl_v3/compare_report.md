# Run comparison

- **A**: `SmolVLM-500M-Instruct / v3_questionnaire@14414ec5`
- **B**: `Qwen2-VL-2B-Instruct / v3_questionnaire@14414ec5`
- 50 shared frames, 10 scenes

Δ = B − A. 95% CI from a bootstrap over scenes (frames within a scene are correlated). The p-value is an exact paired sign-flip test on per-scene differences (frames of a scene are not independent, so testing happens at scene level). With only 10 scenes, CIs are wide: treat differences whose CI crosses 0 as inconclusive.

| Metric | A | B | Δ | 95% CI of Δ | Scene sign-flip p | Verdict |
|---|---|---|---|---|---|---|
| Object micro F1 | 63.4% | 73.4% | 10.0% | [6.3%, 14.4%] | 0.002 | B better |
| Mean frame object F1 | 59.9% | 70.6% | 10.7% | [4.1%, 17.1%] | 0.018 | B better |
| Presence accuracy: car | 98.0% | 100.0% | 2.0% | [0.0%, 6.0%] | 1.000 | inconclusive |
| Presence accuracy: truck | 42.0% | 84.0% | 42.0% | [25.9%, 60.0%] | 0.004 | B better |
| Presence accuracy: bus | 88.0% | 94.0% | 6.0% | [-4.0%, 20.0%] | 0.750 | inconclusive |
| Presence accuracy: pedestrian | 80.0% | 82.0% | 2.0% | [-6.0%, 12.0%] | 1.000 | inconclusive |
| Presence accuracy: two_wheeler | 82.0% | 78.0% | -4.0% | [-18.0%, 8.0%] | 0.781 | inconclusive |
| Presence accuracy: traffic_cone | 62.0% | 94.0% | 32.0% | [16.0%, 52.0%] | 0.008 | B better |
| Presence accuracy: barrier | 22.0% | 42.0% | 20.0% | [6.0%, 36.0%] | 0.125 | borderline |
| Accuracy: time_of_day | 100.0% | 100.0% | 0.0% | [0.0%, 0.0%] | 1.000 | inconclusive |
| Accuracy: road_condition | 60.0% | 78.0% | 18.0% | [6.0%, 32.0%] | 0.055 | borderline |
| Accuracy: scene_type | 52.0% | 62.0% | 10.0% | [-12.0%, 32.0%] | 0.531 | inconclusive |
| Accuracy: traffic_side | 40.0% | 38.0% | -2.0% | [-14.0%, 10.0%] | 1.000 | inconclusive |
| Valid structured output | 100.0% | 100.0% | 0.0% | [0.0%, 0.0%] | 1.000 | inconclusive |
| Mean latency (s) | 17.42 | 18.14 | 0.72 | [0.42, 1.02] | 0.004 | A better |

## Largest disagreements

**scene-0103 / frame 39**. GT objects `{'car': '6+'}`

- A (F1 0.40): A car is parked on the road. The road is empty. There are cars parked on both sides of the road.
- B (F1 1.00): The image depicts a city street with a mix of old and new buildings. The street is lined with parked cars on both sides, and there are no visible pedestrians or cyclists. The lighting is natural, suggesting it is daytime. The road appears to be in good condition, with no visible potholes or debris. The buildings on either side are of different architectural styles, indicating a diverse urban landscape.

**scene-0796 / frame 29**. GT objects `{'truck': '1-2'}`

- A (F1 0.50): A car is on the road. There are trees on both sides of the road.
- B (F1 0.00): The image depicts a quiet, suburban street in a well-maintained area. The sky is clear, suggesting a sunny day. The road is wide and appears to be in good condition, with clear lane markings and no visible potholes. On the left side of the road, there is a blue banner with white text, possibly advertising a business or event. The right side of the road is bordered by a green fence, and there are trees and shrubs along the sidewalk. A few vehicles are visible in the distance, including a car and a truck. The overall atmosphere is calm and orderly, typical of a residential or commercial neighborhood.

**scene-0757 / frame 40**. GT objects `{'car': '1-2'}`

- A (F1 0.50): A white van is driving on a street. The van has the word "Aetna" on the top. There are traffic lights on the side of the road. There are buildings on both sides of the street. There are people walking on the sidewalk.
- B (F1 1.00): The image depicts an urban street scene with a focus on a white van labeled "Aetna" parked at an intersection. The street is marked with pedestrian crosswalks and traffic lights, indicating a busy area. The sky is overcast, suggesting a cloudy day. There are construction barriers and scaffolding visible on the left side of the image, indicating ongoing development or renovation work. The road conditions appear to be clear, with no visible traffic or pedestrians in the immediate vicinity.

**scene-0916 / frame 0**. GT objects `{'pedestrian': '6+'}`

- A (F1 0.50): The image is taken from the front of a car. The car is parked on the road. The road is empty. There are two people riding bicycles on the road. There are two people walking on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk. There are two people standing on the sidewalk.
- B (F1 1.00): The image depicts the front view of a large, multi-story building with a modern architectural style. The building has a light-colored facade with multiple levels, and there are several windows visible. The ground level of the building appears to be a parking area or a courtyard, with a paved area and some greenery. There are a few people visible in the background, including a few individuals walking on the sidewalk and a few standing near the building. The lighting in the image is natural, suggesting it is daytime. The road conditions appear to be clear, with no visible traffic or pedestrians.

**scene-0916 / frame 30**. GT objects `{'car': '6+'}`

- A (F1 0.50): A car is parked on the road. There are trees and bushes on the side of the road.
- B (F1 1.00): The image depicts a parking lot with several cars parked along the edge of a road. The lighting is natural, suggesting it might be daytime. The road appears to be in good condition, with clear markings and no visible damage. There are trees and greenery in the background, indicating a park or a similar outdoor area. The overall scene suggests a quiet, possibly residential or university-like setting.

**scene-1077 / frame 10**. GT objects `{'car': '3-5'}`

- A (F1 0.50): A car is parked on the side of the road. The road is empty. There are trees on the side of the road. There are street lights on the side of the road.
- B (F1 1.00): The image depicts a nighttime scene on a city street. The road is well-lit by streetlights and vehicle headlights, creating a bright and somewhat chaotic atmosphere. There are multiple lanes of traffic, with cars and other vehicles visible in the distance. The road is bordered by trees and a sidewalk on the left side, and there are no visible pedestrians or cyclists in the immediate vicinity. The overall condition of the road appears to be in good condition, with no visible potholes or debris.
