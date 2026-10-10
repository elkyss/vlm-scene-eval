# Scene-level evaluation: `SmolVLM-500M-Instruct` with prompt `scene_open@c03d290e`

10 scenes. Each scene is shown as 3 views of 6 frames (one VLM call per view); the final description is the view most consistent with the others. Claims are judged by `nli-deberta-v3-base` against the fact sheet; objects are checked against the 3D boxes (CHAIR) without a judge.

## Headline

**Final** = the chosen view's description (95% CI from a bootstrap over scenes). **Macro** = mean of per-scene rates. **View A** and **mean of views** show how much the self-consistency choice changes the result. **Spread** = within-scene max-min across views. **Shuffled** = each description scored against another scene: a metric that does not get clearly worse there is not measuring content.

| Metric | Final | Macro | View A | Mean of views | Spread | Shuffled |
|---|---|---|---|---|---|---|
| CHAIR_i: invented object mentions / all object mentions | 0.0% [0.0%, 0.0%] | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| CHAIR_s: descriptions with an invented object | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Object coverage: clearly visible classes mentioned | 23.8% [20.4%, 28.6%] | 25.5% | 27.9% | 25.8% | 16.2% | 23.8% |
| Claims supported by the facts | 26.7% [7.3%, 51.2%] | 37.3% | 31.9% | 33.2% | 75.0% | 33.3% |
| Claims that cannot be verified (no annotation covers them) | 53.3% | 41.0% | 48.9% | 54.8% | 68.3% | 44.4% |
| Claims supported by annotation-based facts | 24.4% | 27.3% | 27.7% | 15.4% | 43.3% | 20.0% |
| Human-sentence items covered | 11.9% [4.1%, 20.0%] | 12.2% | 10.2% | 10.2% | 15.0% | 3.4% |

## Is the description about this scene?

A generic description ("a car on a street in daylight") is supported in almost any scene. The difference between the own scene and the shuffled control shows how much of the content is specific to this scene. Zero or below means the description is no better than a generic one. For reference, the oracle control (fact sheet as description) scores about +40 points on claims supported.

| Metric | Own − shuffled |
|---|---|
| Claims supported: own scene minus shuffled scene | -6.7% |
| Object coverage: own scene minus shuffled scene | 0.0% |
| Human-sentence coverage: own scene minus shuffled scene | 8.5% |

**Conclusion:** the descriptions are measurably specific to their own scene on the human sentence (more than 5% better than on a shuffled scene).

## Contradictions (indicative only)

A claim counts as contradicted when the NLI judge reads the whole fact sheet as contradicting it. The automatic check below shows this verdict is much less reliable than "supported", so contradiction rates are reported but not used for conclusions.

| Metric | Value |
|---|---|
| Claims contradicted | 20.0% [0.0%, 50.0%] |
| Shuffled control: claims contradicted | 22.2% |
| Judge check: 'supported' object claims whose object is in view (n=0) | – |
| Judge check: 'contradicted' object claims whose object is absent (n=1) | 0.0% |

## Output quality

| Metric | Value |
|---|---|
| Agreement between views (facts all views agree on) | 70.0% |
| Empty descriptions | 0.0% |
| Repetition loops | 60.0% |
| Mean words per description | 49.10 |
| Mean latency per call (s) | 13.30 |

## Similarity to the human sentence (secondary)

Whole-text similarity is reported for completeness. It rewards topical overlap, not correctness, which is why the claim-level checks above are the main result.

| Metric | Value |
|---|---|
| Mean embedding cosine to scene.description | 0.27 |
| Description closest to its own scene's sentence (of all scenes) | 0.0% |

## Per scene

