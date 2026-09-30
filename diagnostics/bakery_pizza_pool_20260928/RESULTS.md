# Bakery/Pizza route pool — 2026-09-28 02:24 UTC

**Pass development into full saved-panel integration; no promotion yet.**
All 66 games complete DONE/DONE/720 with no recorded errors. The capture at
observation 144 confirms BAKERY/PIZZA_SHOP in both seats of all three
fixtures. All 11 immutable schedules share the actual first 144 incumbent
raw actions. The full pool and selection rule were frozen before outcomes.

The rule selects complete route **113615383**, using wins first, then
win points, then summed paired margin difference. It rescues two of the
three public losses. Incumbent was an explicit no-change option with zero
both-seat wins; the unchanged route's complete-schedule alias also retains
the original three losses.

| Fixture | Incumbent margin, seats 0 / 1 | Selected margin, seats 0 / 1 | Outcome |
|---|---:|---:|---|
| mhw | -21,260 / -21,260 | -9,646 / -29,166 | loss / loss |
| high frequency farming | -7,539 / -7,539 | +17,170 / +16,639 | win / win |
| Navier-stokes | -7,764 / -7,764 | +26,065 / +26,065 | win / win |

The paired margin change totals +120,253 across six seat games. The mhw
seat-1 deficit worsens; it is reported rather than used as an unannounced
cash veto. The selected candidate is
`a823911f88ada31ac00f8020c50d374c334d3130d89a93c220c864b5738134be`.
It is saved as `candidate_selected.py` and separately backed up in the
workspace root as `main_candidate_bakery_pizza_20260928_a823911f.py`.

## Full saved-panel integration — 2026-09-28 02:34 UTC

All 100 games complete DONE/DONE/720 with no recorded errors. The three
affected fixtures exactly match their selected component outcomes; every
unaffected fixture exactly matches the incumbent. Every incumbent winning
seat is preserved. Candidate: **2/30** public-loss sweeps (4W/0D/56L),
**17/20** top-team sweeps (34W/0D/6L), **19/50** combined both-seat sweeps.

**Pass integration; advance to the frozen reacting pilot.** The outcome-blind
prefix scan has started in the new 2911000–2911511 range. Evidence:
`full_panel.json`, `full_panel.jsonl`.

## Bounded activation scan — 2026-09-28 03:04 UTC

**Not qualified to advance under the frozen coverage gate.** The scan
finished all 512 allowed incumbent-versus-incumbent prefixes, finding only
three both-seat activations; four were required. Against the market policy,
it found four within 416 prefixes. There are 935 prefix games total,
including the opposite-seat checks. No full-game strength outcomes were
selected or measured, so this is insufficient activation evidence, not a
measured win-rate rejection. Preserve the candidate and the two saved-tape
rescues; do not promote or enlarge the bounded experiment retrospectively.
Evidence: `pilot_eligibility.json`, `pilot_prefixes.jsonl`.

## mhw mechanism diagnosis — 2026-09-28 03:07 UTC

All four repeated fast-engine traces exactly match the previously saved
native rewards and statuses. The candidate increases own cash by 8,735 in
seat 0 and 5,791 in seat 1. Rival cash changes by -2,879 and +13,697,
respectively; the competitive margin changes are +11,614 and -7,906.

Both new-seat traces have **identical own private state at every one of
719 observations**, successful scheduled land purchases, zero failed
PLANT commands and zero non-PASS worker commands with no state change.
Their complete generated shop paths are also identical. At step 282, the
fixed rival tries to plant WHEAT at (1,8). That tile is a WEED in the
seat-0 candidate game and empty in seat 1; the first productive rival-farm
difference therefore appears at observation 283. Shared market state
first differs at observation 405, own cash at 433, and own issued orders
at step 456. This is a rival physical-execution and shared-market
divergence, not evidence for repairing our worker commands. It does not
prove that this single plot explains the entire final cash gap.

**Accept the diagnosis; reject a generic own-worker repair from it.**
Evidence: `SEAT_DIAGNOSIS_PLAN.md`, `mhw_traces.json`, `mhw_analysis.json`
and the four hash-receipted compressed observation/action traces.

The source main remains exact 4ee. No candidate here includes the rejected
b6ebf9ad or fb6c5413 changes. No Kaggle activity occurred.

Evidence: `PLAN.md`, `pool.json`, `screen.jsonl`, `screen.json`,
`selection.json`, and `native_harness_provenance.json`.
