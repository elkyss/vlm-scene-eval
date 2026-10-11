# Scene-level evaluation: `Qwen2-VL-2B-Instruct` with prompt `scene_guided@53a32872`

10 scenes. Each scene is shown as 3 views of 6 frames (one VLM call per view); the final description is the view most consistent with the others. Claims are judged by `nli-deberta-v3-base` against the fact sheet; objects are checked against the 3D boxes (CHAIR) without a judge.

## Headline

**Final** = the chosen view's description (95% CI from a bootstrap over scenes). **Macro** = mean of per-scene rates. **View A** and **mean of views** show how much the self-consistency choice changes the result. **Spread** = within-scene max-min across views. **Shuffled** = each description scored against every other scene (pooled): a metric that does not get clearly worse there is not measuring content.

| Metric | Final | Macro | View A | Mean of views | Spread | Shuffled |
|---|---|---|---|---|---|---|
| CHAIR_i: invented object mentions / all object mentions | 4.0% [0.0%, 13.0%] | 3.3% | 4.0% | 5.4% | 8.3% | 19.1% |
| CHAIR_s: descriptions with an invented object | 10.0% | 10.0% | 10.0% | 10.0% | 20.0% | 36.7% |
| Object coverage: clearly visible classes mentioned | 55.8% [43.9%, 68.2%] | 54.7% | 55.8% | 54.7% | 23.8% | 45.0% |
| Claims supported by the facts | 38.0% [32.1%, 44.6%] | 39.0% | 38.3% | 34.3% | 23.1% | 28.4% |
| Claims that cannot be verified (no annotation covers them) | 43.5% | 42.3% | 44.9% | 50.1% | 26.8% | 39.3% |
| Claims supported by annotation-based facts | 26.9% | 27.6% | 27.1% | 25.5% | 20.7% | 20.5% |
| Human-sentence items covered | 44.1% [36.2%, 52.5%] | 44.4% | 40.7% | 50.3% | 17.5% | 30.1% |

## Supported claims by type

The judge is not equally reliable for every kind of claim. Its validation on claims with known truth (`validate-judge`) shows how often a *false* claim of each type is wrongly marked supported: read each row's supported rate with that error in mind. Small validation counts (e.g. 10 turn claims) are weak evidence.

| Claims about | Claims | Supported | Judge validation: false claims wrongly supported |
|---|---|---|---|
| How vehicles move (our car or others) | 14 | 28.6% | ego motion 30.0% (n=30), turn 0.0% (n=10) |
| Which objects are present | 25 | 52.0% | objects 18.5% (n=65) |
| Time of day, road condition | 16 | 62.5% | time of day 0.0% (n=30) |
| Kind of place, traffic side | 22 | 27.3% | not validated |
| Anything else (buildings, signs, weather...) | 31 | 25.8% | not validated |

## Is the description about this scene?

A generic description ("a car on a street in daylight") is supported in almost any scene. Each description is therefore also scored against every other scene, and the gap (own scene minus the other scenes) shows how much of the content is specific to this scene. The CI comes from a bootstrap over scenes and the p-value from a sign-flip test on the per-scene gaps, as in a comparison of two runs. A gap whose CI includes 0 is no evidence of scene-specific content. For reference, the oracle control (fact sheet as description) scores about +45 points on claims supported.

| Metric | Own − other scenes [95% CI] | Sign-flip p |
|---|---|---|
| Claims supported: own scene minus other scenes | 9.6% [4.3%, 15.8%] | 0.010 |
| Object coverage: own scene minus other scenes | 10.9% [3.0%, 18.3%] | 0.023 |
| Human-sentence coverage: own scene minus other scenes | 13.9% [7.2%, 21.5%] | 0.004 |

**Conclusion:** the descriptions are measurably specific to their own scene on claims, objects, the human sentence (95% CI above 0 and p < 0.05).

## Contradictions (indicative only)

A claim counts as contradicted when the NLI judge reads the whole fact sheet as contradicting it. The automatic check below shows this verdict is much less reliable than "supported", so contradiction rates are reported but not used for conclusions.

| Metric | Value |
|---|---|
| Claims contradicted | 18.5% [9.9%, 29.0%] |
| Shuffled control: claims contradicted | 32.3% |

## Output quality

