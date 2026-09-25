# Kaggriculture agent research memory

Rating snapshot checked: 2026-09-25 06:19 UTC. This is a living research log,
not a claim that the agent beats every opponent. Update the dated findings below after each
completed experiment, with the artifact and a clear promotion/rejection decision.
`AGENTS.md` points future workspace work to this file.

## Mission and operating constraints

- Optimize `main.py` for the live Kaggriculture 30-day / 720-turn competition.
  Winning means more final bank coins than the opponent, not merely higher
  production. All possible opponent policies cannot be exhaustively proven.
- **Do not submit again without the user's fresh explicit request.** The
  user authorized submissions 56529771 and 56530281 separately; no other
  upload is authorized by this file or by the continuing optimization goal.
- Preserve the dirty worktree and user-owned files. Make candidate changes in
  separate experimental files first. Do not replace `main.py` based only on a
  hand-picked replay or one-seat improvement.
- The user prefers `gpt-6-luna` subagents with `max` effort. When seeking
  ChatGPT.com GPT-6 Pro strategy advice, share only aggregate results unless
  the user explicitly authorizes more; never share credentials or account data.
- Read `README.md` and `INSTRUCTIONS.md` as game context, but verify disputed
  mechanics against the installed `kaggle-environments` engine. Their town
  center consumption descriptions differ; `INSTRUCTIONS.md` documents the
  1.32.7 behavior used in local parity checks.

## Current authoritative state

