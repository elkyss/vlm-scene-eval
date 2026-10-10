# Scene-level evaluation: `SmolVLM-500M-Instruct` with prompt `scene_guided@97a6fd64`

10 scenes. Each scene is shown as 3 views of 6 frames (one VLM call per view); the final description is the view most consistent with the others. Claims are judged by `nli-deberta-v3-base` against the fact sheet; objects are checked against the 3D boxes (CHAIR) without a judge.

## Headline

**Final** = the chosen view's description (95% CI from a bootstrap over scenes). **Macro** = mean of per-scene rates. **View A** and **mean of views** show how much the self-consistency choice changes the result. **Spread** = within-scene max-min across views. **Shuffled** = each description scored against another scene: a metric that does not get clearly worse there is not measuring content.

| Metric | Final | Macro | View A | Mean of views | Spread | Shuffled |
|---|---|---|---|---|---|---|
| CHAIR_i: invented object mentions / all object mentions | 7.1% [0.0%, 21.4%] | 5.0% | 7.1% | 2.4% | 5.0% | 7.1% |
| CHAIR_s: descriptions with an invented object | 10.0% | 10.0% | 10.0% | 3.3% | 10.0% | 10.0% |
| Object coverage: clearly visible classes mentioned | 29.5% [25.0%, 35.0%] | 29.8% | 30.2% | 30.3% | 20.5% | 29.5% |
| Claims supported by the facts | 32.1% [19.3%, 46.4%] | 32.1% | 35.2% | 32.8% | 32.6% | 26.8% |
| Claims that cannot be verified (no annotation covers them) | 44.6% | 44.5% | 40.7% | 46.7% | 33.0% | 48.2% |
| Claims supported by annotation-based facts | 26.8% | 27.3% | 27.8% | 23.8% | 22.4% | 19.6% |
| Human-sentence items covered | 22.0% [14.7%, 30.0%] | 22.5% | 20.3% | 20.9% | 26.4% | 22.0% |

## Supported claims by type

The judge is not equally reliable for every kind of claim. Its validation on claims with known truth (`validate-judge`) shows how often a *false* claim of each type is wrongly marked supported: read each row's supported rate with that error in mind. Small validation counts (e.g. 10 turn claims) are weak evidence.

| Claims about | Claims | Supported | Judge validation: false claims wrongly supported |
|---|---|---|---|
| How vehicles move (our car or others) | 17 | 35.3% | ego motion 30.0% (n=30), turn 0.0% (n=10) |
| Which objects are present | 9 | 55.6% | objects 18.5% (n=65) |
| Time of day, road condition | 5 | 20.0% | time of day 0.0% (n=30) |
| Kind of place, traffic side | 17 | 17.6% | not validated |
| Anything else (buildings, signs, weather...) | 8 | 37.5% | not validated |

## Is the description about this scene?

A generic description ("a car on a street in daylight") is supported in almost any scene. The difference between the own scene and the shuffled control shows how much of the content is specific to this scene. Zero or below means the description is no better than a generic one. For reference, the oracle control (fact sheet as description) scores about +40 points on claims supported.

| Metric | Own − shuffled |
|---|---|
| Claims supported: own scene minus shuffled scene | 5.4% |
| Object coverage: own scene minus shuffled scene | 0.0% |
| Human-sentence coverage: own scene minus shuffled scene | 0.0% |

**Conclusion:** the descriptions are measurably specific to their own scene on claims (more than 5% better than on a shuffled scene).

## Contradictions (indicative only)

A claim counts as contradicted when the NLI judge reads the whole fact sheet as contradicting it. The automatic check below shows this verdict is much less reliable than "supported", so contradiction rates are reported but not used for conclusions.

| Metric | Value |
|---|---|
| Claims contradicted | 23.2% [9.3%, 38.0%] |
| Shuffled control: claims contradicted | 25.0% |
| Judge check: 'supported' object claims whose object is in view (n=7) | 100.0% |
| Judge check: 'contradicted' object claims whose object is absent (n=3) | 0.0% |

## Output quality

| Metric | Value |
|---|---|
| Agreement between views (facts all views agree on) | 43.2% |
| Empty descriptions | 0.0% |
| Repetition loops | 10.0% |
| Mean words per description | 45.30 |
| Mean latency per call (s) | 10.99 |

## Similarity to the human sentence (secondary)

Whole-text similarity is reported for completeness. It rewards topical overlap, not correctness, which is why the claim-level checks above are the main result.

| Metric | Value |
|---|---|
| Mean embedding cosine to scene.description | 0.34 |
| Description closest to its own scene's sentence (of all scenes) | 10.0% |

## Per scene

