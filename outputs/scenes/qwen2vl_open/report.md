# Scene-level evaluation: `Qwen2-VL-2B-Instruct` with prompt `scene_open@62f61a19`

10 scenes. Each scene is shown as 3 views of 6 frames (one VLM call per view); the final description is the view most consistent with the others. Claims are judged by `nli-deberta-v3-base` against the fact sheet; objects are checked against the 3D boxes (CHAIR) without a judge.

## Headline

**Final** = the chosen view's description (95% CI from a bootstrap over scenes). **Macro** = mean of per-scene rates. **View A** and **mean of views** show how much the self-consistency choice changes the result. **Spread** = within-scene max-min across views. **Shuffled** = each description scored against every other scene (pooled): a metric that does not get clearly worse there is not measuring content.

| Metric | Final | Macro | View A | Mean of views | Spread | Shuffled |
|---|---|---|---|---|---|---|
| CHAIR_i: invented object mentions / all object mentions | 4.3% [0.0%, 12.5%] | 2.8% | 9.1% | 6.0% | 13.0% | 18.4% |
| CHAIR_s: descriptions with an invented object | 10.0% | 10.0% | 20.0% | 13.3% | 30.0% | 33.3% |
| Object coverage: clearly visible classes mentioned | 51.2% [35.9%, 64.7%] | 48.8% | 46.5% | 48.5% | 16.8% | 40.6% |
| Claims supported by the facts | 21.0% [11.1%, 30.7%] | 20.3% | 21.7% | 21.5% | 19.9% | 9.9% |
| Claims that cannot be verified (no annotation covers them) | 53.0% | 49.3% | 55.7% | 58.7% | 24.7% | 53.6% |
| Claims supported by annotation-based facts | 19.0% | 18.5% | 18.9% | 19.2% | 15.3% | 8.4% |
| Human-sentence items covered | 35.6% [24.2%, 47.3%] | 36.3% | 37.3% | 37.3% | 20.5% | 26.7% |

## Supported claims by type

The judge is not equally reliable for every kind of claim. Its validation on claims with known truth (`validate-judge`) shows how often a *false* claim of each type is wrongly marked supported: read each row's supported rate with that error in mind. Small validation counts (e.g. 10 turn claims) are weak evidence.

| Claims about | Claims | Supported | Judge validation: false claims wrongly supported |
|---|---|---|---|
| How vehicles move (our car or others) | 24 | 8.3% | ego motion 30.0% (n=30), turn 0.0% (n=10) |
| Which objects are present | 25 | 48.0% | objects 18.5% (n=65) |
| Time of day, road condition | 5 | 40.0% | time of day 0.0% (n=30) |
| Kind of place, traffic side | 22 | 0.0% | not validated |
| Anything else (buildings, signs, weather...) | 24 | 20.8% | not validated |

## Is the description about this scene?

A generic description ("a car on a street in daylight") is supported in almost any scene. Each description is therefore also scored against every other scene, and the gap (own scene minus the other scenes) shows how much of the content is specific to this scene. The CI comes from a bootstrap over scenes and the p-value from a sign-flip test on the per-scene gaps, as in a comparison of two runs. A gap whose CI includes 0 is no evidence of scene-specific content. For reference, the oracle control (fact sheet as description) scores about +45 points on claims supported.

| Metric | Own − other scenes [95% CI] | Sign-flip p |
|---|---|---|
| Claims supported: own scene minus other scenes | 11.1% [3.9%, 18.8%] | 0.016 |
| Object coverage: own scene minus other scenes | 10.6% [5.0%, 16.7%] | 0.012 |
| Human-sentence coverage: own scene minus other scenes | 8.9% [-3.7%, 21.8%] | 0.186 |

**Conclusion:** the descriptions are measurably specific to their own scene on claims, objects (95% CI above 0 and p < 0.05).

## Contradictions (indicative only)

A claim counts as contradicted when the NLI judge reads the whole fact sheet as contradicting it. The automatic check below shows this verdict is much less reliable than "supported", so contradiction rates are reported but not used for conclusions.

| Metric | Value |
|---|---|
| Claims contradicted | 26.0% [10.4%, 45.1%] |
| Shuffled control: claims contradicted | 36.6% |

## Output quality

| Metric | Value |
|---|---|
| Agreement between views (facts all views agree on) | 51.0% |
| Empty descriptions | 0.0% |
| Repetition loops | 20.0% |
| Mean words per description | 100.70 |
| Mean latency per call (s) | 10.19 |

