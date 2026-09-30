# Runtime partial planting — frozen before outcomes, 2026-09-28

## Mechanism and architecture check

Native Kaggriculture cancels every PLANT request for a crop if the total
request count exceeds owned seeds. The current main file is a recorded
schedule selector with market wrappers; its current callable code has no
runtime partial-planting guard. The older V43 architecture did have an
atomic guard, as recorded in agent.md; this is not a claim that the older
work was missing that feature. Exact traces on complete route 113349962
show two WHEAT requests with one seed at steps 187/188 and three with one
seed at 261. No planting succeeds in those turns. The alternative DECEM
route likewise cancels two strawberries despite owning one seed.

Build two immutable candidates: exact current 4ee plus this guard, and
the existing YARN/FARMERS complete-route 113349962 candidate d271754e
plus this same guard. Exclude every animal-funding, Bakery/Pizza,
opening-selector and other rejected change.

If and only if a crop has a positive seed inventory smaller than its
current PLANT request count, execute a copy of our current unit commands
in the native physical transition model, in farmer/hand order. Retain
each blocked-crop PLANT only when it actually consumes one available seed
in that model; replace unsuccessful/excess requests with PASS. Apply all
other commands unchanged to the scratch state so same-turn movement,
harvest/clear and planting interactions remain correctly ordered. No
new seeds, money, worker actions or market orders are added; no future
observations or rival private states are available to the guard.

## Prospective development gates

Test both immutable arms on current Boey, DECEM, the saved Yaroslav loss
live-114283577, and winning controls Kaggledew and Majkel, both seats:
20 fast diagnostic games. Verify that the Yaroslav ID resolves to that
team before building the manifest. Require all DONE/DONE/720 and zero
errors, at least one new both-seat win versus main, all old winning seats
preserved, and actual guard activation in every rescued matchup. Select
by most rescued both-seat matchups, then win points, then paired margin
change, then incumbent-based arm. Include no change as the default if
neither passes. This is development selection, not independent validation.

On success, repeat the selected arm's ten games through the original
native framework and require exact cash/telemetry parity and valid
runtime; then test all 50 frozen targets in both seats, retaining all
incumbent winning seats with at least one new sweep and no errors.

Freeze a separate outcome-blind native activation/confirmation plan
before any fresh reacting strength results, with original shops, both
seats and at least current 4ee plus f6a756cf market references. Actual
guard activation must be represented separately from route-only gains.
Both stages require nonregression per reference and strict pooled
win-point gain; confirmation also requires a positive lower 95%
whole-seed bootstrap bound. Saved public-win regressions and both-seat
local file-loader checks remain mandatory before promotion.

Main stays exact 4ee and is backed up already. No Kaggle access or upload.
The user's required 50/50 local endpoint is unchanged.
