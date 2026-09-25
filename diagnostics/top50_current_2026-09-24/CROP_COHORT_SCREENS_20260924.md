# Crop-cohort screens — 2026-09-24

The frozen incumbent is `main.py` SHA-256
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`:
67/100 paired-route wins and 133/200 seat wins on the selected top-50 public
**fixed-action** replay panel. These are development tests, not adaptive matches
or a Kaggle ranking estimate. All results below used the installed native
Kaggriculture 1.32.7 simulator unless explicitly labeled fixed-shop.

| Experimental candidate | Screen | Result versus incumbent | Decision |
| --- | --- | --- | --- |
| `exp_agent_carrot_cohort_20260924.py`, one day-11 carrot crop in place of strawberry | First 20 routes, both seats | Six routes changed; all six paired margins fell. The same six selected seeds with `_ALLOW_REPLANT=true` still fell versus incumbent. No tested loss was rescued. | Reject; do not promote. The borrowed strawberry calendar also does not certify a complete repeated-carrot lifecycle. |
| `main_tomato_early_start_exp_2026-09-24.py`, existing tomato project day 15 instead of 18 | Six selected losses and matched controls, plus same-seed extra routes: 14 routes/28 games | Excluding episode 112933084 changed from −78,392 to −84,128 paired margin; no loss was rescued. | Reject; do not promote. |
| `main_tomato_shops2_exp_2026-09-24.py`, tomato project threshold two active shops rather than three | Same 14 routes/28 games | ActiveMusyoku episodes 112937075 and 112941285 fell by 5,300 and 9,796 paired-margin coins; no loss was rescued. | Reject; do not promote. |
| `main_straw_tomato_swap_exp_2026-09-24.py`, up to 13 day-11 strawberry purchases/plants converted to tomato under observed tomato support and no strawberry shop | Full 100 routes/200 games | Exactly two paired routes changed. ActiveMusyoku 112937075 improved −16,466 → −10,102 (own cash +11,670 across seats, rival cash +5,306). Gatswei 112936562 worsened −13,136 → −15,328 (own cash −12,110, rival cash −9,918). Outcomes stayed **67/100 route wins and 133/200 seat wins**; all games `DONE`, candidate max action 291.7 ms. | Do not promote: zero win gain, one loss regression, only two exposed routes. |
| `exp_h6_hinge_price_20260924.py`, use the installed engine's exact scarce-market hinge/target for carrot, tomato and egg in H6 sell-slot scoring | Full 100 routes/200 games | The corrected price function matched engine quotes for all nine products at sampled inventories. Forty-two route margins changed: 21 rose, 21 fell; total paired-margin change +878 coins, total own-cash change +730 over 200 games. **No win change:** 67/100 routes, 133/200 seats; all games `DONE`. | Keep as a documented pricing-model correction candidate, but do not promote on current competitive evidence. |
| `exp_agent_day6_tomato_cohort_20260924.py`, convert at most eight incumbent day-6 strawberry seed purchases/plantings to tomato when both currently visible shops demand tomato and none demand strawberry | Predeclared 11-seed loss/control panel (12 routes/24 games), then the one eligible ActiveMusyoku 112937075 route (both seats) | The 12-route panel had **zero eligible routes and zero score changes**, so it cannot support an improvement claim. On the eligible route, both native seats still lost: our/rival cash 78,118/85,118 versus incumbent 79,685/87,918 in each seat. Own cash **fell 1,567 per seat** despite paired margin improving by 2,466 because the rival fell more. All 26 games `DONE`. | Reject; do not promote an own-cash regression based on a margin artifact. |
| `exp_premium_sizing_20260925.py`, ablate the incumbent's eligible late tomato project to half (five seeds/tiles, incumbent staffing calendar) or omit | Two preselected losses and one control, both seats, Full/Half/Omit native replays | Only Excluding 112933084 activated the project. Its own cash per seat was **116,023 Full / 104,078 Half / 108,145 Omit**, still a loss in both seats for every arm. Half confirmed five seed purchases, five plants and 40 successful tomato sales in the traced seat. The other loss/control were unchanged. All 18 games `DONE`; a separate Full pass-through check matched the frozen control. | Reject both reduced arms; no own-cash improvement or rescued loss. This single activated route and unchanged staffing do not rule out a better complete allocator. |

For the ActiveMusyoku 112937075 seat-0 mechanism check, the unchanged native
shop sequence was replayed in a separately labeled forced-shop environment
for *both* arms. Incumbent cash stayed 79,685 versus rival 87,918 (margin
−8,233). The day-11 swap produced our 83,405 versus rival 88,361 (margin
−4,956): own cash +3,720, rival cash +443, one-seat margin +3,277.
Successful own sales were 51 tomato units for 4,292 coins and 140 strawberry
units for 2,477 coins, versus zero tomato and strawberry receipts 3,461 for
the incumbent. The native candidate produced our 85,520 versus rival 90,571
in that seat, so the additional native change is not a same-shop policy effect.
The fixed-shop result remains a loss; it does not validate a general trigger.

The day-6 variant was separately replayed with the incumbent's exact shop
sequence forced in both arms for the eligible route, seat 0. Under that
controlled shop path it earned our 82,047 versus rival 87,801 (margin −5,754),
compared with the incumbent's 79,685 versus 87,918 (margin −8,233). Thus own
cash rose 2,362 and the rival fell 117 under fixed shops, but neither this
controlled seat nor either native seat won. The native counterfactual changed
future shop draws and reversed the own-cash sign. This is evidence of a path-
sensitive experimental branch, not a robust policy improvement.
The first observed shop-path divergence was at step 504 (day 21): the native
incumbent unlocked another `SMOOTHIE_SHOP`, while the native variant unlocked
`FARMERS_MARKET`. The variant's native milk sales were 253 units for 28,233
coins, versus the incumbent's 266 for 33,414; with shops forced to the
incumbent path, variant milk sales remained 266 for 33,414. The 5,181-coin
native milk-receipt drop helps explain why the fixed-shop gain did not carry
over; it does not establish a general profit expectation for the crop swap.

Stored native benchmark outputs are `carrot_cohort_first20_20260924.json`,
`carrot_replant_6seed_pilot_20260924.json`,
`tomato_day15_12seed_pilot_20260924.json`,
`tomato_two_shops_12seed_pilot_20260924.json`, and
`straw_tomato_swap_100routes_20260924.json`, plus
`h6_hinge_100routes_20260924.json` in this directory. The two
forced-shop event traces are `active_112937075_main_fixedshops_trace_20260924.json.gz`
and `active_112937075_swap_fixedshops_trace_20260924.json.gz`; the former
reproduced the frozen native incumbent exactly. None of these experimental
candidates was copied into `main.py` or submitted to Kaggle.

The day-6 variant's outputs are `day6_tomato_11seed_pilot_20260925.json`,
`day6_tomato_active_pilot_20260925.json`, and
`active_112937075_day6_tomato_fixedshops_trace_20260925.json.gz` and
`active_112937075_day6_tomato_native_trace_20260925.json.gz` in this
directory.

The bounded Full/Half/Omit pilot is in
`diagnostics/premium_sizing_20260925/` at the workspace root. Native rival cash
on the activated Excluding route was 155,219 Full, 152,403 Half, and 177,808
Omit per seat; therefore paired-margin changes cannot be interpreted as own
profit. The Half trace confirms the reduced planting actually executed, but
its unchanged full staffing calendar makes this a sizing ablation, not a
fully optimized cohort planner. No fixed-shop sizing counterfactual or fresh
reactive-opponent check was run because both reduced native arms failed the
predeclared own-cash gate.