## Similarity to the human sentence (secondary)

Whole-text similarity is reported for completeness. It rewards topical overlap, not correctness, which is why the claim-level checks above are the main result.

| Metric | Value |
|---|---|
| Mean embedding cosine to scene.description | 0.39 |
| Description closest to its own scene's sentence (of all scenes) | 20.0% |

## Per scene

| Scene | Human sentence | Model description (final) | Human items covered | Errors |
|---|---|---|---|---|
| scene-0061 | Parked truck, construction, intersection, turn left, following a van | The drive begins with a white car driving down a street lined with trees and buildings. The car turns left at an intersection, passing a construction site with orange traffic cones and a large orange excavator. The car then continues down the street, passing more traffic and construction barriers. The drive ends with the car turning right at another intersection, passing more traffic and construction barriers. The street is quiet and empty, with only a few cars and pedestrians visible. | 3/5 | missed: two_wheeler; 3 contradicted claim(s), indicative |
| scene-0103 | Many peds right, wait for turning car, long bike rack left, cyclist | The drive begins with a car driving down a city street, passing through a series of buildings with large windows and brick facades. The street is lined with parked cars and pedestrians, and there are traffic lights and street signs visible. As the drive progresses, the car turns onto a different street, passing through a different set of buildings and streets. The drive continues through a series of intersections, with traffic lights and street signs visible. The buildings on both sides of the street are similar in design, with large windows and brick facades. The sky is overcast, and the overall atmosphere is busy and bustling. | 1/4 | missed: traffic_cone, truck, two_wheeler; 6 contradicted claim(s), indicative |
| scene-0553 | Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller | The drive begins with a straight path through a city intersection, with traffic lights and construction cranes visible in the background. As the drive progresses, the camera captures a group of pedestrians crossing the street, adding a dynamic element to the otherwise static scene. The camera then shifts to a different angle, showing a different section of the cityscape, with more buildings and a different perspective on the intersection. The drive continues with a straight path, passing through more traffic and pedestrians, before finally ending with a view of the intersection from a different angle. | 1/5 | missed: barrier, bus, car, truck; 2 contradicted claim(s), indicative |
| scene-0655 | Parking lot, parked cars, jaywalker, bendy bus, gardening vehicles | The drive begins with a white truck driving down a two-lane road with a median. The truck is followed by a white car and a white SUV. As the drive continues, a white bus appears on the right side of the road. The road is lined with trees and buildings on both sides. The sky is clear, and the sun is shining. The drive ends with the white bus driving away from the camera. | 1/5 | missed: pedestrian, traffic_cone; 4 contradicted claim(s), indicative |
| scene-0757 | Arrive at busy intersection, bus, wait at intersection, bicycle, peds | The drive begins with a red van driving down a street, followed by a white car. As the drive progresses, a silver car appears, and a cyclist rides by. The drive then continues with a white truck and a silver car. The cyclist returns, and the drive ends with a white car driving down the street. | 2/5 | missed: bus, traffic_cone; 7 contradicted claim(s), indicative |
| scene-0796 | Scooter, peds on sidewalk, bus, cars, truck, fake construction worker, bicycle, cross intersection, car overtaking us | The drive begins on a two-lane road with a yellow line in the center. The road is flanked by trees and a sidewalk on the left. There are several traffic signs and streetlights along the road. As the drive progresses, the road widens and becomes a four-lane road with a yellow line in the center. The road is flanked by more trees and a sidewalk on the left. The road continues to widen and becomes a four-lane road with a yellow line in the center. The road is flanked by more trees and a sidewalk on the left. The road continues to widen and becomes a four-lane road with a yellow line in the center. The road is flanked by more trees and a sidewalk on the left. The road continues to widen and becomes a four-lane road with a yellow line in the center. The road is flanked by more trees and a sidewalk on the left. The road continues to widen and becomes a four-lane road with | 1/9 | missed: car, pedestrian, truck |
| scene-0916 | Parking lot, bicycle rack, parked bicycles, bus, many peds, parked scooters, parked motorcycle | The drive begins with a person walking towards a parking lot. As the camera follows the person, they eventually reach a parking space. The camera then captures a group of people standing near a bus stop, with a bus waiting nearby. The camera then pans to the right, showing a parking lot with several cars parked in it. The camera then returns to the parking lot, capturing a person walking towards the parking lot. The camera then pans to the left, showing a parking lot with a truck parked in it. The camera then returns to the parking lot, capturing a person walking towards the parking lot. The camera then pans to the right, showing a parking lot with a truck parked in it. The camera then returns to the parking lot, capturing a person walking towards the parking lot. The camera then pans to the left, showing a parking lot with a truck parked in it. The camera then returns to the parking lot, capturing a person walking towards the parking lot. The camera then pans to the | 3/7 | invented: bus; missed: two_wheeler |
| scene-1077 | Night, big street, bus stop, high speed, construction vehicle | The image depicts a nighttime drive on a road with multiple lanes. The road is illuminated by streetlights and the headlights of the vehicles. The scene is dark, with only the headlights and streetlights providing illumination. The road is lined with trees on both sides, and there are several vehicles in the lanes, including a car in the foreground and others further down the road. The overall atmosphere is calm and quiet, with no visible traffic or pedestrians. The image captures the quietness of the night drive, with the headlights and streetlights providing the only source of light. | 2/5 | missed: barrier, truck; 3 contradicted claim(s), indicative |
| scene-1094 | Night, after rain, many peds, PMD, ped with bag, jaywalker, truck, scooter | The image depicts a nighttime scene on a city street, with a car driving down the road. The street is lined with trees and buildings, and there are several vehicles and pedestrians visible. The road has white lines and arrows indicating directions, and there are traffic lights and street signs visible. The overall atmosphere is calm and quiet, with the only sound being the occasional car engine or pedestrian footsteps. | 3/8 | missed: bus, two_wheeler |
| scene-1100 | Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting | The image depicts a nighttime scene on a city street, with several cars and a motorcycle visible. The street is wet, indicating recent rain, and there are traffic lights and signs visible. The scene includes a bridge with greenery on the left side and a building with a sign on the right side. The overall atmosphere is calm and quiet, with no visible pedestrians or people. The image captures the quietness of the night and the stillness of the city. | 4/6 | missed: pedestrian; 1 contradicted claim(s), indicative |