| Scene | Human sentence | Model description (final) | Human items covered | Errors |
|---|---|---|---|---|
| scene-0061 | Parked truck, construction, intersection, turn left, following a van | The drive is in a city. The road is wet from rain. The road is lined with trees and buildings. There are traffic cones on the side of the road. There is a white car parked on the side of the road. | 1/5 | missed: barrier, pedestrian, truck, two_wheeler |
| scene-0103 | Many peds right, wait for turning car, long bike rack left, cyclist | The drive is through a downtown area. The road is wet from recent rain. The road is lined with buildings and there are cars parked on both sides of the road. There is a pedestrian crossing in the background. The car is driving down the road. | 1/4 | missed: pedestrian, traffic_cone, truck, two_wheeler; 2 contradicted claim(s), indicative |
| scene-0553 | Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller | The drive is from the left to the right. The place is a city. The lighting is bright. The road users are cars and pedestrians. The road is a road. The road is a road. The road is a road. | 1/5 | missed: barrier, bus, truck, two_wheeler; 1 contradicted claim(s), indicative |
| scene-0655 | Parking lot, parked cars, jaywalker, bendy bus, gardening vehicles | The drive is through a city street. The street is wide and has a clear lane in the middle. There are trees and buildings on both sides of the street. The road is clear and there are no cars on it. The car is driving straight and is in the middle lane. | 0/5 | missed: bus, pedestrian, traffic_cone, truck; 4 contradicted claim(s), indicative |
| scene-0757 | Arrive at busy intersection, bus, wait at intersection, bicycle, peds | The drive is through a downtown area. The road is wet from recent rain. The streetlights are on. There are cars and trucks on the street. The street is lined with buildings. | 2/5 | missed: bus, two_wheeler |
| scene-0796 | Scooter, peds on sidewalk, bus, cars, truck, fake construction worker, bicycle, cross intersection, car overtaking us | The drive is in a city. The road is clear and there are no other cars. The road is lined with trees and there are buildings in the background. The car is driving on the right side of the road. | 1/9 | missed: pedestrian, truck, two_wheeler; 2 contradicted claim(s), indicative |
| scene-0916 | Parking lot, bicycle rack, parked bicycles, bus, many peds, parked scooters, parked motorcycle | The drive is from a driveway to a street. The car is driving on the right side of the street. The street is lined with trees and bushes. There are cars parked on the street. | 1/7 | missed: pedestrian, truck, two_wheeler |
| scene-1077 | Night, big street, bus stop, high speed, construction vehicle | The drive is long and straight, with a few trees on either side of the road. The road is paved and has white lines marking the lanes. There are no cars visible on the road, but there are a few cars parked on the side of the road. The light from the streetlights is visible, and the road is clear of any debris. The car is driving in the right lane, and the driver is looking straight ahead. | 2/5 | missed: barrier, bus, truck; 3 contradicted claim(s), indicative |
| scene-1094 | Night, after rain, many peds, PMD, ped with bag, jaywalker, truck, scooter | The drive is from the left to the right. The place is a street with a car driving away from the camera. The lighting is dark. The road is wet. The road users are cars and a truck. The road is lined with trees and street lights. | 3/8 | invented: truck; missed: pedestrian, two_wheeler; 1 contradicted claim(s), indicative |
| scene-1100 | Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting | The drive is from the left to the right. The car is driving on a road. The road is wet. There are cars on the road. There are trees and buildings on the right. There are street lights on the left. | 1/6 | missed: pedestrian, two_wheeler |

## Details per scene

<details><summary>scene-0061: view 2 chosen, view agreement 40.0%</summary>

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

- **supported**: The drive is in a city.  
  ↳ supporting fact: _The drive is in Singapore._
- **neutral**: The road is wet from rain.
- **neutral**: The road is lined with trees and buildings.
- **supported**: There are traffic cones on the side of the road.  
  ↳ supporting fact: _There are traffic cones._
- **neutral**: There is a white car parked on the side of the road.

**Human sentence items**

- **contradicted**: Parked truck
- **neutral**: construction
- **supported**: intersection
- **neutral**: turn left
- **neutral**: following a van

</details>

<details><summary>scene-0103: view 2 chosen, view agreement 33.3%</summary>

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

- **neutral**: The drive is through a downtown area.
- **neutral**: The road is wet from recent rain.
- **contradicted**: The road is lined with buildings and there are cars parked on both sides of the road.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: There is a pedestrian crossing in the background.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The car is driving down the road.  
  ↳ supporting fact: _Our car is driving._

**Human sentence items**

- **supported**: Many peds right
- **contradicted**: wait for turning car
- **contradicted**: long bike rack left
- **contradicted**: cyclist

</details>

<details><summary>scene-0553: view 0 chosen, view agreement 16.7%</summary>

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

- **contradicted**: The drive is from the left to the right.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The place is a city.  
  ↳ supporting fact: _The drive is in Boston._
- **neutral**: The lighting is bright.
- **supported**: The road users are cars and pedestrians.  
  ↳ supporting fact: _It is daytime._
- **supported**: The road is a road.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._
- **supported**: The road is a road.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._
- **supported**: The road is a road.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._

**Human sentence items**

- **neutral**: Wait at intersection
- **contradicted**: bicycle
- **neutral**: large truck
- **neutral**: peds crossing crosswalk
- **supported**: ped with stroller

</details>

<details><summary>scene-0655: view 1 chosen, view agreement 50.0%</summary>

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
- There are no bicycles or motorcycles.
- There are traffic cones.
- There are no road barriers.

