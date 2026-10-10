# Scene-level evaluation: `mock-table` with prompt `scene_open@c03d290e`

10 scenes. Each scene is shown as 3 views of 6 CAM_FRONT frames (one call per view); the final description is the most consistent view. Claims are judged by `nli-deberta-v3-base` against the fact sheet; objects are checked against the 3D boxes (CHAIR) without a judge.

## Headline

**Final** = the chosen view's description (95% CI from a bootstrap over scenes). **Macro** = mean of per-scene rates. **View A** and **mean of views** show how much the self-consistency choice changes the result. **Spread** = within-scene max-min across views. **Shuffled** = each description scored against another scene: a metric that does not get clearly worse there is not measuring content.

| Metric | Final | Macro | View A | Mean of views | Spread | Shuffled |
|---|---|---|---|---|---|---|
| CHAIR_i: invented object mentions / all object mentions | 0.0% [0.0%, 0.0%] | 0.0% | 0.0% | 0.0% | 0.0% | 21.4% |
| CHAIR_s: descriptions with an invented object | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 60.0% |
| Object coverage: clearly visible classes mentioned | 100.0% [100.0%, 100.0%] | 100.0% | 100.0% | 100.0% | 0.0% | 69.0% |
| Claims supported by the facts | 100.0% [100.0%, 100.0%] | 100.0% | 100.0% | 100.0% | 0.0% | 57.3% |
| Claims contradicted by the facts | 0.0% [0.0%, 0.0%] | 0.0% | 0.0% | 0.0% | 0.0% | 34.3% |
| Claims that cannot be verified (no annotation covers them) | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 8.4% |
| Claims supported by annotation-based facts | 88.1% | 88.2% | 88.1% | 88.2% | 0.9% | 48.3% |
| Human-sentence items covered | 54.2% [44.2%, 64.9%] | 55.0% | 55.9% | 54.2% | 7.1% | 44.1% |

## Output quality

| Metric | Value |
|---|---|
| Agreement between views (facts all views agree on) | 89.8% |
| Empty descriptions | 0.0% |
| Repetition loops | 0.0% |
| Mean words per description | 65.50 |
| Mean latency per call (s) | 0.00 |

## Similarity to the human sentence (secondary)

Whole-text similarity is reported for completeness. It rewards topical overlap, not correctness, which is why the claim-level checks above are the main result.

| Metric | Value |
|---|---|
| Mean embedding cosine to scene.description | 0.48 |
| Description closest to its own scene's sentence (of all scenes) | 20.0% |

## Per scene

