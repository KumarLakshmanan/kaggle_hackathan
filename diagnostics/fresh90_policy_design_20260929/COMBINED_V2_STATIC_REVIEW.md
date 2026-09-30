# Combined v2 static review — 2026-09-29

## Result

No source-level deployment blocker found in v2. The candidate SHA-256 matches
`combined_v2_manifest.json` (`4802aa95c1b960f6bdbA3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4`;
case-insensitive). Compared with v1, the only source change is removing
`YARN_STORE|SMOOTHIE_SHOP: 113640729`, consistent with the manifest and the
reported v1 public-panel regressions.

## Checks

- **Selected schedules and opening prefix:** Decoded the embedded `_DATA`
  schedule tables from the frozen cb76 parent and v2. For each of the eight
  selected rules, the complete schedule's steps 0–143 exactly equal the
  incumbent opening (0–71) plus the incumbent first-shop route (72–143).
  The rule map is consulted for the pair beginning at step 144. This validates
  the intended common executed prefix; it does not independently validate the
  post-step-144 schedule choices.
- **FarmIce override:** The inherited tape branch triggers only at step 144
  for `FARMERS_MARKET|ICE_CREAM_SHOP` when the rival's public board contains a
  MELON plant. That pair is absent from v2's selected rules, so the new rules
  do not collide with it. The active flag resets at step 0; a synthetic
  trigger followed by a new step-0 call confirmed the reset. The branch still
  returns a fixed full-game tape once triggered; it is inherited from cb76 and
  remains a separate generalization risk, not introduced by this combination.
- **Funded-land suffix:** It only moves one already-scheduled `BUY_LAND` order
  to the end, and only after idle/mirror market simulations pass its state and
  cash guards. It constructs a new market list and assigns it to the fresh
  action dictionary after the checks; exceptions return the unmodified parent
  action. The simulator uses idle/mirror forecasts, so it does not establish
  that an unknown reacting rival will preserve the same market result.
- **Loader and state reset:** The file parses and imports; the named
  `kaggle_fresh_execution_schedule_entrypoint` is callable and returned the
  expected `{farmer, hands, market}` shape at steps 0, 144 and 718. A selected
  `ICE_CREAM_SHOP|SMOOTHIE_SHOP` observation reported route `113332529` at
  step 144. Calling step 0 afterward reset the episode-scoped FarmIce flag.

## Validation limits

V1 lost four cb76 winning seats on public27 (reported by root), which prompted
v2 to remove the `YARN_STORE|SMOOTHIE_SHOP` route. The v2 manifest correctly
marks public27 as development data. `COMBINATION_PLAN.md` still contains the
original public27 no-regression gate language, so do not present a v2 result on
that same panel as independent validation. Reserved2/reserved3 and untouched
native seeds remain necessary for any later promotion decision. No games were
run for this review.