## Details per scene

<details><summary>scene-0061: view 1 chosen, view agreement 50.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving.
- Our car turns left.
- There are cars.
- Most cars are moving.
- There are trucks.
- Most trucks are stopped.
- There are pedestrians.
- Most pedestrians are walking.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are parked.
- There are traffic cones.
- There are road barriers.

**Claims of the description**

- **neutral**: The drive begins with a white car driving down a street lined with trees and buildings.
- **supported**: The car turns left at an intersection.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **neutral**: The scene shows: passing a construction site with orange traffic cones and a large orange excavator.
- **supported**: The car then continues down the street.  
  ↳ supporting fact: _There are bicycles or motorcycles._
- **supported**: The scene shows: passing more traffic and construction barriers.  
  ↳ supporting fact: _There are bicycles or motorcycles._
- **contradicted**: The drive ends with the car turning right at another intersection.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The scene shows: passing more traffic and construction barriers.  
  ↳ supporting fact: _There are bicycles or motorcycles._
- **contradicted**: The street is quiet and empty.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The scene shows: with only a few cars and pedestrians visible.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **contradicted**: Parked truck
- **supported**: construction
- **supported**: intersection
- **supported**: turn left
- **neutral**: following a van

</details>

<details><summary>scene-0103: view 0 chosen, view agreement 100.0%</summary>

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
- There are traffic cones.
- There are no road barriers.

**Claims of the description**

- **contradicted**: The drive begins with a car driving down a city street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The scene shows: passing through a series of buildings with large windows and brick facades.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The street is lined with parked cars and pedestrians.  
  ↳ supporting fact: _It is daytime._
- **neutral**: There are traffic lights and street signs visible.
- **contradicted**: As the drive progresses, the car turns onto a different street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The scene shows: passing through a different set of buildings and streets.  
  ↳ supporting fact: _The drive is in Boston._
- **neutral**: The drive continues through a series of intersections.
- **neutral**: The scene shows: with traffic lights and street signs visible.
- **contradicted**: The buildings on both sides of the street are similar in design.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The scene shows: with large windows and brick facades.  
  ↳ supporting fact: _Most pedestrians are walking._
- **contradicted**: The sky is overcast.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The overall atmosphere is busy and bustling.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **supported**: Many peds right
- **neutral**: wait for turning car
- **neutral**: long bike rack left
- **contradicted**: cyclist

</details>