| Scene | Human sentence | Model description (final) | Human items covered | Errors |
|---|---|---|---|---|
| scene-0061 | Parked truck, construction, intersection, turn left, following a van | It is daytime. The drive passes an intersection. The drive is in Singapore, where vehicles drive on the left. Our car is driving. Our car turns left. There are cars. Most cars are moving. There are trucks. Most trucks are stopped. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. Most bicycles or motorcycles are parked. There are traffic cones. There are road barriers. | 4/5 | none |
| scene-0103 | Many peds right, wait for turning car, long bike rack left, cyclist | It is daytime. The drive is in Boston, where vehicles drive on the right. Our car is driving. Our car drives straight ahead. There are cars. Most cars are parked. There are trucks. Most trucks are parked. There are no buses. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. There are traffic cones. There are no road barriers. | 2/4 | none |
| scene-0553 | Wait at intersection, bicycle, large truck, peds crossing crosswalk, ped with stroller | It is daytime. The drive passes an intersection. The drive is in Boston, where vehicles drive on the right. Our car is stopped. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are buses. Most buses are moving. There are pedestrians. Most pedestrians are walking. There are no bicycles or motorcycles. There are no traffic cones. There are road barriers. | 1/5 | none |
| scene-0655 | Parking lot, parked cars, jaywalker, bendy bus, gardening vehicles | It is daytime. The scene is in a parking lot. The drive is in Boston, where vehicles drive on the right. Our car is driving. Our car drives straight ahead. There are cars. Most cars are parked. There are trucks. Most trucks are parked. There are buses. Most buses are stopped. There are pedestrians. Most pedestrians are walking. There are no bicycles or motorcycles. There are traffic cones. There are no road barriers. | 2/5 | none |
| scene-0757 | Arrive at busy intersection, bus, wait at intersection, bicycle, peds | It is daytime. The drive passes an intersection. The drive is in Boston, where vehicles drive on the right. Our car is moving slowly. Our car stops for part of the drive. Our car drives straight ahead. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are buses. Most buses are moving. There are no pedestrians. There are bicycles or motorcycles. Most bicycles or motorcycles are ridden. There are no traffic cones. There are no road barriers. | 4/5 | none |
| scene-0796 | Scooter, peds on sidewalk, bus, cars, truck, fake construction worker, bicycle, cross intersection, car overtaking us | It is daytime. The drive passes an intersection. The drive is in Singapore, where vehicles drive on the left. Our car is driving fast. Our car drives straight ahead. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are pedestrians. Most pedestrians are walking. There are no traffic cones. There are no road barriers. | 5/9 | none |
| scene-0916 | Parking lot, bicycle rack, parked bicycles, bus, many peds, parked scooters, parked motorcycle | It is daytime. The scene is in a parking lot. The drive is in Singapore, where vehicles drive on the left. Our car is driving. Our car turns right. There are cars. Most cars are parked. There are trucks. Most trucks are parked. There are no buses. There are pedestrians. Most pedestrians are standing. There are bicycles or motorcycles. Most bicycles or motorcycles are parked. There are no traffic cones. There are no road barriers. | 4/7 | none |
| scene-1077 | Night, big street, bus stop, high speed, construction vehicle | It is night. The drive is in Singapore, where vehicles drive on the left. Our car is driving fast. Our car turns left. There are cars. Most cars are moving. There are trucks. Most trucks are moving. There are no pedestrians. There are no traffic cones. There are road barriers. | 4/5 | none |
| scene-1094 | Night, after rain, many peds, PMD, ped with bag, jaywalker, truck, scooter | It is night. The road is wet. The drive is in Singapore, where vehicles drive on the left. Our car is driving. Our car turns left. There are cars. There are no trucks. There are buses. Most buses are moving. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. There are no traffic cones. There are no road barriers. | 3/8 | none |
| scene-1100 | Night, peds in sidewalk, peds cross crosswalk, scooter, PMD, difficult lighting | It is night. The drive is in Singapore, where vehicles drive on the left. Our car is stopped. There are cars. Most cars are moving. There are no trucks. There are pedestrians. Most pedestrians are walking. There are bicycles or motorcycles. Most bicycles or motorcycles are ridden. There are no traffic cones. There are no road barriers. | 3/6 | none |

## Details per scene

<details><summary>scene-0061: view 0 chosen, view agreement 100.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- The drive is in Singapore, where vehicles drive on the left.
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
  ↳ fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ fact: _The drive passes an intersection._
- **supported**: The drive is in Singapore, where vehicles drive on the left.  
  ↳ fact: _The drive is in Singapore, where vehicles drive on the left._
- **supported**: Our car is driving.  
  ↳ fact: _Our car is driving._
- **supported**: Our car turns left.  
  ↳ fact: _Our car turns left._
- **supported**: There are cars.  
  ↳ fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are stopped._
- **supported**: Most trucks are stopped.  
  ↳ fact: _Most trucks are stopped._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ fact: _Most bicycles or motorcycles are parked._
- **supported**: Most bicycles or motorcycles are parked.  
  ↳ fact: _Most bicycles or motorcycles are parked._
- **supported**: There are traffic cones.  
  ↳ fact: _There are traffic cones._
- **supported**: There are road barriers.  
  ↳ fact: _There are road barriers._

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
- The drive is in Boston, where vehicles drive on the right.
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
  ↳ fact: _It is daytime._
- **supported**: The drive is in Boston, where vehicles drive on the right.  
  ↳ fact: _The drive is in Boston, where vehicles drive on the right._
- **supported**: Our car is driving.  
  ↳ fact: _Our car drives straight ahead._
- **supported**: Our car drives straight ahead.  
  ↳ fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ fact: _Most cars are parked._
- **supported**: Most cars are parked.  
  ↳ fact: _Most cars are parked._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are parked._
- **supported**: Most trucks are parked.  
  ↳ fact: _Most trucks are parked._
- **supported**: There are no buses.  
  ↳ fact: _There are no buses._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ fact: _There are bicycles or motorcycles._
- **supported**: There are traffic cones.  
  ↳ fact: _There are traffic cones._
- **supported**: There are no road barriers.  
  ↳ fact: _There are no road barriers._

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
- The drive is in Boston, where vehicles drive on the right.
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
  ↳ fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ fact: _The drive passes an intersection._
- **supported**: The drive is in Boston, where vehicles drive on the right.  
  ↳ fact: _The drive is in Boston, where vehicles drive on the right._
- **supported**: Our car is stopped.  
  ↳ fact: _Our car is stopped._
- **supported**: There are cars.  
  ↳ fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ fact: _Most trucks are moving._