| Metric | Value |
|---|---|
| Agreement between views (facts all views agree on) | 52.1% |
| Empty descriptions | 0.0% |
| Repetition loops | 0.0% |
| Mean words per description | 99.50 |
| Mean latency per call (s) | 10.37 |

## Similarity to the human sentence (secondary)

Whole-text similarity is reported for completeness. It rewards topical overlap, not correctness, which is why the claim-level checks above are the main result.

| Metric | Value |
|---|---|
| Mean embedding cosine to scene.description | 0.41 |
| Description closest to its own scene's sentence (of all scenes) | 20.0% |

## Per scene

| Scene | Human sentence | Model description (final) | Human items covered | Errors |
|---|---|---|---|---|
| scene-0061 | Parked truck, construction, intersection, turn left, following a van | The image depicts a street scene in an urban area with a mix of vehicles and pedestrians. The road is a two-way street with a white line dividing the lanes. There are several cars and a truck visible, along with a pedestrian crossing. The street is lined with trees and buildings, and there are construction barriers and orange traffic cones indicating ongoing roadwork. The lighting is natural daylight, and the sky is clear with some clouds. The car in the foreground is stopped at a traffic light, and there are no visible pedestrians in the immediate vicinity. The overall condition of the road appears to be in good condition, with no visible potholes or significant wear and tear. | 2/5 | missed: two_wheeler; 2 contradicted claim(s), indicative |
| scene-0103 | Many peds right, wait for turning car, long bike rack left, cyclist | The image depicts a city street with a mix of commercial and residential buildings. The street is lined with parked cars on both sides, and there are several pedestrians walking along the sidewalks. The sky is overcast, suggesting a cloudy day. The road conditions appear to be clear, with no visible traffic or pedestrians in the immediate vicinity. The street is well-lit, with streetlights and traffic lights visible. The car in the foreground is driving down the street, and there are no visible obstacles or hazards in the immediate vicinity. | 1/4 | missed: traffic_cone, truck, two_wheeler; 6 contradicted claim(s), indicative |
| scene-0553 | Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller | The image depicts a city street scene with a clear sky and a few scattered clouds. The street is a four-lane road with a pedestrian crossing marked by white lines. There are several traffic lights visible, including a red light at the intersection. The road is relatively empty, with only a few vehicles and pedestrians visible. The buildings in the background are modern and tall, suggesting a commercial or business district. The lighting is natural daylight, indicating it is daytime. The road users include pedestrians and a few cars, with some vehicles stopped at the traffic lights. The car in the foreground is driving forward, while the others are either waiting or moving through the intersection. | 2/5 | missed: barrier, bus, truck, two_wheeler; 3 contradicted claim(s), indicative |
| scene-0655 | Parking lot, parked cars, jaywalker, bendy bus, gardening vehicles | The image depicts a city street with a mix of commercial and residential buildings. The street is lined with parked cars and a few vehicles in motion. There are construction cones and traffic signs indicating roadwork or maintenance. The sky is clear, suggesting it is a sunny day. The road appears to be relatively empty, with only a few pedestrians visible. The buildings on either side of the street have large windows and some have fire escapes. The overall atmosphere is calm and typical of a busy urban area. | 2/5 | missed: bus, truck; 2 contradicted claim(s), indicative |
| scene-0757 | Arrive at busy intersection, bus, wait at intersection, bicycle, peds | The image depicts a busy urban street scene with various vehicles and construction equipment. The sky is overcast, suggesting a cloudy day. The street is lined with buildings, some of which are under construction with scaffolding. There are multiple traffic lights, street signs, and a variety of vehicles, including a Coca-Cola delivery van, a bus, and a truck. A cyclist is visible on the road, and the road appears to be in a state of moderate traffic. The overall atmosphere is busy and active, typical of a city center. | 3/5 | missed: traffic_cone; 3 contradicted claim(s), indicative |
| scene-0796 | Scooter, peds on sidewalk, bus, cars, truck, fake construction worker, bicycle, cross intersection, car overtaking us | The drive takes place on a two-lane road with a yellow center line, surrounded by trees and greenery. The road is well-maintained, with clear lane markings and a few vehicles visible. There are traffic lights at the intersection, and a blue sign indicating the end of a school zone. The sky is clear, suggesting a sunny day. The car is driving forward, following the lane markings, and appears to be in a residential or suburban area. | 3/9 | missed: bus, pedestrian |
| scene-0916 | Parking lot, bicycle rack, parked bicycles, bus, many peds, parked scooters, parked motorcycle | The image depicts a parking lot with several cars parked along the sides of the road. The parking lot is surrounded by trees and a building with multiple floors. The lighting is natural, suggesting it is daytime. There are people walking in the background, and the road appears to be clear of any significant obstructions. The car in the foreground is driving away from the camera, and the road is empty except for the car and a few other vehicles. | 2/7 | missed: truck, two_wheeler; 1 contradicted claim(s), indicative |
| scene-1077 | Night, big street, bus stop, high speed, construction vehicle | The image depicts a nighttime drive on a multi-lane road with a few cars visible in the distance. The road is well-lit by streetlights and the headlights of the vehicles, creating a bright and somewhat chaotic scene. The sky is dark, indicating it is nighttime. The road is wet, as evidenced by the reflections on the road surface, suggesting recent rain. The cars are driving in the same direction, with some vehicles visible in the foreground and others further back. The overall atmosphere is busy and somewhat chaotic, with the headlights and streetlights creating a high-contrast environment. The car in the foreground appears to be driving forward, following the traffic flow. | 3/5 | missed: barrier, truck |
| scene-1094 | Night, after rain, many peds, PMD, ped with bag, jaywalker, truck, scooter | The image depicts a nighttime scene on a city street, likely in an urban area. The street is busy with traffic, including cars and trucks, and there are pedestrians walking along the sidewalk. The lighting is dim, with streetlights and vehicle headlights illuminating the area. The road conditions appear to be wet, as evidenced by the reflections on the pavement and the presence of puddles. There are several buildings along the street, including a large shopping center with illuminated signs. The overall atmosphere is quiet and somewhat deserted, with no visible pedestrians or vehicles in the immediate foreground. The car in the foreground is driving down the street, following the traffic flow. | 4/8 | invented: truck; missed: two_wheeler; 2 contradicted claim(s), indicative |
| scene-1100 | Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting | The image depicts a nighttime urban scene with a busy street intersection. The street is wet, indicating recent rain, and the road is illuminated by streetlights and vehicle headlights. There are several cars and a motorcycle visible, with their headlights on, suggesting they are either waiting to turn or have just turned. The traffic appears to be moderate, with no visible congestion. There is a pedestrian crossing with a blue sign, and a bus stop with a sign and a bench. The background features tall buildings with illuminated windows, and a bridge or overpass with greenery on the sides. The overall atmosphere is calm and quiet, with no visible pedestrians or vehicles in motion. | 4/6 | missed: pedestrian; 1 contradicted claim(s), indicative |

