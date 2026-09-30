# Fixed DSM opening transplant — 2026-09-26

## Hypothesis

The current 100-route regression screen has 31 losses. Several largest
losses show a day-six rival farm with roughly nine or ten strawberry tiles
versus our four. The top-ten DSM loss showed nine rival strawberries. I
tested whether transplanting its complete saved first-144-turn opening into
every current route would improve the initial production portfolio.

`build_dsm_opening.py` took the first 144 public actions from DSM episode
113531265 (route file SHA-256 `e71754c3...`) and replaced the experimental
agent's chassis route prefixes, leaving the later policy source unchanged.
The source replay has no future-shop input in the candidate at runtime, but
its actions were chosen in a different match. The resulting separate
`exp_dsm_opening_20260926.py` hashes to `17da6a17...`.

## Pilot result and decision

On a new native engine seed 2610800 with both seats, the candidate and
current `main.py` reacted to one another. Both games ended `DONE`, but the
candidate earned 50,303 coins against 149,113 for current `main.py`, a
98,810-coin loss in each seat. Day-six candidate farm contained only two
strawberry tiles, ten melon tiles, two cows, one sheep, three empty pastures
and two weeds. It did **not** reproduce the DSM source farm, which had nine
strawberry tiles at day six in its original episode. The large failure
already invalidated the transplant hypothesis; the preselected route panel
and further native seed block were not run.

**Reject.** A saved action prefix is not a portable complete production
policy: funding, worker movement and farm state can diverge immediately when
the price path and reacting opponent change. Any opening replacement needs a
state-aware executor that funds purchases and repairs deviations. No
`main.py` change or Kaggle upload resulted. Raw pilot with both seat captures:
`dsm_opening_pilot.json`.

## 2026-09-26 correction and direct-action retest

Inspection after this report found a confound: the candidate patched
`_IMPL.chassis.routes` during import, but `_alt_install()` restores the
first 96 actions of route 0 from `_ALT_RAW` on step 0. The pilot therefore
did **not** directly execute DSM's full first-144 action prefix. Its bad
day-six farm is evidence about that partial route transplant, not proof
that DSM's original opening fails on a fresh game.

`build_dsm_direct_prefix.py` made a separate wrapper that calls the parent
each step for initialization and directly returns the saved DSM action on
steps 0–143. That corrected test reproduced the source's nine strawberries,
eight melons, five cows and three sheep on both the original seed and a
fresh seed, in both seats. Yet after handing control back to `main.py` at
step 144, it lost by 61,713 coins per seat on the original seed and 37,531
per seat on the fresh seed. The subsequent route requires its own farm state.

The **full** saved DSM action route won by 17,199 coins per seat against
current `main.py` on its original seed and `BRUNCH_SPOT,YARN_STORE` shops,
but lost by 18,802 per seat on fresh seed 2610930 with
`PET_CAFE,PET_CAFE`. All eight games across these two pilots ended `DONE`.
**Decision remains no promotion:** the opening is portable, while the tested
continuations do not provide an adaptive, broadly stronger policy. See
`dsm_direct_prefix_pilot.json` and `dsm_full_raw_pilot.json`.

An additional predeclared eight-seed native screen (2610940–2610947), both
seats, measured the complete raw DSM schedule against reacting `main.py`.
It won only **1/8 seed pairs and 2/16 seat games**, losing 160,296 coins
of total seat-game margin; every game ended `DONE`. It won the
`PET_CAFE,YARN_STORE` seed by 6,679 per seat and lost the other seven,
by 1,996–34,484 per seat. **Reject full raw DSM as a general replacement.**
Its strong original-route result was scenario-specific. See
`dsm_raw_native_screen.json`.
