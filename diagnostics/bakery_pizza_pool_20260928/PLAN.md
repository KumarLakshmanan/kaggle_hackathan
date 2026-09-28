# Bakery/Pizza complete-route pool — frozen 2026-09-28 02:12 UTC

## Rationale and scope

The hash-checked coverage inventory in
`diagnostics/compatible_route_coverage_20260928/coverage.json` identifies
BAKERY/PIZZA_SHOP as the largest remaining public-loss cluster: mhw
(live-114235177), high frequency farming (live-114243994) and Navier-stokes
(live-114289837). No current top-20 entry or saved public win has that pair
in its recorded incumbent prefix. This is development selection, not an
independent test. Earlier experiments on older architectures remain rejected.

Keep source main SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Use target manifest SHA-256
`524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20`.
Do not combine this search with the pending b6ebf9ad candidate.

## Finite candidate pool and development selection

Deduplicate current routes by all 719 raw actions and retain exactly those
whose first 144 actions equal the actual incumbent opening: opening[0:72]
plus its BAKERY first-shop route[72:144]. This yields the 11 route IDs
113334903, 113340658, 113357237, 113416130, 113431477, 113470868,
113478215, 113615383, 113618016, 113639519, 113835510.

Each candidate changes only the BAKERY|PIZZA_SHOP map entry and all its
descendants to one complete route. Preserve the existing queue and other
reactive layers. No action, quantity, threshold or schedule tuning within
the pool. Save standalone file hashes before any outcomes. Test all three
fixtures in both seats, native engine 1.32.7, hidden configuration seed,
original generated shops, 720 turns: 66 games. Capture first-two shops at
observation 144 and verify the expected pair in both seats.

Require complete DONE/DONE/720 games and zero recorded policy errors. Include
unchanged incumbent outcomes as the explicit no-change option. Select by
most both-seat sweeps, then most seat win points (1/0.5/0), then summed
paired margin change, then lowest numeric route ID. Require at least one
new both-seat win to continue; otherwise reject the finite pool. Any known
incumbent winning seat must be preserved. Do not introduce a cash-only
rejection after a win improvement.

## Full saved-panel gate

Run the selected single file against all 50 frozen fixtures in both seats.
Require exact selected-component rewards on the three affected fixtures,
exact incumbent rewards everywhere else, no errors, all DONE/DONE/720 and
all incumbent winning seats preserved. This remains development/regression.

## Independent reacting gates, conditional on saved-panel pass

References: unchanged current main (hash above) and local
`public_market_smart_f6a756cf_20260927.py`, SHA-256
`f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`.
Use original generated shops, engine 1.32.7, full 720-turn configuration,
hidden configuration seed, and reload policies per game.

Select active seeds without seeing final outcomes by running only the
unchanged incumbent/reference prefix through observation 144. In ascending
order, take the first four seeds per reference in 2911000–2911511 where
both seats have BAKERY/PIZZA_SHOP. Confirmation, only on pilot pass, takes
the first eight such seeds per reference from 2912000–2913023. Scan seat 0
first and seat 1 only after a hit. Save shops/errors/status, no terminal
rewards. The ranges had no previous occurrence in local markdown research
before this plan. If activation is insufficient, report it without extending
the bound after seeing strength results. This estimates conditional effects
on this branch, not global leaderboard performance.

Run incumbent and candidate on each selected reference/seed in both seats:
32 full pilot games and 64 confirmation games. Require all DONE/DONE/720,
zero recorded errors and actual candidate activation in every selected game.
Require no reference-specific win-point regression and strict pooled
win-point gain in both stages. Confirmation also requires the lower endpoint
of a 95% paired-seed bootstrap interval to be strictly positive: 10,000
draws, RNG 2913099, resample whole distinct seeds including both seats and
all reference games with that seed. Normalize total win-point difference
by candidate game count. Stop early only on a mathematically irreversible
gate failure, retaining the bound and incomplete count.

Before any promotion, freeze and pass the 54 saved public-win regression
and both-seat local Kaggle file-loader checks. Preserve and back up main.
No Kaggle access or upload. The user's full 50/50 local objective remains
the goal; a partial repair does not complete it.