<details><summary>scene-0553: view 1 chosen, view agreement 66.7%</summary>

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
- There are no bicycles or motorcycles.
- There are no traffic cones.
- There are road barriers.

**Claims of the description**

- **contradicted**: The drive begins with a straight path through a city intersection.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The scene shows: with traffic lights and construction cranes visible in the background.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: As the drive progresses, the camera captures a group of pedestrians crossing the street.
- **neutral**: The scene shows: adding a dynamic element to the otherwise static scene.
- **supported**: The camera then shifts to a different angle.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: The scene shows: showing a different section of the cityscape.  
  ↳ supporting fact: _The drive is in Boston._
- **neutral**: The scene shows: with more buildings and a different perspective on the intersection.
- **neutral**: The drive continues with a straight path.
- **neutral**: The scene shows: passing through more traffic and pedestrians, before finally ending with a view of the intersection from a different angle.

**Human sentence items**

- **contradicted**: Wait at intersection
- **contradicted**: bicycle
- **contradicted**: large truck
- **supported**: peds crossing crosswalk
- **contradicted**: ped with stroller

</details>

<details><summary>scene-0655: view 0 chosen, view agreement 50.0%</summary>

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

- **contradicted**: The drive begins with a white truck driving down a two-lane road with a median.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The truck is followed by a white car and a white SUV.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: As the drive continues, a white bus appears on the right side of the road.
- **contradicted**: The road is lined with trees and buildings on both sides.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The sky is clear.
- **neutral**: The sun is shining.
- **contradicted**: The drive ends with the white bus driving away from the camera.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **contradicted**: Parking lot
- **contradicted**: parked cars
- **neutral**: jaywalker
- **neutral**: bendy bus
- **supported**: gardening vehicles

</details>

<details><summary>scene-0757: view 0 chosen, view agreement 20.0%</summary>

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

- **contradicted**: The drive begins with a red van driving down a street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The scene shows: followed by a white car.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: As the drive progresses, a silver car appears.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: A cyclist rides by.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The drive then continues with a white truck and a silver car.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The cyclist returns.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The drive ends with a white car driving down the street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **neutral**: Arrive at busy intersection
- **contradicted**: bus
- **contradicted**: wait at intersection
- **supported**: bicycle
- **supported**: peds

</details>

<details><summary>scene-0796: view 0 chosen, view agreement 0.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving fast.
- Our car drives straight ahead.
- There are cars.
- Most cars are moving.
- There are trucks.
- Most trucks are moving.
- There are pedestrians.
- Most pedestrians are walking.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **neutral**: The drive begins on a two-lane road with a yellow line in the center.
- **neutral**: The road is flanked by trees and a sidewalk on the left.
- **neutral**: There are several traffic signs and streetlights along the road.
- **neutral**: As the drive progresses, the road widens and becomes a four-lane road with a yellow line in the center.
- **neutral**: The road is flanked by more trees and a sidewalk on the left.
- **neutral**: The road continues to widen and becomes a four-lane road with a yellow line in the center.
- **neutral**: The road is flanked by more trees and a sidewalk on the left.
- **neutral**: The road continues to widen and becomes a four-lane road with a yellow line in the center.
- **neutral**: The road is flanked by more trees and a sidewalk on the left.
- **neutral**: The road continues to widen and becomes a four-lane road with a yellow line in the center.
- **neutral**: The road is flanked by more trees and a sidewalk on the left.
- **neutral**: The road continues to widen and becomes a four-lane road with.

**Human sentence items**

- **neutral**: Scooter
- **neutral**: peds on sidewalk
- **neutral**: bus
- **supported**: cars
- **neutral**: truck
- **neutral**: fake construction worker
- **neutral**: bicycle
- **neutral**: cross intersection
- **neutral**: car overtaking us

</details>

<details><summary>scene-0916: view 1 chosen, view agreement 60.0%</summary>

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

- **neutral**: The drive begins with a person walking towards a parking lot.
- **supported**: As the camera follows the person, they eventually reach a parking space.  
  ↳ supporting fact: _Most bicycles or motorcycles are parked._
- **neutral**: The camera then captures a group of people standing near a bus stop.
- **neutral**: The scene shows: with a bus waiting nearby.
- **neutral**: The camera then pans to the right.
- **supported**: The scene shows: showing a parking lot with several cars parked in it.  
  ↳ supporting fact: _Most cars are parked._
