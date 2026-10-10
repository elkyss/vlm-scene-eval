# Scene-level evaluation: `mock-oracle` with prompt `scene_open@c03d290e`

10 scenes. Each scene is shown as 3 views of 6 frames (one VLM call per view); the final description is the view most consistent with the others. Claims are judged by `nli-deberta-v3-base` against the fact sheet; objects are checked against the 3D boxes (CHAIR) without a judge.

## Headline

**Final** = the chosen view's description (95% CI from a bootstrap over scenes). **Macro** = mean of per-scene rates. **View A** and **mean of views** show how much the self-consistency choice changes the result. **Spread** = within-scene max-min across views. **Shuffled** = each description scored against another scene: a metric that does not get clearly worse there is not measuring content.

| Metric | Final | Macro | View A | Mean of views | Spread | Shuffled |
|---|---|---|---|---|---|---|
| CHAIR_i: invented object mentions / all object mentions | 0.0% [0.0%, 0.0%] | 0.0% | 0.0% | 0.0% | 0.0% | 21.4% |
| CHAIR_s: descriptions with an invented object | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 60.0% |
| Object coverage: clearly visible classes mentioned | 100.0% [100.0%, 100.0%] | 100.0% | 100.0% | 100.0% | 0.0% | 69.0% |
| Claims supported by the facts | 100.0% [100.0%, 100.0%] | 100.0% | 100.0% | 100.0% | 0.0% | 58.8% |
| Claims that cannot be verified (no annotation covers them) | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 9.8% |
| Claims supported by annotation-based facts | 88.9% | 89.0% | 88.9% | 88.9% | 0.8% | 52.3% |
| Human-sentence items covered | 62.7% [54.4%, 70.9%] | 62.0% | 61.0% | 62.1% | 4.4% | 47.5% |

## Supported claims by type

The judge is not equally reliable for every kind of claim. Its validation on claims with known truth (`validate-judge`) shows how often a *false* claim of each type is wrongly marked supported: read each row's supported rate with that error in mind. Small validation counts (e.g. 10 turn claims) are weak evidence.

| Claims about | Claims | Supported | Judge validation: false claims wrongly supported |
|---|---|---|---|
| How vehicles move (our car or others) | 58 | 100.0% | ego motion 30.0% (n=30), turn 0.0% (n=10) |
| Which objects are present | 60 | 100.0% | objects 18.5% (n=65) |
| Time of day, road condition | 11 | 100.0% | time of day 0.0% (n=30) |
| Kind of place, traffic side | 9 | 100.0% | not validated |
| Anything else (buildings, signs, weather...) | 15 | 100.0% | not validated |

## Is the description about this scene?

A generic description ("a car on a street in daylight") is supported in almost any scene. The difference between the own scene and the shuffled control shows how much of the content is specific to this scene. Zero or below means the description is no better than a generic one. For reference, the oracle control (fact sheet as description) scores about +40 points on claims supported.

| Metric | Own − shuffled |
|---|---|
| Claims supported: own scene minus shuffled scene | 41.2% |
| Object coverage: own scene minus shuffled scene | 31.0% |
| Human-sentence coverage: own scene minus shuffled scene | 15.3% |

**Conclusion:** the descriptions are measurably specific to their own scene on claims, objects, the human sentence (more than 5% better than on a shuffled scene).

## Contradictions (indicative only)

A claim counts as contradicted when the NLI judge reads the whole fact sheet as contradicting it. The automatic check below shows this verdict is much less reliable than "supported", so contradiction rates are reported but not used for conclusions.

| Metric | Value |
|---|---|
| Claims contradicted | 0.0% [0.0%, 0.0%] |
| Shuffled control: claims contradicted | 31.4% |
| Judge check: 'supported' object claims whose object is in view (n=333) | 99.1% |
| Judge check: 'contradicted' object claims whose object is absent (n=32) | 28.1% |

## Output quality

| Metric | Value |
|---|---|
| Agreement between views (facts all views agree on) | 89.8% |
| Empty descriptions | 0.0% |
| Repetition loops | 0.0% |
| Mean words per description | 68.50 |
| Mean latency per call (s) | 0.00 |