- **supported**: There are buses.  
  ↳ fact: _There are buses._
- **supported**: Most buses are moving.  
  ↳ fact: _Most buses are moving._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: There are no bicycles or motorcycles.  
  ↳ fact: _There are no bicycles or motorcycles._
- **supported**: There are no traffic cones.  
  ↳ fact: _There are no traffic cones._
- **supported**: There are road barriers.  
  ↳ fact: _There are road barriers._

**Human sentence items**

- **neutral**: Wait at intersection
- **contradicted**: bicycle
- **supported**: large truck
- **neutral**: peds crossing crosswalk
- **contradicted**: ped with stroller

</details>

<details><summary>scene-0655: view 0 chosen, view agreement 100.0%</summary>

**Fact sheet (reference)**

- It is daytime.
- The scene is in a parking lot.
- The drive is in Boston, where vehicles drive on the right.
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
  ↳ fact: _It is daytime._
- **supported**: The scene is in a parking lot.  
  ↳ fact: _The scene is in a parking lot._
- **supported**: The drive is in Boston, where vehicles drive on the right.  
  ↳ fact: _The drive is in Boston, where vehicles drive on the right._
- **supported**: Our car is driving.  
  ↳ fact: _Our car drives straight ahead._
- **supported**: Our car drives straight ahead.  
  ↳ fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ fact: _Most cars are parked._
- **supported**: Most cars are parked.  
  ↳ fact: _Most cars are parked._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are parked._
- **supported**: Most trucks are parked.  
  ↳ fact: _Most trucks are parked._
- **supported**: There are buses.  
  ↳ fact: _There are buses._
- **supported**: Most buses are stopped.  
  ↳ fact: _Most buses are stopped._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: There are no bicycles or motorcycles.  
  ↳ fact: _There are no bicycles or motorcycles._
- **supported**: There are traffic cones.  
  ↳ fact: _There are traffic cones._
- **supported**: There are no road barriers.  
  ↳ fact: _There are no road barriers._

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
- The drive is in Boston, where vehicles drive on the right.
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
  ↳ fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ fact: _The drive passes an intersection._
- **supported**: The drive is in Boston, where vehicles drive on the right.  
  ↳ fact: _The drive is in Boston, where vehicles drive on the right._
- **supported**: Our car is moving slowly.  
  ↳ fact: _Our car is moving slowly._
- **supported**: Our car stops for part of the drive.  
  ↳ fact: _Our car stops for part of the drive._
- **supported**: Our car drives straight ahead.  
  ↳ fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ fact: _Most trucks are moving._
- **supported**: There are buses.  
  ↳ fact: _There are buses._
- **supported**: Most buses are moving.  
  ↳ fact: _Most buses are moving._
- **supported**: There are no pedestrians.  
  ↳ fact: _There are no pedestrians._
- **supported**: There are bicycles or motorcycles.  
  ↳ fact: _Most bicycles or motorcycles are ridden._
- **supported**: Most bicycles or motorcycles are ridden.  
  ↳ fact: _Most bicycles or motorcycles are ridden._
- **supported**: There are no traffic cones.  
  ↳ fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ fact: _There are no road barriers._

**Human sentence items**

- **supported**: Arrive at busy intersection
- **supported**: bus
- **neutral**: wait at intersection
- **supported**: bicycle
- **supported**: peds

</details>

<details><summary>scene-0796: view 0 chosen, view agreement 62.5%</summary>

**Fact sheet (reference)**

- It is daytime.
- The drive passes an intersection.
- The drive is in Singapore, where vehicles drive on the left.
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
  ↳ fact: _It is daytime._
- **supported**: The drive passes an intersection.  
  ↳ fact: _The drive passes an intersection._
- **supported**: The drive is in Singapore, where vehicles drive on the left.  
  ↳ fact: _The drive is in Singapore, where vehicles drive on the left._
- **supported**: Our car is driving fast.  
  ↳ fact: _Our car is driving fast._
- **supported**: Our car drives straight ahead.  
  ↳ fact: _Our car drives straight ahead._
- **supported**: There are cars.  
  ↳ fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ fact: _Most trucks are moving._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: There are no traffic cones.  
  ↳ fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ fact: _There are no road barriers._

**Human sentence items**

- **contradicted**: Scooter
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
- The drive is in Singapore, where vehicles drive on the left.
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
  ↳ fact: _It is daytime._
- **supported**: The scene is in a parking lot.  
  ↳ fact: _The scene is in a parking lot._
- **supported**: The drive is in Singapore, where vehicles drive on the left.  
  ↳ fact: _The drive is in Singapore, where vehicles drive on the left._
