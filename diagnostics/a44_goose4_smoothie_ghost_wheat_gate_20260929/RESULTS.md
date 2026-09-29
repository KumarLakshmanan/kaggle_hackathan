# Ghost Ice wheat route result

Completed 2026-09-29 04:08 IST. Fixed action tapes only; this is not reactive validation.

## Candidate and frozen trigger

Candidate SHA-256: `228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767`.
Exact 6d parent SHA-256: `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.

At step 72 on the source bridge, route `113360743` applies only to `ICE_CREAM_SHOP|M8+|C>S|G0` when public WHEAT inventory is <= 9,975. The bound 208-seat feature census has exactly two triggers, the two seats of `live-114288168`; it has no top20 or public-win activations.

## Outcome panel

A first runner attempt in `outcome_run_20260929` wrote 11 of 12 games but was invalid: its telemetry checker received the panel row instead of the actual game result. The partial ledger is preserved and excluded. The corrected, separately frozen V2 package includes synthetic positive/negative checks for that telemetry path and passed all 50 frozen hashes before running.

V2 result: receipt SHA-256 `510339d20aace4317f7dfc4330b7a8f4e59d1edcc5fd458f474fdefb3c702f8`; 12-row ledger SHA-256 `a060e1441ee0ac37e8e83c3e81203797fecc78ad0d306e27ca98a21cbcf6831c`.

All 12 games were DONE/DONE at 720 frames with no candidate errors and all telemetry checks passed. Both target seats won at +1,298 margin. The exact 6d margins were -2,253 and +1,425, for paired margin changes of +3,551 and -127 respectively. All ten non-trigger controls exactly preserved the 6d result, candidate reward, opponent reward, and margin.

The static census and tested control rows imply the standalone Ghost derivative changes one full loss30 sweep: **22/30 to 23/30**. Top20 remains **19/20**, and public-win remains **53/54**. This score is for Ghost composed on 6d alone. The separate Kwa derivative independently reaches 23/30; their combined candidate has not yet been built or tested.

## Decision

Retain this as a promising narrow fixed-tape patch. Do not promote it or upload it. Next compose it with the independently tested Kwa route and validate the combined policy, since both candidates share a parent. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; Kaggle was not checked.
