# Complete route 125 on Pizza Shop / Yarn Store — 2026-09-26

## Hypothesis and selection

The R108 route library has a complete route 125 for the observed day-6 shop pair
`PIZZA_SHOP,YARN_STORE`, but the later V92 table unconditionally selects the
sheep-heavy route 9. The standalone candidate
`exp_pizza_yarn_route125_20260926.py` restores route 125 for steps 144–647
only on that public shop pair. Its route is a whole production schedule (four
cows, four sheep, three geese in the source plan), not an isolated crop swap.
The rest of the incumbent policy and final route-2 phase remain intact.

The fixed-action development screen predeclared three matching-shop routes
(fresh Boey loss, Fourth Quadrant loss, Ghost Rule win) and two other-shop
controls. The native test then selected the first four matching-shop seeds
from seed 2609600 onward before evaluating the route: 2609666, 2609713,
2609785, 2609800, found after scanning 201 seeds. These are four distinct
games; the two seats gave identical cash outcomes on each seed.

## Results

| Saved action tape | Current local paired margin | Route 125 paired margin |
| --- | ---: | ---: |
| Boey, fresh top-20 loss | -5,722 | -3,838 |
| Fourth Quadrant, top-100 loss | -8,532 | -7,540 |
| Ghost Rule, top-100 win | +21,850 | +15,010 |
| Dmytro Maliarenko, other-shop control | +3,346 | +3,346 |
| 吃白饭的大肥鱼, other-shop control | +123,554 | +123,554 |

The saved matching-shop losses remain losses and the win narrows. All ten
games were DONE. The matching-shop improvements cannot be read as reactive
agent strength because opponent actions were frozen.

The matched native A/B played current `main.py` versus itself for controls
and route 125 versus reacting current `main.py` for treatments, in both seats:

| Seed | Treatment margin, either seat | Own cash change, either seat | Reacting rival cash change, either seat |
| --- | ---: | ---: | ---: |
| 2609666 | +5,924 | +5,042 | -882 |
| 2609713 | +3,457 | -208 | -3,665 |
| 2609785 | -1,696 | +1,446 | +3,142 |
| 2609800 | -10,867 | +27,599 | +38,466 |

Every control margin was zero. Treatment won 2/4 distinct seeds and lost 2/4;
the average margin was -795.5 per distinct game. Counting both seats, own
cash rose 67,758 and rival cash rose 74,122, a net margin change of -6,364.
The route activated for all 504 eligible turns in each of eight treatments;
all 16 native games were DONE. Maximum treatment agent call was 136.9 ms.

## Decision

**Reject unconditional route-125 restoration.** It does not rescue the
predeclared saved losses and its reactive average is negative, including a
10,867-coin loss. Keep the current local `main.py` SHA-256
`6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`.
No Kaggle upload occurred. The native comparison is only four distinct seeds
against one reacting policy, so it cannot establish that route 125 is always
bad; it is enough to withhold promotion.

Reproduce from the workspace root:

```powershell
python -B -X utf8 diagnostics\top10_goal_20260926\scan_pizza_yarn_seeds.py
python -B -X utf8 diagnostics\top10_goal_20260926\reactive_pizza_yarn_route125.py
```

Artifacts: `pizza_yarn_5routes_summary.json`, `pizza_yarn_route125_5routes.json`,
`native_pizza_yarn_seeds.json`, and `reactive_pizza_yarn_route125.json`.
