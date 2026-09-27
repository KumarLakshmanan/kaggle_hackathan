# Full saved top-100 diagnostic — 2026-09-26 22:26 UTC

The unchanged later-shop candidate SHA-256 `68aad090...` played all
100 routes from the frozen 2026-09-26 07:08 UTC panel, both seats,
original seeds and shops, engine 1.32.7. The candidate and incumbent
results use the **same exact panel summary SHA-256**. All 200 candidate
and 200 incumbent games finished DONE/DONE. The candidate won **80/100
paired routes and 160/200 seat-games**, versus the incumbent's **66/100
paired routes and 132/200 seats**. Its total paired margin across the
100 routes was 1,843,902 coins higher. It flipped 27 incumbent losses
to wins but also flipped 13 incumbent wins to losses. It beat all ten
saved rank-1–10 routes, versus the incumbent's nine, but the full
100-route objective remains **20 routes short**.

The first-two shops matched between incumbent and candidate in only
**134/200 seat comparisons**. This is the game's native action-dependent
RNG, not a test error; changes in weeds/actions can change later shop
draws. Thus the panel comparison measures each agent in its original
native game, not a fixed-shop paired causal effect.

The largest candidate losses were Dipam Chakraborty (paired −143,330),
mtmr_s1 (−137,422), Victor @ Tufa Labs (−100,060), Christoffer Thimsen
(−97,660), and Arda Ceylan (−70,790). Four of these five opened with
ICE_CREAM_SHOP/BRUNCH_SPOT. Those four are especially concerning:
the incumbent had **positive** paired margins on all four, while the
candidate lost them. The fifth opened BRUNCH_SPOT/BRUNCH_SPOT.
Exact day-nine native captures of the four ICE/BRUNCH losses found third
shops FARMERS_MARKET, BRUNCH_SPOT, PET_CAFE, and SMOOTHIE_SHOP; all
still used source episode 113445495 at that point. Three lacked an
exact-compatible matching third-shop source route. The candidate's
day-nine farm money was 84–186 coins in these cases, but the loss cause
requires a full cash/production ledger, not that checkpoint alone.

**Decision: retain rejection of this exact candidate as a replacement;
no `main.py` edit or Kaggle upload.** The fixed rival action tapes satisfy
the user's saved-route measurement target, but cannot establish
independent strength against reacting rivals or predict a Kaggle rating.
The 20 remaining losses and 13 incumbent-win regressions make a
strategy improvement necessary before promotion. Focus first on the
ICE_CREAM_SHOP/BRUNCH_SPOT failure cluster, then verify any change on
fresh native reacting opponents in both seats.

Evidence: `TOP100_DIAGNOSTIC_PLAN.md`, `top100_diagnostic.json`,
`top100_analysis.json`, `ice_brunch_loss_captures.json`, and the frozen
incumbent `../top100_refresh_2026-09-26_0708/main_100routes.json`.

## Cash and source-state follow-up — 2026-09-26 22:31 UTC

Exact native event ledgers for Dipam and mtmr_s1 reproduced both
candidate and incumbent cash totals. Against Dipam, candidate own cash
was **62,963** versus incumbent own cash **134,683** on the same saved
opponent route; late-period own MILK and STRAWBERRY net cash fell
24,527 and 24,157 relative to the incumbent. Against mtmr_s1, the
candidate's WOOL net cash fell 22,635 in days 10–19 and 30,191 in
days 20–29 relative to incumbent, while the reacting rival cash in the
fixed-route game increased. These are route-specific diagnostics.

For the Dipam game, the candidate emitted **all 719 actions exactly**
from its selected Shunki source episode 113445495. At sampled turns
72, 144, 216, 240, 288, 360, 480, 600, and 718, the farm's crop and
animal tile counts matched the source replay exactly despite different
later shop sequences. The candidate's own cash remained around the
source route's modest level; the incumbent's different production
schedule earned over twice as much on that case. This rules out a
misrouted or invalid action as the main explanation of this loss. The
fixed public route itself is too weak for this opponent/shop case.

**Research decision: stop using exact Shunki route imitation as the
primary route to top ten or all 100 wins.** Retain artifacts as evidence,
but focus new work on the stronger incumbent's adaptive production and
market schedule. No main edit or Kaggle upload. Evidence:
`ice_brunch_cash_ledgers.json`, `ice_brunch_source_state_comparison.json`,
`trace_ice_brunch_ledgers.py`, and `compare_ice_brunch_source_state.py`.