- `main.py` SHA-256:
  `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
  It was unchanged between the two latest uploads.
- Kaggle submissions: 56529771 and 56530281, both `COMPLETE` at last check.
  At 2026-09-25 06:19 UTC the displayed public ratings were 2387.7 and
  2393.8 respectively. Ratings move as matches complete; these are not final
  leaderboard rank predictions. The competition README says only the latest
  two submissions remain tracked, so do not make redundant uploads.
- The frozen refreshed top-50 public **fixed-action** panel contains 100
  captured opponent routes, each tested with both seats: `main.py` won
  **67/100 route pairs, 133/200 seat-games**, all `DONE`. This panel does not
  model how opponents respond to changed actions and is now development data,
  not an untouched holdout. Evidence and commands:
  `diagnostics/top50_current_2026-09-24/RESULTS.md` and
  `diagnostics/top50_current_2026-09-24/main_100routes.json`.
- Five early live episodes from 56529771 were wins with both players `DONE`;
  local fixed-tape reruns reproduced both final cash values and statuses
  exactly. See `diagnostics/live_submission_56529771_20260925/RESULTS.md`.
  This validates those engine/harness cases, not universal opponent coverage.
- The latest 24 completed public episodes of 56530281, sampled at 2026-09-25
  06:19 UTC, were **13 wins / 11 losses**. Both agents were `DONE` in every
  match; eight losses were under 1,100 coins and the largest was 4,003.
  In 21/24 episodes the opponent's farmer action matched ours on at least
  718/720 turns. This shows many near-mirror policies, **not** that their
  complete decisions or economic effects are identical. The downloaded
  replays, generated summary, and exact local reruns are under
  `diagnostics/live_submission_56530281_20260925/`.
- For those 24 actual seed/seat combinations, local `main.py` versus the
  extracted opponent tape reproduced both final cash totals and both `DONE`
  statuses **24/24 exactly**. The two-seat panel was 13/24 route wins and
  26/48 seat wins, all `DONE`. This is simulator parity and fixed-action
  development evidence, not proof against adaptive versions of those rivals.

## Findings and rejected approaches

| Date | Finding | Decision / evidence |
| --- | --- | --- |
| 2026-09-24 | Four-tile crop-cycle pilot certified only one rotating lane and reduced the top-20 panel from 37/40 to 36/40 route wins. | Reject; `diagnostics/block_planner_findings_20260924.md`. |
| 2026-09-24 | Day-6 route, early tomato, day-11 carrot/strawberry swaps, and late-tomato Full/Half/Omit screens either failed to rescue losses or reversed controls. | Reject; `diagnostics/top50_current_2026-09-24/RESULTS.md` and linked reports. |
| 2026-09-25 | Unconditional sheep-heavy route 9 won 58/100 routes and 113/200 seats versus baseline 67/100 and 133/200; it rescued four losses but reversed 13 wins. | Reject; `diagnostics/top50_current_2026-09-24/route_force_9_100routes_20260925.json`. |
| 2026-09-25 | A day-6 public-state one-feature selector for route 9 had no safe full-panel switch; whole-team leave-one-out fell to 64/100 routes and 127/200 seats. | Reject; `diagnostics/top50_current_2026-09-24/ROUTE9_PUBLIC_SELECTOR_20260925.md`. |
| 2026-09-25 | Avoiding one final hire every day has an optimistic wage bound greater than deficits on four near-tie losses; feasibility is not proven. Blunt hire caps had regressed earlier. | Investigate task-preserving worker consolidation; `diagnostics/top50_current_2026-09-24/WORKER_CONSOLIDATION_BOUND_20260925.md`. |
| 2026-09-25 | Boey empty-shed SELL attempts were zero-stock no-ops, not lost quoted revenue. The immediate on-access delivery ceiling was only 101 or 129 gross coins per seat versus five-figure deficits. | No policy candidate; `diagnostics/boey_sell_20260925/REPORT.md` and `exp_boey_sell_20260925.py`. |
| 2026-09-25 | Replacing the opening wheat buy/sell roundtrip with a direct five-wheat buy left the 24 live routes at 13/24 wins and 26/48 seats; mean own cash −2.67 coins per game, no loss rescued. | Reject; `diagnostics/live_submission_56530281_20260925/OPENING_NET5_SCREEN.md`. |
| 2026-09-25 | Extending own-plan sale advance from four to eight turns gained two fixed-tape route wins (15/24, 30/48 seats) without outcome reversals, but one rescue lowered own cash 214 across seats and the mean margin gain was mostly rival-cash suppression. | Fails predeclared causal gate; do not promote. `diagnostics/live_submission_56530281_20260925/SALE_ADVANCE_LOOK8_SCREEN.md`. |
| 2026-09-25 | GPT-6 Pro proposed a strictly independent adjacent SELL swap. A corrected 24-game scan had 209 premium SELL-after-SELL pairs in all 24 episodes, but zero after BUY_SEED/HIRE and zero with a provably inert preceding sale. The first scan had accidentally excluded seat 1 because the downloaded replay omits its `step` field. | No eligible strict intervention; do not implement or broaden post hoc. `diagnostics/live_submission_56530281_20260925/PRO_MARKET_SWAP_PLAN.md`. |
| 2026-09-25 | A replay-validated immediate-receipt model found 184 trusted adjacent active premium-sale comparisons. Even a hindsight oracle gained only 337 total own-receipt coins across 24 games (108 across 11 losses) by taking all isolated positive swaps; no individual lost game gained more than 49. | Low-leverage; not a promoted candidate. `diagnostics/live_submission_56530281_20260925/active_sell_swap_bound.py` and the swap plan. |
| 2026-09-25 | A bounded final-day worker-consolidation search found zero eligible insertion windows for the donor's two economic bundles on one near-tie loss and one winning control. Removing the hire alone changed production and cash and is not a valid treatment. | No task-preserving rule supported in this search scope; `diagnostics/worker_consolidation_20260925/REPORT.md`. |
| 2026-09-25 | A premium-inventory hold test sold the same 247 strawberry units on its low-demand target but reduced strawberry receipts by 20 and own terminal cash by 889. Four routes in both seats completed baseline, fixed-shop and native trials. | Reject target strawberry-hold hypothesis; broader milk/wool hold effects on controls are mixed and inconclusive. `diagnostics/premium_sale_hold_20260925/RESULTS_20260925.md`. |
| 2026-09-25 | A saved live-replay market model matched 4,627/4,627 eligible cash receipts. Seven of 11 losses sold fewer CARROT units than the opponent; one 351-coin loss involved enormous purchased-wheat roundtrips, so gross SELL revenue is misleading. | Prioritize net cash and production diagnostics, not blind sale-order tuning. `diagnostics/live_clone_margin_20260925/REPORT.md`. |
| 2026-09-25 | Ranking existing H6 sale slots by executable post-unit stock rather than requested quantity changed 25 recorded turns. A 48-game frozen panel stayed 13/24 route wins and 26/48 seat wins, with no rescue and small mixed cash effects. | Reject; `diagnostics/live_submission_56530281_20260925/H6_EXECUTABLE_RANK_SCREEN.md`. |
| 2026-09-25 | A corrected late five-plant WHEAT→CARROT swap activated on the standard skeleton and finished 48 frozen games but stayed 13/24 route and 26/48 seat wins. One target's +251 carrot receipts were offset by −210 wheat receipts and −40 extra seed cost: +1 own terminal coin. | Reject; no loss flipped and a +140 win narrowed to +6. `diagnostics/live_submission_56530281_20260925/LATE_CARROT_SWAP_SCREEN.md`. |
| 2026-09-25 | A separate opponent-aware investment planner estimated own cash minus rival market-price externality; a 12-day crop-cycle variant tested faster liquidity. Both lost 0/4 reactive games to `main.py`. Across eight matched-shop A/B seats versus frozen v1, terminal margin improved 6/8 margins by mean +1,593 but lowered mean own cash 2,180 and flipped no losses. | Reject both for promotion; preserve the research model, not a stronger agent. `research_margin_planner_20260925/RESULTS.md`. |

The loss clusters include severe price/production deficits and near ties; no
single adjustment has passed broad promotion gates. Route-specific rescue on a
fixed tape may simply be opponent non-adaptation or a future-shop difference.

## Verification protocol for any new candidate

1. State a falsifiable hypothesis and predeclare target losses plus winning
   controls. Only use information visible in the agent observation at action
   time; never route on replay ID, seed, future shops, or opponent private
   inventory.
2. Compare candidate and frozen `main.py` on identical seeds, both seats,
   against fixed-shop/fixed-action cases; report final cash, margin, status,
   flips and per-action runtime. Where accessible, also run reactive agents.
3. Run the full 100-route panel before promotion. Seek fresh routes or
   independent reactive/live checks because the existing panel has been used
   repeatedly for development. Inspect negative controls and worst regressions.
4. Promote to `main.py` only when the evidence supports a genuine win-rate
   improvement without invalid actions or timeouts. Recompute SHA-256 and
   record the code change and verification in this file. A Kaggle submission
   still needs a separate explicit user request.

Useful commands from the workspace root:

```powershell
python route_panel_benchmark.py --candidate main.py --summary diagnostics\top50_current_2026-09-24\routes\summary.json --workers 8 --json-out diagnostics\top50_current_2026-09-24\main_100routes.json
python -X utf8 -m diagnostics.live_submission_56529771_20260925.replay_parity
Get-FileHash -Algorithm SHA256 -LiteralPath .\main.py
& 'C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe' competitions submissions kaggriculture
```

## Active next work

- Diagnose item/day cash divergence and actionable observations in the 11
  recent live losses; near-mirror farm actions make sale ordering, market
  fills, and small labor differences especially important. Keep the 24-route
  panel as development evidence and use independent reactive checks before
  promotion.
- The separate active-sale subagent stopped on a usage limit before it could
  complete its full-game treatment. A local, replay-validated immediate
  receipt screen now indicates little available headroom; do not mistake the
  absent full-game report for a successful candidate.
- The independent live near-mirror worker stopped at a usage limit, but its
  saved evidence has been summarized in `diagnostics/live_clone_margin_20260925/REPORT.md`.
  Seven carrot shortfalls matched fewer planting requests; in each, the
  first divergent rival CARROT planting replaced our WHEAT planting. A
  standalone late five-plant swap failed its 24-route screen. A genuinely
  dynamic crop portfolio would need to predict **net** crop value, preserve
  feed/sale schedules and pass independent reactive games. Investigate full net cash ledgers;
  gross SELL receipts alone can be dominated by purchased-product roundtrips.
  The Boey failed-SELL, premium inventory-hold, and bounded
  worker-consolidation experiments have finished with negative conclusions;
  do not infer stronger impossibility claims from their limited searches.
- Ask GPT-6 Pro for a new observation-legal approach if the live-loss audit or
  those experiments demonstrate unresolved losses. The previous consultation
  suggested **task-preserving** worker consolidation: remove a trailing HIRE
  only when all work can be rescheduled with identical physical output, not a
  blanket hire cap. See the bound report above.

## Append-only findings log

- **2026-09-25 06:19 UTC — memory created.** No change to `main.py` and no
  Kaggle upload in this step. Current ratings and frozen-panel evidence are
  snapshots, not guarantees. Future experiments should add dated entries here
  and update the authoritative-state bullets when the file or evidence changes.
- **2026-09-25 06:35 UTC — first live audit.** Downloaded the newest 24 public
  episodes for submission 56530281, classified 13 wins / 11 losses, and
  verified 24/24 exact final-cash/status local parity. Extracted 24 fixed
  opponent routes and reran both seats (26 wins / 22 losses). Boey failed-SELL
  diagnosis was rejected as too small to matter. `main.py` remains unchanged;
  no Kaggle upload occurred.
- **2026-09-25 06:39 UTC — opening roundtrip rejected.** A uniform direct-buy
  replacement changed small cash amounts but rescued no live loss or seat;
  13/24 route and 26/48 seat wins were unchanged. No `main.py` edit or upload.
- **2026-09-25 — eight-turn sale advance screened.** It improved the
  fixed-action score to 15/24 routes and 30/48 seats but failed the frozen
  own-cash rescue criterion. It is not in `main.py` and was not submitted.
- **2026-09-25 — GPT-6 Pro consultation and exposure scan.** With the user's
  approval, sent only aggregate live-match and prior-experiment findings;
  no code, names, credentials, or personal data. Its independent same-turn
  sale-swap proposal had zero strictly eligible events across 24 actual public
  matches after validating unit-action stock. Stopped without modifying
  `main.py` or uploading.
- **2026-09-25 — seat-1 replay-scan correction.** The first exposure report
  accidentally filtered seat-1 observations, which omit `step` in the public
  replay. Recomputed from the row index: 209 active adjacent sale pairs in
  all 24 games, but still zero independent/inert earlier orders. A validated
  active-sale oracle screen found only 108 own-receipt coins of positive
  isolated swap potential across all 11 losses. No main-file edit or upload.
- **2026-09-25 — independent negative screens finished.** The bounded
  worker-rescheduling search found zero feasible insertions on two traces;
  removing a hire without preserving tasks did not solve the near tie. A
  four-route premium hold screen made the targeted low-demand strawberry
  loss worse despite withholding orders. Neither candidate was promoted or
  submitted.
- **2026-09-25 — live cash model summarized.** The worker stopped at a
  usage limit after saving a validated market attribution artifact. A local
  summary found a seven-of-11 carrot quantity shortfall pattern and a
  wheat buy/sell gross-revenue trap. No main-file edit or upload.
- **2026-09-25 — stock-clipped H6 ranking rejected.** The standalone
  candidate completed 48 frozen games, but won the same 13/24 routes and
  26/48 seats. Fourteen margins shifted only slightly and no loss flipped.
  The predeclared screen gate failed; `main.py` remains unchanged.
- **2026-09-25 — late crop swap rejected.** Corrected a replay-row/policy-step
  offset after the first no-treatment harness run, then verified activation
  and completed 48 actual treatment games. No outcome flipped. Exact trace
  on a targeted loss showed only +1 own coin after selling ten extra carrot
  but ten fewer wheat and paying more for seed. `main.py` remains unchanged;
  no submission occurred.

- **2026-09-25 — independent planner research started.** A separate task is
  developing `research_dynamic_planner_20260925/`: an observation-driven
  portfolio and worker-job planner from scratch, with no incumbent import or
  recorded routes. Its source, tests and reports stay in that directory so
  the concurrent incumbent experiments can continue independently. It is
  experimental; no strength claim, main-file replacement or upload yet.
- **2026-09-25 — independent planner v1 rejected.** Engine-backed economics
  and scheduling tests passed (10/10), and a full seed-0 smoke game completed
  with 131,774 coins and zero unit no-ops/deaths. But v1 lost all eight
  reactive seat/seed games versus `main.py` (mean own 62,037; mean margin
  −61,743), and won only 1/12 paired saved-action top-50 routes versus
  `main.py`'s 9/12 on those same routes. Day-12 cash was 2,581 versus 19,740
  after an animal-heavy opening. **Reject for promotion**; see
  `research_dynamic_planner_20260925/RESULTS.md` and linked JSON.
- **2026-09-25 — independent planner v2–v4 ablations rejected.** Opening
  animal/slow-crop quotas, a later slow-crop cap, and a late staple bonus
  each lost 0/4 reactive games in two seeds/both seats. Under the observed
  v1 seed-0 shop schedule, v2 and v3 worsened both seat margins; v4 changed
  seat-0 margin only +300 while worsening seat 1 by 5,434, with no win.
  These are fixed-shop diagnostics, not independent validation. **Reject all
  three variants; no `main.py` edit or Kaggle submission.**
- **2026-09-25 — independent planner v5 throughput objective rejected.** A
  cash-plus-worker-commitment score improved seed-0 day-12 cash to 12,741,
  but grew to 41 strawberries by day 15 and lost all four reactive games;
  mean own final cash 44,311 and mean margin −79,501. Its matched-shop
  seed-0 margin was −107,073 in both seats, worse than v1's roughly −64k.
  Ten mechanical unit checks remained green. **Reject for promotion.**
  `research_dynamic_planner_20260925/RESULTS.md` contains the full controls.
- **2026-09-25 — GPT-6 Pro complete-bundle strategy proposed, untested.**
  An aggregate-only consultation recommended reactive terminal-rollout
  comparisons of complete funded work/harvest/sale commitments, distilled
  into a small observation-only selector while keeping the tested executor.
  First screen: one genuinely contested investment decision, exact control
  wrapper, matched-shop and native held-outs, and separate own/rival cash
  attribution. The animal fertilizer by-product may defeat a naive
  earliest-sale trigger; verify activation before allocating a large run.
  **Research direction only, not promoted or submitted.** See
  `research_dynamic_planner_20260925/PRO_STRATEGY.md`.
- **2026-09-25 — terminal-rollout research harness validated.** Added
  `research_dynamic_planner_20260925/terminal_rollout.py` to compare reactive
  A/B policies in both seats, optionally pinning only exogenous shops and
  decomposing terminal margin into own and rival cash. Four new accounting
  unit tests passed (14/14 total). The same-agent matched-shop control was
  bit-for-bit identical in both seats. Replaying the already rejected v5
  against v1 under the same shops lost 20,651/21,289 own coins while giving
  the rival 22,007/20,890 more, a 42,658/42,179 margin regression. **This is
  a measurement tool, not a promoted agent; `main.py` stays unchanged and
  no Kaggle submission occurred.** See `PRO_STRATEGY.md` and
  `rollout_identity_seed0.json` / `rollout_v1_v5_matched_seed0.json`.
- **2026-09-25 — rival-aware investment planner and short-cycle alternative rejected.**
  New `research_margin_planner_20260925/agent.py` reuses the independently
  tested v1 executor while two different observation-only investment scorers
  test paired terminal margin and short-cycle liquidity. Four mechanism tests
  passed. The control wrapper reproduced v1 in both seed-0 seats. Each new
  policy lost all four reactive games against `main.py` on seeds 0 and 42.
  Terminal-margin A/B versus v1 with exogenous shops matched on four seeds,
  both seats, improved six of eight margins by a mean 1,593 but decreased mean
  own cash 2,180, and rescued zero losses. A native seed-17 audit found zero
  unit no-ops but four plant deaths. **Neither policy was promoted or
  submitted; `main.py` hash remains
  `04B0BDC3BBE319D969170DDC8007BD6300AF254A98151D6EF990C9ED2EBBABC1`.**
  Details and raw evidence: `research_margin_planner_20260925/RESULTS.md`.
- **2026-09-25 — capped-animal-feed rescue screened; no credible candidate.**
  Read the installed Kaggriculture 1.32.7 engine and `diagnostics/live_clone_margin_20260925/REPORT.md`.
  A plausible refinement to `_r85_feed` would skip a feed only when tomorrow's
  scheduled animal production is due, the fed and unfed outcomes both clip to
  the same held-yield cap, the animal is not already unfed, wheat is actually
  carried, no second same-day feed/care invalidates the saving, and the current
  policy schedules a safe feed tomorrow. A scan of all 24 actual live episodes
  (including 11 losses) found **zero** such opportunities. The engine says
  feeding preserves the animal and unlocks care bonus, while its hard yield cap
  clips production; preserving one WHEAT is worth cash only if it later avoids
  a purchase or is sold. Because the trigger never occurred, no A/B was run and
  no intervention is recommended. See
  `diagnostics/novel_strategy_review_20260925.md`. `main.py` was not edited and
  nothing was submitted.
