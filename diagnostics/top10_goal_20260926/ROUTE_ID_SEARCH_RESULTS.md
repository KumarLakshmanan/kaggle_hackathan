# Complete route-ID search on targeted losses — 2026-09-26

The current submission contains 41 complete route schedules. They share
the same first-144-turn opening except route 1, so the experimental
`exp_route_probe_20260926.py` kept the normal opening and overrode the
chosen route only after the first two public shops appeared. The control
using route 9 on DSM reproduced current `main.py` exactly (−17,199 per
seat, both `DONE`). No Kaggle upload occurred.

On DSM's saved `BRUNCH_SPOT,YARN_STORE` scenario, all 41 routes were
screened in seat 0 under original shops. **None won**. Route 126 narrowed
the deficit most, to −12,820 from −17,199, but this did not meet the
loss-rescue gate. Raw rankings: `route_id_search_dsm.json`.

On the three largest saved `YARN_STORE,PIZZA_SHOP` losses, all 41 routes
were screened in seat 0. Route 10 was the only route to rescue any:
YumeNeko +7,126, mtmr_s1 −10,375, Lucas Boesen −18,094. The same route
was then checked in **both seats** on those three losses and two older
matching-shop winning controls, all `DONE`:

| Route | Baseline paired margin | Route 10 paired margin |
| --- | ---: | ---: |
| YumeNeko | −41,408 | +2,041 (seat 0 +7,126; seat 1 −5,085) |
| mtmr_s1 | −50,044 | −20,750 |
| Lucas Boesen | −40,088 | −36,188 |
| RS Turley, winning control | +270,144 | +273,042 |
| 吃白饭的大肥鱼, winning control | +123,554 | +108,380 |

The control regression was −15,174 paired coins. The frozen saved routes
are development tapes. A reactive check on eight previously selected native
seeds with exactly `YARN_STORE,PIZZA_SHOP`, both seats, compared route 10
against current `main.py`. **Route 10 lost all 16 games**, by 759–3,899
coins per seat, for −43,866 total margin. All shops matched and all games
ended `DONE`. These seeds were used for an earlier route-100 test, so they
are not a fresh holdout; the uniformly adverse result is enough to reject
this candidate before broader promotion.

**Reject route 10 and retain the current route selector.** A fixed-action
rescue did not survive reacting play. Source and evidence:
`build_route_probe.py`, `route_id_search_yarn_pizza.json`,
`route10_yarn_pizza_controls.json`, and
`reactive_route10_yarn_pizza.json`.
