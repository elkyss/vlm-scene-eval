# Scene-level evaluation: `mock-fixed` with prompt `scene_open@c03d290e`

10 scenes. Each scene is shown as 3 views of 6 frames (one VLM call per view); the final description is the view most consistent with the others. Claims are judged by `nli-deberta-v3-base` against the fact sheet; objects are checked against the 3D boxes (CHAIR) without a judge.

## Headline

**Final** = the chosen view's description (95% CI from a bootstrap over scenes). **Macro** = mean of per-scene rates. **View A** and **mean of views** show how much the self-consistency choice changes the result. **Spread** = within-scene max-min across views. **Shuffled** = each description scored against another scene: a metric that does not get clearly worse there is not measuring content.

| Metric | Final | Macro | View A | Mean of views | Spread | Shuffled |
|---|---|---|---|---|---|---|
| CHAIR_i: invented object mentions / all object mentions | 10.0% [0.0%, 25.0%] | 10.0% | 10.0% | 10.0% | 0.0% | 10.0% |
| CHAIR_s: descriptions with an invented object | 20.0% | 20.0% | 20.0% | 20.0% | 0.0% | 20.0% |
| Object coverage: clearly visible classes mentioned | 41.9% [34.0%, 51.5%] | 45.0% | 41.9% | 42.2% | 7.0% | 41.9% |
| Claims supported by the facts | 20.0% [5.0%, 35.0%] | 20.0% | 20.0% | 16.7% | 10.0% | 20.0% |
| Claims that cannot be verified (no annotation covers them) | 45.0% | 45.0% | 45.0% | 50.0% | 10.0% | 45.0% |
| Claims supported by annotation-based facts | 20.0% | 20.0% | 20.0% | 16.7% | 10.0% | 20.0% |
| Human-sentence items covered | 16.9% [7.7%, 25.9%] | 16.7% | 16.9% | 16.9% | 0.0% | 16.9% |

## Supported claims by type

The judge is not equally reliable for every kind of claim. Its validation on claims with known truth (`validate-judge`) shows how often a *false* claim of each type is wrongly marked supported: read each row's supported rate with that error in mind. Small validation counts (e.g. 10 turn claims) are weak evidence.

| Claims about | Claims | Supported | Judge validation: false claims wrongly supported |
|---|---|---|---|
| How vehicles move (our car or others) | 10 | 40.0% | ego motion 30.0% (n=30), turn 0.0% (n=10) |
| Which objects are present | 10 | 0.0% | objects 18.5% (n=65) |
| Time of day, road condition | 0 | – | time of day 0.0% (n=30) |
| Kind of place, traffic side | 0 | – | not validated |
| Anything else (buildings, signs, weather...) | 0 | – | not validated |

## Is the description about this scene?

A generic description ("a car on a street in daylight") is supported in almost any scene. The difference between the own scene and the shuffled control shows how much of the content is specific to this scene. Zero or below means the description is no better than a generic one. For reference, the oracle control (fact sheet as description) scores about +40 points on claims supported.

| Metric | Own − shuffled |
|---|---|
| Claims supported: own scene minus shuffled scene | 0.0% |
| Object coverage: own scene minus shuffled scene | 0.0% |
| Human-sentence coverage: own scene minus shuffled scene | 0.0% |

**Conclusion:** the descriptions fit other scenes as well as (or better than) their own. There is no evidence that they describe this particular scene; treat the other scores of this run as reflecting generic text.

## Contradictions (indicative only)

A claim counts as contradicted when the NLI judge reads the whole fact sheet as contradicting it. The automatic check below shows this verdict is much less reliable than "supported", so contradiction rates are reported but not used for conclusions.

| Metric | Value |
|---|---|
| Claims contradicted | 35.0% [15.0%, 55.0%] |
| Shuffled control: claims contradicted | 35.0% |
| Judge check: 'supported' object claims whose object is in view (n=0) | – |
| Judge check: 'contradicted' object claims whose object is absent (n=15) | 53.3% |

## Output quality

| Metric | Value |
|---|---|
| Agreement between views (facts all views agree on) | 100.0% |
| Empty descriptions | 0.0% |
| Repetition loops | 0.0% |
| Mean words per description | 13.00 |
| Mean latency per call (s) | 0.00 |

## Similarity to the human sentence (secondary)

Whole-text similarity is reported for completeness. It rewards topical overlap, not correctness, which is why the claim-level checks above are the main result.

| Metric | Value |
|---|---|
| Mean embedding cosine to scene.description | 0.24 |
| Description closest to its own scene's sentence (of all scenes) | 10.0% |

## Per scene

