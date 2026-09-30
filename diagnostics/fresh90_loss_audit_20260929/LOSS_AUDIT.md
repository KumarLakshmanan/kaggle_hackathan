# Fresh90 candidate loss audit — 2026-09-29

## Scope

Read-only audit of candidate `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74` using the saved top100 V3 ledger, the 32-seed native confirmation, older archive V3 ledger, and existing policy reports. No games were run and no policy files were changed.

The saved top100 snapshot is the 100-team panel frozen at 2026-09-29 11:03:38 UTC, not the refreshed latest-episode panel now being collected under `diagnostics/fresh90_improvement_20260929/PLAN.md`. Treat the top100 counts below as a source for hypotheses only. The native confirmation is 32 hidden configuration seeds, four opponents, both seats, candidate and 4ee.

## Fresh native losses

The candidate lost 17 of 256 games, versus 19 losses for 4ee. Fifteen candidate loss rows match a 4ee loss at the same seed, opponent, and seat, with exactly the same margin. They fall into these unchanged blocks:

| Seed / opponent | Candidate losing seats | Margin each | Candidate shop pair | Change vs 4ee |
|---|---:|---:|---|---|
| 12929307 / V35 | 0, 1 | -6,231 | ICE_CREAM_SHOP / YARN_STORE | Same losses |
| 12929309 / 4ee and ae349 | 0 | -3,839 | ICE_CREAM_SHOP / PIZZA_SHOP | Same losses |
| 12929310 / 4ee | 0 | -1,473 | BRUNCH_SPOT / PIZZA_SHOP | Same loss |
| 12929311 / C95 | 0, 1 | -7,072 | FARMERS_MARKET / BAKERY | Same losses |
| 12929320 / 4ee and ae349 | 1 | -1,909 | BAKERY / YARN_STORE | Same losses |
| 12929321 / 4ee and ae349 | 0 | -2,172 | ICE_CREAM_SHOP / PIZZA_SHOP | Same losses |
| 12929325 / 4ee and ae349 | 0 | -1,560 | PET_CAFE / ICE_CREAM_SHOP | Same losses |
| 12929332 / 4ee and ae349 | 1 | -1,961 | FARMERS_MARKET / YARN_STORE | Same losses |

The only new native losses are the two seats on seed 12929315 against 4ee. The candidate selects BRUNCH_SPOT / BRUNCH_SPOT route `113373693` for 575 calls; it changes both baseline draws into losses at -7,657. Against ae349 on that seed, the same candidate route changes two wins into draws. It is not a general route improvement: on seed 12929324 against C95 it changes both baseline losses at -43,300 into wins at +20,030. The route caused a net zero seed-point change across those two activated blocks. In this confirmation it activated only eight of 256 candidate games and only on the Brunch / Brunch pair.

The other fresh outcome changes are both improvements on seed 12929312. The partial-planting repair activates once, keeps one planting request and removes one, changing two candidate draws into wins against 4ee and two losses into draws against ae349. This is a concrete execution repair, but the native panel shows one changed seed block, not a broad gain. The Brunch / Smoothie and Ice Cream / Pet repairs never activated in these 32 seeds.

There are no associated candidate policy, queue, purchase, or planting errors in these losses. The JSONL receipt stores the first capture, final reward, and aggregate telemetry, but no per-turn actions, daily inventory, worker assignment, missed production, or market transitions. Therefore it supports outcome and branch attribution, but it cannot establish a physical failure mechanism for the unchanged losses. Avoid attributing these outcomes to feed, labor, crops, or sales without a trace.

## Saved top100 loss clusters

On the older 11:03 snapshot, V3 scores 145/200 wins and 55 losses; 4ee scores 141/200. The 90% target would require at least 181/200, or 36 additional wins from this baseline. The repeated losing shop-pair groups are:

| Ordered first-two-shop pair | Losing seats | Fixtures | V3 route override active? |
|---|---:|---|---|
| YARN_STORE / PET_CAFE | 4 | Smackaveli, pensukesan | No |
| SMOOTHIE_SHOP / PIZZA_SHOP | 4 | seek inspiration, ready or not here i come | No |
| PIZZA_SHOP / ICE_CREAM_SHOP | 4 | forever young, Pico | No |
| YARN_STORE / FARMERS_MARKET | 4 | DSM, monsaraida | No |
| YARN_STORE / BAKERY | 3 | Victor @ Tufa Labs, atsushi11o7 | No |