## Details per scene

<details><summary>scene-0061: view 2 chosen, view agreement 50.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving.
- Our car turns left.
- There are cars.
- There are trucks.
- Most trucks are stopped.
- There are pedestrians.
- Most pedestrians are walking.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are parked.
- There are traffic cones.
- There are road barriers.

**Claims of the description**

- **supported**: The image depicts a street scene in an urban area with a mix of vehicles and pedestrians.  
  ↳ supporting fact: _The drive is in Singapore._
- **neutral**: The road is a two-way street with a white line dividing the lanes.
- **supported**: There are several cars and a truck visible, along with a pedestrian crossing.  
  ↳ supporting fact: _Most trucks are stopped._
- **neutral**: The street is lined with trees and buildings.
- **neutral**: There are construction barriers and orange traffic cones indicating ongoing roadwork.
- **supported**: The lighting is natural daylight.  
  ↳ supporting fact: _It is daytime._
- **neutral**: The sky is clear with some clouds.
- **neutral**: The car in the foreground is stopped at a traffic light.
- **contradicted**: There are no visible pedestrians in the immediate vicinity.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The overall condition of the road appears to be in good condition.
- **contradicted**: The scene shows: with no visible potholes or significant wear and tear.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **neutral**: Parked truck
- **supported**: construction
- **supported**: intersection
- **neutral**: turn left
- **neutral**: following a van

</details>

<details><summary>scene-0103: view 2 chosen, view agreement 60.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- Vehicles drive on the right side of the road.
- The drive is in Boston.
- Our car is driving.
- Our car drives straight ahead.
- There are cars.
- Most cars are parked.
- There are trucks.
- Most trucks are parked.
- There are no buses.
- There are pedestrians.
- Most pedestrians are walking.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are parked.
- There are traffic cones.
- There are no road barriers.

