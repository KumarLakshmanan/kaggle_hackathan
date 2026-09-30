# Kaggriculture workspace notes

Read [agent.md](agent.md) before changing the competition agent. It is the
living research memory: current submitted hash, simulator parity, benchmark
panels, failed and promising experiments, and reproduction commands. Add a
dated finding with evidence and a clear promotion/rejection decision after
each completed experiment; update the current-state section if `main.py` or
the Kaggle status changes. Do not treat fixed replay tapes as independent
validation of a policy change.

`main.py` is the Kaggle submission artifact. Prefer testing changes in a
separate experimental candidate first, then verify both seats, original-shop
and reactive behavior before promotion. Preserve existing worktree edits.
Never submit to Kaggle without a fresh explicit user request for that upload.
No strategy can be guaranteed to beat every possible opponent.

## Decision research lessons (2026-09-26)

- Match the promotion objective to the competition rating: wins, draws and
  losses are primary. Report cash margins to diagnose mechanisms, but do
  not reject an otherwise independently validated win-rate improvement
  solely because a rare loss is large. Freeze criteria before new results,
  keep both seats together when estimating uncertainty, and compare more
  than one reacting policy. The prospective reassessment is documented in
  `diagnostics/winrate_review_20260927/PLAN.md`.
- Judge changes by paired head-to-head wins and `delta_own - delta_rival`.
  The tested day-six route switch raised our cash by 5,392 coins but raised
  the rival's by 17,686, reducing paired margin by 12,294. Own cash alone
  can reward a competitively harmful shared-market change.
- Compare a proposed investment with the incumbent's *whole existing
  commitment*. A day-11 sheep expansion duplicated sheep, land, feed and
  worker obligations already scheduled by route 9; its forecast selected
  three losing native seed pairs. A complete route switch avoided that
  overlap but did not improve wins in the tested block.
- Account for worker execution and timing. Forced route 0 increased our
  non-PASS actions with no state change from 20 to 59 and from 24 to 66 in
  two activated traces. An attractive portfolio is insufficient if its
  task schedule fails to turn work into saleable output.
- Treat future shops and rival market response as uncertainties. Holding
  shops fixed reversed one sheep intervention's measured effect, while a
  reacting rival gained wool receipts under both complete-route switches.
  Use native reactive games for promotion; matched shops and saved action
  tapes are causal diagnostics and regression controls.
- The two distinct commitment-controller experiments were rejected. Keep
  the incumbent until a new candidate earns promotion under the original
  gates. See `diagnostics/commitment_controller_20260926/ARCHITECTURE_REASSESSMENT.md`
  and its linked ledgers and predeclared plans.
- An independent Stockfish-inspired beam search was built as a separate
  agent on 2026-09-26, but the former bundle-search v2 lost all four
  fresh paired seeds (eight seats) to reacting `main.py` with mean seat
  margin -88,281. The deeper search and strawberry-fertilizer versions also
  lost their tested games. The gap was physical execution: investment pace,
  funding order, worker travel, feed and fertilizer collection. Search
  forecasts must model an executable schedule and shared-market response;
  search depth alone did not earn promotion. See
  `diagnostics/search_agent_20260926/RESULTS.md`.
- Published-code ideas must be checked against the current file before
  adding them: `main.py` already included public V43 overflow and atomic
  planting guards. A coherent wheat-reserve transplant failed its frozen
  margin gate. Physical FEED ownership from a published scheduler improved
  the separate search agent on a four-seed development panel, but gained only
  449 paired-margin coins on four untouched confirmation seeds and still lost
  every seat to `main.py`. Preserve the prior research version; do not infer a
  leaderboard gain from fewer missing-supply events. See
  `diagnostics/public_supply_inspiration_20260926/FEED_RESULTS.md`.
- A 2026-09-26 physical-gap audit found only two terminal milk units across
  29 live losses, seven clipped animal-production units across three native
  diagnostic games, and no fully idle last hired hand on 90 analyzed days.
  Complete public V43 and v48 policies also lost their two-seat native pilot
  to current `main.py`. Do not infer a broad win opportunity from terminal
  stock, generic no-op cleanup, trailing-hire trimming or a public score;
  target a funded production bundle and verify its market effects. See
  `diagnostics/physical_gap_20260927/RESULTS.md`.
- A one-day earlier switch to the complete common route-2 schedule changed
  day-26 production and passed all native execution checks, but improved
  only two of four fresh paired seeds. A coherent route is a valid unit of
  experimentation, not evidence of a reliable gain. See
  `diagnostics/late_route_transition_20260927/RESULTS.md`.
- Check both state compatibility and trigger frequency for later route
  switches. Seven route tapes were identical through day 17, yet a rule
  using the two newest shops switched only one of 16 fresh paired seeds and
  lost cash on that seed. Freeze an activation threshold before testing;
  sparse activation cannot support promotion. See
  `diagnostics/day18_shop_retarget_20260927/RESULTS.md`.
