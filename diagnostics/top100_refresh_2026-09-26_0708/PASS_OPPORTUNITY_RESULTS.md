# Same-tile `PASS` probe — 2026-09-26 19:44 UTC

`audit_pass_opportunities.py` used only the existing complete native Boey
and mhw candidate-seat-0 traces. The first raw count was corrected before
policy construction: nonongoing crops carry a positive `yield_units` value
before first maturity, when the engine ignores `HARVEST`. The saved output
`pass_opportunities_two_losses.json` applies the engine's first-yield days.

| Trace | Our `PASS` commands | `PASS` with immediate legal same-tile action | Distinct feedable animal/day pairs with no later same-day feed |
| --- | ---: | ---: | ---: |
| Boey | 756 | 217 | **50** |
| mhw | 737 | 203 | **34** |

The raw opportunity count repeats the same tile across turns and is not a
cash estimate. Most full-yield crops and `CARE`/fertilizer opportunities were
handled later by the scheduled workers. All 84 unhandled feedable animal/day
pairs had zero prior consecutive unfed days; the contemplated extra feed was
for possible fed-care production, not animal escape prevention. The probe
met the predeclared threshold to investigate, but it did not support a direct
policy promotion. A narrow isolated feed candidate was built and rejected
after its four-game smoke; see `../pass_feed_20260927/RESULTS.md`.