- **neutral**: The camera then returns to the parking lot, capturing a person walking towards the parking lot.
- **neutral**: The camera then pans to the left.
- **supported**: The scene shows: showing a parking lot with a truck parked in it.  
  ↳ supporting fact: _Most trucks are parked._
- **neutral**: The camera then returns to the parking lot, capturing a person walking towards the parking lot.
- **neutral**: The camera then pans to the right.
- **supported**: The scene shows: showing a parking lot with a truck parked in it.  
  ↳ supporting fact: _Most trucks are parked._
- **neutral**: The camera then returns to the parking lot, capturing a person walking towards the parking lot.
- **neutral**: The camera then pans to the left.
- **supported**: The scene shows: showing a parking lot with a truck parked in it.  
  ↳ supporting fact: _Most trucks are parked._
- **neutral**: The camera then returns to the parking lot, capturing a person walking towards the parking lot.
- **neutral**: The camera then pans to the.

**Human sentence items**

- **supported**: Parking lot
- **contradicted**: bicycle rack
- **contradicted**: parked bicycles
- **supported**: bus
- **supported**: many peds
- **contradicted**: parked scooters
- **contradicted**: parked motorcycle

</details>

<details><summary>scene-1077: view 0 chosen, view agreement 75.0%</summary>

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

- **neutral**: The image depicts a nighttime drive on a road with multiple lanes.
- **neutral**: The road is illuminated by streetlights and the headlights of the vehicles.
- **supported**: The scene is dark.  
  ↳ supporting fact: _It is night._
- **neutral**: The scene shows: with only the headlights and streetlights providing illumination.
- **contradicted**: The road is lined with trees on both sides.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: There are several vehicles in the lanes, including a car in the foreground and others further down the road.
- **neutral**: The overall atmosphere is calm and quiet.
- **contradicted**: The scene shows: with no visible traffic or pedestrians.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The image captures the quietness of the night drive.
- **contradicted**: The scene shows: with the headlights and streetlights providing the only source of light.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **supported**: Night
- **supported**: big street
- **neutral**: bus stop
- **contradicted**: high speed
- **neutral**: construction vehicle

</details>

<details><summary>scene-1094: view 2 chosen, view agreement 60.0%</summary>

**Fact sheet (reference)**

- It is night.
- The road is wet.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving.
- Our car turns left.
- There are cars.
- There are no trucks.
- There are buses.
- Most buses are moving.
- There are pedestrians.
- Most pedestrians are walking.
- There are bicycles or motorcycles.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **supported**: The image depicts a nighttime scene on a city street.  
  ↳ supporting fact: _There are pedestrians._
- **supported**: The scene shows: with a car driving down the road.  
  ↳ supporting fact: _Our car is driving._
- **neutral**: The street is lined with trees and buildings.
- **supported**: There are several vehicles and pedestrians visible.  
  ↳ supporting fact: _Most buses are moving._
- **neutral**: The road has white lines and arrows indicating directions.
- **neutral**: There are traffic lights and street signs visible.
- **neutral**: The overall atmosphere is calm and quiet.
- **supported**: The scene shows: with the only sound being the occasional car engine or pedestrian footsteps.  
  ↳ supporting fact: _The drive is in Singapore._

**Human sentence items**

- **supported**: Night
- **neutral**: after rain
- **supported**: many peds
- **supported**: PMD
- **neutral**: ped with bag
- **neutral**: jaywalker
- **contradicted**: truck
- **contradicted**: scooter

</details>

<details><summary>scene-1100: view 0 chosen, view agreement 28.6%</summary>

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

- **supported**: The image depicts a nighttime scene on a city street.  
  ↳ supporting fact: _There are pedestrians._
- **supported**: The scene shows: with several cars and a motorcycle visible.  
  ↳ supporting fact: _There are bicycles or motorcycles._
- **neutral**: The street is wet.
- **neutral**: The scene shows: indicating recent rain.
- **neutral**: There are traffic lights and signs visible.
- **neutral**: The scene includes a bridge with greenery on the left side and a building with a sign on the right side.
- **neutral**: The overall atmosphere is calm and quiet.
- **contradicted**: The scene shows: with no visible pedestrians or people.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The image captures the quietness of the night and the stillness of the city.

**Human sentence items**

- **supported**: Night
- **supported**: peds in sidewalk
- **contradicted**: peds cross crosswalk
- **contradicted**: scooter
- **supported**: PMD
- **supported**: difficult lighting

</details>
