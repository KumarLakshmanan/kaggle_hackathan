# Complete schedule selector: development and replay regression

Frozen candidate: `exp_shunki_shop_optimized_20260927.py`, SHA-256
`94f0602f0a6a2d4c1af84f8caf93ee802335582485dd2f796a8c7e5a09846604`.
Parent: submitted `3cc0f69f...`.

220 one-seat development games tested every eligible full schedule in six
first-two-shop histories. Four shop-only replacements strictly increased
within-group wins and were frozen before full-panel testing. No opponent
identity, seed or future shop is a policy input. Opening actions through
turn 143 are unchanged. Source filtering permits only adjacent balanced
product buy/sell quantity differences, so independent cash validation is
still necessary.

## Full saved top-50 panel

- Parent: 42/50 matchups won in both seats, 84/100 seat wins.
- Candidate: **45/50 both-seat wins, 91/100 seat wins**, all DONE/DONE.
- Added both-seat wins: DECEM, Snorlax, marwar22.
- Previous both-seat wins lost: zero.
- ymg_aq is split: +1,190 in seat 0, -1,167 in seat 1; it is not a sweep.
- Remaining losses: Majkel1337, seek inspiration, We wanna be tomatos,
  Breaking1800, plus the split ymg_aq matchup.

These saved opponents were used for development and regression; this is
not independent policy validation or a forecast of a live rank.

## Decision

Pass the predeclared replay gate and advance the exact frozen candidate to
independent native confirmation. Separate outcome-blind panels select the
first eight seeds per changed branch for each of four reacting opponents.
448 games follow selection; see PLAN.md and native/manifest.json. Native
results conclusively failed. **Reject for promotion; no new upload.**

## Independent native rejection — 01:09 UTC

Outcome-blind selection completed on all four panels. The run stopped after
352 completed games, all DONE/DONE, because the predeclared pooled external
win gate had become mathematically impossible. The current main won
182/192 external seat games. The candidate had 144 points from 160 games;
even 32 wins in all its remaining external games would produce only
176/192. The unplayed head-to-head stage cannot rescue that joint gate.

Against frozen 489, candidate won 60/64 versus main at 64/64. Against 08aa,
candidate won 52/64 versus main at 54/64. The remaining C95/new and
head-to-head games were cancelled to avoid testing after a decisive failure.
The frozen candidate is **rejected**, despite 45/50 replay sweeps. Main
remains the uploaded 3cc artifact. Exact checkpoint and proof are in
`native/early_rejection.json`; do not resume this rejected experiment or
mistake an absent 448-game completion file for a still-running process.