**Claims of the description**

- **contradicted**: The image depicts a city street with a mix of commercial and residential buildings.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The street is lined with parked cars on both sides.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: There are several pedestrians walking along the sidewalks.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The sky is overcast.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The scene shows: suggesting a cloudy day.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The road conditions appear to be clear.
- **contradicted**: The scene shows: with no visible traffic or pedestrians in the immediate vicinity.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The street is well-lit.  
  ↳ supporting fact: _It is daytime._
- **supported**: The scene shows: with streetlights and traffic lights visible.  
  ↳ supporting fact: _There are traffic cones._
- **supported**: The car in the foreground is driving down the street.  
  ↳ supporting fact: _Our car is driving._
- **supported**: There are no visible obstacles or hazards in the immediate vicinity.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **supported**: Many peds right
- **contradicted**: wait for turning car
- **contradicted**: long bike rack left
- **contradicted**: cyclist

</details>

<details><summary>scene-0553: view 0 chosen, view agreement 75.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- Vehicles drive on the right side of the road.
- The drive is in Boston.
- Our car is stopped.
- There are cars.
- Most cars are moving.
- There are trucks.
- Most trucks are moving.
- There are buses.
- Most buses are moving.
- There are pedestrians.
- Most pedestrians are walking.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are ridden.
- There are no traffic cones.
- There are road barriers.

**Claims of the description**

- **neutral**: The image depicts a city street scene with a clear sky and a few scattered clouds.
- **neutral**: The street is a four-lane road with a pedestrian crossing marked by white lines.
- **neutral**: There are several traffic lights visible, including a red light at the intersection.
- **contradicted**: The road is relatively empty.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The scene shows: with only a few vehicles and pedestrians visible.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The buildings in the background are modern and tall.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The scene shows: suggesting a commercial or business district.  
  ↳ supporting fact: _The drive is in Boston._
- **supported**: The lighting is natural daylight.  
  ↳ supporting fact: _It is daytime._
- **supported**: The scene shows: indicating it is daytime.  
  ↳ supporting fact: _The drive passes an intersection._
- **neutral**: The road users include pedestrians and a few cars.
- **neutral**: The scene shows: with some vehicles stopped at the traffic lights.
- **supported**: The car in the foreground is driving forward.  
  ↳ supporting fact: _The drive passes an intersection._
- **neutral**: The others are either waiting or moving through the intersection.

**Human sentence items**

- **supported**: Wait at intersection
- **contradicted**: bicycle
- **contradicted**: large truck
- **supported**: peds crossing crosswalk
- **contradicted**: ped with stroller

</details>

<details><summary>scene-0655: view 0 chosen, view agreement 42.9%</summary>

**Fact sheet (reference)**

- It is daytime.
- The scene is in a parking lot.
- Vehicles drive on the right side of the road.
- The drive is in Boston.
- Our car is driving.
- Our car drives straight ahead.
- There are cars.
- Most cars are parked.
- There are trucks.
- Most trucks are parked.
- There are buses.
- Most buses are stopped.
- There are pedestrians.
- Most pedestrians are walking.
- There are no bicycles or motorcycles.
- There are traffic cones.
- There are no road barriers.

**Claims of the description**

- **supported**: The image depicts a city street with a mix of commercial and residential buildings.  
  ↳ supporting fact: _Most buses are stopped._
- **supported**: The street is lined with parked cars and a few vehicles in motion.  
  ↳ supporting fact: _Our car is driving._
- **neutral**: There are construction cones and traffic signs indicating roadwork or maintenance.
- **neutral**: The sky is clear.
- **supported**: The scene shows: suggesting it is a sunny day.  
  ↳ supporting fact: _It is daytime._
- **supported**: The road appears to be relatively empty.  
  ↳ supporting fact: _There are no road barriers._
- **contradicted**: The scene shows: with only a few pedestrians visible.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The buildings on either side of the street have large windows and some have fire escapes.
- **contradicted**: The overall atmosphere is calm and typical of a busy urban area.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **supported**: Parking lot
- **supported**: parked cars
- **contradicted**: jaywalker
- **contradicted**: bendy bus
- **contradicted**: gardening vehicles

</details>

