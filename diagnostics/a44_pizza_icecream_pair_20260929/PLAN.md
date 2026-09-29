# Exact-6d Pizza/Ice Cream continuation experiment

## Status

Static candidate only. No game transitions or simulator calls have been run.
Root `main.py` remains unchanged. This is a replay hypothesis, not a promotion.

## Hypothesis

On the exact 6d candidate, the public step-144 pair
`PIZZA_SHOP|ICE_CREAM_SHOP` occurs only on both seats of loss fixture
`live-114238112` in the frozen 208-seat feature panel. Three public-win
fixtures share its step-72 key `PIZZA_SHOP|M8+|C>S|G0`, but reveal Pizza/Pizza,
Pizza/Bakery, or Pizza/Yarn at step 144. The gate therefore includes all four
fixtures/eight seats and requires exact outcome preservation on the six
controls.

An older route-member screen found route `113339524` rescued both target seats
by 1,539 coins, but that result used a different policy prefix and is not
reused as an outcome. Its farmer and hand actions match the incumbent Pizza
root route through turn 143; the only raw action difference in that span is
the balanced Wheat buy/sell quantity at turn 79 (16 versus 15). Route
`113332529` had larger older-screen margins but diverged in physical actions
from turn 96, so it is not the predeclared choice. This experiment changes
only the exact pair's route-map subtree at step 144 on the source bridge,
provided the public step-72 key also matches.

## Frozen gates

The static builder must verify the exact 6d parent candidate and receipts,
count the step-144 public pair and step-72 key in every seat trace, and show
exactly two trigger rows, both target seats on the source branch, with zero
top20/public-win trigger rows. The three same-key public-win fixtures are
nontriggers and must preserve their outcomes exactly. It must verify the route
has 719 actions, the candidate matches its parent on all eight fixture traces
through step 143, and the modified scheduler resolves to route `113339524` from
step 144 onward. The commit may change only route-map keys beginning with the
exact pair; it must not alter Goose4/Smoothie rules, FARMICE schedules, or donor
state.

The outcome runner will be a separate eight-game fixed-tape diagnostic. It
passes only if both target seats become wins, all six control outcomes and
cash rewards match exact 6d, all games finish cleanly at 720 frames, and the
source/key/pair/route telemetry matches. This remains saved-replay evidence;
reactive native games are still required for independent qualification.

## Main risk

The route screen's wins cannot be reused as exact-6d outcomes. At step 144 the
target has 808 cash, no hired hands, 9 wheat, and 7 fertilizer; switching the
later schedule must be tested from that actual state and evaluated against
opponent market response through a full game.
