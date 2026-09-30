# Saved-route coverage inventory — 2026-09-28 02:10 UTC

**Decision: accept a separate bounded Bakery/Pizza development experiment;
do not infer a policy improvement from coverage.** The 30 saved public losses
span 22 first-two-shop pairs. The largest cluster is BAKERY/PIZZA_SHOP:
three losses (mhw, high frequency farming, Navier-stokes), no saved public
wins and no current top-20 entries in that pair. Eleven unique complete
routes share the incumbent's actual first 144 raw actions. The current
day-six route 113817611 is an exact full-action alias of 113618016.

The existing compatible-route candidate affects a different two-pair set
and is being qualified separately. Do not combine it with this new search
before either earns its own qualification. Earlier route-101/110 experiments
used the older 489fe8e4 architecture, different tapes, and different gates;
their rejection remains unchanged. This audit does not rerun those artifacts.

The inventory covers all 84 saved public games and the 20 top teams. It
checks immutable source, cohort, feature and assessment hashes. For the 61
previously extracted public games, replay hashes agree with the frozen
feature file; the other 23 replays were decompressed and their raw hashes
verified during this audit. Public coverage describes the original recorded
seat. Top-20 first-two-shop observations agree across the two local seats.

No candidate outcomes were collected. Main remains exact 4ee. No Kaggle
request was made. Reproduce with `python -X utf8
diagnostics/compatible_route_coverage_20260928/audit.py`; see `coverage.json`.