<details><summary>scene-0757: view 0 chosen, view agreement 37.5%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- Vehicles drive on the right side of the road.
- The drive is in Boston.
- Our car is moving slowly.
- Our car stops for part of the drive.
- Our car drives straight ahead.
- There are cars.
- Most cars are moving.
- There are trucks.
- There are buses.
- Most buses are moving.
- There are no pedestrians.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are ridden.
- There are traffic cones.
- There are no road barriers.

**Claims of the description**

- **supported**: The image depicts a busy urban street scene with various vehicles and construction equipment.  
  ↳ supporting fact: _There are traffic cones._
- **contradicted**: The sky is overcast.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The scene shows: suggesting a cloudy day.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The street is lined with buildings, some of which are under construction with scaffolding.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: There are multiple traffic lights, street signs.
- **supported**: A variety of vehicles, including a Coca-Cola delivery van, a bus.  
  ↳ supporting fact: _Most buses are moving._
- **supported**: A truck.  
  ↳ supporting fact: _There are trucks._
- **supported**: A cyclist is visible on the road.  
  ↳ supporting fact: _Most bicycles or motorcycles are ridden._
- **supported**: The road appears to be in a state of moderate traffic.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._
- **neutral**: The overall atmosphere is busy and active, typical of a city center.

**Human sentence items**

- **neutral**: Arrive at busy intersection
- **supported**: bus
- **neutral**: wait at intersection
- **supported**: bicycle
- **supported**: peds

</details>

<details><summary>scene-0796: view 2 chosen, view agreement 20.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving fast.
- Our car drives straight ahead.
- There are cars.
- Most cars are moving.
- There are no trucks.
- There are buses.
- Most buses are moving.
- There are pedestrians.
- Most pedestrians are walking.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **neutral**: The drive takes place on a two-lane road with a yellow center line, surrounded by trees and greenery.
- **neutral**: The road is well-maintained.
- **supported**: The scene shows: with clear lane markings and a few vehicles visible.  
  ↳ supporting fact: _There are cars._
- **neutral**: There are traffic lights at the intersection.
- **neutral**: A blue sign indicating the end of a school zone.
- **neutral**: The sky is clear.
- **supported**: The scene shows: suggesting a sunny day.  
  ↳ supporting fact: _It is daytime._
- **neutral**: The car is driving forward, following the lane markings.
- **neutral**: Appears to be in a residential or suburban area.

**Human sentence items**

- **neutral**: Scooter
- **neutral**: peds on sidewalk
- **neutral**: bus
- **supported**: cars
- **neutral**: truck
- **neutral**: fake construction worker
- **contradicted**: bicycle
- **supported**: cross intersection
- **supported**: car overtaking us

</details>

<details><summary>scene-0916: view 0 chosen, view agreement 33.3%</summary>

**Fact sheet (reference)**

- It is daytime.
- The scene is in a parking lot.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving.
- Our car turns right.
- There are cars.
- Most cars are parked.
- There are trucks.
- Most trucks are parked.
- There are no buses.
- There are pedestrians.
- Most pedestrians are standing.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are parked.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **supported**: The image depicts a parking lot with several cars parked along the sides of the road.  
  ↳ supporting fact: _Most cars are parked._
- **contradicted**: The parking lot is surrounded by trees and a building with multiple floors.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The lighting is natural.  
  ↳ supporting fact: _It is daytime._
- **supported**: The scene shows: suggesting it is daytime.  
  ↳ supporting fact: _There are pedestrians._
- **supported**: There are people walking in the background.  
  ↳ supporting fact: _There are pedestrians._
- **supported**: The road appears to be clear of any significant obstructions.  
  ↳ supporting fact: _There are no road barriers._
- **neutral**: The car in the foreground is driving away from the camera.
- **neutral**: The road is empty except for the car and a few other vehicles.

**Human sentence items**

- **supported**: Parking lot
- **contradicted**: bicycle rack
- **contradicted**: parked bicycles
- **neutral**: bus
- **supported**: many peds
- **contradicted**: parked scooters
- **contradicted**: parked motorcycle

</details>

<details><summary>scene-1077: view 0 chosen, view agreement 80.0%</summary>

**Fact sheet (reference)**

- It is night.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving fast.
- Our car turns left.
- There are cars.
- Most cars are moving.
- There are trucks.
- Most trucks are moving.
- There are no pedestrians.
- There are no traffic cones.
- There are road barriers.

**Claims of the description**

