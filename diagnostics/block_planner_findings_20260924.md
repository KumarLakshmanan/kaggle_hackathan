# Four-site rotating crop-block experiment (local only)

Status: **rejected for promotion**. No change to `main.py`; no Kaggle submission.

## Source and legality

- Frozen parent: `H:\hackathan\main.py`, SHA-256 `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
- Prototype: `H:\hackathan\exp_agent_block_planner_20260924.py`, current SHA-256 `74b32ea89d345188640d8dbea2a9e86ac6133e6ae8d7a3491b88d3acd257bf70`. A second-lane toggle was added after the default one-lane panel; the default remains disabled and its decision/action path is unchanged, but the exact current source was not rerun on the full panel after the user's stop request.
- The wrapper reads its own observation (farm/worker positions, crops, seeds, cash, current shops and market), plus the frozen parent's own action tape to certify a worker calendar. It does not read opponent identity, replay outcome, seed, or future shops. Fixed-shop forcing appears **only in the local diagnostic harness**, not the candidate.
- Candidate menu: `INCUMBENT`, `CARROT`, `WHEAT`, `DEFER` for four naturally empty day-11 sites `(4,5),(4,6),(3,5),(3,6)`. The default observed Artem path chooses WHEAT for `(4,5)` and leaves the others incumbent. An opt-in local toggle adds a second physically feasible WHEAT lane at `(4,6)`. This remains a partial block, **not** a complete four-tile solution.

## Certified one-lane calendar

The day-11 hour-2 strawberry-seed order is changed to one WHEAT seed before the hour-3 PLANT; the inherited hour-4 WATER remains. On day 14 an extra seed is bought at hour 1; the existing worker waters `(4,5)` at hour 2, harvests two units at hour 3, replants at hour 4, waters at hour 5, drops and sells the two carried units at hour 6, and rejoins its inherited position by hour 8. On day 16 a different worker replaces its initial WEST/EAST detour with SOUTH/WATER/HARVEST/DROP/SOUTH, selling two more units and rejoining its route by hour 6. These same-turn purchases, unit actions, drops and sells were verified in the event traces. No FEED/CARE action is directly overridden.

In the Artem fixed-shop trace, all four additional WHEAT sales succeeded (two at 42, two at 40), both seed buys succeeded, and FEED/CARE success counts stayed at the parent's 281/389. The engine also automatically drops carried inventory into the shed at midnight, subject to shed capacity; explicit DROP is used here to sell promptly, not because undelivered cargo would necessarily be lost.

## Margins (candidate minus opponent, seat 0)

| Saved-replay matchup | Parent native | WHEAT native | WHEAT, original shops forced | CARROT native | CARROT, original shops forced |
| --- | ---: | ---: | ---: | ---: | ---: |
| Artem loss, seed 672555253 | -6,073 | -5,832 | -5,793 | -6,033 | -6,009 |
| TheEggman exposed winning control, seed 994487214 | +7,243 | -1,393 | +7,600 | not tested | not tested |

The original-shop parent control reproduced +7,243. The fixed-shop WHEAT lift was +280 on Artem and +357 on the winning control, but Artem still lost. CARROT's fixed-shop lift on Artem was only +64. The native winning control flipped to a loss (-8,636 margin change) because the modified tile occupancy changed later weed RNG consumption and therefore shop draws: the original sixth/seventh shops were FARMERS_MARKET/YARN_STORE; the candidate drew ICE_CREAM_SHOP/BRUNCH_SPOT. This is a legitimate native outcome, not a reason to report the forced-shop gain as a win.

The unchanged Dieter winning route, seed 326566221, scored +68 in both native and forced-shop tests: its current-shop projection favored the incumbent strawberry and the intervention did not activate.

## Broader saved-replay screen and efficiency

`diagnostics/block_planner_top20_40routes_final.json` ran the exact final source against 40 old top-20 saved routes, both seats (80 games). All 80 agents finished `DONE`. Parent: 37/40 route wins, 74/80 seat wins. Prototype: 36/40 route wins, 72/80 seat wins. Six route pairs activated; two improved and four regressed, with a summed paired-margin change of -46,095 and one winning route flipping to a loss. The final run measured 4.66 ms/call mean, 584 ms maximum, 16.1 s/game mean wall time under eight concurrent workers. A previous behavior-identical run measured 3.34 ms/call; concurrency/system load makes these timing numbers noisy. The parent historical panel measured 2.80 ms/call. A simultaneous single-control trace measured 2.04 ms/call for the wrapper versus 2.01 ms/call for the parent.

The opt-in two-lane refinement (`_ENABLE_SECOND_LANE=true`) was tested on the Artem loss and exposed TheEggman win, seat 0, native and fixed-shop. On Artem the margins were -5,602 native and -5,506 fixed-shop (still losses, versus -6,073 parent). On TheEggman they were -1,762 native and +7,720 fixed-shop (versus +7,243 parent). The second lane planted and watered before each day boundary, harvested one unit on day 14 and two on day 18, and requested post-midnight sales. It was **not** run on the full 40-route panel after the user stopped testing. This refinement also fails both hard promotion gates: no fixed-shop loss rescue and a prior native winning-route reversal.

## Why a complete four-tile rotating block is not yet feasible in this wrapper

On the inspected loss path, the day-14 worker for `(3,5)` and `(3,6)` visits them at hours 8 and 10, then has a dense inherited sequence of crop watering, wheat harvest/replant/water and movement through hour 23. Replacing WATER by HARVEST is possible and midnight auto-drop can deliver the crop, but a second PLANT followed by same-day WATER needs two more actions at that site; there are no idle slots to insert them and still rejoin the inherited sequence. A separate idle-slot calendar **does** allow `(4,6)` to harvest/replant/water on day 14 and harvest the replacement on day 18, as the opt-in test demonstrates. Merely changing PLANT without immediate WATER is invalid: the new short crop becomes a WEED at that day boundary.

The one feasible lane becomes empty after its second harvest on day 16. The native simulator's weed generator consumes RNG only on empty cells and its shop unlock uses that same day's RNG. Emptying the lane changes future shop draws, creating large losses on some routes. Keeping occupancy invariant through later shop unlocks while continuing harvest/replant would require reallocating worker actions beyond the certified idle detours (and checking feed, shed capacity and market sales for the whole shift). That is a broader routing redesign, not a safe one-line crop substitution. This prototype should remain experimental and should **not** be merged into `main.py`.