## Similarity to the human sentence (secondary)

Whole-text similarity is reported for completeness. It rewards topical overlap, not correctness, which is why the claim-level checks above are the main result.

| Metric | Value |
|---|---|
| Mean embedding cosine to scene.description | 0.49 |
| Description closest to its own scene's sentence (of all scenes) | 20.0% |

## Per scene

| Scene | Human sentence | Model description (final) | Human items covered | Errors |
|---|---|---|---|---|
| scene-0061 | Parked truck, construction, intersection, turn left, following a van | It is daytime. The drive passes an intersection. Vehicles drive on the left side of the road. The drive is in Singapore. Our car is driving. Our car turns left. There are cars. Most cars are moving. There are trucks. Most trucks are stopped. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. Most bicycles or motorcycles are parked. There are traffic cones. There are road barriers. | 4/5 | none |
| scene-0103 | Many peds right, wait for turning car, long bike rack left, cyclist | It is daytime. Vehicles drive on the right side of the road. The drive is in Boston. Our car is driving. Our car drives straight ahead. There are cars. Most cars are parked. There are trucks. Most trucks are parked. There are no buses. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. There are traffic cones. There are no road barriers. | 2/4 | none |
| scene-0553 | Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller | It is daytime. The drive passes an intersection. Vehicles drive on the right side of the road. The drive is in Boston. Our car is stopped. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are buses. Most buses are moving. There are pedestrians. Most pedestrians are walking. There are no bicycles or motorcycles. There are no traffic cones. There are road barriers. | 2/5 | none |
| scene-0655 | Parking lot, parked cars, jaywalker, bendy bus, gardening vehicles | It is daytime. The scene is in a parking lot. Vehicles drive on the right side of the road. The drive is in Boston. Our car is driving. Our car drives straight ahead. There are cars. Most cars are parked. There are trucks. Most trucks are parked. There are buses. Most buses are stopped. There are pedestrians. Most pedestrians are walking. There are no bicycles or motorcycles. There are traffic cones. There are no road barriers. | 2/5 | none |
| scene-0757 | Arrive at busy intersection, bus, wait at intersection, bicycle, peds | It is daytime. The drive passes an intersection. Vehicles drive on the right side of the road. The drive is in Boston. Our car is moving slowly. Our car stops for part of the drive. Our car drives straight ahead. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are buses. Most buses are moving. There are no pedestrians. There are bicycles or motorcycles. Most bicycles or motorcycles are ridden. There are no traffic cones. There are no road barriers. | 3/5 | none |
| scene-0796 | Scooter, peds on sidewalk, bus, cars, truck, fake construction worker, bicycle, cross intersection, car overtaking us | It is daytime. The drive passes an intersection. Vehicles drive on the left side of the road. The drive is in Singapore. Our car is driving fast. Our car drives straight ahead. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are pedestrians. Most pedestrians are walking. There are no traffic cones. There are no road barriers. | 6/9 | none |
| scene-0916 | Parking lot, bicycle rack, parked bicycles, bus, many peds, parked scooters, parked motorcycle | It is daytime. The scene is in a parking lot. Vehicles drive on the left side of the road. The drive is in Singapore. Our car is driving. Our car turns right. There are cars. Most cars are parked. There are trucks. Most trucks are parked. There are no buses. There are pedestrians. Most pedestrians are standing. There are bicycles or motorcycles. Most bicycles or motorcycles are parked. There are no traffic cones. There are no road barriers. | 4/7 | none |
| scene-1077 | Night, big street, bus stop, high speed, construction vehicle | It is night. Vehicles drive on the left side of the road. The drive is in Singapore. Our car is driving fast. Our car turns left. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are no pedestrians. There are no traffic cones. There are road barriers. | 4/5 | none |
| scene-1094 | Night, after rain, many peds, PMD, ped with bag, jaywalker, truck, scooter | It is night. The road is wet. Vehicles drive on the left side of the road. The drive is in Singapore. Our car is driving. Our car turns left. There are cars. There are no trucks. There are buses. Most buses are moving. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. There are no traffic cones. There are no road barriers. | 5/8 | none |
| scene-1100 | Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting | It is night. Vehicles drive on the left side of the road. The drive is in Singapore. Our car is stopped. There are cars. Most cars are moving. There are no trucks. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. Most bicycles or motorcycles are ridden. There are no traffic cones. There are no road barriers. | 5/6 | none |

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