| Scene | Human sentence | Model description (final) | Human items covered | Errors |
|---|---|---|---|---|
| scene-0061 | Parked truck, construction, intersection, turn left, following a van | The car is driving down the street. | 1/5 | missed: barrier, pedestrian, traffic_cone, truck, two_wheeler |
| scene-0103 | Many peds right, wait for turning car, long bike rack left, cyclist | The drive is on a street with cars parked on both sides. There are buildings on both sides of the street. | 1/4 | missed: pedestrian, traffic_cone, truck, two_wheeler; 2 contradicted claim(s), indicative |
| scene-0553 | Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller | The first image shows a person walking across the street in front of a crosswalk. The second image shows a person walking across the street in front of a traffic light. The third image shows a person walking across the street in front of a traffic light. The fourth image shows a person walking across the street in front of a traffic light. The fifth image shows a person walking across the street in front of a traffic light. The sixth image shows a person walking across the street in front of a traffic light. | 2/5 | missed: barrier, bus, car, truck |
| scene-0655 | Parking lot, parked cars, jaywalker, bendy bus, gardening vehicles | The first image shows a street with a car driving away from the camera. The second image shows a car driving towards the camera. The third image shows a car driving away from the camera. The fourth image shows a car driving towards the camera. The fifth image shows a car driving away from the camera. The sixth image shows a car driving towards the camera. | 0/5 | missed: bus, pedestrian, traffic_cone, truck; 1 contradicted claim(s), indicative |
| scene-0757 | Arrive at busy intersection, bus, wait at intersection, bicycle, peds | The first image shows a street scene with a car driving past a street sign. The second image shows a car driving past a street sign. The third image shows a car driving past a street sign. The fourth image shows a car driving past a street sign. The fifth image shows a car driving past a street sign. The sixth image shows a car driving past a street sign. | 0/5 | missed: bus, traffic_cone, truck, two_wheeler; 6 contradicted claim(s), indicative |
| scene-0796 | Scooter, peds on sidewalk, bus, cars, truck, fake construction worker, bicycle, cross intersection, car overtaking us | The first image shows a street with a car driving away from the camera. The second image shows a car driving towards the camera. The third image shows a car driving away from the camera. The fourth image shows a car driving towards the camera. The fifth image shows a car driving away from the camera. The sixth image shows a car driving towards the camera. | 2/9 | missed: pedestrian, truck |
| scene-0916 | Parking lot, bicycle rack, parked bicycles, bus, many peds, parked scooters, parked motorcycle | The drive is from the front camera of a car. The car is driving on a street. There are trees, bushes, and houses in the background. There are cars parked on the side of the street. | 1/7 | missed: pedestrian, truck, two_wheeler |
| scene-1077 | Night, big street, bus stop, high speed, construction vehicle | The first image shows a car driving down a road. The second image shows a car driving down the road. The third image shows a car driving down the road. The fourth image shows a car driving down the road. The fifth image shows a car driving down the road. The sixth image shows a car driving down the road. | 0/5 | missed: barrier, truck |
| scene-1094 | Night, after rain, many peds, PMD, ped with bag, jaywalker, truck, scooter | The car is driving down the street. | 0/8 | missed: pedestrian, two_wheeler |
| scene-1100 | Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting | The first image shows a car driving down a street. The second image shows a car parked on the side of the street. The third image shows a car driving down the street. The fourth image shows a car driving down the street. The fifth image shows a car driving down the street. The sixth image shows a car driving down the street. | 0/6 | missed: pedestrian, two_wheeler |

## Details per scene

<details><summary>scene-0061: view 0 chosen, view agreement 66.7%</summary>

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

- **supported**: The car is driving down the street.  
  ↳ supporting fact: _The drive passes an intersection._

**Human sentence items**

- **contradicted**: Parked truck
- **contradicted**: construction
- **supported**: intersection
- **contradicted**: turn left
- **contradicted**: following a van

</details>

<details><summary>scene-0103: view 1 chosen, view agreement 50.0%</summary>

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

- **contradicted**: The drive is on a street with cars parked on both sides.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: There are buildings on both sides of the street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **supported**: Many peds right
- **neutral**: wait for turning car
- **contradicted**: long bike rack left
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

- **neutral**: The first image shows a person walking across the street in front of a crosswalk.
- **neutral**: The second image shows a person walking across the street in front of a traffic light.
- **neutral**: The third image shows a person walking across the street in front of a traffic light.
- **neutral**: The fourth image shows a person walking across the street in front of a traffic light.
- **neutral**: The fifth image shows a person walking across the street in front of a traffic light.
- **neutral**: The sixth image shows a person walking across the street in front of a traffic light.

**Human sentence items**

- **supported**: Wait at intersection
- **neutral**: bicycle
- **neutral**: large truck
- **supported**: peds crossing crosswalk
- **neutral**: ped with stroller

