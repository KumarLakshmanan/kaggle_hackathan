# Mirror pure-sale protection pilot — rejected, 2026-09-26

The isolated candidate `exp_mirror_pure_sale_20260926.py` has SHA-256
`d8ef9af55b6e39f716fdd5b5b1ce4e88fbab90df30304d0b01b6d6b8cd8e97d7`.
It was built from current submitted `main.py` SHA-256 `489fe8e4...` under the
frozen `PURE_SALE_MIRROR_PLAN.md`. On a visible physical mirror, it relaxes
the first-future-sale protection only when the future market turn contains
exclusively `SELL` orders. Non-mirror policy, production, shops, and the
strawberry 24-turn window are unchanged.

The development panel comprises all 29 losses and the ten closest wins from
the latest 100 public games of submission 56572390. It contains 39 distinct
public rival action histories. The baseline reproduced **all 39 live terminal
cash pairs exactly in their original seats**. Baseline and candidate each
completed 78 original-seed, both-seat games, all `DONE`.

The candidate rescued **2 of 29 original-seat losses**, versus a predeclared
minimum of five: 𝕯𝖊𝖔𝖉𝖎𝖒𝖘 & 𝕮𝖔 changed from −374 to +64, and JinchengZhang1 from
−208 to +426. It reversed none of the ten close control wins. Across the 39
original seats, our terminal cash rose 2,163, fixed rivals' cash rose 518,
and margin rose 1,645. Twenty-six original-seat games changed. The candidate
reported no errors; maximum candidate call was 269 ms in this run. See
`pure_sale_dev_baseline39.json`, `pure_sale_dev_candidate39.json`, and
`pure_sale_dev_comparison.json`.

**Decision: reject at the predeclared development gate.** The own-cash gain
is real within these fixed-route simulations but the two rescues do not meet
the five-rescue threshold, and the 29 public routes are development data rather
than independent reactive validation. Do not broaden this pilot to the saved
top-100 panels or fresh reactive seeds, promote it to `main.py`, or upload it.
The current local/uploaded `main.py` remains SHA-256 `489fe8e4...`.