- **supported**: It is daytime.  
  ↳ supporting fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ supporting fact: _The drive passes an intersection._
- **supported**: Vehicles drive on the left side of the road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **supported**: The drive is in Singapore.  
  ↳ supporting fact: _The drive is in Singapore._
- **supported**: Our car is driving.  
  ↳ supporting fact: _Our car is driving._
- **supported**: Our car turns left.  
  ↳ supporting fact: _Our car turns left._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are stopped._
- **supported**: Most trucks are stopped.  
  ↳ supporting fact: _Most trucks are stopped._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ supporting fact: _Most bicycles or motorcycles are parked._
- **supported**: Most bicycles or motorcycles are parked.  
  ↳ supporting fact: _Most bicycles or motorcycles are parked._
- **supported**: There are traffic cones.  
  ↳ supporting fact: _There are traffic cones._
- **supported**: There are road barriers.  
  ↳ supporting fact: _There are road barriers._

**Human sentence items**

- **supported**: Parked truck
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

- **supported**: It is daytime.  
  ↳ supporting fact: _It is daytime._
- **supported**: Vehicles drive on the right side of the road.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._
- **supported**: The drive is in Boston.  
  ↳ supporting fact: _The drive is in Boston._
- **supported**: Our car is driving.  
  ↳ supporting fact: _Our car drives straight ahead._
- **supported**: Our car drives straight ahead.  
  ↳ supporting fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are parked._
- **supported**: Most cars are parked.  
  ↳ supporting fact: _Most cars are parked._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are parked._
- **supported**: Most trucks are parked.  
  ↳ supporting fact: _Most trucks are parked._
- **supported**: There are no buses.  
  ↳ supporting fact: _There are no buses._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ supporting fact: _There are bicycles or motorcycles._
- **supported**: There are traffic cones.  
  ↳ supporting fact: _There are traffic cones._
- **supported**: There are no road barriers.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **supported**: Many peds right
- **contradicted**: wait for turning car
- **contradicted**: long bike rack left
- **supported**: cyclist

</details>

<details><summary>scene-0553: view 1 chosen, view agreement 88.9%</summary>

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

- **supported**: It is daytime.  
  ↳ supporting fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ supporting fact: _The drive passes an intersection._
- **supported**: Vehicles drive on the right side of the road.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._
- **supported**: The drive is in Boston.  
  ↳ supporting fact: _The drive is in Boston._
- **supported**: Our car is stopped.  
  ↳ supporting fact: _Our car is stopped._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: There are buses.  
  ↳ supporting fact: _There are buses._
- **supported**: Most buses are moving.  
  ↳ supporting fact: _Most buses are moving._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: There are no bicycles or motorcycles.  
  ↳ supporting fact: _There are no bicycles or motorcycles._
- **supported**: There are no traffic cones.  
  ↳ supporting fact: _There are no traffic cones._
- **supported**: There are road barriers.  
  ↳ supporting fact: _There are road barriers._

**Human sentence items**

- **supported**: Wait at intersection
- **contradicted**: bicycle
- **supported**: large truck
- **neutral**: peds crossing crosswalk
- **contradicted**: ped with stroller

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

- **supported**: It is daytime.  
  ↳ supporting fact: _It is daytime._
- **supported**: The scene is in a parking lot.  
  ↳ supporting fact: _The scene is in a parking lot._
- **supported**: Vehicles drive on the right side of the road.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._
- **supported**: The drive is in Boston.  
  ↳ supporting fact: _The drive is in Boston._