**Claims of the description**

- **neutral**: The drive is through a city street.
- **contradicted**: The street is wide and has a clear lane in the middle.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: There are trees and buildings on both sides of the street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The road is clear and there are no cars on it.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The car is driving straight and is in the middle lane.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **contradicted**: Parking lot
- **neutral**: parked cars
- **contradicted**: jaywalker
- **contradicted**: bendy bus
- **contradicted**: gardening vehicles

</details>

<details><summary>scene-0757: view 1 chosen, view agreement 25.0%</summary>

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
- Most trucks are moving.
- There are buses.
- Most buses are moving.
- There are no pedestrians.
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are ridden.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **neutral**: The drive is through a downtown area.
- **neutral**: The road is wet from recent rain.
- **neutral**: The streetlights are on.
- **supported**: There are cars and trucks on the street.  
  ↳ supporting fact: _Most trucks are moving._
- **neutral**: The street is lined with buildings.

**Human sentence items**

- **supported**: Arrive at busy intersection
- **neutral**: bus
- **neutral**: wait at intersection
- **contradicted**: bicycle
- **supported**: peds

</details>

<details><summary>scene-0796: view 1 chosen, view agreement 66.7%</summary>

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
- There are bicycles or motorcycles.
- Most bicycles or motorcycles are ridden.
- There are no traffic cones.
- There are no road barriers.

**Claims of the description**

- **supported**: The drive is in a city.  
  ↳ supporting fact: _The drive is in Singapore._
- **contradicted**: The road is clear and there are no other cars.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The road is lined with trees and there are buildings in the background.
- **contradicted**: The car is driving on the right side of the road.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **contradicted**: Scooter
- **contradicted**: peds on sidewalk
- **contradicted**: bus
- **supported**: cars
- **contradicted**: truck
- **neutral**: fake construction worker
- **contradicted**: bicycle
- **neutral**: cross intersection
- **contradicted**: car overtaking us

</details>

<details><summary>scene-0916: view 0 chosen, view agreement 100.0%</summary>

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

- **neutral**: The drive is from a driveway to a street.
- **supported**: The car is driving on the right side of the street.  
  ↳ supporting fact: _Our car turns right._
- **neutral**: The street is lined with trees and bushes.
- **supported**: There are cars parked on the street.  
  ↳ supporting fact: _Most cars are parked._

**Human sentence items**

- **supported**: Parking lot
- **contradicted**: bicycle rack
- **contradicted**: parked bicycles
- **contradicted**: bus
- **contradicted**: many peds
- **contradicted**: parked scooters
- **contradicted**: parked motorcycle

</details>

<details><summary>scene-1077: view 1 chosen, view agreement 25.0%</summary>

**Fact sheet (reference)**

- It is night.
- Vehicles drive on the left side of the road.
- The drive is in Singapore.
- Our car is driving fast.
- Our car drives straight ahead.
- There are cars.
- Most cars are moving.
- There are trucks.
- Most trucks are moving.
- There are buses.
- Most buses are moving.
- There are no pedestrians.
- There are no traffic cones.
- There are road barriers.

**Claims of the description**

- **neutral**: The drive is long and straight.
- **contradicted**: The scene shows: with a few trees on either side of the road.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The road is paved and has white lines marking the lanes.
- **contradicted**: There are no cars visible on the road.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: There are a few cars parked on the side of the road.
- **neutral**: The light from the streetlights is visible.
- **neutral**: The road is clear of any debris.
- **contradicted**: The car is driving in the right lane.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **supported**: The driver is looking straight ahead.  
  ↳ supporting fact: _Our car drives straight ahead._

**Human sentence items**

- **supported**: Night
- **supported**: big street
- **contradicted**: bus stop
- **contradicted**: high speed
- **contradicted**: construction vehicle

</details>

<details><summary>scene-1094: view 0 chosen, view agreement 0.0%</summary>

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

- **neutral**: The drive is from the left to the right.
- **supported**: The place is a street with a car driving away from the camera.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **supported**: The lighting is dark.  
  ↳ supporting fact: _It is night._
- **supported**: The road is wet.  
  ↳ supporting fact: _The road is wet._
- **contradicted**: The road users are cars and a truck.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The road is lined with trees and street lights.

**Human sentence items**

- **supported**: Night
- **neutral**: after rain
- **contradicted**: many peds
- **neutral**: PMD
- **supported**: ped with bag
- **contradicted**: jaywalker
- **supported**: truck
- **contradicted**: scooter

</details>

<details><summary>scene-1100: view 1 chosen, view agreement 75.0%</summary>

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

- **neutral**: The drive is from the left to the right.
- **supported**: The car is driving on a road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **neutral**: The road is wet.
- **supported**: There are cars on the road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **neutral**: There are trees and buildings on the right.
- **neutral**: There are street lights on the left.

**Human sentence items**

- **neutral**: Night
- **contradicted**: peds in sidewalk
- **neutral**: peds cross crosswalk
- **contradicted**: scooter
- **neutral**: PMD
- **supported**: difficult lighting

</details>
