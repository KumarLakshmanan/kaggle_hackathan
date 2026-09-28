# Fresh DECEM and Majkel loss structure — 27 September 2026

The exact 4ee agent was rerun in seat 0 against the **fresh selected public
action tape** for DECEM (rank 1, episode 114253158, seed 1699455618) and
Majkel1337 (rank 6, episode 114244331, seed 1254482898). The native 1.32.7
engine used original shops. Passive hooks called the original simulator
functions once and recorded successful per-unit market commits, purchases,
land/hire commands and worker state changes. Both games finished
DONE/DONE/720 and reproduced the top-20 assessment's final cash exactly.
Seat 1 has the same loss margin; this detailed physical audit is seat 0.

| Opponent | Our cash at last hour of day 18 | Rival cash | Our/rival land | Our/rival hands | Our/rival changed worker commands through day 18 | Our/rival non-PASS commands with no state change through day 18 |
|---|---:|---:|---:|---:|---:|---:|
| DECEM | 31,320 | 54,621 | 2 / 3 | 12 / 12 | 2,320 / 3,458 | 375 / 8 |
| Majkel1337 | 34,281 | 56,268 | 2 / 3 | 11 / 11 | 2,523 / 3,494 | 424 / 59 |

At terminal, the no-change counts grow to **1,149 vs 43** against DECEM and
**1,043 vs 65** against Majkel. These are actual non-PASS worker commands
observed under the native engine. The rival has a third land quadrant and
more usable crop/animal positions, while our route repeatedly schedules work
that leaves no state change. The gap reflects a whole commitment and its
worker execution; removing isolated no-ops would not create the rival's
production system.

| Opponent | Our sale receipts | Our purchase spend | Our net | Rival sale receipts | Rival purchase spend | Rival net | Final cash margin |
|---|---:|---:|---:|---:|---:|---:|---:|
| DECEM | 238,972 | 167,080 | 71,892 | 155,671 | 19,227 | 136,444 | −63,151 |
| Majkel1337 | 216,113 | 137,841 | 78,272 | 180,357 | 21,585 | 158,772 | −77,373 |

The net column is successful market sales minus all successful per-unit
market purchases; it excludes daily operating costs and atomic hires/land.
It explains most of each final cash deficit. Our high gross sales mostly
include WHEAT buy/sell cycling: WHEAT purchase spend is **145,804** against
DECEM and **114,695** against Majkel. Our WHEAT net receipts are −56 and
+3,435, respectively, despite 3,593 and 3,082 units sold. The rivals spend
only 5,667 and 7,065 on WHEAT product purchases.

DECEM's rival receives 57,015 from STRAWBERRY, 26,677 from MILK, 16,236
from MELON and 13,085 from EGG. At the last hour of day 18 it has 55 planted
tiles, 5 cows, 8 sheep and 7 geese; we have 35 planted tiles, 2 cows, 3
sheep and 4 geese. Majkel's rival receives 55,731 from MILK, 31,295 from
WOOL and 14,118 from TOMATO. Its day-18 position has 55 planted tiles, 11
cows, 8 sheep and 21 tomato plots; ours has 33 planted tiles, 3 cows, 3
sheep and 3 tomato plots. Those sales and assets are coherent bundles funded
early enough to work; adding a late isolated animal or crop command to our
existing schedule would leave the land, feed, seed and worker obligations
unaddressed.

## Existing complete route compatibility

The current route chosen from the first two shops is embedded route
113371344 for DECEM's BRUNCH_SPOT/BRUNCH_SPOT game and 113474133 for
Majkel's PIZZA_SHOP/SMOOTHIE_SHOP game. Of the 145 embedded routes, only
route 113371344 matches DECEM's **full physical sequence** from day 6
through day 17. For Majkel, route IDs 113339524, 113356062 and 113474133
match, but their entire day-18-to-end action suffixes are byte-identical.
Thus neither state has a distinct already embedded complete suffix ready
for a day-18 switch. The previously rejected route-switch experiments remain
rejected; no new switch was run here. The rivals' complete schedules are
tested separately in `FULL_TAPE_PILOT_RESULTS.md`.

**Decision:** Accept the funded-production and execution gap as a diagnosis.
Reject a ready-made embedded late route switch and any policy promotion from
these fixed tapes. A future candidate would need an early, funded schedule
chosen from observable shops and farm state, followed by native reacting
validation. No `main.py` edit or Kaggle upload was made.

Evidence: `decem_current_seat0_events.json.gz`,
`majkel_current_seat0_events.json.gz`, `fresh_loss_structure.json`,
`route_compatibility.json`, `FULL_TAPE_PILOT_PLAN.md`, and
`FULL_TAPE_PILOT_RESULTS.md`.
