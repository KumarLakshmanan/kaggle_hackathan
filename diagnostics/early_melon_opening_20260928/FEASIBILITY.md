# Early MELON opening feasibility — 2026-09-28

## Decision

**No-go; do not build a day 0–5 MELON branch from this evidence.** The exact 4ee policy has no day 0–5 MELON planting in its route library or in the saved loss/failure traces. Getting a first sale earlier requires a new opening schedule that reallocates land, seed funding, and crop-care work. The existing route library offers day-6 plantings, but the prior day-six route screens did not establish a margin-positive change and are already sparse on live losses. No policy outcomes were run for this feasibility check.

## Frozen evidence and method

- Current artifact: `main.py`, SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- Exact native loss traces: 30 files in `diagnostics/loss_class_20260927/traces/`; current top-20 failures: DECEM, Boey, and Vadim in `diagnostics/loss_class_20260927/top20_traces/`. The saved Majkel1337 episode is the top-20 winning control. No Kaggle access or data collection occurred.
- Decoded the existing `_DATA` schedules from `main.py` read-only: 72-step common opening and 145 full routes, each with 719 actions. Scanned farmer and hired-hand actions for `PLANT MELON`.
- `diagnostics/current_top20_20260927_172258/RESULTS.md` records the existing result: 17/20 top-20 both-seat sweeps. This check did not rerun or alter those controls.

## Findings

- Across the 30 loss traces, first successful MELON seed purchase and first planting occurred on the same day: day 6 in 4 episodes, day 7 in 6, day 8 in 1, day 9 in 14, day 13 in 2, and day 16 in 3. None planted during days 0–5.
- The three current top-20 failures first bought and planted MELON on day 9 (DECEM), day 10 (Boey), and day 10 (Vadim). The saved winning Majkel control also comes from the same route family.
- None of the 145 complete schedules plants MELON before step 144 (days 0–5). The earliest existing schedules plant at step 152 (day 6, hour 8); five routes support that timing, including viable `YARN_STORE|PIZZA_SHOP` shop prefixes. Thus there is no existing full route that supplies the requested day 0–5 opening.
- At the top-20 failures’ saved step-144 captures, all 25 NW tiles were occupied: DECEM had 10 strawberry, 8 pasture, 7 wheat; Boey 10 strawberry, 9 pasture, 6 wheat; Vadim 11 strawberry, 8 pasture, 6 wheat. Their cash was $860, $357, and $756 respectively, with zero MELON seed stock and zero hired hands at the capture. A new crop would displace an existing use of land or require buying land, while also funding a seed and fitting planting/watering/harvest into the scheduled work.
- The current step-0 market queue already uses all 10 request slots and contains no MELON seed purchase. An early seed purchase would need both available market-order capacity somewhere in days 0–5 and reserved cash; the day-0 queue itself is full. Planting and crop care also require scheduled work and occupied land to be reassigned, so this is not an additive one-action patch.

## Prior evidence and rejection

`diagnostics/portfolio_research_20260927/FEASIBILITY.md` found that its shop-pair trigger covered only 1/30 saved losses and also 3/54 wins; compatible day-six route alternatives added only 1–4 post-day-six MELON planting requests. `diagnostics/route_portfolio_20260927/RESULTS.md` found tested route swaps improved target fixed-tape margins by only 447–2,688 coins, below the frozen 5,000 gate. `diagnostics/commitment_controller_20260926/ROUTE_RESULTS.md` records a day-six switch where own cash rose 5,392 while rival cash rose 17,686, worsening paired margin by 12,294.

The route library’s earliest viable MELON schedule is day 6, not day 0–5, and existing early land and market commitments leave no funded, unoccupied slot for an earlier crop in the inspected failures. A new day 0–5 schedule would be a whole opening-portfolio change. An unconditional version would alter the schedule underlying the 17 current top-20 winning controls; a conditional version has no existing early-route branch and has not been validated. Its safety and market effect cannot be inferred from these fixed replays. **Reject at feasibility; preserve the incumbent and require a separately frozen whole-schedule plan plus both-seat reacting validation before reconsidering.**