- **supported**: Our car is driving.  
  ↳ supporting fact: _Our car drives straight ahead._
- **supported**: Our car drives straight ahead.  
  ↳ supporting fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are parked._
- **supported**: Most cars are parked.  
  ↳ supporting fact: _Most cars are parked._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are parked._
- **supported**: Most trucks are parked.  
  ↳ supporting fact: _Most trucks are parked._
- **supported**: There are buses.  
  ↳ supporting fact: _There are buses._
- **supported**: Most buses are stopped.  
  ↳ supporting fact: _Most buses are stopped._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: There are no bicycles or motorcycles.  
  ↳ supporting fact: _There are no bicycles or motorcycles._
- **supported**: There are traffic cones.  
  ↳ supporting fact: _There are traffic cones._
- **supported**: There are no road barriers.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **supported**: Parking lot
- **supported**: parked cars
- **neutral**: jaywalker
- **contradicted**: bendy bus
- **contradicted**: gardening vehicles

</details>

<details><summary>scene-0757: view 1 chosen, view agreement 87.5%</summary>

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

- **supported**: It is daytime.  
  ↳ supporting fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ supporting fact: _The drive passes an intersection._
- **supported**: Vehicles drive on the right side of the road.  
  ↳ supporting fact: _Vehicles drive on the right side of the road._
- **supported**: The drive is in Boston.  
  ↳ supporting fact: _The drive is in Boston._
- **supported**: Our car is moving slowly.  
  ↳ supporting fact: _Our car is moving slowly._
- **supported**: Our car stops for part of the drive.  
  ↳ supporting fact: _Our car stops for part of the drive._
- **supported**: Our car drives straight ahead.  
  ↳ supporting fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: There are buses.  
  ↳ supporting fact: _There are buses._
- **supported**: Most buses are moving.  
  ↳ supporting fact: _Most buses are moving._
- **supported**: There are no pedestrians.  
  ↳ supporting fact: _There are no pedestrians._
- **supported**: There are bicycles or motorcycles.  
  ↳ supporting fact: _Most bicycles or motorcycles are ridden._
- **supported**: Most bicycles or motorcycles are ridden.  
  ↳ supporting fact: _Most bicycles or motorcycles are ridden._
- **supported**: There are no traffic cones.  
  ↳ supporting fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **neutral**: Arrive at busy intersection
- **supported**: bus
- **neutral**: wait at intersection
- **supported**: bicycle
- **supported**: peds

</details>

<details><summary>scene-0796: view 0 chosen, view agreement 62.5%</summary>

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

- **supported**: It is daytime.  
  ↳ supporting fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ supporting fact: _The drive passes an intersection._
- **supported**: Vehicles drive on the left side of the road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **supported**: The drive is in Singapore.  
  ↳ supporting fact: _The drive is in Singapore._
- **supported**: Our car is driving fast.  
  ↳ supporting fact: _Our car is driving fast._
- **supported**: Our car drives straight ahead.  
  ↳ supporting fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: There are no traffic cones.  
  ↳ supporting fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **supported**: Scooter
- **supported**: peds on sidewalk
- **contradicted**: bus
- **supported**: cars
- **supported**: truck
- **neutral**: fake construction worker
- **contradicted**: bicycle
- **supported**: cross intersection
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

- **supported**: It is daytime.  
  ↳ supporting fact: _It is daytime._
- **supported**: The scene is in a parking lot.  
  ↳ supporting fact: _The scene is in a parking lot._
- **supported**: Vehicles drive on the left side of the road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **supported**: The drive is in Singapore.  
  ↳ supporting fact: _The drive is in Singapore._
- **supported**: Our car is driving.  
  ↳ supporting fact: _Our car is driving._
- **supported**: Our car turns right.  
  ↳ supporting fact: _Our car turns right._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are parked._
- **supported**: Most cars are parked.  
  ↳ supporting fact: _Most cars are parked._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are parked._
- **supported**: Most trucks are parked.  
  ↳ supporting fact: _Most trucks are parked._
- **supported**: There are no buses.  
  ↳ supporting fact: _There are no buses._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are standing._
