# Mechanism smoke — 2026-09-26 18:45 UTC

The first candidate `exp_mirror_stock_frontload_20260927.py` was run in both
seats on the frozen episode 113642505, which contains the documented
20-strawberry missed sale. Both native games ended `DONE` without wrapper
errors, but candidate and incumbent cash were identical and
`stock_trigger_turns=0`. The candidate's exact current physical-mirror gate
is false at the missed-sale steps because late farm tiles differ (including
weeds and a crop/animal), although worker positions and hand counts match.
The saved public replay shows 283 earlier exact-mirror turns.

**Reject this first gate as a mechanism failure; do not run the full 39-route
screen or promote it.** The trace is a fixed-rival diagnostic only. Measure
the earlier match streak and inventory opportunities before freezing a
revised observation-only rule. `main.py` and Kaggle remain unchanged.

Reproduce: `python -B -X utf8 diagnostics/mirror_stock_frontload_20260927/smoke_case.py`.
Raw output: `smoke_case.json`.
