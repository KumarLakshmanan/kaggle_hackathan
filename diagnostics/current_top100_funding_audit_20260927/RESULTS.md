# Current top-100 failed-purchase audit

Completed 2026-09-27 08:39 UTC.
All 23 non-swept current teams were examined in both seats. All 46 final
cash pairs exactly reproduce the previously saved c68 baseline. This is
outcome-selected development diagnosis, not independent strength evidence.

| Failure | Reason | Recorded attempts |
|---|---|---:|
| BUY_LAND | unchanged | 2 |
| BUY_PRODUCT | shed_full | 28 |
| BUY_PRODUCT | insufficient_cash | 30 |
| BUY_ANIMAL | insufficient_cash | 2 |
| BUY_SEED | insufficient_cash | 12 |

## Concrete mechanism

Against rank 7 (Unknown Mother-Goose), the turn-171 queue purchases one
goose and six cows before selling 20 wheat. The last cow fails at 394 coins
against a 400-coin cost. Advancing the existing 12-wheat sale recovers it
under both passive and mirror one-turn forecasts. All other own resources
are preserved; adjusted cash recovers the fixed purchase cost. The current
identical-resource guard forbids the extra planned cow. The counterfactual
does not establish a full-game gain.

Other failed product buys often concern round trips or capacity; they are
not automatically missing physical feed. Do not treat every failure as an
improvement opportunity.

## Decision

Investigate the narrowly defined, separately backed-up planned-funding
candidate under ../shunki_planned_funding_20260927/PLAN.md. No promotion
or main.py change. The previous procurement candidate remains rejected.

## Instrumentation repairs

The first harness attempt omitted the rawroute prefix and played no games.
The first successful run hooked the state[1] observation farm for seat 1,
but settlement uses state[0] farm objects. Seat-0 measurements were valid;
all 23 affected seat-1 cases were explicitly rerun after correction. Earlier
JSON and seat-1 traces remain preserved. Both cash and measurement coverage
are now complete. See audit.json, summary.json and traces/.