- **supported**: Most pedestrians are standing.  
  ↳ supporting fact: _Most pedestrians are standing._
- **supported**: There are bicycles or motorcycles.  
  ↳ supporting fact: _Most bicycles or motorcycles are parked._
- **supported**: Most bicycles or motorcycles are parked.  
  ↳ supporting fact: _Most bicycles or motorcycles are parked._
- **supported**: There are no traffic cones.  
  ↳ supporting fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **supported**: Parking lot
- **neutral**: bicycle rack
- **supported**: parked bicycles
- **contradicted**: bus
- **supported**: many peds
- **contradicted**: parked scooters
- **supported**: parked motorcycle

</details>

<details><summary>scene-1077: view 0 chosen, view agreement 71.4%</summary>

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

- **supported**: It is night.  
  ↳ supporting fact: _It is night._
- **supported**: Vehicles drive on the left side of the road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **supported**: The drive is in Singapore.  
  ↳ supporting fact: _The drive is in Singapore._
- **supported**: Our car is driving fast.  
  ↳ supporting fact: _Our car is driving fast._
- **supported**: Our car turns left.  
  ↳ supporting fact: _Our car turns left._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ supporting fact: _Most trucks are moving._
- **supported**: There are no pedestrians.  
  ↳ supporting fact: _There are no pedestrians._
- **supported**: There are no traffic cones.  
  ↳ supporting fact: _There are no traffic cones._
- **supported**: There are road barriers.  
  ↳ supporting fact: _There are road barriers._

**Human sentence items**

- **supported**: Night
- **supported**: big street
- **contradicted**: bus stop
- **supported**: high speed
- **supported**: construction vehicle

</details>

<details><summary>scene-1094: view 1 chosen, view agreement 87.5%</summary>

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

- **supported**: It is night.  
  ↳ supporting fact: _It is night._
- **supported**: The road is wet.  
  ↳ supporting fact: _The road is wet._
- **supported**: Vehicles drive on the left side of the road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **supported**: The drive is in Singapore.  
  ↳ supporting fact: _The drive is in Singapore._
- **supported**: Our car is driving.  
  ↳ supporting fact: _Our car is driving._
- **supported**: Our car turns left.  
  ↳ supporting fact: _Our car turns left._
- **supported**: There are cars.  
  ↳ supporting fact: _There are cars._
- **supported**: There are no trucks.  
  ↳ supporting fact: _There are no trucks._
- **supported**: There are buses.  
  ↳ supporting fact: _There are buses._
- **supported**: Most buses are moving.  
  ↳ supporting fact: _Most buses are moving._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ supporting fact: _There are bicycles or motorcycles._
- **supported**: There are no traffic cones.  
  ↳ supporting fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **supported**: Night
- **supported**: after rain
- **supported**: many peds
- **supported**: PMD
- **supported**: ped with bag
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

- **supported**: It is night.  
  ↳ supporting fact: _It is night._
- **supported**: Vehicles drive on the left side of the road.  
  ↳ supporting fact: _Vehicles drive on the left side of the road._
- **supported**: The drive is in Singapore.  
  ↳ supporting fact: _The drive is in Singapore._
- **supported**: Our car is stopped.  
  ↳ supporting fact: _Our car is stopped._
- **supported**: There are cars.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ supporting fact: _Most cars are moving._
- **supported**: There are no trucks.  
  ↳ supporting fact: _There are no trucks._
- **supported**: There are pedestrians.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ supporting fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ supporting fact: _Most bicycles or motorcycles are ridden._
- **supported**: Most bicycles or motorcycles are ridden.  
  ↳ supporting fact: _Most bicycles or motorcycles are ridden._
- **supported**: There are no traffic cones.  
  ↳ supporting fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ supporting fact: _There are no road barriers._

**Human sentence items**

- **supported**: Night
- **supported**: peds in sidewalk
- **supported**: peds cross crosswalk
- **contradicted**: scooter
- **supported**: PMD
- **supported**: difficult lighting

</details>