The remaining losses are spread across pairs, with one or two losing seats each. All six V3 route-override activations on this panel were wins: route `113336042` won both seats of Lucien de Rubempre and retained both Christoffer Thimsen wins; route `113373693` won both Yaroslav seats. None of the 13 top20 losses activated a new route. Thus the existing pair routes show two useful local results, but the top20 deficit and 36-win gap need a broader change than fixing only one pair.

The 55 losses do not reveal the physical bottleneck. These are fixed opponent action tapes, and the ledger has aggregate policy counters rather than decision traces. A shared pair can also include teams with different cash margins; the pair is a useful low-leakage screen key, not proof that one schedule works against all future opponents.

## Existing policy leads and limits

- The most defensible non-donor technique is choosing a complete schedule after observing both shops, while keeping the source opening. Candidate V3 uses this at step 144. It retains all 4ee saved top100 wins and adds four net seats on this old panel. The known routes `113336042` and `113373693` are already in V3; route `113336042` is the clearest saved-panel rescue, while `113373693` has mixed native evidence.
- The V1 source-opening repair (`2c02f9f9`) recovered all nine older top100 regressions and scored 147/200 on that development panel, but its untouched 16-seed native block scored 70/48/10 against 4ee's 72/48/8, a -1.5625-point change. It is a useful no-donor reference, not a demonstrated general improvement.
- The broader public-source candidate `8ccb862a` reached 18/30 old public-loss sweeps and 19/20 top-team sweeps, but lost 19 seats that its exact source won across the 54 public-win controls; combined target-plus-control wins fell from 172 to 163. It also uses the earlier donor opening. The isolated `6a0a3b38` candidate reached 26/30 loss sweeps and 19/20 top20 sweeps, but derives from the donor-based `8f939ada` parent. These results are promising as reference outcomes, not compatible evidence for transplanting their opening.
- Complete public V43 and V48 policy pilots lost both seats to 4ee in the earlier native comparison, by paired margins of -16,012 and -89,581 respectively. Public code or deeper search alone has not supplied a broad executable schedule that passes controls.
- Generic terminal cleanup, last-worker trimming, and isolated stored-product value are already rejected in the research memory. The present receipts give no reason to reopen them.

## Recommended next candidate screen

Once the refreshed latest-episode baseline is frozen, use the repeated losing ordered shop pairs above to screen existing complete route schedules against exact `cb76fbc4`, with each route changing only after its required shops are public. Start with the pairs that cover four saved losing seats and preserve every same-pair candidate win as a control. This uses the actual observed shop route, not a team name, episode ID, or day-one donor state. Recompute pair frequency on the refreshed panel before building the pool; this old snapshot may not select the same targets.

This is an experiment to identify candidate schedules, not evidence that any route will win. The old `residual_91_routes_20260928` screen found complete schedules that rescued some other fixed-tape fixtures, while failing three fixtures after trying 91 schedules each. No stored result establishes that a selected route for the four pairs above is prefix-compatible with `cb76fbc4` or preserves its wins. The pilot needs exact-source prefix checks, same-pair controls, and both-seat outcome comparisons. A survivor still needs the frozen native confirmation in the Fresh90 plan.

## Decision

No existing policy source is already shown to exceed 90% on the refreshed current top100 panel. Keep `cb76fbc4` as the comparison source while the latest episodes are refreshed. The only concrete no-donor branches supported by current evidence are the two existing post-shop routes and partial-planting repair; the fresh block is too sparse to claim broad improvement. A focused pair-route pool over current repeated losses is the most actionable next screen, while the evidence needed to promote it remains missing: fresh pair frequencies, exact-cb schedule compatibility, route-specific wins and retained wins on current episodes, and independent native gains.

Evidence files: `diagnostics/top100_regression_repair_20260929/RESULTS_V3.md`, `TOP100_CASES_V3.md`, `REACTIVE_CASES_V3.md`, `ARCHIVE_CASES_V3.md`, `saved_v3.jsonl`, `reactive_v3_confirm.jsonl`, and `v3_fresh_outcome_changes.json`; `diagnostics/public_90_research_20260928/RESULTS.md`; `diagnostics/residual_91_routes_20260928/RESULTS.md`; `diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/goalpanel_100_retry_20260929/RESULTS.md`.