- **supported**: Our car is driving.  
  ↳ fact: _Our car is driving._
- **supported**: Our car turns right.  
  ↳ fact: _Our car turns right._
- **supported**: There are cars.  
  ↳ fact: _Most cars are parked._
- **supported**: Most cars are parked.  
  ↳ fact: _Most cars are parked._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are parked._
- **supported**: Most trucks are parked.  
  ↳ fact: _Most trucks are parked._
- **supported**: There are no buses.  
  ↳ fact: _There are no buses._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are standing._
- **supported**: Most pedestrians are standing.  
  ↳ fact: _Most pedestrians are standing._
- **supported**: There are bicycles or motorcycles.  
  ↳ fact: _Most bicycles or motorcycles are parked._
- **supported**: Most bicycles or motorcycles are parked.  
  ↳ fact: _Most bicycles or motorcycles are parked._
- **supported**: There are no traffic cones.  
  ↳ fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ fact: _There are no road barriers._

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
- The drive is in Singapore, where vehicles drive on the left.
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
  ↳ fact: _It is night._
- **supported**: The drive is in Singapore, where vehicles drive on the left.  
  ↳ fact: _The drive is in Singapore, where vehicles drive on the left._
- **supported**: Our car is driving fast.  
  ↳ fact: _Our car is driving fast._
- **supported**: Our car turns left.  
  ↳ fact: _Our car turns left._
- **supported**: There are cars.  
  ↳ fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ fact: _Most cars are moving._
- **supported**: There are trucks.  
  ↳ fact: _Most trucks are moving._
- **supported**: Most trucks are moving.  
  ↳ fact: _Most trucks are moving._
- **supported**: There are no pedestrians.  
  ↳ fact: _There are no pedestrians._
- **supported**: There are no traffic cones.  
  ↳ fact: _There are no traffic cones._
- **supported**: There are road barriers.  
  ↳ fact: _There are road barriers._

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
- The drive is in Singapore, where vehicles drive on the left.
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
  ↳ fact: _It is night._
- **supported**: The road is wet.  
  ↳ fact: _The road is wet._
- **supported**: The drive is in Singapore, where vehicles drive on the left.  
  ↳ fact: _The drive is in Singapore, where vehicles drive on the left._
- **supported**: Our car is driving.  
  ↳ fact: _Our car is driving._
- **supported**: Our car turns left.  
  ↳ fact: _Our car turns left._
- **supported**: There are cars.  
  ↳ fact: _There are cars._
- **supported**: There are no trucks.  
  ↳ fact: _There are no trucks._
- **supported**: There are buses.  
  ↳ fact: _There are buses._
- **supported**: Most buses are moving.  
  ↳ fact: _Most buses are moving._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ fact: _There are bicycles or motorcycles._
- **supported**: There are no traffic cones.  
  ↳ fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ fact: _There are no road barriers._

**Human sentence items**

- **supported**: Night
- **neutral**: after rain
- **supported**: many peds
- **neutral**: PMD
- **supported**: ped with bag
- **neutral**: jaywalker
- **contradicted**: truck
- **contradicted**: scooter

</details>

<details><summary>scene-1100: view 0 chosen, view agreement 100.0%</summary>

**Fact sheet (reference)**

- It is night.
- The drive is in Singapore, where vehicles drive on the left.
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
  ↳ fact: _It is night._
- **supported**: The drive is in Singapore, where vehicles drive on the left.  
  ↳ fact: _The drive is in Singapore, where vehicles drive on the left._
- **supported**: Our car is stopped.  
  ↳ fact: _Our car is stopped._
- **supported**: There are cars.  
  ↳ fact: _Most cars are moving._
- **supported**: Most cars are moving.  
  ↳ fact: _Most cars are moving._
- **supported**: There are no trucks.  
  ↳ fact: _There are no trucks._
- **supported**: There are pedestrians.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: Most pedestrians are walking.  
  ↳ fact: _Most pedestrians are walking._
- **supported**: There are bicycles or motorcycles.  
  ↳ fact: _Most bicycles or motorcycles are ridden._
- **supported**: Most bicycles or motorcycles are ridden.  
  ↳ fact: _Most bicycles or motorcycles are ridden._
- **supported**: There are no traffic cones.  
  ↳ fact: _There are no traffic cones._
- **supported**: There are no road barriers.  
  ↳ fact: _There are no road barriers._

**Human sentence items**

- **supported**: Night
- **supported**: peds in sidewalk
- **supported**: peds cross crosswalk
- **contradicted**: scooter
- **contradicted**: PMD
- **neutral**: difficult lighting

</details>
