# Judge validation: `nli-deberta-v3-base`

Claims are generated from each scene's fact sheet in different wording, with known truth (true: objects in view, the real time of day and motion of our car; false: classes with no box in view, the opposite time of day or motion). They are cleaner than real model text, so these are optimistic estimates of the judge's accuracy.

| Claim kind | True claims | False claims | True → supported | False → supported (error) | False → contradicted | True → contradicted (error) |
|---|---|---|---|---|---|---|
| all | 198 | 135 | 100.0% | 15.6% | 75.6% | 0.0% |
| objects | 128 | 65 | 100.0% | 18.5% | 81.5% | 0.0% |
| time_of_day | 30 | 30 | 100.0% | 0.0% | 100.0% | 0.0% |
| ego_motion | 30 | 30 | 100.0% | 30.0% | 30.0% | 0.0% |
| turn | 10 | 10 | 100.0% | 0.0% | 100.0% | 0.0% |

**How to read it.** "True → supported" is how often a correct claim gets credit; "False → supported" is how often a wrong claim is wrongly credited.

**"The car" ambiguity.** "The car is stopped." was judged on 24 views where our car is moving and other cars are present (truth unknown: "the car" may be another car): supported 13, contradicted 11, neutral 0. A contradiction means the judge read "the car" as our car; one reason contradiction rates are indicative only.

**Disagreements (first 15)**

- scene-0061 (ego_motion, false): The vehicle carrying the camera is not moving. → **supported**
- scene-0061 (ego_motion, false): The vehicle carrying the camera is not moving. → **supported**
- scene-0061 (ego_motion, false): The vehicle carrying the camera is not moving. → **supported**
- scene-0103 (objects, false): A road barrier is clearly visible in the scene. → **supported**
- scene-0103 (objects, false): A road barrier is clearly visible in the scene. → **supported**
- scene-0103 (objects, false): A road barrier is clearly visible in the scene. → **supported**
- scene-0553 (ego_motion, false): The vehicle carrying the camera is moving. → **supported**
- scene-0553 (ego_motion, false): The vehicle carrying the camera is moving. → **supported**
- scene-0553 (ego_motion, false): The vehicle carrying the camera is moving. → **supported**
- scene-0655 (objects, false): A road barrier is clearly visible in the scene. → **supported**
- scene-0655 (ego_motion, false): The vehicle carrying the camera is not moving. → **supported**
- scene-0655 (objects, false): A road barrier is clearly visible in the scene. → **supported**
- scene-0655 (ego_motion, false): The vehicle carrying the camera is not moving. → **supported**
- scene-0655 (objects, false): A road barrier is clearly visible in the scene. → **supported**
- scene-0655 (ego_motion, false): The vehicle carrying the camera is not moving. → **supported**