</details>

<details><summary>scene-0655: view 0 chosen, view agreement 66.7%</summary>

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

- **contradicted**: The first image shows a street with a car driving away from the camera.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: The second image shows a car driving towards the camera.
- **neutral**: The third image shows a car driving away from the camera.
- **neutral**: The fourth image shows a car driving towards the camera.
- **neutral**: The fifth image shows a car driving away from the camera.
- **neutral**: The sixth image shows a car driving towards the camera.

**Human sentence items**

- **contradicted**: Parking lot
- **contradicted**: parked cars
- **neutral**: jaywalker
- **contradicted**: bendy bus
- **contradicted**: gardening vehicles

</details>

<details><summary>scene-0757: view 0 chosen, view agreement 50.0%</summary>

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

- **contradicted**: The first image shows a street scene with a car driving past a street sign.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The second image shows a car driving past a street sign.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The third image shows a car driving past a street sign.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The fourth image shows a car driving past a street sign.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The fifth image shows a car driving past a street sign.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: The sixth image shows a car driving past a street sign.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **neutral**: Arrive at busy intersection
- **neutral**: bus
- **neutral**: wait at intersection
- **neutral**: bicycle
- **neutral**: peds

</details>

<details><summary>scene-0796: view 0 chosen, view agreement 100.0%</summary>

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

- **neutral**: The first image shows a street with a car driving away from the camera.
- **neutral**: The second image shows a car driving towards the camera.
- **neutral**: The third image shows a car driving away from the camera.
- **neutral**: The fourth image shows a car driving towards the camera.
- **neutral**: The fifth image shows a car driving away from the camera.
- **neutral**: The sixth image shows a car driving towards the camera.

**Human sentence items**

- **contradicted**: Scooter
- **contradicted**: peds on sidewalk
- **contradicted**: bus
- **supported**: cars
- **contradicted**: truck
- **neutral**: fake construction worker
- **contradicted**: bicycle
- **neutral**: cross intersection
- **supported**: car overtaking us

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

- **neutral**: The drive is from the front camera of a car.
- **supported**: The car is driving on a street.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **neutral**: There are trees, bushes.
- **neutral**: Houses in the background.
- **supported**: There are cars parked on the side of the street.  
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

<details><summary>scene-1077: view 0 chosen, view agreement 0.0%</summary>

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

- **supported**: The first image shows a car driving down a road.  
  ↳ supporting fact: _Our car is driving fast._
- **supported**: The second image shows a car driving down the road.  
  ↳ supporting fact: _Our car is driving fast._
- **supported**: The third image shows a car driving down the road.  
  ↳ supporting fact: _Our car is driving fast._
- **supported**: The fourth image shows a car driving down the road.  
  ↳ supporting fact: _Our car is driving fast._
- **supported**: The fifth image shows a car driving down the road.  
  ↳ supporting fact: _Our car turns left._
- **neutral**: The sixth image shows a car driving down the road.

**Human sentence items**

- **neutral**: Night
- **neutral**: big street
- **neutral**: bus stop
- **neutral**: high speed
- **contradicted**: construction vehicle

</details>

<details><summary>scene-1094: view 0 chosen, view agreement 100.0%</summary>

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

- **supported**: The car is driving down the street.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._

**Human sentence items**

- **neutral**: Night
- **neutral**: after rain
- **contradicted**: many peds
- **contradicted**: PMD
- **contradicted**: ped with bag
- **contradicted**: jaywalker
- **contradicted**: truck
- **contradicted**: scooter

</details>

<details><summary>scene-1100: view 0 chosen, view agreement 100.0%</summary>

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

- **supported**: The first image shows a car driving down a street.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **neutral**: The second image shows a car parked on the side of the street.
- **supported**: The third image shows a car driving down the street.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: The fourth image shows a car driving down the street.  
  ↳ supporting fact: _Most cars are moving._
- **neutral**: The fifth image shows a car driving down the street.
- **neutral**: The sixth image shows a car driving down the street.

**Human sentence items**

- **neutral**: Night
- **contradicted**: peds in sidewalk
- **contradicted**: peds cross crosswalk
- **contradicted**: scooter
- **contradicted**: PMD
- **neutral**: difficult lighting

</details>
