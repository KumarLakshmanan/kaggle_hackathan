# Control-group coverage correction — 2026-09-28 01:47 UTC

Before selecting a route, checking the exact top-20 baseline captures
revealed an error in the development fixture grouping. The original plan
assigned Yizhou to A and Kaggledew Valley to C without checking their
captured first two shops. The actual observations are:

- A, BRUNCH_SPOT / BRUNCH_SPOT: DECEM and live loss leave you.
- B, YARN_STORE / FARMERS_MARKET: Boey and Kaggledew Valley.
- C, SMOOTHIE_SHOP / ICE_CREAM_SHOP: Vadim Vasilenko and Yizhou.

The original 128-job run is retained and allowed to finish. Its 20 A/Yizhou
games and 24 C/Kaggledew games test unaffected controls and cannot substitute
for affected-control coverage. Add all missing B/Kaggledew games (20) and
C/Yizhou games (24) for the same 32 frozen source variants. No strategy,
route pool, selection criterion or pass/fail threshold changes. Retain all
172 raw results; select using the 128 relevant games under the corrected
groups. Verify each top-20 fixture's group against both exact baseline
captures before scheduling. The leave you public-loss source group was
already checked directly in its archived step-144 observation.

Do not call the original `search.py select`, which uses the wrong groups.
Use `complete_controls.py run` and then `complete_controls.py select`.
The original plan and pool remain byte-for-byte preserved, and the
correction is separately hashed. No candidate can proceed without all
affected winning seats checked and preserved. No native outcome has been
used in this route selection, and no promotion is authorized by replay wins.