- **neutral**: The image depicts a nighttime drive on a multi-lane road with a few cars visible in the distance.
- **neutral**: The road is well-lit by streetlights and the headlights of the vehicles.
- **neutral**: The scene shows: creating a bright and somewhat chaotic scene.
- **supported**: The sky is dark.  
  ↳ supporting fact: _It is night._
- **supported**: The scene shows: indicating it is nighttime.  
  ↳ supporting fact: _There are trucks._
- **neutral**: The road is wet, as evidenced by the reflections on the road surface.
- **neutral**: The scene shows: suggesting recent rain.
- **neutral**: The cars are driving in the same direction.
- **supported**: The scene shows: with some vehicles visible in the foreground and others further back.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **neutral**: The overall atmosphere is busy and somewhat chaotic.
- **supported**: The scene shows: with the headlights and streetlights creating a high-contrast environment.  
  ↳ supporting fact: _There are cars._
- **neutral**: The car in the foreground appears to be driving forward, following the traffic flow.

**Human sentence items**

- **supported**: Night
- **supported**: big street
- **neutral**: bus stop
- **supported**: high speed
- **neutral**: construction vehicle

</details>

<details><summary>scene-1094: view 0 chosen, view agreement 62.5%</summary>

**Fact sheet (reference)**

- It is night.
- The road is wet.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving.
- Our car turns left.
- There are cars.
- Most cars are stopped.
- There are no trucks.
- There are pedestrians.
- Most pedestrians are walking.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are ridden.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **supported**: The image depicts a nighttime scene on a city street, likely in an urban area.  
  ↳ supporting fact: _It is night._
- **contradicted**: The street is busy with traffic, including cars and trucks.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: There are pedestrians walking along the sidewalk.
- **supported**: The lighting is dim.  
  ↳ supporting fact: _It is night._
- **supported**: The scene shows: with streetlights and vehicle headlights illuminating the area.  
  ↳ supporting fact: _Our car turns left._
- **supported**: The road conditions appear to be wet, as evidenced by the reflections on the pavement and the presence of puddles.  
  ↳ supporting fact: _The road is wet._
- **neutral**: There are several buildings along the street, including a large shopping center with illuminated signs.
- **neutral**: The overall atmosphere is quiet and somewhat deserted.
- **contradicted**: The scene shows: with no visible pedestrians or vehicles in the immediate foreground.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The car in the foreground is driving down the street, following the traffic flow.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._

**Human sentence items**

- **supported**: Night
- **contradicted**: after rain
- **supported**: many peds
- **supported**: PMD
- **contradicted**: ped with bag
- **contradicted**: jaywalker
- **supported**: truck
- **contradicted**: scooter

</details>

<details><summary>scene-1100: view 0 chosen, view agreement 60.0%</summary>

**Fact sheet (reference)**

- It is night.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is stopped.
- There are cars.
- Most cars are moving.
- There are no trucks.
- There are pedestrians.
- Most pedestrians are walking.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are ridden.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **supported**: The image depicts a nighttime urban scene with a busy street intersection.  
  ↳ supporting fact: _Most cars are moving._
- **neutral**: The street is wet.
- **neutral**: The scene shows: indicating recent rain.
- **neutral**: The road is illuminated by streetlights and vehicle headlights.
- **supported**: There are several cars and a motorcycle visible.  
  ↳ supporting fact: _There are bicycles or motorcycles._
- **neutral**: The scene shows: with their headlights on.
- **supported**: The scene shows: suggesting they are either waiting to turn or have just turned.  
  ↳ supporting fact: _There are cars._
- **neutral**: The traffic appears to be moderate.
- **supported**: The scene shows: with no visible congestion.  
  ↳ supporting fact: _There are no road barriers._
- **neutral**: There is a pedestrian crossing with a blue sign.
- **neutral**: A bus stop with a sign and a bench.
- **neutral**: The background features tall buildings with illuminated windows.
- **supported**: A bridge or overpass with greenery on the sides.  
  ↳ supporting fact: _Most pedestrians are walking._
- **neutral**: The overall atmosphere is calm and quiet.
- **contradicted**: The scene shows: with no visible pedestrians or vehicles in motion.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **supported**: Night
- **supported**: peds in sidewalk
- **supported**: peds cross crosswalk
- **contradicted**: scooter
- **contradicted**: PMD
- **supported**: difficult lighting

</details>
