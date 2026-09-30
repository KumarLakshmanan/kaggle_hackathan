# Persistent mirror stock sale — rejected, 2026-09-26

The isolated `exp_mirror_stock_frontload_latched_20260927.py` (SHA-256
`73aa01509f6ab005e527d600b67bae108184302418b00463310d36931e3b28b2`)
was built from current `main.py` SHA-256 `489fe8e4...` under the frozen
`LATCHED_PLAN.md`. Its 24-turn observed physical-mirror latch permits a late
strawberry shed sale after the tiles diverge, while worker positions remain
equal. The first candidate without a persistent latch is rejected separately
in `MECHANISM_SMOKE.md`.

The two-seat native smoke on public episode 113642505 showed three trigger
turns, zero errors, and moved the fixed-rival margin from −900 to +85. That
checks activation in the documented missed-sale window; it is not a
generalization result.

The frozen development screen used 29 current live losses and ten closest
wins, original seeds in both seats and endogenous shops. The exact incumbent
baseline reproduced every original-seat Kaggle cash pair. All 78 candidate
games ended `DONE`/`DONE`, with zero reported errors and a 186 ms maximum
measured call. In the **39 original seats**, the candidate rescued **eight**
losses and reversed **one** control win. Own cash fell **845**, fixed-rival
cash fell **11,440**, so paired margin improved **10,595**. The aggregate
own-cash sign fails the predeclared promotion gate. Across both seats, the
candidate won 35/78 games and 18/39 route pairs. The original incumbent
won 22/78 and 12/39 on this selected near-mirror screen.

**Decision: reject before fresh reactive and top-100 promotion testing.**
The fixed action tapes do not adapt to the policy and cannot establish
leaderboard strength. The gate's own-cash failure matters even though the
shared market reduced rival cash more. `main.py` and Kaggle remain unchanged.

Reproduce: `python -B -X utf8 diagnostics/mirror_stock_frontload_20260927/build_latched_candidate.py`,
then `python -B -X utf8 route_panel_benchmark.py --candidate
exp_mirror_stock_frontload_latched_20260927.py --summary
diagnostics/live_submission_56572390_20260926/mirror_dev_routes/summary.json
--workers 4 --json-out
diagnostics/mirror_stock_frontload_20260927/latched_dev_candidate39.json`,
then `python -B -X utf8
diagnostics/mirror_stock_frontload_20260927/compare_latched.py`. Raw results:
`smoke_latched.json`, `latched_dev_candidate39.json`,
`latched_dev_comparison.json`.
