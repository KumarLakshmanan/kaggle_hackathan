# Ghost + Kwa + Pizza/Ice Cream composition diagnostic

## Question

Does the previously tested Ghost + Kwa candidate (`7b354498…c0fca2`) retain its
behavior when the frozen Pizza/Ice Cream continuation is appended, and does
route `113339524` rescue both seats of Civitasmass `live-114238112`?

The existing Pizza/Ice Cream package tests only 6d + that route. This package
is rebuilt against the exact Ghost + Kwa parent. It uses the same eight saved
seat fixtures: both target seats and six same-key public-win controls. The
runner plays parent and composed candidate directly on every fixture and seat.

## Frozen gates

- Both target seats finish DONE/DONE at 720 frames and become wins.
- All six controls preserve the direct parent result, both rewards, margin,
  statuses, and frame count exactly.
- The Pizza/Ice Cream telemetry reports the source branch, exact step-72 key,
  exact step-144 pair, route `113339524`, 575 active turns, and zero errors on
  target seats; it remains inactive on controls.
- Ghost and Kwa remain inactive on these Pizza fixtures; their previously
  tested 72-turn triggers are disjoint by first shop.
- Before step 144, the composed candidate's action matches its parent for all
  eight saved observation traces. The static probe checks route-map scope at
  step 144 and performs no simulator transitions.

A pass is fixed-replay evidence for the composition only. It does not establish
reactive qualification or promotion readiness. `main.py` remains unchanged and
Kaggle is out of scope.