| Scene | Human sentence | Model description (final) | Human items covered | Errors |
|---|---|---|---|---|
| scene-0061 | Parked truck, construction, intersection, turn left, following a van | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 1/5 | missed: barrier, traffic_cone, truck, two_wheeler |
| scene-0103 | Many peds right, wait for turning car, long bike rack left, cyclist | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 0/4 | missed: traffic_cone, truck, two_wheeler; 1 contradicted claim(s), indicative |
| scene-0553 | Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 1/5 | missed: barrier, bus, truck, two_wheeler; 1 contradicted claim(s), indicative |
| scene-0655 | Parking lot, parked cars, jaywalker, bendy bus, gardening vehicles | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 0/5 | missed: bus, traffic_cone, truck |
| scene-0757 | Arrive at busy intersection, bus, wait at intersection, bicycle, peds | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 1/5 | invented: pedestrian; missed: bus, traffic_cone, truck, two_wheeler; 1 contradicted claim(s), indicative |
| scene-0796 | Scooter, peds on sidewalk, bus, cars, truck, fake construction worker, bicycle, cross intersection, car overtaking us | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 3/9 | missed: truck |
| scene-0916 | Parking lot, bicycle rack, parked bicycles, bus, many peds, parked scooters, parked motorcycle | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 0/7 | missed: truck, two_wheeler |
| scene-1077 | Night, big street, bus stop, high speed, construction vehicle | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 2/5 | invented: pedestrian; missed: barrier, truck; 2 contradicted claim(s), indicative |
| scene-1094 | Night, after rain, many peds, PMD, ped with bag, jaywalker, truck, scooter | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 0/8 | missed: two_wheeler; 1 contradicted claim(s), indicative |
| scene-1100 | Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting | A car drives along a sunny street. A pedestrian walks on the sidewalk. | 2/6 | missed: two_wheeler; 1 contradicted claim(s), indicative |

## Details per scene

<details><summary>scene-0061: view 0 chosen, view agreement 100.0%</summary>

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

- **neutral**: A car drives along a sunny street.
- **neutral**: A pedestrian walks on the sidewalk.

**Human sentence items**

- **contradicted**: Parked truck
- **contradicted**: construction
- **supported**: intersection
- **contradicted**: turn left
- **contradicted**: following a van

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

- **supported**: A car drives along a sunny street.  
  ↳ supporting fact: _There are cars._
- **contradicted**: A pedestrian walks on the sidewalk.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **contradicted**: Many peds right
- **neutral**: wait for turning car
- **contradicted**: long bike rack left
- **contradicted**: cyclist

</details>

<details><summary>scene-0553: view 0 chosen, view agreement 100.0%</summary>

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

- **neutral**: A car drives along a sunny street.
- **contradicted**: A pedestrian walks on the sidewalk.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **contradicted**: Wait at intersection
- **contradicted**: bicycle
- **contradicted**: large truck
- **supported**: peds crossing crosswalk
- **neutral**: ped with stroller

</details>

<details><summary>scene-0655: view 0 chosen, view agreement 100.0%</summary>

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

- **supported**: A car drives along a sunny street.  
  ↳ supporting fact: _There are cars._
- **neutral**: A pedestrian walks on the sidewalk.

**Human sentence items**

- **contradicted**: Parking lot
- **contradicted**: parked cars
- **neutral**: jaywalker
- **contradicted**: bendy bus
- **contradicted**: gardening vehicles

</details>

<details><summary>scene-0757: view 0 chosen, view agreement 100.0%</summary>

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

- **neutral**: A car drives along a sunny street.
- **contradicted**: A pedestrian walks on the sidewalk.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **neutral**: Arrive at busy intersection
- **contradicted**: bus
- **contradicted**: wait at intersection
- **contradicted**: bicycle
- **supported**: peds

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

- **supported**: A car drives along a sunny street.  
  ↳ supporting fact: _There are cars._
- **neutral**: A pedestrian walks on the sidewalk.

**Human sentence items**

- **contradicted**: Scooter
- **supported**: peds on sidewalk
- **contradicted**: bus
- **supported**: cars
- **contradicted**: truck
- **neutral**: fake construction worker
- **contradicted**: bicycle
- **contradicted**: cross intersection
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

- **supported**: A car drives along a sunny street.  
  ↳ supporting fact: _There are cars._
- **neutral**: A pedestrian walks on the sidewalk.

**Human sentence items**

- **contradicted**: Parking lot
- **contradicted**: bicycle rack
- **contradicted**: parked bicycles
- **contradicted**: bus
- **contradicted**: many peds
- **contradicted**: parked scooters
- **contradicted**: parked motorcycle

</details>

<details><summary>scene-1077: view 0 chosen, view agreement 100.0%</summary>

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

- **contradicted**: A car drives along a sunny street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **contradicted**: A pedestrian walks on the sidewalk.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)

**Human sentence items**

- **contradicted**: Night
- **supported**: big street
- **contradicted**: bus stop
- **supported**: high speed
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

- **contradicted**: A car drives along a sunny street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: A pedestrian walks on the sidewalk.

**Human sentence items**

- **contradicted**: Night
- **contradicted**: after rain
- **contradicted**: many peds
- **contradicted**: PMD
- **neutral**: ped with bag
- **neutral**: jaywalker
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

- **contradicted**: A car drives along a sunny street.  
  ↳ contradicted by the fact sheet as a whole (indicative, see reliability)
- **neutral**: A pedestrian walks on the sidewalk.

**Human sentence items**

- **contradicted**: Night
- **supported**: peds in sidewalk
- **supported**: peds cross crosswalk
- **contradicted**: scooter
- **contradicted**: PMD
- **contradicted**: difficult lighting

</details>
