# Kaggriculture agent research memory

Current fresh-replay research status, **2026-09-30 IST**: experimental candidate `main_candidate_fresh_replay_20260930_4802aa95.py` (SHA-256 `4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4`) is **rejected for promotion**. It improves the newest saved top100 from132/200 to156/200 and top20 from32/40 to36/40; two reserved sets improve263/400 to269/400. However, the frozen reacting screen changes baseline34W/30D/0L to34W/26D/4L. The greater-than90% goal is unmet. Root `main.py` remains exact4eeac9c3 and latest uploaded submission remains56680167/cb76fbc4; no new upload occurred. Full report and every-case CSV index: `diagnostics/fresh90_improvement_20260929/RESULTS.md`. Conditional native/file-loader and untouched32-seed confirmation were not run after the failed performance gate.

Local repair status, 2026-09-29: root `main.py` remains exact `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. Three regression-repair candidates were tested; none passed every frozen promotion gate. Final standalone experimental file: `main_candidate_minimal_repair_20260929_cb76fbc4.py`. See `diagnostics/top100_regression_repair_20260929/RESULTS_V3.md` for all variants, current top100, fresh reacting results, and older archive tradeoffs. No Kaggle access or upload occurred during the repair.

Latest user-authorized experimental upload: submission **56680167**, `main.py`, exact SHA-256 `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`, uploaded 2026-09-29 15:22:07 UTC (20:52:07 IST). Authenticated status checked at 17:04:25 UTC is **COMPLETE**, public score **1840.6**, with 27 completed public episodes available. Local root `main.py` remains exact `4eeac9c3`; this upload does not change the rejected research-promotion decision. Upload receipt: `diagnostics/upload_minimal_repair_20260929_cb76fbc4/upload_receipt.json`; latest status evidence: `diagnostics/fresh90_refresh_20260929/current_submission_56680167.json`.

Previous submission status check: 2026-09-29 12:06:59 UTC. Then-latest 56668607 was COMPLETE at 1836.8; byte-identical 56666114 was COMPLETE at 1767.8. Older 56662188 was COMPLETE at 1249.9, and 56609430 (`4eeac9c3`) was COMPLETE at 2577.6. These are historical, time-specific public scores; no new upload occurred in the top-100 comparison.
Leaderboard last checked: 2026-09-29 17:04:25 UTC, official CSV timestamp 17:04:23 UTC (fresh top100 snapshot, leading score DECEM 2979.8). Source and hashes: `diagnostics/fresh90_refresh_20260929/snapshot.json`. The earlier 11:03 snapshot remains a historical benchmark in `diagnostics/submission_top100_compare_20260929_1104/RESULTS.md`.
This is a living research log,
not a claim that the agent beats every opponent. Update the dated findings below after each
completed experiment, with the artifact and a clear promotion/rejection decision.
`AGENTS.md` points future workspace work to this file.

## Mission and operating constraints

- **2026-09-30 IST — combinedV2 fails reacting qualification; fixed-replay gains do not earn promotion.** All128 planned version/seat games complete cleanly under native transitions: candidate34W/26D/4L versus baseline34W/30D/0L over64 games each. Win points fall49→47; whole-seed95% bootstrap interval for point-rate change is[-0.09375,0]. Four baseline draws become losses at seed22929006, both seats against cb76 and ae349; all activate FarmersMarket/Smoothie route113410114 with zero funded-land turns, losing6114 margin each. V35/C95 aggregate points are unchanged. **Decision: reject exact4802aa95 for promotion, stop conditional native/file-loader and32-seed confirmation, leave root main4ee and latest Kaggle uploadcb76 unchanged.** Do not merely retune this rule on these eight seeds and continue calling that block independent. Sources and root-folder copy are preserved. The prepared operational verifier was statically checked but never run; its existence is not a passing execution receipt. Evidence: `diagnostics/fresh90_improvement_20260929/combined_v2_screen_receipt.json`, `combined_v2_screen_paired_cases.csv`, final report and all-case ledger index.

- **2026-09-30 IST — frozen top-three complete-tape controls also fail the138-game pilot.** Single-tape standalone controls from current ranks1,2,3 (selected by rank before games) score12W/2D/32L,12W/0D/34L and22W/0D/24L on the same46-seat development panel where cb76 scores32W/0D/14L. Their top20 results are10W/2D/28L,10W/0D/30L and20W/0D/20L. All138 games complete cleanly. Each rescues one public-loss opponent in both seats, but the broader win regressions fail the frozen gate. **Decision: reject all three; stop this bounded opening-tape alternative without further candidate searches or promotion.** Rankings alone do not establish transferable recorded schedules. Source provenance, day0 commitments and shared-episode note for ranks2/3: `diagnostics/fresh90_leading_openings_20260930/README.md`. Every case: `diagnostics/fresh90_improvement_20260929/leading_rank*_pilot_comparison.*` and `leading_pilot_decision.json`. CombinedV2 proceeds separately to its predeclared reacting screen.

- **2026-09-30 IST — combinedV2 passes the reserved-replay aggregate gate with a modest6/400 seat gain.** Reserved3 completes at143W/0D/57L versus cb76's137W/0D/63L; top20 is30/40 versus28/40. Alongside reserved2's126/200 tie (top2026/40 versus28/40), the two sets total269/400 candidate wins versus263/400 baseline, a1.5 percentage-point gain. All800 version/seat games across both sets are clean. **Decision: pass the frozen positive-combined-points/no-per-set-decline replay gate; advance exact4802aa95 to the eight-seed, four-reacting-policy screen, still no promotion.** These are correlated fixed-tape generalization controls, not independent policy validation. The newest development gain of24/200 is much larger than the reserved gain. Every case and individual regressions: `diagnostics/fresh90_improvement_20260929/combined_v2_reserved2_comparison.*` and `combined_v2_reserved3_comparison.*`. Root main remains4ee; no upload.

- **2026-09-30 IST — combinedV2 ties the first reserved100 set; development gain has not yet generalized.** Exact4802aa95 and exactcb76 each win126/200 seats and63/100 teams on reserved episode2. Candidate gains4 winning seats and loses4; top20 declines28/40 to26/40. All400 baseline/candidate games are clean. Mean paired margin improves2392.27, but that does not replace the primary win objective. **Decision: no promotion; complete the already-frozen reserved3 set unchanged, requiring positive combined points and no per-set aggregate decline.** This panel will not be used to revise this source or select the rejected opening families. Every case: `diagnostics/fresh90_improvement_20260929/combined_v2_reserved2_comparison.*`.

- **2026-09-29 — current-opening rejection is not attributed to an observed prefix mismatch.** Static review confirms that, although the clustering projection ignores trades, the actual three selected families have identical complete worker and market actions before every possible switch (65/77 through147 before the144 fork;16/83 through82 before72;30/86 through76 before72). No seed, opponent identity or future-observation lookup appears in the router. The poor138-game pilot therefore cannot be explained merely by the projection's general funding caveat. **Decision: close this architecture for now; no further market-helper transplant without a trace-defined failure.** Generic queue helpers reorder existing orders and do not repair the losing schedules' crop/worker commitments. Builder provenance comprehension defect and its one-line repair are documented without changing frozen candidate bytes in `diagnostics/fresh90_policy_design_20260929/OPENING_ROUTER_STATIC_REVIEW.md`. The working regeneration script and existing validation receipts are preserved.

- **2026-09-29 — three current melon-opening families fail the frozen138-game development pilot.** New standalone schedules were selected by physical-prefix family size and frozen rank before games, using only latest100 development tapes. Families65/77,16/83 and30/86 start MELON orders on day0, and each rescues at least one actual public loss in both seats. However, their full46-seat pilot scores are15W/0D/31L,8W/2D/36L and23W/0D/23L versus cb76's32W/0D/14L. Top20 falls to13/40,4W/2D/34L and19/40 respectively. All138 games are clean. **Decision: reject all three raw opening candidates; no full-panel escalation or promotion.** Early melon timing alone is insufficient, and shared physical action prefixes do not prove equal funding when trading histories differ. Exact plan, all cases and decisions: `diagnostics/fresh90_improvement_20260929/OPENING_PILOT_PLAN.md`, `opening_pilot_decision.json`, `opening_family*_pilot_comparison.*`; sources/provenance: `diagnostics/fresh90_current_opening_20260929/`. Reserved outcomes did not select or tune these candidates. Root main remains4ee; no upload.

- **2026-09-29 — combinedV2 restores public controls while retaining24 additional latest100 winning seats.** Exact `4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4` removes only V1's regressing Yarn/Smoothie override. Repeated latest100:156W/0D/44L,78/100 both-seat teams; top20:36W/0D/4L,18/20 teams. Repeated public27:48W/0D/6L,24/27 teams, retaining every original cb76 win. All254 games completed cleanly. Mean paired latest100 margin improves2298.45. **Decision: pass repeated development gates, advance exact bytes to reserved replay controls; no promotion or upload, strictly >90% remains unmet.** Public27 became development after its V1 rejection. Every case is in `diagnostics/fresh90_improvement_20260929/combined_v2_top100_comparison.*` and `combined_v2_public27_comparison.*`. The static audit `diagnostics/fresh90_loss_audit_20260929/LATEST_PUBLIC_LOSSES_56680167_AUDIT.md` finds successful land purchases but much later melon production/sales in all three actual public losses; this motivates a separate coherent-opening experiment and is not a counterfactual win claim.

- **2026-09-29 — combinedV1 fails fresh public-game controls despite fitted top100 gains.** Exactef33a1b6 scores44/54 on all27 latest56680167 public opponent tapes, versus48/54 for exactcb76. Four old winning seats are lost (Max Podd and LoveB4Sunrise in both seats), all under Yarn/Smoothie113640729 with zero funded-land activation; no old loss is rescued. All games are clean. **Decision: reject V1 promotion and its conditional reserved/native escalation.** A separately frozenV2 removes only that one override and must repeat both full development panels; public27 is now development rather than held-out evidence. All source/results remain preserved. `diagnostics/fresh90_improvement_20260929/combined_v1_public27_comparison.*`, `COMBINATION_V2_PLAN.md`. The27 original uploaded seats exactly reproduce every719-action stream, both final rewards and WDL, confirming currentcb76 provenance and local replay mechanics: `public27_reproduction.json`. Root main remains4ee; no upload.

- **2026-09-29 — exact combined candidate completes latest100 at158/200 (79%), top20 at36/40 (90%).** Source `ef33a1b6e89f1214bffa7575ffcbb13053ef4054709cde4c52d76b74207a804a` combines the funded-land repair with nine selected complete route rules; the redundant Yarn/Pet switch is omitted. All200 new runs completed cleanly, preserving every cb76 and funded-land winning seat. It gains26 winning seats over cb76, raises both-seat teams66→79, and improves mean paired margin2204.26. Top20 gains32→36 winning seats and16→18 sweeps. **Decision: pass combined development gate, keep candidate offline for public/reserved/reacting checks; strictly >90% remains unmet.** Every case: `diagnostics/fresh90_improvement_20260929/combined_v1_top100_comparison.*`; exact manifest, plan, jobs, receipts and top20 traces are beside it. Follow-up manifests are frozen before reserved outcomes. Reserved sets share9 and7 episode IDs with development through other teams, so they remain correlated replay controls, not independent policy validation. No promotion or upload.

- **2026-09-29 — funded-land repair completes the full latest100 diagnostic at134/200.** All200 games for exact2a4d093a completed cleanly:134W/0D/66L,67/100 both-seat teams, top20:34W/0D/6L and17/20 both-seat teams. Both Majkel losses are rescued; the other198 rows preserve their rewards and outcomes. Mean paired margin improves189.31 per seat. **Decision: pass the full saved development gate, retain for composition/independent qualification; no promotion or upload.** `diagnostics/fresh90_improvement_20260929/funded_land_full_comparison.*`, source-bound200-job receipt, and `LAND_QUEUE_AUDIT_CLARIFICATION.md` (the frozen plan's eight-coin figure is a forecast, not reconstructed live intraqueue cash). The new combined source omits the Yarn/Pet route change because this general repair already supplies its two added wins.

- **2026-09-29 — deferred existing land purchase rescues a concrete worker-execution failure.** In fresh rank10 Majkel, step242 BUY_LAND failed before later same-turn wheat sales, leaving SW locked after four workers had already been hired. Idle/mirror forecasts place the order8 coins short; exact live cash at that queue index was not reconstructed, because the actual rival sells wheat at that turn. New isolated source `2a4d093a4824c0fac824b292dfa4a93c2403214d74f31b703bfd913daf136eb8` moves the existing order to the queue tail only after idle/mirror exact market checks preserve other own/rival resources and fund exactly one native quadrant. All8 frozen pilot games were clean: the two target margins changed from-10715 to+8159/+8273; six controls were exactly unchanged. **Decision: pass focused pilot, expand to the200-game latest100 panel; no promotion yet.** `diagnostics/fresh90_improvement_20260929/LAND_QUEUE_PLAN.md`, `funded_land_pilot_comparison.*` and exact job/results/trace receipts. No extra land purchase or new worker commitment is introduced; observed net own/rival effects are still required beyond this diagnostic. Static census and forecast limitation: `diagnostics/fresh90_loss_audit_20260929/FUNDED_LAND_AUDIT.md`.

- **2026-09-29 — wider observed-pair route search completes and retains eight development rules.** All292 one-seat screening games across232 prefix-compatible candidates and23 additional losing shop pairs completed cleanly. The predeclared selection advanced17 candidates to114 both-seat games including34 exact reused rows and every affected latest100 baseline win. Eight pair rules passed the no-lost-winning-seat and positive-points gate, adding22 winning seats across their disjoint affected sets; together with the separate top20 rules this implies158/200 only if full composition verifies. The other15 searched pairs had no qualifying continuation. **Decision: retain eight selected rules for combined development, not promotion; the >90% target remains unmet.** `diagnostics/fresh90_improvement_20260929/broad_routes/stage2_decision.json`, `BROAD_ROUTE_PLAN.md` and all variants/ledgers. Several superficially better target routes were rejected because they lost baseline winners. Fixed replay fitting is not independent validation.

- **2026-09-29 — first complete-route search rescues two fresh top20 matchups without sacrificing affected baseline wins.** The frozen33-variant/46-game one-seat screen selected7 variants for40 both-seat target/control games (10 exact rows reused with hashes). Whole route113332529 for IceCream/Smoothie rescues rank8 Anton in both seats (+6926); route113661901 for Yarn/Pet rescues rank10 Majkel (+6502/+6597). Each passes the no-lost-winning-seat gate on every fresh top100 fixture sharing its shop pair. Yarn/Bakery113660799 rescues rank9 akmr (+45) but loses rank85 (-6468), so it is rejected. The passing pair effects imply36/40 top20 wins (90%, not strictly >90%) if composition verifies; this is not yet a combined-file result. **Decision: retain the two passing rules for development composition, no promotion.** `diagnostics/fresh90_improvement_20260929/route_search/stage2_decision.json`, immutable jobs/results and `ROUTE_SEARCH_PLAN.md`. Wider development is frozen separately in `BROAD_ROUTE_PLAN.md`. Root main remains4ee; no upload.

- **2026-09-29 — refreshed top100 baseline is 132/200 (66%), below the requested >90%.** The exact uploaded cb76 candidate completed all200 both-seat games against the outcome-blind latest eligible public episode for each team in the17:04:23 UTC leaderboard snapshot. Results:132W/0D/68L,66/100 teams beaten in both seats; top20:32W/0D/8L,16/20 both-seat wins. All games finished cleanly. There are84 distinct episodes in the100-team panel and15 in top20, so these are correlated fixed-action diagnostics, not100 independent opponents or an online win-rate estimate. The40 top20 rows were reused only after exact source/action/replay hash checks. **Decision: retain as baseline; neither the >90% target nor improvement is established.** Frozen jobs, every case and receipt: `diagnostics/fresh90_improvement_20260929/cb76_top100_jobs*`; collection source hashes in `diagnostics/fresh90_refresh_20260929/`. Root main remains4ee; no upload.

- **2026-09-29 — fresh schedule-rollout V2 activates but earns no additional top20 win.** Exact `e7a5e326fa70b7248582053b5fc177b6bae3d0320fce00df6979d9537724eff8` fixes forecast partial-planting parity and prospectively admits nonnegative predicted paired gains in every scenario with mean>1000, instead of V1's strictly positive1500 minimum. On the freshly downloaded17:04 UTC top20 snapshot, all40 candidate and40 exact-cb76 baseline games completed cleanly. Both versions won32/40 seats and16/20 teams in both seats; no win was gained or lost. Mean margin fell from42202.675 to40059.825. **Decision: reject V2 promotion at its frozen positive-win-point pilot gate; do not run conditional reacting confirmation.** Full paired own/rival deltas are in `diagnostics/fresh90_improvement_20260929/v2_top20_comparison.json`; plans, exact source hashes, complete actions/observations and per-case outcomes are preserved beside it. This snapshot has15 distinct episodes shared by20 teams; fixed actions remain diagnostic only. V1 is also closed without escalation after code review found its simulated planting omitted the deployed repair. Root main remains4ee; no upload.

- **2026-09-29 17:10 UTC — legal-state whole-schedule rollout pilot ties cb76 without activation.** New separate candidate `477fe255da706617b6cacbd549b0426f8b183411b69f2cd810aba6a1b593c76c` uses the embedded exact physical engine at step144 to compare prefix-compatible complete schedules under four explicit forecasts (two hypothetical future seeds crossed with idle/empty and original-router/mirrored rival state). It never reads the real seed, hidden rival inventory or future shops. All32 paired development games (seeds22929001-22929002, cb76/ae349/V35/C95, both seats, both versions) completed cleanly; candidate and cb76 each scored8W/8D/0L with identical rewards and margins in all16 matched scenarios. No candidate schedule switch activated, so no strength gain is established; the fresh-top20 saved pilot remains pending collection. Longest initial observed chooser calls were approximately16 seconds under concurrent load, requiring later actual timeout/loader checks if the candidate earns escalation. **Decision: diagnostic-only, no promotion; preserve the source and frozen pilot evidence.** `diagnostics/fresh90_improvement_20260929/ROLLOUT_PLAN.md`, `rollout_v1_pilot_screen_receipt.json`, and its job/result ledgers. Root main remains4ee; no upload was requested or performed in this research request.

- **2026-09-29 15:22 UTC — user-requested cb76fbc4 experimental upload accepted.** After the final repair report disclosed the inconclusive fresh comparison and the older loss-archive regression, the user explicitly requested: "upload that new candidate to the kaggle please." That request authorized exactly one upload of the delivered `main_candidate_minimal_repair_20260929_cb76fbc4.py`. Preflight verified its full hash, source-bound saved/native/parity/archive receipts, both-seat file-loader checks and intended final callable `kaggle_minimal_route_repair_entrypoint`. The byte-identical staging file `diagnostics/upload_minimal_repair_20260929_cb76fbc4/main.py` was submitted once by Kaggle CLI; return code 0 and a unique new matching submission **56680167** confirm acceptance at 15:22:07 UTC. Initial status PENDING, score unavailable. Both the staged file and unchanged root main were hash-verified after upload. **Decision: user-authorized experimental upload only; research promotion remains rejected.** Saved top100 145/200 and fresh 149W/90D/17L do not establish an online improvement; the older archived losses remain only 3/30 both-seat wins. Exact authorization, timestamps, command output, before/after submission lists and evidence hashes are preserved in `diagnostics/upload_minimal_repair_20260929_cb76fbc4/`. No leaderboard or replay refresh was performed for this upload.

- **2026-09-29 — final minimal repair fixes current replay regressions but remains unqualified.** Exact `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74` is 4ee plus three prefix-compatible whole schedules (Brunch/Brunch, Brunch/Smoothie, IceCream/Pet) and the existing executable partial-planting repair. All nine current top100 regression teams recovered, no lost 4ee wins: 145/200 seat wins and 72/100 both-seat team wins, versus 4ee 141/200 and 70/100, uploaded ae349 131/200 and 65/100. Current top20 remains 27/40 seats and 13/20 sweeps, below the user's 90% target. Selected development reacting results were 40/24/0 versus 32/24/8 W/D/L. All 14 native parity cases and four direct/file-loader runs passed, with exact both-seat action/reward parity and intended final entrypoint. On the separately frozen 32 untouched native seeds 12929301-12929332 (512 games), V3 was 149/90/17 versus 4ee 147/90/19: +0.78125 win-point percentage points, 95% whole-seed bootstrap [-1.5625,+3.125], no aggregate per-opponent point regression, all games clean. Only Brunch/Brunch activated (8/256 candidate games, two seed blocks); the other new route pairs never activated. Planting improved seed 12929312 by two points; Brunch/Brunch lost two on 12929315 against source-style opponents and gained two on 12929324 against C95. The earlier 102-case archive fell to **3/30 loss sweeps and 17/20 top20 sweeps**, compared with ae349 27/30 and 19/20; this explicitly exposes the lost targeted repairs. **Decision: reject promotion; retain the standalone experimental file and keep main.py at 4ee.** This completes the bounded repair plan; do not present the saved gains or small inconclusive native gain as a reliable overall replacement or top10 forecast. Full results and every case: `diagnostics/top100_regression_repair_20260929/RESULTS_V3.md`, `TOP100_CASES_V3.md`, `REACTIVE_CASES_V3.md`, `ARCHIVE_CASES_V3.md`, and `v3_fresh_outcome_changes.json`. Saved ledger SHA `114166062d5064af376b4eed5ca93feddc97f2abd116bf6542c7a27c538cbbf5`; archive ledger SHA `d1a811304f6cfd7cac56551a47d28f3c6e78b21dde37ea79f022b068869bc6ac`. Backups and V1/V2 failures are preserved; no Kaggle access or upload.

- **2026-09-29 — V2 rollback also rejected on fresh reacting games.** Exact `6cd6ff9eed407f3c31c2b432c37da8b3ece8f703a2932d5293f9b93b7e060df3` additionally restores Yarn/Farmers and Farmers/Pizza mappings. It won 145/200 current saved seats (72 team sweeps), retained every 4ee win, and rescued all nine measured regression teams. Its selected development reacting block won 44/18/2 versus 4ee 32/18/14; all 14 native parity and four loader runs passed. Untouched native seeds 12929201-12929216 gave **60/60/8 versus 66/60/2**, -4.6875 win-point percentage points, whole-seed 95% bootstrap [-9.375,0]. All 256 games were clean. V35 alone lost six prior wins under newer IceCream/Ghost and Smoothie source-leaf behavior; the other three opponents tied 4ee exactly. **Decision: reject V2 for promotion.** A process interruption after 71 clean rows was recovered by validating all job/source hashes and resuming missing jobs unchanged; see `confirmation_interruption_20260929.json`. Its completed archive diagnostic won 22/30 loss pairs and 18/20 top20 pairs, versus uploaded ae349 at 27/30 and 19/20; all 102 archive games were clean. Full receipts and RESULTS_V2.md are in `diagnostics/top100_regression_repair_20260929/`. Root main.py remains 4ee; no Kaggle access or upload. V3 is frozen separately in `PLAN_V3.md`: exact 4ee plus three prefix-compatible complete routes and the existing executable planting repair, without later donor/source-leaf controllers; its larger fresh 32-seed block is fixed before outcomes to account for sparse route activation.

- **2026-09-29 — V1 regression repair rejected after native confirmation.** Candidate `2c02f9f9` passed its current saved top100 panel (147/200 wins, all nine regressed teams recovered, no lost 4ee wins), 14 native parity games, and four both-seat direct/file-loader games. Its eight-seed reacting screen improved from 30/24/10 to 36/24/4 W/D/L, but the untouched 16-seed native confirmation reversed the result: candidate 70/48/10 versus 4ee 72/48/8, paired win-point change -1.5625 percentage points, whole-seed 95% bootstrap [-7.8125,+4.6875]. All 256 games were clean. The worsened outcomes used Yarn/Farmers route 113349962 or Farmers/Pizza route 113372534; Brunch/Brunch supplied the C95 rescues. The earlier 102-case archive remained 19/20 top20 sweeps but fell from 27/30 to 23/30 loss sweeps. **Decision: reject V1 for promotion; keep exact source and outcomes as research.** Root main.py remains 4ee and no Kaggle access/upload occurred. Full report: `diagnostics/top100_regression_repair_20260929/RESULTS.md`; per-team results: `TOP100_CASES.md`. The earlier pending entry below is superseded by this completed decision. V2 removes the two implicated route overrides under separately frozen `PLAN_V2.md`; all V1 seeds are development data for V2.

- **2026-09-29 — source-opening repair recovered every measured top-100 regression.** Candidate `2c02f9f9898dc393f8798f1d51a3a4c26a4bf1ddf862770ef66be159d61d6e13` starts from ae349, restores the original source opening and always uses its source controller, and removes the Brunch/Pizza loss-pool override. All 200 development replay games completed DONE/DONE/720 without candidate errors. It won 147/200 seats and swept 73/100 teams, versus 4ee's 141/200 and 70/100 and ae349's 131/200 and 65/100. It recovered all nine regressed team pairs with zero lost 4ee wins, retained the three non-donor rescues, and lost the donor-only Attention Is All You Seed rescue. **Decision: retain as a promising separate candidate pending fresh reacting and loader checks; do not promote yet.** Exact root-folder copy: `main_candidate_regression_repair_20260929_2c02f9f9.py`; current 4ee backup: `main_before_regression_repair_20260929_4eeac9c3.py`. Evidence: `diagnostics/top100_regression_repair_20260929/PLAN.md`, `manifest_v1.json`, `saved_v1_full_receipt.json`, and results SHA-256 `f4ec056bd66b87ab502a06bec60e165d22706ea9dcb22327bb5f1304d4c17fb4`. The top-100 set informed this fix and is development evidence, not independent validation. Root `main.py` remains 4ee; no Kaggle access or upload occurred.

- **2026-09-29 — derived top-100 regression audit explains the older file's edge.** From the 600 clean matched games in `diagnostics/submission_top100_compare_20260929_1104/`, 18 newer-policy seats flip old wins to losses and 8 flip old losses to wins. Eight of the nine regressed team pairs selected the new day-one `shared151` donor bridge; the ninth selected the `BRUNCH_SPOT|PIZZA_SHOP` loss-pool route. Boey fell from +101,543 in both old seats to about -33,400 in both new seats under the donor branch; Anton Tikhonov fell from +514 to -7,481 in both seats under the loss-pool route. Four team pairs were rescued, so the new rules have some local value but a net -10 seat wins on this held-out replay snapshot. `ae349d83`'s Pizza melon fallback did not fire in any of its 200 cases and its rewards exactly matched `257f941d`. This is branch-associated fixed-tape evidence, not single-feature causal ablation or reactive proof. **Decision: keep root `4eeac9c3`; do not promote the newer files.** Evidence: `diagnostics/submission_top100_compare_20260929_1104/RESULTS.md`, `delta_explanation.json`, `explain_deltas.py`, and SHA-bound `local_results.jsonl`.

- **2026-09-29 12:06 UTC — exact downloaded submitted files compared with today's top 100.** Authenticated Kaggle download bound four `main.py` submissions to their local source hashes: 56668607 (08:11:57 UTC, `ae349d83`, score 1836.8 at the final listing), 56666114 (06:55:03 UTC, identical `ae349d83`, 1767.8), 56662188 (04:09:22 UTC, `257f941d`, 1249.9), and 56609430 (2026-09-27 13:10:15 UTC, `4eeac9c3`, 2577.6). The current leaderboard's 100 teams were frozen at 11:03:38 UTC; their latest completed public replay actions were downloaded without outcome filtering. All 600 native engine1.32.7 games against these fixed tapes completed DONE/DONE/720. In both seats for each top-100 team, `4eeac9c3` won 141/200 seats and swept 70/100 teams, versus 131/200 and 65/100 for each newer policy. Top10 was 11/20 and 5/10 sweeps for `4eeac9c3`, versus 7/20 and 3/10 for each newer one. `ae349d83` and `257f941d` had identical reward and outcome in every matched game. **Decision: retain root `main.py` (`4eeac9c3`); reject promoting the newer submitted files on this panel.** This is fixed replay evidence only, not independent reactive validation or a predicted live score. No policy file changed and no Kaggle upload occurred. Evidence: `diagnostics/submission_top100_compare_20260929_1104/RESULTS.md`, `assessment.json`, downloaded source receipt, and native run receipt (result SHA-256 `7ba72ea62b9b399ccc8dc1099a2d86c09ec9e8670b0a63b068d58fd309596832`).

- **2026-09-29 — no evidence-supported next margin candidate after cross-target review.** Luna Max audits of the current ae349 panel and remaining weak fixtures found no safe, material new change. The only saved paired-margin delta remains Pensukesan (+45,291/seat, still losing), with own cash down 12,316 and rival cash down 57,607; the 24-case reactive panel ties uploaded257 exactly with zero margin delta. Fish's tempting shared166 opening loses 19 prior winners; Roman's broad openings damage controls and the 91-route/production-leaf options did not rescue it; DECEM's remaining terminal sale is worth only 44. A separate close-win delivery trial failed its Unknown Mother-Goose control by -565/seat. Decision: keep ae349 unchanged and do not launch another unsupported candidate; fixed-panel thresholds remain 27/30 loss and 19/20 top20, not a live leaderboard guarantee. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; Kaggle was not checked or contacted. Review: `diagnostics/ae349_decem_trace_audit_20260929/REMAINING_MARGIN_REVIEW.md` and `RESULTS.md`.

- **2026-09-29 — exact ae349 DECEM terminal-market rescue lead rejected.** Replayed the exact candidate against both saved DECEM seats and regenerated all 719 candidate actions exactly; both rows matched the hash-bound result at 86,464 vs 95,549, DONE/DONE/720, margin -9,085. On action 718 the agent already sells all requested terminal stock, earning +7,301 margin from a pre-market -16,386. Two fertilizer remain in the shed; the exact market curve prices the next two at $22 each, only +44 and an estimated -9,041 terminal margin. No strategy change can rescue DECEM through final liquidation. Two Luna Max reviews agreed to stop this lane; the prior separate 18-turn sale timing test gained only 59 paired-margin coins. **Reject as a DECEM rescue; keep ae349 unchanged and target an earlier material production/investment mechanism.** Current fixed-panel counts remain 27/30 loss sweeps and 19/20 top20 sweeps; this fixed-tape audit is not reactive validation. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; Kaggle was not checked or contacted. Evidence: `diagnostics/ae349_decem_trace_audit_20260929/RESULTS.md`, analysis SHA-256 `e9e7d6c598656d1558463268740f27f1e7f2a3c2d15c2a8594cbd85062263ff3`; runner receipt is under the same folder.

- **2026-09-29 — ae349d83 margin profile shows a saved-only Pensukesan repair.** An offline audit of the completed 102-row saved panel and 24 matched native reactive scenarios found the fixed goals at 27/30 loss sweeps and 19/20 top20 sweeps. The only saved paired-margin change is the two Pensukesan seats (+45,291 each, still losses); the other 98 goal seats and two public-win controls are unchanged. Against the three reacting policies, ae349 ties uploaded257 in every paired reward and outcome (8W/14D/2L for each arm across 24 scenarios), with zero margin delta and zero activation of its Pizza melon fallback. The narrowest saved wins include live-114267572 (+244/+6,475), forever young (+313/+313), offhand (+670/+670), and top20 Majkel1337 (+2,867). Decision: do not describe the saved margin repair as reactive strength; direct future margin work to a measurable paired own-minus-rival objective and require activation in fresh reacting games before claiming generalization. This is a derived audit of existing receipts, not new game evidence. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; no Kaggle access or upload occurred. Evidence: `diagnostics/margin_profile_ae349_20260929/RESULTS.md`; saved receipt SHA-256 `218297125b45a782f903b2a7aaa178597b708a53f0ffac4f196b404f7b95ce2d`; reactive receipt SHA-256 `53e0968303b1e26c4ec6dfc0681edb2f939d156b9635c5a1aaca5fb99233479e`.

- **2026-09-29 — 257f melon-delivery candidate rejected by its frozen 102-row outcome panel.** Candidate SHA-256 `a8174509cd2679578869b3090a9137d136e22a4e752c2bc9dc822b86a1aade25` was tested against exact 257f parent `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`. All 102 fixed-tape rows completed cleanly at DONE/DONE/720; action parity, prior results, prior telemetry, same-observation parent telemetry, and non-target rewards all passed. The loss30 and top20 preservation panels remained 27/30 and 19/20. On target `live-114271958`, both seats stayed wins and paired margin rose from +670 to +2,307 (+1,637 per seat; our reward +834 and rival reward -803). On control `top20-08-Unknown Mother-Goose-114272024`, both seats stayed wins but margin fell from +4,471 to +3,906 (-565 per seat; our reward -566, rival reward -1), failing the predeclared nonnegative-margin gate. The receipt records `all_rows_pass=false` and `unknown_mother_goose_margin_gate=false`. **Reject this candidate and do not run the conditional reactive confirmation; do not promote it.** This is fixed-tape diagnostic evidence, not a rating or leaderboard estimate. Root research `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; Kaggle was not checked or contacted. Candidate, plan, and evidence are under `diagnostics/melon_delivery_257f_20260929/`. Outcome receipt SHA-256 `aaaa2ed29245e0dcdcb6ca70d993cc91150608543f36f9b8eaf1aa9bba9d6dfe`; outcomes SHA-256 `31d5908c25f4444b0c552d983e77a7e54eb0a9278c177e46fd0f14e4bce754fa`; panel SHA-256 `fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d`; frozen manifest SHA-256 `9e2eec1c6ceef83cd92b1102b2013eab39a95871c390878c79b283d9a06994eb`; plan SHA-256 `5266a9ad965bdb736d3e5839beb3055ef0c8aaff3d56483377b00b903c3f0628`.

- **2026-09-29 06:55 UTC — tested ae349d83 candidate uploaded once by the user's fresh request.** Kaggle accepted exact SHA-256 `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb` as `main.py`, submission **56666114**, at 06:55:03 UTC / 12:25:03 IST; the listing verified PENDING with no score at 06:55:10 UTC. The request "ok can you upload the new candidate to the kaggle please" is consumed. The package verified the candidate bytes and seven bound pilot/saved/reactive/loader evidence files before its single upload. Saved outcomes retain 27/30 loss and 19/20 top20 sweeps in both seats, with Pensukesan margins improved by 45,291 per seat; fresh reacting outcomes remain 8W/14D/2L, identical to uploaded257, with zero new-guard activations. All eight operational native/file-loader games passed. Decision: fulfill the requested experimental upload; no research promotion or proven score/top10 improvement. Root research `main.py` remains exact `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. Exact uploaded file and receipt: `diagnostics/upload_pizza_guard_20260929_ae349d83/main.py` and `upload_receipt.json`. Leaderboard and replays were not refreshed.

- **2026-09-29 — 257f melon-route selector census and native prefixes passed preflight.** The hash-bound incumbent-only census completed 102 saved rows and found the four frozen activations: both seats of `live-114271958` and both seats of `top20-08-Unknown Mother-Goose-114272024`. Both target native prefixes passed through step 716 with the frozen candidate and exact 257f parent bound. These checks support target coverage and execution only; the completed outcome decision is recorded in the finding above. Census receipt SHA-256 `5e9d1ad7533e5c8b2b884ab8c05271f94a541d6ddcc72a1f4213cb2546457bf0`; prefix receipt SHA-256 `d812bc49464921706f61a721081859ee1a6633ef2f12cf2007391f4331bd7f88`; plan: `diagnostics/melon_delivery_257f_20260929/PLAN.md`.

- **2026-09-29 04:53 UTC — step-1 hire-only rescue rejected before full games.** Frozen candidate `b78f593938db50bb5118fc8af4b0736f3bb20ad7da01c80e7a6a96f982a95cbf` appended one HIRE to the exact 6a parent action on both `live-114270587` target seats. The two-seat native prefix passed the opening, order, $5 cost, state-delta, and source-hash checks, but stopped at `native_prefix_gate`; `outcome_receipt.json` records `game_count=0`, no baseline/candidate games, and a failed `step2_and3_parent_actions_match_five_hand_state` check in both seats. The traces show five observed hands and only the parent's four hand commands at steps 2 and 3. Luna Max reviewers checked the bound native core and installed Kaggle parser: both iterate only over commands supplied, so the fifth hand receives no action; it is idle for the rest of the day and is cleared at day end. This is a real worker-utilization gap, not an invalid action-list schema. **Reject the productive-hire hypothesis; do not waive the gate or pad with PASS.** Any follow-up needs a separately frozen, source-bound fifth-hand schedule and a passing two-seat prefix before full games. This did not produce win/loss or margin evidence. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; Kaggle was not checked or contacted. Evidence: `diagnostics/roman_step1_hire_ablation_20260929/RESULTS.md`, `outcome_receipt.json`, and both `prefix_candidate_target*.jsonl.gz` traces.

- **2026-09-29 04:09 UTC — reviewed guarded candidate uploaded once by the user's fresh request.** Kaggle accepted exact `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55` as `main.py`, submission **56662188**, at 04:09:22 UTC / 09:39:22 IST. Listing verified PENDING at 04:09:25 UTC. The request to review and submit the new code is now consumed; do not repeat the uploader. Candidate passed 102 preservation checks and all 12 native direct/file-loader games: correct callable, DONE/DONE/720, 719 calls per player, full action/reward parity, no native or policy errors, minimum remaining overage 59.770622 seconds. Earlier verifier-only `sort` keyword and initialization-log-count defects are preserved in the package's `revisions/` folders; neither changed the candidate or waived a policy failure. Operational receipt SHA-256 `a90a5adf1a943f0434e61ef63cbcbc4985783679c00eb2609e762cbeb6c1f1d5`. Saved results improve a44's 17/30 loss sweeps to 27/30, retain 19/20 top20 and recover 20 losing seats without W/D/L regression. The parent reactive pilot showed identical results to a44 and failed its promotion gates; **this is an experimental upload, not research promotion or evidence of a rating/top10 gain**. Root main remains exact 4ee, with both old and new backups in the root folder. Evidence and exact uploaded file: `diagnostics/upload_pet_source_guard_20260929_257f941d/REVIEW.md`, `loader_parity.json`, and `upload_receipt.json`.

- **2026-09-29 — Roman shared166 rescue rejected after fallback repair.** The first V3 full-game pilot (`86c9d10c…`) lost both target seats by -133,800/-135,802 because its five-worker donor schedule failed at the step-24 day boundary and returned PASS for all 695 later actions; all four controls exactly matched 6a. The V8 fallback candidate (`25461e7595dd2bfb3a53b7303ff0e697f60df7807e9d895783415c9833d1cf4c`, adapter `424c57ec…`) correctly fell back once at step 24 after 23 donor calls, had zero errors, and matched the exact 6a parent on every post-fallback action for both seats. Still, its margins were -130,648/-132,643 versus 6a’s -18,815/-18,815 (paired deterioration -111,833/-113,828). The day-boundary state had only $53 and no animals after the donor’s melon/wheat/pasture commitments. All four controls remained exact wins and all 12 games finished DONE/DONE/720. **Reject; do not promote or upload.** This fixed-tape diagnostic is not independent or reactive validation. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; Kaggle was not checked or contacted. Freeze panel SHA-256 `e3024efdca9e28960e3f7ff021e07a3c60c28b0468b2aaa8fafeb6fdfaddb0c4`; receipt SHA-256 `69eff82fe4a632389b130673f884e72db2eda243c421519e392cb3569cc82021`; outcomes SHA-256 `7058df79c31a76bc5bb86e7bd87600585be935b43f7d0ab11ac586010900d61d`. Evidence: `diagnostics/roman_bridge_shared166_8f_20260929/OUTCOME_PILOT_V3_RESULTS.md` and `diagnostics/roman_bridge_shared166_8f_20260929/6a_outcome_pilot_v8_source_only_20260929/PLAN.md`, `outcome_receipt.json`, and target trace files.

- **2026-09-29 — guarded Pet candidate preserved all 102 saved-replay checks.** Candidate `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55` adds a source-branch guard and actual-branch telemetry to ebf's Pet route selector. All 102 games completed DONE/DONE/720, with zero candidate errors and exact preservation of prior results, rewards, margins and prior telemetry. The 100-seat goal panel remains **27/30 loss sweeps and 19/20 top20 sweeps (92W/0D/8L)**; both public-win control seats remain wins. Against last-uploaded a44's matched saved panel, 20 seats change loss to win, none regress in W/D/L, and mean paired margin improves 2,822.7 coins. These are fixed-tape results, not reactive validation. The old ebf receipt and failed reactive pilot remain unchanged. Decision: accept the reporting/branch correction and proceed to operational file-loader checks for the explicitly requested experimental upload; do not grant research promotion. Root `main.py` remains exact 4ee. Evidence: `diagnostics/pet_source_guard_20260929/RESULTS.md`; preservation receipt SHA-256 `4086a1ebd23431efedcbd178a7e5367cc1e84d8999b1843a4e62d891aa5f2997`.

- **2026-09-29 — fresh three-policy reactive pilot finished with no improvement; research promotion rejected.** All 96 predeclared original-shop games completed DONE/DONE/720 with zero candidate/opponent errors. Uploaded a44, parent 6a and ebf each scored **16 wins / 10 draws / 6 losses** in 32 matched scenarios; results and both rewards were identical in every paired scenario. Each policy earned 21 points, with zero whole-seed deltas and no per-opponent regression. The Pet gate activated in zero of the 32 candidate games (`inconclusive_no_activation`). The frozen strict-gain gate and all-calls-under-1-second gate failed; the largest call was 16,369 ms in old a44, and all games still finished under native execution. Do not relabel these as timeout failures or waive the original screen. Decision: reject research promotion and do not run the conditional 256-game confirmation. The fresh explicit upload request may be fulfilled only as an operationally checked experiment, with the saved-panel/reactive distinction disclosed. The separate source-guard candidate `257f941d` is undergoing preservation and file-loader checks; it is not the exact file tested in this pilot. Root `main.py` remains exact 4ee. Evidence: `diagnostics/a44_ghost_kwa_piice_petmarket114260_reactive_20260929/RESULTS.md`; receipt SHA-256 `86d70abbf809baf29c6227141036624131856bed40b7f04664f13ba7093693c9`.

- **2026-09-29 — requested upload review found the latest a44 public rating far below the older research main.** The user explicitly requested review and one new working, stronger Kaggle upload. That authorization is still unused. A submission-list check for this request found a44 submission `56649310` COMPLETE at **1005.2**, prior 367d submission `56633591` COMPLETE at **2253.5**, and older 4ee submission `56609430` COMPLETE at **2577.6**. Do not keep describing a44 as PENDING or give it the older file's score. This is a submission-status check, not a new leaderboard snapshot. Receipt: `diagnostics/submission_review_20260929/submissions_20260929T033028Z.json`. The 96-game ebf/6a/a44 reactive pilot remains in progress and its original frozen gates remain unchanged. The complete own-submission review included every one of the 44 listed public episodes without outcome filtering: **31 wins, 13 losses, zero draws, zero ERROR/TIMEOUT/INVALID games**, all DONE/DONE at 720 frames. The validation game also completed with positive overage. Evidence: `diagnostics/submission_review_20260929/public_cohort_review.json`, which binds each downloaded replay. The low reported rating is not explained by an observed loading or timeout failure in this cohort; differing opponents and rating histories prevent a causal comparison to the older 4ee score. Decision: finish corrected-candidate preservation and native/file-loader checks before the user-requested experimental upload; do not infer an online gain or research promotion from fitted saved-panel wins. No new upload has occurred and root `main.py` remains exact 4ee.

- **2026-09-29 — 6a + Pet Cafe reached both saved win-rate goals; the strict receipt failed two stale telemetry expectations.** Candidate `ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe` is exact pasture parent `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc` plus the frozen route-113517834 Pet gate. The completed 104-run panel had 100 loss/top20 seats and two paired public-win controls. All runs finished DONE/DONE/720; all 100 panel seats had no W/D/L regressions versus exact 6a. `live-114260122` changed from loss to win in both seats at +22,524 (baseline -32,028), raising loss sweeps from 26/30 to **27/30 (90%)**. Top20 stayed **19/20 (95%)**. Both `public-win-114192390` controls remained wins, but margins fell by 21,106 and 21,699; these reductions are reported, not gated, under the frozen win-rate objective. The sole receipt failure is `public_wheat72` telemetry on both `live-114274897` seats: the historical static census expected 9,975 WHEAT, but the actual exact-6a game state was 9,980; the Pet gate correctly remained inactive and both margins exactly matched 6a (+5,983/+2,235). Target/control telemetry, including 647 active calls, passed. Thus the outcome objectives passed, but the frozen receipt is `passed: false`; this is fixed-tape evidence only and does not qualify the candidate for promotion. Decision: keep as the strongest offline win-rate candidate; before promotion, verify the corrected live-state accounting and run fresh reactive games. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; no Kaggle check/upload occurred. Candidate `ebfbe6e9`; panel SHA-256 `fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d`; receipt SHA-256 `ec2f45acfa6a7988868bb13e657a639e546ced46d148c15456e78679b0d7dcb5`; outcomes SHA-256 `bb1ae8bd2f3a9b892508ce77f101397596fd4d73868791425e6d667fb0bff97a`; baseline receipt `f5b962c853b8812f231c85af41a608e6df1b1ede99dd14c22a2bcaebb10bc8b2`. Evidence: `diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/PLAN.md` and `outcome_receipt.json`.

- **2026-09-29 — Pet Cafe route 113517834 won its target but failed the frozen diagnostic gate.** Exact parent `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`; candidate `8d97d7297f2f7c6a550b3397d98825e2a96da76c5ea060cbdf9a94defda5efb9`. All eight native runs finished DONE/DONE at frame 720. Both `live-114260122` target seats improved from -32,028 to +22,524 (delta +54,552 each). Both `public-win-114192390` controls remained wins, but margins fell from +31,142 to +10,036 (-21,106) and +9,443 (-21,699), so the frozen exact-control-preservation gate failed. All candidate gate checks passed except `active_calls`; the runner expected 648, although `fast_game_cached.play` calls policy steps 0–718 and a step-72-through-718 counter spans 647 calls. The runner receipt stores only the boolean, not the raw count, so this is a likely off-by-one and must be checked explicitly on a fresh run. The 100-panel trigger census had zero top20 hits. Decision: reject this exact diagnostic as configured; do not promote. Because both controls stayed wins and the target loss becomes a win, a separate frozen 6a-plus-Pet 100-seat experiment was run against the loss/top20 win-rate objectives; results are recorded in the next finding. This remains fixed-tape evidence, not reactive qualification. Receipt SHA-256 `19dea82c0bb20e4d496c7bd74eb3818dcea8ab3e315518968cf12c78a9553cd9`; outcomes SHA-256 `c5d85dd1b08c52da8ec66668b77d1b67a44210fc3a585e72efce0d06140a2580`; panel SHA-256 `384d20a18c34e56e0415ac26d6059531632917bb558b92d312dd1c67ec32c694`. Evidence: `diagnostics/a44_ghost_kwa_piice_petmarket114260_fourseat_diagnostic_20260929/PLAN.md` and `outcome_receipt.json`. Root `main.py` remains `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; no Kaggle check/upload occurred.

- **2026-09-29 — Luna Max static ranking staged the next Roman and Pet Cafe checks.** The latest complete frozen panel is the isolated pasture candidate `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`: 26/30 loss sweeps and 19/20 top20 sweeps, with only four of the original five loss fixtures still unresolved. Static review ranked Roman `live-114270587` as the strongest new lead: at step 1, rival hands = 3 and farmer = `[4,3]` select only its two seats in the 208-row census; nearby three-hand controls have `[4,4]`. At the time of that ranking, exact 8f post-HIRE state and market still needed a bounded check; that check passed both seats, as recorded below. The separate Pet Cafe route 113517834 plan is frozen against exact parent `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`, candidate `8d97d7297f2f7c6a550b3397d98825e2a96da76c5ea060cbdf9a94defda5efb9`, and route schedule SHA-256 `a1a8034b190fc1b2a18af82c5ac4a800f31657e7bd52600eb8a542ce35b578e8`. Its public-state gate activates on both `live-114260122` target seats and both historical `public-win-114192390` control seats, with zero triggers in top20. The control replay tape matches the archived replay’s 719 actions, but its observation traces are historical prefixes, so the paired diagnostic must verify runtime gate telemetry and exact-parent outcomes. Preflight passed; the eight-game fixed-tape diagnostic has now run and failed its strict exact-control and telemetry gates, as recorded in the finding below. Decision: keep both leads diagnostic-only; do not promote or upload. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. Evidence: `diagnostics/a44_ghost_kwa_piice_petmarket114260_fourseat_diagnostic_20260929/PLAN.md`; the independent static loss ranking is in this task’s Luna Max review.

- **2026-09-29 — Roman shared166 step-2 prefix bridge passed both seats.** Against the frozen `live-114270587` action tape, the exact V5 parent reproduced both historical seat prefixes. The adapter HIRE then matched the complete predicted own farm/private state, including the independent rival-farm and shared-market snapshots, in both seats. On fresh replays, all seat, replay, tape, opponent-action and adapter-action provenance checks passed before injection; the own-state and public merge guards passed before the donor call. The raw shared166 action remapped as expected, and the native step-2 transition credited two COW units to the intended worker slots in each seat; both game states stayed ACTIVE. Both seats passed the bounded probe. This is fixed-tape prefix evidence only, not a full-game win or reactive validation. Decision: proceed only to a small target/control outcome pilot; do not promote or upload. Root `main.py` was not read or edited, and Kaggle was not contacted. Freeze SHA-256 `c4373d03310495d2a4cdfc3c861c24345dac8dd44f0baa102aa68d68e9838214`; receipt SHA-256 `86508e558d08e4c38143c949fb6e36a56ec459a3b941f6841bc7ee510084c406`. Full evidence: `diagnostics/roman_bridge_shared166_8f_20260929/v5_prefix_probe_20260929/RESULTS.md`.

- **2026-09-29 — isolated THIRD pasture route passes top20 and reaches 26/30 losses, below the 27/30 target.**
  Candidate `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`
  completed all 100 rows against the exact V5 parent
  `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
  All games were DONE/DONE/720 with telemetry passing; both THIRD
  `live-114274897` seats changed from losses to wins (+5,983 and +2,235).
  The 98 non-trigger rows matched V5 outcomes, rewards, margins, statuses,
  frames, and prior-policy telemetry. Loss sweeps rose from 25/30 to 26/30
  (86.7%); top20 remained 19/20 (95%). Paired margin increased by 43,077
  across the two rescued seats, with the other 98 seat margins unchanged.
  Decision: keep offline, do not promote;
  at least one further both-seat loss rescue is needed. The first run stopped
  after 93 rows on a cp1252 console-print error; its partial ledger is
  preserved, and a clean 100-row retry used ASCII-escaped logs. This evidence
  is fixed-tape only, not reactive validation. Root `main.py` remains
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; no
  Kaggle check or upload occurred. Receipt SHA-256
  `f5b962c853b8812f231c85af41a608e6df1b1ede99dd14c22a2bcaeb10bc8b2`;
  full result: `diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/goalpanel_100_retry_20260929/RESULTS.md`.

- **2026-09-29 — isolated THIRD pasture route passed its focused V5 pilot.**
  Candidate `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`
  is rooted in exact V5 `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
  Across eight full fixed-tape native games, both `live-114274897` seats
  changed from losses (-17,760 and -17,099) to wins (+5,983 and +2,235).
  Both `public-win-114193811` ChrisTu controls exactly matched V5 at +1,226.
  All games completed DONE/DONE/720; telemetry passed. The narrowed public
  trigger (five rival hands and one rival pasture) matched only THIRD's two
  seats in the frozen 208-seat census; its Brunch route `113332529` ran for
  647 calls. Decision: retain for a complete saved 30-loss/top20 run, not
  promotion. This is fixed-tape evidence, not reactive validation. Root
  `main.py` remains `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`;
  no Kaggle check or upload occurred. Evidence:
  `diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/outcome_pilot/RESULTS.md`
  (receipt SHA-256
  `3df0ce00b77b635aea8318c2d5f41c608f98bb73bb50507e4b3476c6c09a9777`).

- **2026-09-29 — V5 passed top20 but remained below the loss30 goal on the full 100-seat panel.**
  Candidate `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`
  ran all 60 loss seats and all 40 top20 seats. All 100 games were clean
  DONE/DONE/720 with telemetry passing. The 98 rows outside the Civitas
  Pizza/Ice Cream trigger matched direct V4 results, rewards, margins, statuses,
  and frames exactly; both Civitas seats, both Ghost seats, and both Kwa seats
  won. The loss panel improved from V4's 24/30 to **25/30 sweeps (83.3%)**,
  still below 27/30. The top20 remained **19/20 (95%)**, meeting its 18/20
  threshold. Five loss fixtures remain: `live-114218866` (-53,956 both seats),
  `live-114223292` (-33,224 both), `live-114260122` (-32,028 both),
  `live-114270587` (-18,815 both), and `live-114274897` (-17,760/-17,099).
  Receipt SHA-256
  `c98768b1d7215e1a2adf9e455b103e391a9a338b3202773939ad8bf8f4beeb6f`; panel
  SHA-256 `97f1edb85397081d9278cc8b25be1defe018d3062e35c8ce1691ea37f3b9fb48`.
  Decision: retain for offline research, do not promote; rank the remaining five
  losses and test the next isolated lead. Root `main.py` remains SHA-256
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; no
  Kaggle check or upload occurred. Full evidence:
  `diagnostics/a44_ghost_kwa_piice_goalpanel_20260929/RESULTS.md`.

- **2026-09-29 — Ghost + Kwa + Pizza/Ice Cream passed the paired eight-seat diagnostic.**
  Candidate `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`
  appends the frozen public route `113339524` to Ghost + Kwa V4
  (`7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`).
  Both seats of Civitasmass `live-114238112` changed from V4 losses at `-8,178`
  to wins at `+1,539` (a `+9,717` margin change per seat). All six same-key
  public-win controls exactly matched direct V4 outcomes, rewards, margins,
  statuses, and 720-frame completion. All eight games and activation checks
  passed. The fresh static probe screened 208 saved seats, found only the two
  Civitas trigger seats (zero top20 triggers), and confirmed identical parent
  actions through step 143; the step-144 route edit was limited to
  `PIZZA_SHOP|ICE_CREAM_SHOP`. Receipt SHA-256
  `7d9e9ae29f420e361aec8c3d060089eb8dd969416bf2b65cb2fd23812fada14e`; panel
  SHA-256 `ecf09fbde109bc13922f16851257939923ada9f158dc4e33c2e5e6b1a0f4b247`.
  Decision: retain as a promising offline candidate and verify it on the full
  saved 30-loss/top20 panel; do not promote based on fixed tapes. Root
  `main.py` remains SHA-256
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; no
  Kaggle check or upload occurred. Full evidence:
  `diagnostics/a44_ghost_kwa_piice_combo_20260929/RESULTS.md`.

- **2026-09-29 — full Ghost + Kwa run reached 24/30 loss sweeps and missed the goal.**
  Candidate `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`
  ran both seats across all 30 frozen loss fixtures: 60/60 clean DONE/DONE/720,
  all telemetry passed, all four target seats won, and 56/56 controls exactly
  matched 6d. The result is **24/30 (80%)**, up from 22/30 for exact 6d, below
  the 27/30 goal; top20 remains **19/20 (95%)** from the same candidate’s
  hash-bound prior receipt. Six losses remain: `live-114218866`,
  `live-114223292`, `live-114238112`, `live-114260122`, `live-114270587`,
  `live-114274897`; three more both-seat rescues are needed. Keep this as an
  offline base, not a promotion. The best isolated lead is Civitasmass
  `live-114238112`, using the fresh eight-game target/control plan at
  `diagnostics/a44_pizza_icecream_pair_20260929/PLAN.md`; the earlier route
  screen used a different turn-79 wheat quantity, so its win is only a
  hypothesis. The 6d baseline’s reused rows have a provenance caveat described
  in `diagnostics/a44_ghost_kwa_goalpanel_20260929/RESULTS.md`. Root `main.py`
  remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`;
  no Kaggle check, download, or upload occurred.

- **2026-09-29 — Ghost + Kwa composition passed its 58-game fixed-tape panel.**
  Candidate `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`
  passed 58/58 clean DONE/DONE/720 games, all telemetry, all four target wins,
  and 54/54 exact 6d controls. It retained 19/20 top-team both-seat sweeps
  (95%, the 6d baseline) and changed the six selected `loss30`-tagged rows
  from four to six both-seat sweeps by rescuing Kwa (`live-114227779`) and
  Ghost (`live-114288168`). The full 30-loss panel was not run; 24/30 is only
  a projection from the 22/30 6d baseline plus these two rescues, below the
  27/30 goal. Keep as an offline experimental composition. The full loss30
  follow-up is recorded above; no reactive qualification or promotion follows
  from fixed tapes. Root `main.py` remains SHA-256
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`, and
  Kaggle was not checked or changed. Full evidence and audit caveats:
  `diagnostics/a44_ghost_kwa_combo_20260929/RESULTS.md`.

- **2026-09-29 04:22 IST — Pasture guard + Brunch route candidate rejected on its frozen outcome gate.** Candidate `5b4ef52d19cb8ffb310b2bb067c725810241668667a0b5b468ac09b6b9215506` won both `live-114274897` fixed-tape seats (+5,983 and +2,235 versus 6d losses -17,760 and -17,099), but it also changed both `public-win-114193811` controls from margin +1,226 to +8,353. The derivative changed the step-1 bridge selector globally: `shared151` now required zero rival pastures, so all four jobs selected `source` while exact 6d selected `shared151`. The later Brunch leaf was inactive on ChrisTu, but its earlier branch change had already altered play; the target wins cannot be attributed to the leaf. All four games were clean DONE/DONE/720; exact controls and overall gates failed. Preserve as descriptive fixed-tape evidence, reject for promotion, and do not count as an isolated Brunch rescue. Receipt SHA-256 `0c7ecfbc89a0110c7aa18796ce2d814643262d6589c412fedf5e8016c302a1ec`; ledger SHA-256 `83598f5fea57693e9202bcf8b061f5f05e1dd44d922eddcdf81d21a846b9a468`. Full failure analysis: `diagnostics/a44_goose4_smoothie_pasture_source_20260929/RESULTS.md`.

- **2026-09-29 04:08 IST — Ghost Ice wheat route passed its corrected 12-game fixed-tape panel.** Candidate `228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767` derives from exact 6d parent `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`. On source bridge step 72, it selects route `113360743` for `ICE_CREAM_SHOP|M8+|C>S|G0` only when public WHEAT stock is at most 9,975. Both seats of `live-114288168` now win at +1,298; the 6d margins were -2,253 and +1,425. All ten non-trigger controls exactly matched 6d results, rewards, and margins; all 12 games were DONE/DONE at 720 frames with telemetry and zero candidate errors. The 208-seat static census found only the target pair activates, so the standalone Ghost derivative moves the saved 6d loss30 sweep count from 22/30 to 23/30; top20 stays 19/20 and public-win stays 53/54. The earlier 11/12 runner attempt is preserved but excluded because its telemetry checker read the panel row; the new V2 package passed synthetic positive/negative telemetry checks and all 50 frozen hashes. Receipt `diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/outcome_run_v2_20260929/run_receipt.json` SHA-256 `510339d20aace4317f7dfc4330b7a8f4e59d1edcc5fd458f474fdefb3c702f8`; result ledger SHA-256 `a060e1441ee0ac37e8e83c3e81203797fecc78ad0d306e27ca98a21cbcf6831c`. Decision: keep as a promising separate patch, but do not promote; this is fixed-tape evidence only. Next, compose and validate it with the separate Kwa rescue before estimating a combined panel. Root `main.py` stays at SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; no Kaggle access occurred.

- **2026-09-28 21:58 UTC — Kwa wheat-zero route splice passed its frozen
  six-game fixed-replay diagnostic.** Candidate
  `36f1a351c4b85b62d7c5fb07489927821d98823c57d0e7131e19eb186951a54e`,
  derived from exact local 6d parent `6d3d1c0d…`, changed only the step-72
  source-branch BRUNCH route when rival WHEAT plots were zero. Both seats of
  `live-114227779` won at +4,118 margin, improving the hash-bound 6d combined
  result by +7,976 per seat. Four wheat-positive control seats matched the
  6d combined receipt exactly; all six games were clean and every frozen gate
  passed. The integrated saved panel moves from 22/30 to 23/30 loss sweeps,
  while top20 stays 19/20 and public wins stay 53/54. Decision: retain as a
  promising narrow candidate and proceed to reactive native qualification;
  do not promote to `main.py` because this run used fixed tapes. Full evidence,
  run receipt, and hashes are in
  `diagnostics/a44_kwa_wheat_zero_20260929/RESULTS.md`. Root `main.py` and
  Kaggle status were not changed or checked.

- **2026-09-28 ~21:50 UTC — Civitasmass step-72 selector rejected without a
  game test.** Its full step-72 public state matches the winning
  `public-win-114288078` control, so a stateless route selector cannot isolate
  it. Routes `113332529` and `113339524` have older-parent replay rescues but
  regress same-key winning controls. A historical WHEAT inventory of 9,984
  isolates the two target seats in the saved corpus, but differs from controls
  by only 1–3 units at unchanged price 30; this looks like a replay fingerprint,
  not an economic trigger. See
  `diagnostics/production_leaf_selector_20260928/RESULTS.md` and
  `diagnostics/production_pair_continuations_20260928/RESULTS.md`.

- **2026-09-28 18:22 UTC — exact a44c8c2c uploaded by fresh request.**
  The user asked, "upload the current updated main.py to the kaggle please".
  This authorization was consumed by submission **56649310**, named
  **main.py**, at **18:22:44 UTC / 23:52:44 IST**. The listing verified
  PENDING at 18:22:46 UTC; no score was available. Exact a44c8c2c wins
  19/20 top-team and 17/30 public-loss saved fixtures in both seats.
  All eight native direct/file-loader games passed, including all 719
  actions for both players, rewards, telemetry, timing and entrypoint.
  Operational receipt SHA:
  `40384781e30ba377e4d1d5268a689cac9e6acc56fdfc7c1de4cc058ab4d83dc9`.
  Its uploaded copy is
  `diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py`; the identical
  root-folder backup is preserved. This explicitly requested experimental
  upload does not establish research promotion: broader public preservation
  and reacting qualification are incomplete. Root main remains 4ee for
  active hash-bound studies. `upload_receipt.json` records one successful
  attempt. Any additional upload needs a fresh explicit user request.
  Only submission listings were read; the leaderboard/replays remain frozen.

- **2026-09-28 16:19 UTC — user clarified the offline priority order.**
  First reach at least **18/20 (90%)** of the latest downloaded top-team
  fixtures, then **27/30 (90%)** of the frozen public-loss fixtures, counting
  a fixture only when both seats win. After those thresholds, seek larger
  paired cash margins for each opponent while preserving wins. Continue
  using the local corpus; no Kaggle checks or downloads. Exact uploaded
  367d2e76 currently has 19/20 and 13/30, so the first saved-panel threshold
  is met and fourteen more public-loss sweeps are needed for the second.
  The frozen 30 losses were originally recorded from 4ee; they are not a
  newly downloaded loss cohort from submission 56633591. See the hash-bound
  baseline ledger in `diagnostics/goal90_20260928/BASELINE.json` and its
  readable `BASELINE.md`. Independent promotion requirements remain.

- **2026-09-28 07:35 UTC — exact 367d2e76 uploaded by fresh request.**
  The user's request to upload the new changed main.py authorized one
  combined observed-hire recovery upload. It was consumed by submission
  **56633591**, named **main.py**, at **07:35:56 UTC / 13:05:56 IST**.
  Kaggle listing verified PENDING at 07:35:59 UTC; no score was available.
  All 200 saved-panel games and eight operational file-loader games passed
  first. Candidate 367d2e76 wins 13/30 saved public-loss fixtures and 19/20
  saved top-team fixtures in both seats, retaining prior winning seats.
  This is an explicitly requested experimental upload; reacting
  qualification is incomplete. Root main remains the exact 4ee research
  baseline, while the uploaded copy is
  `diagnostics/upload_hire_recovery_20260928_367d2e76/main.py`.
  Only submission listings were read. The frozen leaderboard/replay corpus
  is unchanged. The receipt records one successful attempt; do not repeat
  it. Any additional upload requires a fresh explicit user request.

- **2026-09-28 03:54 UTC — exact 06803086 uploaded by explicit request.**
  The user's annotation “upload it to online”, followed by “to kaggle
  submissions”, authorized one upload of the backed-up partial-planting
  candidate. That authorization was consumed by **56628152**. Both-seat
  file-loader parity passed first. Reacting qualification is incomplete,
  so this is an experimental submission, not a research-qualified
  promotion. Local main remains 4ee. Only submission listings were read;
  the frozen leaderboard/replay corpus is unchanged. Any additional
  upload requires another fresh explicit request.

- **2026-09-28 01:54 UTC — one explicit experimental upload completed.**
  The user's annotation on “New candidate”, “can you please upload it to
  the kaggle please”, authorized the exact root-folder fb6c5413 candidate.
  This authorization was consumed by submission **56625741**. The later
  native rejection was disclosed before uploading. This was a user-requested
  experimental submission, not a research-qualified promotion. Main remains
  4ee as the local research baseline. Only the submission listing was read
  to verify the upload; the leaderboard and replay corpus were not refreshed.
  Any further upload requires another fresh explicit request.

- **2026-09-27 ~18:20 UTC — user froze the local evaluation corpus.** Do not
  check Kaggle or download further episodes/leaderboard data. Focus on the 30
  losses in the saved `cohort_180951.json` from uploaded 4ee and the already
  downloaded current top-20 panel in
  `diagnostics/current_top20_20260927_172258/`. Count both-seat wins against
  those recorded replies; use separate local reactive native games to guard
  against overfitting fixed action tapes. No further upload is authorized.

- **2026-09-27 01:46 UTC — crop conversion feasibility rejected.** Filtering
  the passive crop audit by maturity and the actual replacement coordinates
  leaves usable three-command windows on only four of eight early plots in
  each BAKERY/PET case, and none of the two PET/PET plots. Melons require a
  different subsequent watering and harvest chain before the scheduled field
  conversion. No candidate or strength test was run. Preserve the audit;
  next test the concrete missed-cow procurement failure under the separate
  frozen `diagnostics/shunki_procurement_repair_20260927/PLAN.md`. Main remains
  3cc, 42/50 sweeps. See `diagnostics/shunki_crop_demand_20260927/RESULTS.md`.

- The user updated the active objective on 2026-09-27 to win all **50**
  current top-team replay matchups and reach the live top 10. Download a
  fresh top-50 panel and report both route wins and both-seat wins. Older
  top-100 results remain historical research evidence. The latest user
  instruction also explicitly asks to check the **fresh current top 100**,
  not yesterday's downloads; the latest11:37UTC snapshot completed testing
  at11:55UTC with73/99 external both-seat sweeps and146/198 external wins.
  Our rank98 entry is a separate self-control. The morning07:27 panel
  remains77/100. Keep the original50 regression objective and report the
  fresh current100 separately. See
  `diagnostics/current_top100_20260927_1137/RESULTS.md`,
  `diagnostics/current_top100_20260927_0730/RESULTS.md` and
  `diagnostics/top50_refresh_20260927_2303/PLAN.md`.
- Optimize `main.py` for the live Kaggriculture 30-day / 720-turn competition.
  Winning means more final bank coins than the opponent, not merely higher
  production. All possible opponent policies cannot be exhaustively proven.
- **Every upload requires a fresh explicit user request.** The earlier
  authorizations were consumed by submissions 56529771, 56530281, 56547116,
  56568576, 56569042 and 56572390. The user's renewed 2026-09-27 request
  explicitly allows deploying a new `main.py` if needed to pursue the goal.
  That conditional authorization was consumed by submission **56591314**
  at 2026-09-26 23:38:58 UTC. The newer explicit approval to promote and
  upload c68fa46f was consumed by **56602057** at 2026-09-27 07:25:37 UTC.
  The user's subsequent request, "please check and update it also please",
  authorized ONE new upload of a qualified update. This authorization was
  consumed by **56609430** at2026-09-27 13:10:15UTC. Any further upload
  requires another fresh explicit request. The preceding conditional
  request to upload if not already uploaded did not trigger a duplicatec68.
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

- **2026-09-29 08:11 UTC — exact ae349d83 re-uploaded once on a fresh explicit request.** The user's annotation, "can you upload the file again please", authorized a new upload of the same tested file. Kaggle accepted **56668607**, `main.py`, at **08:11:57 UTC / 13:41:57 IST**; the listing verified PENDING with no score at 08:11:59 UTC. SHA-256 remains `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`; this repeats 56666114 without strategy changes. The exact source and seven pilot/saved/reactive/loader evidence files were reverified before the one-shot upload. This fresh authorization is consumed. Decision: fulfill the requested experimental repeat; no research promotion, new test results, claimed queue fix, or score/rank improvement. Root research `main.py` remains exact `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. Package and receipt: `diagnostics/reupload_pizza_guard_20260929_ae349d83/main.py` and `upload_receipt.json`; before/after submission listings and uploader provenance are in the same folder. Prior upload receipts remain preserved. Leaderboard and replays were not refreshed.

- **2026-09-29 07:43 UTC — pending-upload diagnosis, read-only.** At the user's request to explain the hour-long spinner, the authenticated SDK confirmed submission **56666114** is still PENDING, 48.1 minutes after its 06:55:03 UTC upload. Its `error_description` and public score are empty; server `total_bytes` and the exact local uploaded file both equal 2,025,599. The episode endpoint at 07:41:43 UTC returned `No episodes found` (the CLI's empty-list message, not an agent failure). The competition's evaluation documentation says a self-play validation episode precedes entry into matchmaking and failed validation is marked Error. Current evidence supports an unfinished server validation/evaluation process; it does not expose the exact queue/worker cause, establish an outage, or prove online execution has succeeded. No resubmission or code change was made. Latest detailed receipt: `diagnostics/upload_pizza_guard_20260929_ae349d83/status_details_20260929T074312Z.json`; listing/episode response: `status_20260929T074143Z.json` in the same package. The list also now reports previous 257f submission 56662188 COMPLETE at 1259.3; do not attribute that score to ae349d83. Leaderboard was not refreshed.

- **2026-09-29 06:55 UTC — latest submitted file is ae349d83; research main remains 4ee.** Submission **56666114** is PENDING with no score as last checked at 06:55:10 UTC. Exact standalone upload: `diagnostics/upload_pizza_guard_20260929_ae349d83/main.py`, matching `main_candidate_improved_20260929.py` (SHA-256 `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`). Receipt and listing are in that package. Prior uploaded257 is backed up as `main_uploaded_backup_257f941d_20260929.py`; its original submission was 56662188. Root `main.py` remains SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`, backed up as `main_before_candidate_4eeac9c3_20260929.py`. The new file passed the saved regression panel and all eight native/file-loader checks. Saved loss/top20 sweeps remain **27/30 and 19/20**, with narrower Pensukesan losses. Fresh reacting comparison was **8W/14D/2L**, identical to uploaded257, so research promotion remains rejected. This explicitly requested experimental upload is complete; another upload needs another explicit user request. Leaderboard/top20 were not refreshed.

- **2026-09-29 03:16 IST — do not transplant the pasture leaf from saved 6d features alone.**
  The 208-row census finds exactly four branch changes under the pasture
  guard: both seats of THIRD and ChrisTu move from `shared151` to `source`;
  only THIRD's saved shared151 rows show the Brunch-goose key. Those rows do
  not reveal the step72 state after switching to source, and the passed v6
  prefix belongs to a different cb5/a44-based policy. The direct 6d port is
  therefore paused before candidate creation. Next evidence is a four-seat
  source-branch prefix from the exact 6d Goose4+Smoothie policy; only then
  decide whether the Brunch leaf is supported. No full games or main change.

- **2026-09-29 03:04 IST — pasture v6 source prefixes pass after a telemetry-harness correction.**
  V6 preserves the failed v5 receipt and changes only the telemetry
  bookkeeping: it removes the complete fixed set of candidate-only bridge
  and leaf fields from the shared-core equality, checks those fields
  separately, and records any remaining shared-value mismatch. The
  fourteen-row receipt passes: ten hash-bound v3 donor rows and four fresh
  exact-a44 source prefixes. Both THIRD seats match observations through72
  and differ only in the intended step72 Brunch route; both ChrisTu seats
  match actions through72 with the leaf inactive. All error ledgers are
  empty. Root verified all534 manifest bindings. This is a prefix result,
  not a terminal outcome; no full game is counted and the candidate is not
  promoted. A separate derivative from current 6d + Smoothie is being
  prepared for the affected fixtures before any outcome pilot. Candidate SHA
  `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`;
  runner SHA `18692b763631326e228f712e04fbddadaefc460522152e246b3c400d6ffd098f`;
  result SHA `5e445fbcb87455a2ca0137f9005b978aa4fe9a251cc9fd465a77e4fa6afef3b4`.
  Review: `diagnostics/pasture_guard_source_leaf_20260928/PREFIX_V6_RESULTS_REVIEW.md`.
  Root main remains4ee; no Kaggle check, download, or upload.

- **2026-09-29 03:04 IST — narrow Ghost Ice wheat gate remains a test proposal.**
  Root rechecked all16 evidence input hashes and the208 feature rows. The
  public rule `source + ICE_CREAM_SHOP|M8+|C>S|G0 + WHEAT<=9975` matches only
  both seats of `live-114288168`, with zero top20/public triggers; ten other
  seats share the coarse Ice key and remain inactive. Its earlier +1,298
  route result came from a different exact367 parent, so it is not a measured
  6d result. A successful Ghost sweep could add at most one, taking22/30 to
  23/30. Keep as a replay-trained hypothesis; a separate exact-6d derivative
  and no-op preflight are in progress. No games, promotion, or main.py edits.
  Evidence: `diagnostics/residual_ice_wheat_gate_20260929/PROPOSAL.md` and
  `evidence.json`.

- **2026-09-29 02:49 IST — pasture v5 completed, but its receipt failed one harness gate.**
  The runner completed four fresh exact-a44 source prefixes plus ten hash-
  bound reused donor rows. The receipt is complete but `passed:false`; all
  four fresh rows fail only `intended_bridge_and_leaf_telemetry_only_gate`.
  Observations match through step72; actions match through step71, with only
  the intended THIRD step72 route difference. ChrisTu remains inactive, and
  all error ledgers are empty. Root rechecked all528 manifest bindings.
  Static code review found the telemetry comparator leaves candidate-only
  bridge fields in its shared-core comparison even though the direct source
  reference does not expose them and the bridge fields are separately gated.
  Preserve v5 as failed; do not override its receipt or launch full games.
  A separately versioned v6 harness correction is under review. Candidate
  SHA `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`;
  v5 runner SHA `6f30dfd2449a5f558cbb3fa6634725d8c2ef2201b94cade81dc90213f9f81b09`;
  receipt SHA `a670041c00631067b35ab8967984260ce5a2995444537b8651681b9a01d87cc4`.
  Review: `diagnostics/pasture_guard_source_leaf_20260928/PREFIX_V5_RESULTS_REVIEW.md`.
  No complete-game outcomes, main.py changes, Kaggle checks or uploads.

- **2026-09-29 02:23 IST — pasture prefix v4 did not pass its frozen gate.**
  The complete14-row receipt reuses10 previously passing donor prefixes and
  runs four fresh exact-a44 source-branch prefixes. All four candidate/source
  pairs match full observations0–72; actions match0–71, with only the intended
  THIRD step72 action difference. The THIRD leaf key and route match, ChrisTu
  stays inactive, and error ledgers are empty. V4 nevertheless records
  `passed:false`: the direct source function produced an empty reference
  telemetry mapping, and its ChrisTu runtime key was compared with a feature
  row from the a44 outer `shared151` path. Preserve this as a failed receipt;
  **do not start the full-game pilot** until a separate frozen adjudicator
  corrects these evidence gates without relaxing state/action requirements.
  Runner SHA `7b666235d813c37102f35abce559ff83f7212fd3f1bcfddd297cc7531fc1c407`;
  result SHA `33b594d4042a4db4c59fd5d7eee5c9940ffcf7e35d918e48289c81ec285ae416`.
  Review: `diagnostics/pasture_guard_source_leaf_20260928/PREFIX_V4_RESULTS_REVIEW.md`.
  No complete-game outcome, main.py change, Kaggle check or upload.

- **2026-09-29 02:17 IST — Goose4 + Smoothie repairs one further frozen
  loss sweep.** The exact-a44-bound integration completes its 12 affected
  seat games DONE/DONE/720 with zero policy errors and expected activation;
  the other196 seats are reused only after the static decision-equivalence
  proof. Across the combined frozen panel it reaches22/30 loss sweeps and
  45/60 wins versus a44's17/30 and34/60, with five total rescues and no
  source-winning fixture regressions. Top20 remains19/20; public-win remains
  53/54. Compared with Goose4 alone, Smoothie adds one sweep and two wins.
  Keep as a separate candidate; **reject promotion for now** because it is
  fixed-tape evidence, still five sweeps short of27/30, and lacks reacting
  validation. Candidate SHA `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`;
  combined result SHA `5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d`.
  Detailed evidence: `diagnostics/a44_goose4_smoothie_source_20260929/RESULTS.md`.
  Root main remains4ee; no Kaggle check, download or upload occurred.

- **2026-09-29 01:40 IST — a44-bound Goose four-leaf selector gains four
  frozen loss sweeps but misses the 90% gate.** All208 candidate games are
  clean. On the frozen loss30 panel it reaches21/30 two-seat sweeps and
  43/60 wins, versus a44's17/30 and34/60: four full rescues plus a one-seat
  repair on Ghost Rule114288168. It loses no prior sweep. The public-win
  panel remains53/54 with no result changes; top20 remains19/20 unchanged.
  Reject for promotion because it is six loss sweeps short of27/30, and the
  evidence uses fixed tapes only. The runner's post-game gate initially
  stopped because 20 route IDs were integer/string mismatches; a separately
  hashed read-only audit confirms all208 activations after scalar
  normalization and leaves original rows untouched. Candidate SHA
  `c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632`;
  audit SHA `64876242941a2e538224791e1f9dc9b6133fb10e8cc3725d8a6cf188f3fc5a3b`.
  Full evidence: `diagnostics/a44_source_bridge_goose_4leaf_20260929/RESULTS.md`.
  Root `main.py` remains4ee; no Kaggle status check or upload occurred.

- **2026-09-29 01:43 IST — pasture prefix harness aborted before a proof job.**
  The frozen 14-job prefix runner hit `IndexError` while forming first-shop
  telemetry at observation1, where the fixture correctly had no unlocked
  shop yet. The progress ledger remains empty and no 72-step prefix result
  was written. The policy/candidate and original manifest were not changed.
  Preserve the failed attempt and use a separately hash-bound runner version
  that represents the pre-shop state safely; rerun static verification before
  any prefix jobs. No full-game outcome pilot ran. Evidence and follow-up:
  `diagnostics/pasture_guard_source_leaf_20260928/`.

- **2026-09-29 01:55 IST — pasture prefix v3 exposes a wrong fallback comparator.**
  All14 jobs completed (1,008 native transitions), with10/10 donor-vs-a44
  controls passing and zero policy/guard errors. The four target/fallback
  jobs fail because v3 compares the candidate's exact-a44 `source` branch
  against different `32e` turn-0/turn-1 actions. THIRD activates the intended
  `BRUNCH_SPOT|M8+|C>S|G+ -> 113332529` leaf; ChrisTu stays on source and
  leaves its key inactive, but those checks were also bound to the wrong
  reference context. **Do not treat this as candidate outcome evidence or
  start the full-game pilot.** Freeze v4 against exact a44, allow only the
  intended THIRD action at step72, and preserve the v3 ledger unchanged.
  Result receipt SHA `2689b164e553660a61e08d116c2d9c955acce6e332fe088754f1e10039acdba4`;
  analysis: `diagnostics/pasture_guard_source_leaf_20260928/PREFIX_V3_RESULTS_REVIEW.md`.

- **2026-09-29 00:47 IST — observed-hire native pilot rejected under its
  frozen early-stop gate.** The original 512-game pilot ended at499/512 with
  all499 unique games clean. Neither recovery arm activated; only one
  distinct seed remained possible, below the required two, so the runner
  correctly cancelled the last13 jobs. `repair_main` (467a9dfe) scored
  89/124 win points against4ee versus the control's90/126, with zero paired
  margin change and no activation. `repair_integrated` (367d2e76) scored
  87/124 versus90/126, lost two market-reference games relative to control,
  and reduced paired margin by83,918 coins across124 matched games. Both
  fail activation and win gates; no confirmation or promotion. Summary SHA
  `016d7b42da754471a824c13d792e748a23e872c5081f755bc574f882f5f8c86b`,
  game-ledger SHA
  `1c1ea7249f0d705e4e1b0d28d52bff3b3c92f6f11cff741601ad44b56d76d450`.
  See `diagnostics/observed_hire_recovery_20260928/RESULTS.md`.

- **2026-09-29 00:14 IST — Goose production selector completes.**
  The frozen exact367 source arm `production_goose` finishes200/200 clean
  target games, 18/30 public-loss and19/20 top-team both-seat wins. It
  rescues Ebi114229792, Dieter114249897, keiz114258293, kibuna114267572 and
  THIRD114274897 while retaining the old source's target wins. It has
  a44-specific losses on booming114232208, mhw114235177, booming114279308
  and Yaroslav114283577, so a straight replacement yields only one net
  sweep over a44. **Keep as a promising selector; do not promote.** It needs
  a public-state merge against exacta44 and full public/reacting checks.
  Full receipt SHA `c3fbc3fc8c0243701db15d0abd596b63a93109267cce16e34753e1659c3c2506`;
  selected file SHA `5c97b54905274914a63a05d8eee5830754ea5f3bbb8e055db04ec6efa0d39ae3`.
  The56 source public-win controls cover only affected fixtures, not the
  whole public54 panel. Saved tapes are development evidence. See
  `diagnostics/production_leaf_selector_20260928/RESULTS.md`.

- **2026-09-29 00:14 IST — Smoothie second-shop screen completes.**
  All132 frozen cases finish cleanly; the first-shop Smoothie/M8+/cow-heavy
  leaf has a preserving continuation for every observed second shop and
  retains its target rescue. Selected routes are in
  `diagnostics/smoothie_pair_continuations_20260928/selection.json`;
  candidate SHA `b4af93f784800d309cf64475ec91eed0c4ad5e009f3140f6d3894dec6ff6f768`,
  screen SHA `221fcab550707148908fa8678c93b62da9b31fd28751266dff30282c687f8519`.
  This uses exact367 source features/outcomes; it has not been integrated
  with a44 or checked against a44's unique wins. **Advance to a44-bound
  integration/regression work; no promotion yet.**

- **2026-09-29 — pasture guard preflight found missing implementation.**
  a44 source hash and the source-only Brunch leaf wiring check out, but the
  pasture count helper is unused, the step1 shared151 predicate is unchanged,
  and no a44-bound builder,208 feature rows, candidate, pool, controls or
  preflight receipt existed. No outcome games ran. The fixed pilot is not
  ready until those bindings/checks are built and frozen. See
  `diagnostics/pasture_guard_source_leaf_20260928/STATIC_AUDIT.md`.

- **2026-09-29 01:17 IST — live offline work.** Exact a44 remains the latest
  uploaded artifact, 19/20+17/30 on frozen tapes; the next goal still needs
  ten more public-loss sweeps while preserving at least18/20 top sweeps.
  The older reacting hire-recovery pilot is terminal/rejected at499/512.
  The a44-bound Goose candidate passed its 450-artifact static manifest
  check and all108 a44 public controls completed cleanly at106W/0D/2L
  (53/54 both-seat sweeps). The candidate phase is at29/208; early triggered
  target losses remain losses so far, while the first fixture won in both
  seats. The Luna-max pasture candidate and its 14-job native-prefix manifest
  passed static checks; the prefix run is queued until Goose releases the
  simulator. Smoothie132 is
  complete. No Kaggle checks/downloads/uploads have occurred since the user's
  no-Kaggle instruction.

- **2026-09-28 18:22 UTC — current submitted artifact is a44c8c2c.**
  Submission56649310 is PENDING; no new score or rank is known. Root main
  remains4ee for running research. The backed-up submitted standalone file
  and eight-game operational receipt are in
  `diagnostics/upload_adaptive_donor_20260928_a44c8c2c/`. Experimental upload
  authorized by the user's fresh request; no research promotion inferred.

- **2026-09-28 — PET/Pizza second-shop continuation repair rejected.**
  All264 frozen cases completed cleanly after eight exact-prefix proofs.
  Neither early production family has a compatible continuation for every
  affected shop pair that retains all source367 winning seats. Selected
  families are empty, despite target rescues. Keep source behavior; no
  candidate promotion. See `diagnostics/production_pair_continuations_20260928/selection.json`.
  Screen SHA `37fdfe4cdd4daf99e79bce2f0c573a9cf1b99ada704a8d24b16a6ba751085f62`.

- **2026-09-28 — Ice finalists rejected on all42 frozen controls.**
  Routes113384557/113801171 achieve4/7 sweeps but lose keiz and four public
  winning seats;113360743 achieves5/7, rescues Ghost and keiz, but loses
  four public winning seats. All42 games clean, all six Ghost results match
  the immutable910 screen. No selected finalist; preserve source.
  See `diagnostics/ice_finalist_controls_20260928/RESULTS.md`, receipt
  `b15df5fad00d825ac9bc683db120a38c7847852e40700ad0410eab2091f05b2e`.

- **2026-09-28 — Third donor pair repair rejected.**
  All three prefix-compatible alternative BRUNCH/PIZZA continuations lose
  both seats; none rescues live114274897. Public54 prefix discovery found
  no affected pair contexts. No selected combined candidate; preservea44.
  See `diagnostics/adaptive_third_pair_repair_20260928/`, screen receipt
  `7dd95c02468e14c2d1fec9e1da0f62825c35863b5bf5660c12cfc272aee34749`.
  A separate opening audit found Third has one visible rival pasture at
  observation1 while five successful donor151 fixtures have zero. That
  observable distinction is a new development lead, not a proven win.

- **2026-09-28 — full8ccb public preservation result: reject.**
  All108 candidate games completed cleanly:89W/19L,44/54 sweeps versus
  exact367's108W,54/54. Nineteen source-winning seats are lost across ten
  fixtures; combined target100+public108 win count falls from172 to163.
  Policy regressions, not execution errors. Preserve its backup as rejected
  research; it was not uploaded under the current request. Receipt:
  `diagnostics/public_90_research_20260928/public_candidate.json`, SHA
  `8ae8e538cefeaed3253b6eb11a7c997dabdc8fc9f29bdc49011a8bd1d00c8f2e`.

- **2026-09-28 — broader8ccb preservation gate fails on completed rows.**
  All108 exact367 public controls win,54/54 sweeps; their receipt is
  `261291b2638314629e15050041c8b354503327b087311425dc56e778d6198dae`.
  Exact8ccb's ongoing108-case public test has already lost ChrisTu114193811
  in both seats (+8,353 source to-1,758) and Sakura114199617 (-12,892).
  **Reject broader-win preservation; complete/report the frozen remaining
  cases without changing the file or gate.** Its18/30 and19/20 saved-target
  counts and32-case framework parity remain valid but do not earn promotion.
  Production-leaf/compatible-continuation studies are separate repairs.

- **2026-09-28 — full91-route expansion finishes910 clean cases.**
  Bakerybooming114232208 has one winning schedule,113349962(+3,006 both).
  IceGhost114288168 has six; frozen finalists113384557/113360743/113801171
  have worst-seat margins+1,406/+1,298/+844. Roman, PizzaPens and Smoothie
  Fish have no rescue among91 schedules each. **Advance the finalists to
  affected controls; reject that finite pool for the three unresolved
  cases.** These are810 new plus100 reused development outcomes, not
  independent games. Bakery overlaps a44c's existing rescue. No combined
  count changes. Receipt SHA:
  `efab80fb79d112082ade79dea84acac0c872e383aaade2de0abdaa6a211b80b7`.
  See `diagnostics/residual_91_routes_20260928/RESULTS.md`.
  Its two workers are released; the frozen264-case PET/Pizza continuation
  screen is now active in session25419. The separate132-case Smoothie
  pool passes four prefix comparisons and remains queued.

- **2026-09-28 — original-framework parity confirms8ccb's five rescues.**
  All16 changed target fixtures in both seats (32 games) match the complete
  fast receipt exactly in own/rival rewards, result, frames, statuses and
  full telemetry. DONE/DONE/720, zero errors and no lost source-winning
  seat. **Pass execution parity; advance to the frozen54-public-win
  regression, not promotion.** This is not reacting or file-loader evidence.
  Parity SHA: `f21fe4f09427681794ea6efa40139d32a1398f607e642eab779112f27b67c600`.
  See `diagnostics/public_90_research_20260928/native_parity.json`.

- **2026-09-28 — compatible second-shop repair pools frozen.**
  Two production leaves rescue Ghost114260122/Civitasmass but regress
  public controls. Their rival72 aggregate portfolios coincide with some
  controls. A new264-game pool tests10/13 exact144-prefix-compatible
  continuations over all8/4 affected fixtures, both seats. Eight short
  prefix pairs reproduce144 actions/145 observations exactly. **Advance
  to its frozen member screen after the91-route screen frees workers.**
  Pool SHA: `3002fbca7152cf84bab637e4899a13efec2f1c0fa785cac6bb362bb697827344`.
  Prefix SHA: `a7bd8698e59c0c63354e7bef98c2238d2cbc5f0a1519dbaf81d819c83ed6bdb8`.
  See `diagnostics/production_pair_continuations_20260928/PLAN.md`.
  A separate132-game Smoothie pool targets the same mechanism: the
  forever-young rescue and yfy regression share identical72 counts.
  Both plans reject the entire early leaf if any observed shop pair lacks
  a continuation preserving all exact source-winning seats. No promotion.

- **2026-09-28 17:58 UTC — adaptive donor-pair repair full panel passes.**
  Exacta44c8c2c finishes100 fast-transition rows (24 verified pilot reuses,
  76 new), all clean. It wins19/20 top-team and17/30 public-loss fixtures
  in both seats,72W/0D/28L. It preserves all66 exact32e winning seats and
  all16 known ceed winning seats within ceed's24-seat pilot scope. Three
  new rescues versus32e are booming114232208, mhw114235177 and
  booming114279308. **Advance for broader controls and compatible
  integration; not research promotion.** Among its13 remaining public
  failures, only THIRD114274897 uses donor151 (BRUNCH_SPOT|PIZZA_SHOP), so
  appending a source-only production leaf would not fix that fixture.
  Receipt SHA: `ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732`.
  Backup:`main_candidate_adaptive_donor_pair_repair_20260928_a44c8c2c.py`.
  See `diagnostics/adaptive_donor_pair_repair_20260928/FULL_RESULTS.md`.

- **2026-09-28 — exact8ccb combined saved-target panel passes.**
  All100 fast native-transition games finish cleanly:18/30 public-loss and
  19/20 top-team both-seat wins,74W/0D/26L. Every64 exact367 winning seat
  remains a win. New rescues are Civitasmass114238112, keiz114258293,
  Ghost114260122, kibuna114267572 and Yaroslav114283577. Total paired margin
  rises29,241 across100 seats. **Advance to original-framework parity and
  the54-public-win regression panel; no research promotion yet.**
  Root backup `main_candidate_early_public_8ccb862a.py` is unchanged.
  Full receipt SHA: `330ab7523ed226366838283a46cb6689c19aca85d9988855390b65297de7743a`.
  This receipt excludes original-framework/schema/timeout/file-loader
  checks and independent reacting opponents. See
  `diagnostics/public_90_research_20260928/combined_full.json`.

- **2026-09-28 — final-day timing repairs one narrow development loss.**
  Three frozen horizons/six games on ICE113332529 versus Ghost114288168
  all finish cleanly. Horizon18 sells15 existing milk/strawberry units at
  step700: own+45, rival-14, margin-21 to+38 in both seats. Horizons12/6
  lose and are rejected. All719 physical actions/farms/bags/seeds match
  the control. **Retain horizon18 as a lead pending affected controls;
  no promotion or combined-count increase.** The full91-route screen may
  provide a stronger route for the same fixture. See
  `diagnostics/terminal_sale_timing_20260928/RESULTS.md`.
  Screen SHA: `cab187b6453ed827d6ff588bc800528b95c96948b0e285814ad4cbcf67c243f0`.

- **2026-09-28 — donor-pair repair passes its separate24-seat pilot.**
  Exacta44c8c2c wins10/12 both-seat fixtures, retaining all32e and known
  ceed winning seats. Compatible donor151 route2 fixes Boey at+10,714 and
  booming114279308 at+3,298/+2,542; prior booming114232208 and mhw rescues
  remain. **Advance to separately frozen exactfull50; no promotion.**
  The original48-game bridge rejection remains unchanged. Receipt SHA:
  `82953029de1373927b43ffb766dbdaf02b18990d71e534a4a78705c78af517a3`.
  See `diagnostics/adaptive_donor_pair_repair_20260928/RESULTS.md`.

- **2026-09-28 17:29 UTC — both adaptive bridge pilots rejected.**
  The frozen48 games complete cleanly. Five-hand ceed697f improves the
  twelve-fixture pilot from7 to8 both-seat wins, rescuing booming114232208
  and mhw114235177 but losing Boey in both seats. The zero-hand extension
  finishes5/12 and also loses offhand, Yaroslav and Vadim. **Reject both
  under their unchanged prior-winning-seat gate; no full50 follows.**
  Keep physical feasibility and competitive qualification distinct.
  Receipt SHA: `224cae4a3f69ac480ee2979db33df1d21aaaa5ff3ba2cfa3f2c3183fbdd91605`.
  See `diagnostics/adaptive_opening_bridge_20260928/DEVELOPMENT_RESULTS.md`.
  A separate bounded donor151 repair now tests only the two actual shop
  pairs implicated by Boey and unresolved booming114279308; three schedules
  share their exact first151 actions. Preserve both the original32e wins
  and ceed's two rescues. This new study does not revise the old rejection.

- **2026-09-28 — three earlier-commitment branches pass affected controls.**
  All100 retention games are clean. Select ICE113535489, PET113517834 and
  PIZZA113332529 under the frozen prior-winning-seat gate; reject the other
  first-shop families. The exact combined file is
  **8ccb862a215da429097f9c2f895defe9b8aa90eaae019964e1d831c5d889b638**,
  backed up as `main_candidate_early_public_8ccb862a.py`. **Advance to its
  exact full100 development games, now running under supervisor89557.**
  Component results imply18/30 public losses and19/20 top, but those totals
  are not verified until the combined receipt completes. PET's Yaroslav
  win overlaps the separate animal repair; do not add it twice.
  Retention SHA: `329d00860ce5eb676c3cc5e84902272b1933887fa75677838397501832e1b422`.

- **2026-09-28 — adaptive opening engineering prefixes pass.**
  Both ceed697f and be5172f7 pass their16 paired24-turn prefixes across
  eight rival opening classes, both seats:32 total prefix comparisons.
  Turn1 procurement/spawn, donor151 end8 catch-up, donor150 permutation
  and end23 physical/private convergence pass. The five-hand arm also has
  zero own/rival end23 cash delta in every comparison; the zero-hand
  extension has small explicitly reported cash differences. **Advance
  unchanged to the separately frozen48-game development pilot34172.**
  This is execution feasibility, not terminal strength. Its partial
  outcomes already include a lost Boey win, so the original preservation
  gate cannot pass; finish/report both arms without changing that gate.
  Prefix SHA: `befb989d8e8f5c393df3d9ad2a41eddff2e04a84001d36b66f60958a12d02e31`.
  See `diagnostics/adaptive_opening_bridge_20260928/RESULTS.md`.

- **2026-09-28 17:14 UTC — both standalone donor replacements rejected.**
  The frozen full stage finishes200 clean rows, reusing40 pilot rows:
  shared151 has11/20 top sweeps and9/30 public-loss sweeps; shared166 has
  9/20 and12/30. Each loses36 source-winning seats. Both fail their
  unchanged full gates. **Reject both standalone replacements; no native
  promotion escalation.** Keep their code as possible varied reacting
  references, subject to separate native compatibility. Across the study
  there are220 distinct fast outcomes (60 pilot plus160 additional full).
  Full SHA: `97d1df983a9f4121c0563704346a9a61a26cd2acdb8033a985c3d60768073a99`.
  See `diagnostics/donor_opening_agents_20260928/RESULTS.md`. Session70981
  is terminal and released. A separately frozen public-production leaf
  selector is now being prepared; no donor outcome is relabeled a pass.

- **2026-09-28 — exact Ghost near-loss has no terminal stock repair.**
  ICE/113332529 exactly reproduces81,439 versus81,460 in both seats.
  At the final unit phase every bag empties; all93 delivered units have
  matching scheduled sale quantities, below shed capacity100. An optimistic
  reachability audit finds no collect/harvest-and-deliver opportunity in
  any unit's idle suffix after its last committed command. **Reject extra
  final liquidation or idle-suffix collection as a repair for this exact
  trace.** No candidate was changed. The two diagnostic reproductions are
  duplicate development cases, not independent strategy games. See
  `diagnostics/ghost_terminal_audit_20260928/RESULTS.md`.
  Trace audit SHA: `21735e69e1f4e84e327a6e373838ebeba9eef58416b965a9acce9fad4f0ada43`.

- **2026-09-28 17:12 UTC — earlier-route screen completes; expansion starts.**
  All 320 ten-medoid games finish cleanly. Twelve finalists across seven
  first-shop families advance to their frozen control-retention stage.
  Eleven residual fixtures have at least one rescue across alternatives;
  this is an oracle count, not a combined policy result. The sequential
  supervisor 89557 now performs matched step72 features, their audit,
  affected controls and conditional exact integration. Target receipt SHA:
  `a588a300e8354b59f7edebbbdf74aee937efb3e7bd3c23736f11e1ec4317a7bb`.
  A separate predeclared library expansion in
  `diagnostics/residual_91_routes_20260928/` addresses only the five fixtures
  lacking any medoid rescue. It tests all91 distinct complete schedules
  from the common72-action opening:910 fixture-seat cases, including100
  hash-verified prior cases and810 new cached-input games. Session16891
  uses at most two short-lived workers. No extra target or changed gate.

- **2026-09-28 17:06 UTC — input-memory fix verified; pilot resumed.**
  The new streaming input audit verifies104 fixtures/102 unique replays
  against their full decompressed hashes without retaining their histories.
  Its compact cache is2,056,362 bytes. A separate cached diagnostic helper
  exactly reproduces all719 observation/action records and native terminal
  rewards/full telemetry for32e Yaroslav in both seats. **Accept for future
  explicitly bound experiments only; existing frozen helpers unchanged.**
  See `diagnostics/stream_replay_io_20260928/RESULTS.md` and its receipts.
  With5.9GB virtual memory free and PID30560 absent, archive its stale lock
  and resume the original observed-hire pilot from199 verified jobs in
  **session38438 with one worker**. Its hashes, seeds and gates are unchanged.

- **2026-09-28 17:03 UTC — whole-opening donor pilot completes.**
  All60 games are clean. shared151 wins2/7 donor fixtures and1/3 top
  controls; shared166 wins5/7 and1/3. **Advance these two exact files to
  their frozen full50 stage**, which still must reach18/20 top and14/30
  public losses. shared150 wins4/7 but loses all three top controls:
  **reject its standalone promotion; no full stage for that file.** The
  alternatives lose prior source wins, so no combined improvement is
  inferred. Full session70981 is one sequential worker,200 planned rows
  including40 reused pilot rows. See
  `diagnostics/donor_opening_agents_20260928/PILOT_RESULTS.md`.
  Pilot SHA: `3cd290b6e3fb446ec707d550e65ec17ce8363bc06e1b29d30fe18a93a10357b7`.

- **2026-09-28 17:01 UTC — animal-liquidity full native panel passes.**
  Exact **32e299fe** completes all 100 saved-target games, clean
  DONE/DONE/720, with no policy errors or source-winning-seat regressions.
  It wins **14/30 public-loss fixtures and 19/20 top-team fixtures** in
  both seats: **33/50 sweeps, 66W/0D/34L**. Yaroslav is the only newly won
  fixture, +902 per seat instead of -324; all other cash pairs are
  unchanged. **Accept this saved-panel improvement; independent reacting
  qualification remains unlaunched, so no research promotion.** The
  user's public-loss target still needs 13 additional both-seat wins.
  Root backup: `main_candidate_animal_liquidity_20260928_32e299fe.py`.
  Full receipt: `diagnostics/animal_liquidity_20260928/native_full.json`,
  SHA `51c8eab6805bd24c5907e58d845786e8c47ea4bc12e5737eb080e344938e5f8f`.
  Session 81725 exited successfully and released memory. Root main stays
  4ee; latest uploaded file remains 367d2e76. No Kaggle access or upload.

- **2026-09-28 16:53 UTC — host memory pressure, checkpoint preserved.**
  Two donor-study replay loads failed with MemoryError before the affected
  games began. With only about 0.46 GB virtual memory free, stop only the
  root observed-hire pilot coordinator 30560 and its worker children.
  Session 31417 is terminal from this resource interruption, not from a
  research gate. Its checkpoint has **199 valid JSON rows, 199 unique jobs**,
  SHA `30b57af0d50a693f92a1be425787c1a8f79a6f2c8bf7b09adb4b86ab5f04b956`.
  Resume the same frozen inputs with **one worker** after shorter checks
  finish; do not restart completed jobs or alter the candidate criteria.
  Animal full session 81725 and early route session 93285 continue one
  worker each. Donor pilot has 25 saved rows and waits for animal full to
  release memory before resuming. No unrelated user process was stopped.
  See the observed-hire resource-interruption receipt for exact evidence.

- **2026-09-28 16:53 UTC — frozen donor provenance audit completed.**
  All 50 selected opponent tapes are verified against their recorded
  replay actions and manifest hashes. Comparing them with all 145 source
  routes gives 7,250 comparisons: none has a compatible source opening
  through turn 72 or 144, including normalized physical commands.
  **Reject direct insertion into the existing route library.** The donors
  contain 43 distinct physical openings. Three groups share exact openings
  with one another through 151, 150 and 166 actions respectively, allowing
  a separately frozen whole policy from turn zero with public second-shop
  selection. **Advance those three architectures to development only.**
  Their separate 60-game pilot runs one worker in session 98872; no result
  or promotion is inferred. See
  `diagnostics/frozen_reply_donor_audit_20260928/RESULTS.md` and
  `diagnostics/donor_opening_agents_20260928/`.
  Inventory SHA: `e36a7716ab1b7fcf2c42dcd4979e37f099b0ce9ffe2d8b29d8cee700c6db6155`.
  Cross-donor SHA: `ffad1dedd4baaf03c99a08842ddaa2a43fbc34f71aa41390c29e7814e1cf6c19`.

- **2026-09-28 16:33 UTC — two distinct DECEM experiments rejected.**
  Joint queue/quantity candidate b78fc7fb finishes 12 clean development
  games: DECEM improves by 2,204 per seat but still loses at -6,881;
  Boey regresses from +4,935 to -8,058. Its first missing wheat seed
  follows a three-coin shortfall at step 248, then physical and shop
  divergence. **Reject; no native escalation.** A separate physical
  delivery candidate 6a933a6e also finishes 12 clean games and retains all
  ten winning control seats. It successfully delivers fertilizer earlier
  and restores the blocked strawberry, but DECEM still loses at -8,681:
  own cash rises 24,746 while rival cash rises 24,342, only +404 relative.
  **Reject under its separate frozen rescue gate; no native escalation.**
  Neither candidate is combined with the source. Evidence:
  `diagnostics/decem_90_research_20260928/RESULTS.md` and
  `diagnostics/decem_90_research_20260928/delivery/RESULTS.md`.
  Screen SHAs: `27902c12174ce68bb1a04f4a11e18c3aff5b7fbda9468cad7a53c2ff52038061`
  and `3b13171e43dd1f9dc39cf679eec5c53fb6062dc2d4dc0e49f04ef419a6d64d10`.

- **2026-09-28 16:31 UTC — animal-liquidity repair advances.**
  Exact **32e299fe047a79290d5025b4e2be455ae13d948020beae2d77cb44a7c17dc31e**
  passes 12 development and 12 original-native parity games, clean with
  exact rewards/full telemetry and no prior-winning-seat regressions.
  It newly beats Yaroslav in both seats at **+902** instead of -324.
  The one existing sheep order is funded from held nonfeed goods; it is
  placed/fed and existing seeds/crops/shop path remain identical. Own cash
  changes -352, rival -1,578, paired margin +1,226. **Advance unchanged to
  full 100-game saved regression; no research promotion.** Session **81725**
  runs one worker and reuses the 12 exact native rows. Do not assume a
  14/30 combined total until the full receipt passes. Native parity SHA:
  `a71c23a809fee6d19ee15aaccbb2f6c6d2dd82375fb83caeb2a301234a418962`.
  A separate independent 298xxxx plan is prepared, with no reacting
  outcomes yet. The original recovery pilot continues as 31417. See
  `diagnostics/animal_liquidity_20260928/` for plans and receipts.

- **2026-09-28 16:22 UTC — interrupted native pilot safely resumed.**
  Old session 82809 is missing and its recorded coordinator PID 31648 is
  absent; no matching Python process remains. The unchanged checkpoint has
  61 unique games, SHA
  `7277916aa112e869bdae1ee516f397b1fb38acf8b2046b9355050506344f75a1`.
  Preserve the interruption audit and archived stale lock in the observed-
  hire directory. Resume exact frozen inputs with two workers in session
  **31417**, `native.py pilot --workers 2`; it confirms 61/512 loaded.
  Do not duplicate or replace the run. This is unfinished qualification,
  not a failed or completed independent result. Separate agents own new
  early-commitment route research, DECEM market research and the already
  frozen animal-liquidity draft; each uses one benchmark worker and separate
  files. Root main and all existing source/hash-bound inputs are preserved.

- **2026-09-28 07:36 UTC — parent 8dde independent pilot rejected.**
  Session 82556 stopped under its frozen impossibility bound after
  **368/384** planned games, all clean. Against reacting 4ee, main records
  3W/56D/3L (31 points from 62 games), while 8dde records 8W/40D/14L
  (28 points from 62). Even winning its two remaining games gives only
  30 points, below main's already recorded 31. **Reject 8dde promotion;
  no confirmation or final preservation stages.** Partial pooled counts
  are unequal (main 124 games, source/new 122 each); do not report a
  completed 384-game result. Activation passed; execution was clean.
  Receipt SHA:
  `370e7e26acc0e77f8eb130a74a06ee829f092f1d7c9c8180253ac863f5585efa`.
  This parent rejection became available after the explicitly requested
  experimental 367d2e76 upload. The exact new recovery files retain their
  separate frozen qualification, now running in session **82809**; no
  inherited parent pass is available. Root main remains 4ee.

- **2026-09-28 07:35 UTC — recovery full panels pass; experimental upload.**
  Full session 13956 is terminal: 200/200 original-native games are clean,
  exact affected-case telemetry/rewards match, and no parent winning seat
  regresses. Main-parent 467a9dfe has **1/30 + 17/20 = 18/50** sweeps;
  integrated 367d2e76 has **13/30 + 19/20 = 32/50**, 64W/0D/36L. Both
  newly rescue Junliang in both seats. **Advance both exact candidates to
  their frozen independent pilot, not research promotion.** Seventeen
  public-loss fixtures and DECEM remain unresolved in the combined file.
  Full receipt SHA:
  `1cd02ac25079a1df229ad528c51a94ec467181a4adcd1e6ab13248ff4fd82545`.
  Separate operational file-loader session 47717 passes all eight games
  on Junliang and Boey, both seats, all 719 actions for both players and
  rewards exact, no errors/overage deficit, intended final callable.
  Loader receipt SHA:
  `caa82e5b35e4b6cadb5eeb8bd4694a5f5082e64f8a926ba0fa16599a7f468e33`.
  User-requested experimental upload **56633591** is accepted/PENDING;
  its full receipt is in
  `diagnostics/upload_hire_recovery_20260928_367d2e76/upload_receipt.json`.
  Root main remains 4ee. Final research preservation helpers now exist in
  `diagnostics/native_preservation_20260928/` and retain their required
  independent confirmation/public-win gates; these have not passed.
  Independent recovery pilot started in session **82809**, three workers,
  512 initial games; frozen stop/activation/win-point gates remain intact.
  The parent 8dde pilot **82556** subsequently stopped/rejected; see above.

- **2026-09-28 07:05 UTC — observed recovery native parity passes.** All
  24 games match fast rewards and full telemetry exactly, clean
  DONE/DONE/720. **Advance both exact arms to full saved-panel validation,
  not promotion.** Full session 13956 evaluates 200 games with 24 reused.
  Mechanism traces show 15/15 animals fed instead of 11/15, and 29
  strawberries at day 9 instead of 21. Fresh 296xxxx panels and the
  independent four-arm plan are frozen; ten synthetic gate checks pass.
  No new reacting outcomes exist under that plan yet. Root main remains
  4ee; parent 8dde's pilot stays separate. See
  `diagnostics/observed_hire_recovery_20260928/RESULTS.md`.

- **2026-09-28 06:59 UTC — observed-hire recovery passes development.**
  The new feedback rule retries two actual missing hires, delays their
  work one turn and catches each up by omitting one CARE. All 24 games
  are clean; both main-parent 467a9dfe and integrated-parent 367d2e76
  newly win Junliang Ye in both seats at **+2,957**, preserving the other
  tested outcomes. Per-seat paired gain is +15,891 versus 4ee and +19,012
  versus 8dde; own/rival changes are separately recorded. **Advance to
  original-native parity, not promotion.** Session 35044 runs 24 games;
  full panels, fresh reacting qualification, public wins and loader checks
  remain required. Both exact candidates are backed up at the root.
  The earlier preemptive guard remains rejected; the parent's 8dde pilot
  82556 continues separately. Main stays 4ee; no Kaggle access. See
  `diagnostics/observed_hire_recovery_20260928/RESULTS.md`.

- **2026-09-28 06:52 UTC — preemptive hire-funding rule rejected.** All
  24 games are clean but neither 2537b11b nor 2325138d activates; final
  cash pairs equal their respective parents, with zero rescues. **Reject
  both exact arms, no native escalation or loosening of this rule.** At
  Junliang step 192 the idle forecast predicts 2/4 hires before/after,
  but mirror forecasts predict 4/4. The frozen strict-all-scenarios guard
  therefore refuses the state. A new actual-feedback repair would need
  to detect the failed hire, fund a retry and reconcile delayed worker
  actions; it is not an engineering relabeling of this rejection.
  Evidence: `diagnostics/scheduled_hire_funding_20260928/RESULTS.md`.
  Session 58054 is terminal; 8dde native pilot 82556 continues unchanged.

- **2026-09-28 — residual 8dde execution audit identifies unfunded hires.**
  All 42 repeated games (19 unresolved targets plus Boey/Majkel, both
  seats) match native rewards and complete telemetry exactly. Fifteen
  unresolved fixtures have no no-ops among present workers. Explicit
  absent-worker accounting isolates Junliang Ye: four scheduled hires at
  step 192 fund only two, leaving 45 commands without a worker; eight
  strawberries die unwatered at 215. **Accept the mechanism for a bounded
  separate test, no promotion.** Existing wheat buys precede those hires.
  The frozen scheduled_hire_funding plan tests one guarded reorder on
  4ee and 8dde parents, six fixtures/both seats each, 24 fast games in
  session 58054. Both candidates are backed up at the root (2537b11b and
  2325138d); neither changes main or the running 8dde native pilot 82556.
  Evidence: `diagnostics/residual_execution_20260928/RESULTS.md` and
  `diagnostics/scheduled_hire_funding_20260928/PLAN.md`. No Kaggle access.

- **2026-09-28 06:36 UTC — full 8dde995d panel passes; native pilot starts.**
  All 100 original-native games are clean DONE/DONE/720, with exact
  affected-case parity and every main/source winning seat retained:
  **12/30 public-loss sweeps + 19/20 top-team sweeps = 31/50**.
  Eighteen public-loss fixtures and DECEM remain unresolved. **Advance to
  the frozen independent whole-policy pilot, not promotion.** Session
  82556 runs 384 games on the preselected 32 seeds, both references,
  all three arms and both seats. Confirmation, all 54 public wins and
  actual loader checks remain conditional gates. Full receipt SHA:
  `a01df893b3e032aa9aa017360fecc2039308bc58e7dd12595852e6bcfc21de89`.
  Root main stays 4ee; latest authorized upload remains 56628152/06803086.
  No further Kaggle access. See
  `diagnostics/public_loss_route_pool_20260928/RESULTS.md`.

- **2026-09-28 06:36 UTC — direct Farm/Ice controller family rejected.**
  All 180 development games finish cleanly, with 575 actual controller
  turns per game. None of the 15 exact-prefix-compatible schedules wins
  either Ebi or boominginging in both seats; all target games are losses.
  **Reject at the frozen target-win gate.** No selected candidate, native
  qualification or integration follows. This corrects the earlier inert
  base-map experiment by testing the active controller itself. Selection
  SHA `ce99a47c3de260609b1974344f39c8a556b6974c298f4a1fb27632e156f4c850`.
  See `diagnostics/farmice_controller_pool_20260928/RESULTS.md`.

- **2026-09-28 06:22 UTC — 8dde995d native parity passes.** All 42
  affected-case games match fast rewards and full telemetry exactly;
  clean DONE/DONE/720 and all prior winning seats retained. Eleven
  additional public-loss pairs are native-confirmed on these development
  fixtures. **Advance to the full 50-target panel, not promotion.**
  Parity session 36073 is terminal. The full run reuses 36 target rows;
  the six public-win rows remain separate. Independent whole-policy
  gates, all 54 public wins and loader checks remain pending. Main stays
  4ee; no Kaggle access. Evidence:
  `diagnostics/public_loss_route_pool_20260928/native_parity.json`.

- **2026-09-28 06:17 UTC — broad pool selects 8dde995d.** All 1,026
  variant games plus 52 prior controls complete cleanly. Ten selected
  shop-pair changes add **11 public-loss both-seat wins**, preserving all
  affected main/source winning seats. **Pass development and advance to
  native parity, not promotion.** Combined candidate SHA
  `8dde995de6430dcdb7c3dae57bc7a42885ea1b230583c9b0eaf062d1361d3432`
  is backed up as `main_candidate_public_loss_routes_20260928_8dde995d.py`.
  Session 36073 runs its 42 affected-case original-native games; the full
  50-target panel and whole-policy gates remain mandatory. G07 is not
  selected: its base-map changes were preempted by the old Farm/Ice
  controller. A separately frozen direct-controller pool now runs 180
  games in session 59500, with 15 exact-prefix-compatible tapes and all
  six affected fixtures. Main and Kaggle remain unchanged. Evidence:
  `diagnostics/public_loss_route_pool_20260928/selection.json` and both
  experiment RUN_STATE files.

- **2026-09-28 05:45 UTC — Farm/Ice base-map substitutions are preempted.**
  The broad G07 rows keep the existing melon-triggered `_FARMICE_TAPE`;
  all 154 inspected games have that controller active. Their route-map
  telemetry does not prove an actual schedule change. **Accept the static
  diagnosis and a separate controller-tape feasibility path, no promotion.**
  Fifteen distinct embedded schedules match the controller's exact first
  144 actions and can be investigated directly under a new plan. Both
  failed fixtures (Ebi/boominginging) and all four winning controls remain
  required. No new controller candidate or game exists. Do not change the
  running broad pool or relabel its inert rows as independent evidence.
  See `diagnostics/farmice_controller_pool_20260928/FEASIBILITY.md` and
  `diagnostics/public_loss_route_pool_20260928/PREEMPTION_FINDING.md`.

- **2026-09-28 05:39 UTC — 2dd39764 reacting pilot fails to improve.**
  All 96 native games are clean. Main and source each score 18W/12D/2L;
  new scores 24W/0D/8L. Each arm has **24 win points from 32 games**
  (draw=0.5). All per-reference/branch nonregression gates pass, but the
  frozen strict pooled improvement gate fails against both controls.
  **Reject exact 2dd for promotion; do not run confirmation.** The
  -48,384 paired-margin diagnostic is not the rejection criterion.
  Its 19/20 top-team + 1/30 public-loss saved sweeps remain development
  evidence. Source 068's missing coverage remains a separate finding.
  Main stays 4ee; no Kaggle access. Only the broader new-policy pool
  continues, with its distinct whole-policy gates frozen before these
  outcomes. Evidence: `diagnostics/guarded_route_pool_20260928/native_pilot.json`
  SHA `c4273be786c060731ab315764892a93124007514b786213d0cf839bbacb75d24`.

- **2026-09-28 05:38 UTC — earlier first-BRUNCH family rejected.** All
  182 games (91 complete compatible schedules, both seats) finish cleanly
  but lose to the saved DECEM reply. Best margins are -5,114 in both seats
  for routes 113365392/113437157/113529057, versus source 2dd's -9,085.
  **Reject at the frozen both-seat win gate.** No shortlist, retention,
  native qualification, root candidate or promotion follows. The 24
  controls passed; all candidate bytes, outcomes and unused independent
  seed panels remain preserved. Main stays 4ee; no Kaggle access. Evidence:
  `diagnostics/early_brunch_route_20260928/{target.json,shortlist.json,RESULTS.md}`.

- **2026-09-28 05:24 UTC — earlier BRUNCH controls pass.** All 24
  source/main games reproduce the required first-shop coverage and public
  original-seat cash, with clean DONE/DONE/720. **Advance to the frozen
  91-route DECEM screen, no promotion.** Target stage is session 45057.
  Its completed control stage 52680 is terminal. A progress paragraph
  accidentally appended to the frozen plan was removed by restoring its
  exact original hash; rules, candidates, seeds and jobs are unchanged.
  See `diagnostics/early_brunch_route_20260928/RESULTS.md`.

- **2026-09-28 05:11 UTC — remaining-loss controls pass.** All 52 games
  are clean DONE/DONE/720; original public cash and source shop coverage
  agree. **Advance the frozen pool to development screening, no promotion.**
  Session 23766 runs 1,026 variant games over 21 branches. Whole-policy
  native helper/gate checks are frozen separately before their outcomes.
  The 2dd A/C native prefixes passed 32/32 at 05:09 UTC, so its original
  96-game reacting pilot now runs in session 63515. Separately a static
  inventory found 91 complete schedules compatible through action 71 for
  the remaining DECEM case. Its first-shop experiment is frozen in
  `diagnostics/early_brunch_route_20260928/PLAN.md`: 24 winning controls,
  182 DECEM games, at most five finalists, then all affected controls.
  Main stays 4ee; no Kaggle access and no new qualified candidate.

- **2026-09-28 05:02 UTC — 2dd39764 changed-branch coverage passes.**
  The finite scan completed 784 prefixes with four both-seat seeds per
  changed A/C branch and reacting reference. **Advance to original-engine
  prefix verification, not promotion.** No terminal reacting results yet.
  Session 15096 is terminal; verification now runs in session 19905.
  Separately, the complete remaining-loss pool is frozen: 21 branches,
  222 variants, 1,026 candidate games and 52 affected-public-win controls.
  Its 32/64 whole-policy seed panels were frozen before any development
  outcomes. Control stage runs in session 73859; variants are gated on
  fresh source shop coverage and original public cash parity. Main remains
  4ee; Kaggle is untouched. See the guarded/public_loss route-pool folders.

- **2026-09-28 04:44 UTC — 2dd39764 passes the full saved target panel.**
  All 100 native games are clean DONE/DONE/720; exact affected-case parity
  and all original/source winning seats are retained. Results: **19/20**
  top-team sweeps and **1/30** public-loss sweeps, **20/50** total. Vadim
  and leave you 114289228 are rescued; DECEM and 29 public losses remain.
  **Pass replay regression; no promotion.** The frozen changed-branch
  native scan now runs in session 15096. Its new helper is hash-bound;
  synthetic gate checks passed without running strategy outcomes. Source
  qualification remains insufficient, so this branch evidence cannot
  authorize overall promotion by itself. Main is exact 4ee and Kaggle
  remains untouched. See
  `diagnostics/guarded_route_pool_20260928/{native_full.json,RESULTS.md}`.

- **2026-09-28 04:42 UTC — 06803086 bounded coverage is insufficient.**
  The 2,606-prefix pilot scan completed, with both route quotas and the
  4ee other-guard quota filled, but zero market other-guard seeds through
  2922047. **Do not advance or promote under that plan.** No terminal
  strength outcomes were run; this is not a measured win-rate failure.
  Session 40895 is terminal. Preserve the frozen range and missing-stratum
  finding; any different integrated qualification needs a new plan and
  fresh evidence. Main remains 4ee, uploaded source remains experimental.
  Evidence: `diagnostics/partial_planting_20260928/pilot_eligibility.json`.

- **2026-09-28 04:30 UTC — 2dd39764 native parity passes.** All twelve
  combined-candidate games exactly match development cash and full
  telemetry, DONE/DONE/720 and zero recorded errors. **Advance to the
  full 50-target panel, not promotion.** Session 74172 is running those
  100 native games with three workers, reusing eight target parity rows
  and keeping four public-win controls separate. Source 06803086's own
  frozen qualification scan remains live in session 40895 through block
  2921535; market other-guard coverage remains zero, so no terminal
  strength tests have run. Main stays 4ee; no Kaggle access. Evidence:
  `diagnostics/guarded_route_pool_20260928/{native_parity.json,RUN_STATE.md}`.

- **2026-09-28 04:27 UTC — guarded route pool selects 2dd39764.**
  All 144 development games are clean DONE/DONE/720. Frozen selection
  chooses A113373693 and C113453388 on source 06803086. Both-seat margins:
  leave you +3,256; Vadim +16,140; DECEM still -9,085. Yizhou/Orest/Rio
  remain wins, including the recovered opposite-seat Rio control (-705
  to +1,472). C's win points rise 5 to 8 despite a -18,395 aggregate
  margin change; apply the predeclared win gate. Earlier C113377257 loses
  Rio -16,242 both and is now excluded by the expanded affected controls.
  **Pass development, not promotion.** Combined SHA
  `2dd397645df739ee41e73a0d91f9e749863068b18bf31319ab338c980094ba34`
  is preserved in the experiment and as root backup
  `main_candidate_guarded_routes_20260928_2dd39764.py`. Twelve original
  native parity games run in session 46566; full 50-target and independent
  gates remain outstanding. Main remains 4ee; no Kaggle. Evidence:
  `diagnostics/guarded_route_pool_20260928/{selection.json,RESULTS.md,RUN_STATE.md}`.

- **2026-09-28 04:13 UTC — complete source-prefix coverage accepted.**
  All 208 prefixes (50 target fixtures plus 54 saved wins, both seats)
  finish ACTIVE/ACTIVE at observation 144, with zero errors and no early
  partial-plant activation. Source 06803086's 40 top-team shop captures
  match the original 4ee counterfactual captures. Sixteen archived
  community games have different shop pairs, so raw replay shops cannot
  classify a replacement policy's trajectory. The assertion caught this
  before new candidate outcomes. **Accept corrected coverage; proceed
  with development, not promotion.** A separately frozen 22-route A/C
  pool now tests DECEM/leave you and Vadim/Yizhou/Orest Myth/Rio, both
  seats, while retaining the source's planting repair. Its 144-game screen
  runs in session 74890; no selection yet. A static inventory maps all
  32 unresolved targets to 23 shop-pair branches with 4–15 compatible
  schedules each, including affected saved wins. This supports the full
  30-loss objective, without claiming those schedules win. Root main
  and uploaded source are unchanged; no Kaggle. See
  `diagnostics/guarded_route_pool_20260928/{RESULTS.md,RUN_STATE.md}`.

- **2026-09-28 03:54 UTC — newest submitted artifact is 06803086.**
  Kaggle accepted `main_candidate_partial_planting_20260928_06803086.py`
  as **56628152** at **03:54:13 UTC (09:24:13 IST)**. The listing was
  verified **PENDING** at 03:54:18 UTC, with no score yet. Exact SHA-256:
  `068030868689db5eb1e9a4a4427bededa8fbc13cae14e1003eb6be5440a6da42`.
  Four local native direct/file games reproduce all 719 action pairs and
  final rewards in both seats against saved Boey, with the new guard
  active, no recorded errors, DONE/DONE/720 and full overage remaining.
  The loader selects `kaggle_partial_planting_entrypoint`. **Accept the
  packaging check and user-requested experimental upload; strength
  promotion remains pending.** Saved-panel results remain 18/20 top-team
  sweeps and 0/30 public-loss sweeps. Root main is still exact 4ee; the
  active local research scan is preserved. Byte-identical upload backup,
  evidence hashes, authorization and official receipt are saved under
  `diagnostics/upload_partial_planting_20260928_06803086/`.

- **2026-09-28 — historical 06803086 qualification checkpoint, superseded
  by the 04:42 UTC insufficient-coverage result above.** The
  outcome-blind pilot scan is running in unified session 40895, PID 10212;
  do not duplicate it. At completed block 2921799, route-stratum eligible
  pairs are 4ee=2/2, market=2/2; other guard pairs are 4ee=2/2,
  market=0/2. No terminal strength outcomes have run. This is
  a sparse-activation checkpoint, not a rejection or promotion. All 54
  saved public-win fixtures are also hash-verified and prospectively
  frozen for later preservation checks; no new results on them. Exact
  main and root candidate backup hashes reverify. See
  `diagnostics/partial_planting_20260928/RUN_STATE.md` for resumption.

- **2026-09-28 03:31 UTC — 06803086 passes all 100 saved-panel games.**
  All DONE/DONE/720 and error-free; all 34 incumbent winning seats remain
  wins. Result: **18/20** top-team sweeps, **0/30** public-loss sweeps,
  **18/50** combined; only Boey is rescued. **Advance to the separately
  frozen reacting plan, not promotion.** New outcome-blind prefixes use
  pilot 2920000–2922047 and confirmation 2923000–2927095, with both
  route-branch and other guard-activation strata. Compare new against
  current main and route-only, versus 4ee and market references. Main
  remains exact 4ee; no Kaggle. Evidence:
  `diagnostics/partial_planting_20260928/{native_full.json,NATIVE_PLAN.md}`.

- **2026-09-28 03:28 UTC — faster reacting harness matches eight known
  native games.** Exact terminal cash/status/telemetry parity covers both
  seats of 4ee/b6eb against 4ee and the market reference; initial state
  also matches fresh native initialization. **Accept for development and
  outcome-blind prefix selection only.** Framework strength, runtime and
  file loading remain separate mandatory gates. No new strength evidence
  comes from these repeated games. Evidence:
  `diagnostics/physical_route_rollout_20260928/reactive_parity.json`.

- **2026-09-28 03:23 UTC — 06803086 native development parity passes.**
  All ten original-framework games match fast cash and telemetry exactly,
  DONE/DONE/720 and zero errors, including Boey +4,935 in both seats.
  Its repeated mechanism trace confirms three successful WHEAT plants
  using existing seeds; four excess commands become PASS. Future shops
  first differ from route-only at observation 288, so the margin gain is
  not simply crop receipts. **Advance to all 50 saved fixtures/both seats;
  no promotion or reacting-strength claim.** Main remains 4ee. Evidence:
  `diagnostics/partial_planting_20260928/{native_parity.json,boey_mechanism.json}`.

- **2026-09-28 03:21 UTC — partial planting plus a complete route rescues
  Boey in development.** All 20 fast games are clean. Main-plus-guard
  57f41f1e rescues none and is rejected. Route 113349962 plus the same
  guard, exact 06803086, changes three turns per Boey seat and improves
  route-only -1,577 to +4,935 (main -20,873). Kaggledew stays a win +4,877;
  Majkel stays a win +13,889, with Yaroslav/DECEM still losses. **Advance
  only the route arm to original native parity and full-panel gates.**
  This is development, not independent strength. Main remains exact 4ee.
  Evidence: `diagnostics/partial_planting_20260928/{RESULTS.md,fast_screen.json}`.

- **2026-09-28 03:15 UTC — scheduled sheep funding rejected.** Exact
  7fad3c80 on route 113349962 completes all four fast diagnostic games
  cleanly. Moving the existing sale before the sheep order recovers one
  sheep but leaves only 27 coins, preventing the next wheat purchases.
  Boey worsens -1,577 to -5,419 in both seats; Kaggledew stays +4,877.
  Own cash falls 18,442 versus rival -14,600, paired margin -3,842.
  **Reject at the frozen rescue gate; no native escalation/promotion.**
  The whole existing feed/seed commitment still has to be funded. Main
  remains 4ee. Evidence:
  `diagnostics/scheduled_animal_funding_20260928/{RESULTS.md,fast_screen.json}`.

- **2026-09-28 — complete-route execution audit isolates a missed sheep.**
  Six repeated development traces reproduce known native rewards exactly:
  DECEM -10,636 on 113373693, Boey -1,577 and Kaggledew +4,877 on
  113349962, both seats. Boey has 495 coins before a scheduled 500-coin
  SHEEP order and 527 after the later WHEAT sale; its pickup/placement
  then fail, leaving scheduled care work on empty pasture. Kaggledew has
  462 coins and no sellable wheat, so the same funding opportunity is
  absent. **Accept the diagnosis only.** Later feed/cash and shared-market
  effects require a separately frozen policy test. The old generic seed
  prefund and procurement rejections remain valid. Main stays 4ee.
  Evidence: `diagnostics/route_execution_gap_20260928/{RESULTS.md,audit.json}`.

- **2026-09-28 03:07 UTC — Bakery/Pizza coverage gate incomplete; no
  promotion.** The bounded scan finishes 512 4ee prefixes with only three
  eligible both-seat activations (four required); market finds four in
  416 prefixes, 935 prefix games overall. No terminal strength outcomes
  ran. Preserve a823911f's two fixed-loss rescues as development evidence;
  reject advancement under this frozen gate, without claiming a measured
  win-rate failure. The repeated mhw traces exactly reproduce native
  results: own private state is identical across seats for all 719 steps,
  with no failed worker commands or land purchases. Rival WHEAT planting
  at (1,8) fails on a weed in one seat, followed by market/cash divergence.
  This does not justify an own-worker patch. Main remains 4ee. Evidence:
  `diagnostics/bakery_pizza_pool_20260928/{RESULTS.md,pilot_eligibility.json,mhw_analysis.json}`.

- **2026-09-28 02:55 UTC — observable-history balanced quantities rejected.**
  Exact `96e965b8…3efbf8` finishes all 12 fast diagnostic games cleanly,
  retaining both controls but rescuing no target. All final rewards/margins
  equal incumbent outcomes, despite 1–2 accepted changes per game in three
  fixtures. **Reject at the frozen rescue gate; no native escalation.**
  Ranges 2914200–2914203 and 2914300–2914307 remain unused. Main stays 4ee;
  Bakery/Pizza's separate native activation scan continues. Evidence:
  `diagnostics/observable_quantity_20260928/{RESULTS.md,fast_screen.json}`.

- **2026-09-28 02:47 UTC — observable-history queue reorder rejected.**
  Candidate `10452303…ca712` completes all 12 fast diagnostic games cleanly
  and preserves Majkel/Kaggledew wins, but rescues none of four close loss
  fixtures. Yaroslav improves -324 to -167, Kucing -2,857 to -2,825, leave
  you -2,999 to -2,919; Vadim stays -400. It activates 1–9 queue changes
  per game. **Reject at its frozen rescue gate; no native escalation.**
  The feature's past-flow parity does not imply useful future forecasts.
  Reserved 2914000–2914003 and 2914100–2914107 remain unused. Main stays 4ee.
  Evidence: `diagnostics/observable_queue_20260928/{RESULTS.md,fast_screen.json}`.

- **2026-09-28 02:40 UTC — full-policy fast diagnostic harness matches native.**
  All six selected a823911f games across the three Bakery/Pizza tapes and
  both seats exactly match native rewards, DONE/DONE/720 and telemetry.
  Runtime is 6.35–7.34 s per game; max callback 0.267–0.326 s. **Accept for
  development diagnostics only.** It omits framework schema/timeout/file
  loading, so original native gates stay mandatory. This repeats known
  games and adds no independent strength evidence. Main remains 4ee; the
  outcome-blind Bakery/Pizza native activation scan continues separately.
  Evidence: `diagnostics/physical_route_rollout_20260928/fast_agent_parity.json`.

- **2026-09-28 02:34 UTC — Bakery/Pizza integration passes; reacting scan
  starts.** Exact `a823911f` completes all 100 fixed games DONE/DONE/720
  without recorded errors. All component and unaffected-incumbent rewards
  match exactly; no existing winning seat is lost. Result: 2/30 public-loss
  sweeps and 17/20 top-team sweeps, 19/50 overall. **Advance to its frozen
  reacting qualification; no promotion.** The new prefix-only scan uses
  2911000–2911511 and has no final-outcome selection. Main stays exact 4ee.
  Evidence: `diagnostics/bakery_pizza_pool_20260928/full_panel.json`.

- **2026-09-28 02:33 UTC — observable past rival net-flow feature passes
  after price-floor correction.** Initial full-product inversion failed
  because price-1 sales do not add market supply. Original artifacts are
  preserved. With explicit unknowns at midnight/possible floor-priced
  products, legal-observation inference matches independent accounting on
  48,698/49,680 product-transitions (98.02%) across all 5,520 non-midnight
  seat-transitions; zero known-value mismatches. **Accept as a measured
  historical feature, not a forecast or policy.** No rival private data or
  action enters the feature; those appear only in the test's ground truth.
  Evidence: `diagnostics/physical_route_rollout_20260928/{FLOW_CORRECTION.md,flow_parity.json,RESULTS.md}`.

- **2026-09-28 02:29 UTC — fast native physical rollout prerequisite passes.**
  A separate pure transition module extracted from engine 1.32.7 reproduces
  2,300 consecutive transitions across four frozen replay continuations,
  with exact farms, market/town, both private states and terminal rewards.
  Each 575-step continuation plus parity comparisons takes 0.139–0.181 s
  locally. **Accept the engineering prerequisite, not a policy.** Known
  seed, both private states and future recorded actions are harness-only;
  any deployed chooser still needs legal-observation forecasts for hidden
  information and separate runtime/reacting gates. No alternative route
  outcomes or candidate were generated by this audit. Main remains 4ee.
  Evidence: `diagnostics/physical_route_rollout_20260928/{RESULTS.md,parity.json,native_core.py}`.

- **2026-09-28 02:24 UTC — Bakery/Pizza development selects route113615383.**
  All 66 immutable-pool games finish DONE/DONE/720 with no recorded errors;
  both seats show the intended first-two-shop branch. The frozen win-first
  rule selects two rescued public-loss fixtures: high frequency farming
  +17,170/+16,639 and Navier-stokes +26,065/+26,065. mhw remains a loss
  (-9,646/-29,166), including a seat-1 cash regression. **Advance to full
  saved-panel integration, not promotion.** Candidate SHA `a823911f…8134be`
  is separately backed up as `main_candidate_bakery_pizza_20260928_a823911f.py`.
  It changes only Bakery/Pizza and does not include rejected candidates.
  The 100-game panel is running; fresh reacting qualification remains
  required. Main stays exact 4ee; no Kaggle request. Evidence:
  `diagnostics/bakery_pizza_pool_20260928/{RESULTS.md,selection.json,PLAN.md}`.

- **2026-09-28 02:18 UTC — compatible-route candidate rejected by its
  reacting pilot.** All 32 full games complete DONE/DONE/720 without
  recorded errors; every candidate game activates. Against 4ee, incumbent
  1W/6D/1L becomes candidate 7W/0D/1L (+3 win points). Against the distinct
  market policy, incumbent 6W/2L becomes candidate 4W/4L (-2 points). The
  pooled +1 does not pass the frozen requirement of no reference-specific
  regression. **Reject exact b6ebf9ad; no confirmation or promotion.**
  Its 19/50 saved sweeps remain development evidence only. The outcome-blind
  scan used 240 prefixes, selecting four both-seat activations per reference;
  pilot seeds are now spent. Main remains exact 4ee. The separately frozen
  66-game Bakery/Pizza pool is now running. No Kaggle request was made.
  Evidence: `diagnostics/compatible_route_pool_20260928/{RESULTS.md,native_pilot.json,pilot_eligibility.json}`.

- **2026-09-28 02:12 UTC — remaining-loss coverage identifies a separate
  Bakery/Pizza route pool.** The 30 saved losses span 22 first-two-shop pairs;
  the largest pair covers mhw, high frequency farming and Navier-stokes.
  Eleven unique existing complete routes share its actual first 144 raw
  actions. No saved public win or current top-20 entry has that pair in the
  recorded prefix. **Accept a separate finite development search, not a
  promotion.** Its 66-game pool, win-first selection, full-panel check and
  new reacting seed ranges are frozen before candidate outcomes. Keep the
  pending b6ebf9ad qualification separate. Main stays exact 4ee. Evidence:
  `diagnostics/compatible_route_coverage_20260928/{coverage.json,RESULTS.md}`
  and `diagnostics/bakery_pizza_pool_20260928/PLAN.md`.

- **2026-09-28 02:07 UTC — compatible-route combined integration passed.**
  Exact `b6ebf9ad` completes all 100 frozen games DONE/DONE/720 without
  recorded errors and exactly matches selected route components plus every
  unaffected incumbent outcome. It improves the saved target from 17/50 to
  **19/50 both-seat sweeps**: 1/30 public losses (2W/58L) and 18/20 top teams
  (36W/4L), preserving every incumbent winning seat. **Advance to the frozen
  native reacting pilot; do not promote yet.** The prefix-only activation
  scan is running on new bounded seed ranges, without final-outcome seed
  selection. Main remains exact 4ee; this research made no Kaggle request.
  Evidence: `diagnostics/compatible_route_pool_20260928/{full_panel.json,NATIVE_PLAN.md}`.

- **2026-09-28 01:59 UTC — complete compatible-route development selection
  rescues Vadim and one saved public loss.** All 172 retained games finish
  DONE/DONE/720 with no recorded errors; corrected grouping selects from
  128 relevant games across all 32 immutable routes. The frozen rule chooses
  BRUNCH/BRUNCH route113373693 (leave you +3,256 both seats; DECEM -10,636)
  and SMOOTHIE/ICE route113377257 (Vadim +3,771 both; Yizhou +102,559 both).
  No YARN/FARMERS alternative rescues Boey, so that mapping stays incumbent.
  **Pass development only.** Combined candidate SHA `b6ebf9ad…6147c` is
  backed up as `main_candidate_compatible_routes_20260928_b6ebf9ad.py` and
  is running the full 50-fixture both-seat integration/regression panel.
  Native activation ranges, two reacting references and win-point gates are
  frozen separately before those outcomes. Do not combine with rejected
  fb6c5413 or promote on tapes. Main stays exact 4ee; no Kaggle activity.
  Evidence: `diagnostics/compatible_route_pool_20260928/{RESULTS.md,selection.json,NATIVE_PLAN.md}`.

- **2026-09-28 01:54 UTC — exact fb6c5413 uploaded by explicit request.**
  Kaggle accepted `main_candidate_observable_opening_20260928_fb6c5413.py`
  as submission **56625741**, dated 01:54:52 UTC (07:24:52 IST), with status
  **PENDING** when verified at 01:54:57 UTC; there is no score or remote
  validation pass yet. SHA-256 is
  `fb6c54136017eccc9df2652d2826a14346520c6c0d51ce855321ff51be6693f2`.
  Local callable selection and the earlier 100-game integration pass verify
  the exact selected artifact. Its native qualification remains rejected:
  user authorization to upload does not turn it into a strength improvement.
  Main remains SHA `4eeac9c3…783ed` and was not replaced, preserving ongoing
  local experiments. Candidate bytes are separately backed up with the
  upload receipt. No leaderboard/replay download was performed. Evidence:
  `diagnostics/upload_observable_opening_20260928_fb6c5413/upload_receipt.json`.

- **2026-09-28 01:52 UTC — native opening failure traced; route control
  coverage corrected before selection.** Passive seed2908000/seat0 traces
  exactly reproduce current 4ee's +21,597 and rejected selector's -21,317.
  Selector buys both additional land quadrants, loses no animals, and sells
  more MILK (264 versus 138 units) for less money (3,202 versus 7,538).
  Current earns 80,810 WOOL versus selector 6,099, under different native
  shop paths. **Accept diagnosis; no generic feed/land patch is justified.**
  During the finite route-pool screen, exact baseline captures exposed my
  incorrect grouping of winning controls: Yizhou belongs to SMOOTHIE/ICE
  (C), Kaggledew to YARN/FARMERS (B). The original plan/results are preserved;
  `CONTROL_FIX.md` freezes 44 missing affected-control games and excludes
  44 unaffected-control games from selection. Strategies and selection gates
  stay fixed; no route is selected before complete corrected coverage. Main
  remains exact 4ee and Kaggle is untouched. Evidence:
  `diagnostics/opening_probe_v2_20260928/native_failure_ledger.json` and
  `diagnostics/compatible_route_pool_20260928/CONTROL_FIX.md`.

- **2026-09-28 01:36 UTC — opening selector rejected by reacting evidence.**
  Exact `fb6c5413` keeps its 24/50 saved-reply development result, but loses
  all ten completed native games to the public market policy while current
  4ee wins all ten. It selects V43 for that reference. Other completed
  paired blocks match the incumbent: 1W/10D/1L each against 4ee and 12W each
  against V43. After 68 distinct games the pilot was stopped: the candidate
  can earn at most six remaining points against market, below the ten the
  incumbent already holds, so its frozen nonregression gate is impossible.
  All completed games are DONE/DONE/720 with no recorded errors. The raw
  checkpoint also has 32 duplicated keys with identical semantic outcomes;
  the audit retains them but counts each key once. Duplicate execution
  provenance is unconfirmed. **Reject fb6c5413; no confirmation or promotion.**
  Main remains exact 4ee (0/30 loss sweeps, 17/20 top-team sweeps). A separate
  frozen 32-route, 128-game compatible-schedule development search is running
  in `diagnostics/compatible_route_pool_20260928/`; no outcome from it is
  independently validating. No Kaggle activity. Evidence:
  `diagnostics/opening_probe_v2_20260928/{RESULTS.md,pilot.json,audit_pilot_rejection.py}`.

- **2026-09-28 01:31 UTC — separate comparison review, not an upload.**
  `MAIN_COMPARISON_20260928.md` compares current 4ee with the standalone
  root-folder `main_candidate_observable_opening_20260928_fb6c5413.py` and
  summarizes retained, rejected and unfinished research. Readiness is
  **not ready**: 24/50 saved both-seat sweeps, still 17/20 top teams, with
  independent qualification incomplete. Local callable selection verifies
  the intended `kaggle_observable_portfolio_entrypoint`; this is not a full
  file-loader game pass. This review chat briefly duplicated the native
  pilot already launched in the research chat. The review's own process
  was stopped, leaving the original pilot running. At the audit there were
  72 raw checkpoint rows but only 40 unique jobs; all 32 duplicate pairs
  agree on every field except runtime measurements. Raw rows are preserved.
  The resume reader now deduplicates exact jobs and rejects conflicting
  outcomes; duplicate runs receive no extra statistical weight. Candidate
  bytes and qualification criteria did not change. Evidence:
  `diagnostics/opening_probe_v2_20260928/duplicate_execution_audit.json`.

- **2026-09-28 01:24 UTC — complete-route reassessment rejected; opening
  candidate integration passed.** Candidate `61a1dcd6…2b263` changed three
  exact-prefix-compatible second-shop commitments with all descendant
  transitions fixed. All ten saved top-20 pilot games completed cleanly,
  but no failed fixture became a win: DECEM improves -62,163 to -5,114 per
  seat, Boey -20,873 to -19,039, and Vadim worsens -400 to -3,903. Yizhou
  and Kaggledew remain both-seat wins. **Reject this candidate at its
  frozen rescue gate; no conditional wider/native run.** Separately, the
  packaged opening selector `fb6c5413…693f2` completed all 100 integration
  games with exact selected-arm rewards/results, zero errors and all
  incumbent winning seats preserved. Its fresh 96-game native pilot has
  started. A root-folder copy is
  `main_candidate_observable_opening_20260928_fb6c5413.py`; main remains
  exact 4ee. The user now requests a consolidated comparison and upload
  readiness verdict; this is not upload authorization. Evidence:
  `diagnostics/compatible_route_reassessment_20260928/RESULTS.md` and
  `diagnostics/opening_probe_v2_20260928/integration.json`.

- **2026-09-28 01:23 UTC — opening selector integration passed; compatible
  three-route pilot rejected.** Packaged `fb6c5413` completed all 100
  integration games with exact selected-arm/reward parity, DONE/DONE/720
  and zero recorded errors. The frozen 96-game native reacting pilot is
  running; no strength or promotion claim yet. A separate exact-prefix
  compatible complete-route candidate `61a1dcd6` finished ten diagnostic
  games cleanly but rescued none of DECEM, Boey or Vadim. DECEM improved
  from -62,163 to -5,114 per seat, Boey to -19,039, Vadim worsened to
  -3,903; Yizhou and Kaggledew remained wins. **Reject 61a1dcd6 at its
  pilot gate.** Main remains exact 4ee; no Kaggle activity. Evidence:
  `diagnostics/opening_probe_v2_20260928/integration.json` and
  `diagnostics/compatible_route_reassessment_20260928/RESULTS.md`.

- **2026-09-28 01:18 UTC — revised common opening passed its development
  gate.** All 110 prefix checks passed; the 4ee arm matches the complete
  turn-3 state and all 100 full-game incumbent outcomes exactly. All 200
  both-arm development games finished DONE/DONE/720. A bounded rule using
  only rival first-turn cash and net WHEAT buying recovers **7/30** saved
  public-loss replies in both seats while retaining **17/20** top-team
  sweeps (49W/0D/51L across 100 seats), versus 17/50 total incumbent sweeps.
  Its total margin delta is -258,954 but win points are primary. The more
  aggressive 29/50 rule loses two incumbent winning seats and is rejected.
  **Pass the preserving 24/50 rule into separate qualification, not
  promotion.** Packaged candidate SHA `fb6c5413…693f2` is now undergoing
  exact integration checks; native pilot and confirmation criteria were
  frozen before candidate outcomes. DECEM, Boey and Vadim are still lost.
  Main remains exact 4ee; no Kaggle check, download or upload. Evidence:
  `diagnostics/opening_probe_v2_20260928/{RESULTS.md,arms.json,selection.json,NATIVE_PLAN.md}`.

- **2026-09-28 00:58 UTC — first observable-opening fork completed; market
  parity revision in progress.** Its 200 local fixed-tape games all finished
  DONE/DONE/720. The 4ee arm rescued three public-loss pairs and Vadim
  (+3,655 per seat), but lost M & M & P & Q and Unknown Mother-Goose, ending
  3/30 public-loss sweeps and 16/20 top-team sweeps. V43 arm scored 13/30
  and 12/20. The small visible-state selector's best development result was
  28/50 sweeps, with three old top-team wins lost; no allowed rule preserved
  all incumbent wins. **Reject these exact arms for promotion.** The new
  `opening_probe_v2_20260928` revision preserves incumbent trade indices and
  reconstructs the parent observation while commuting two early farmer
  actions. Its first verification process ended without a completed file;
  the harness now frees dynamic modules and checkpoints bounded batches.
  Revised candidate bytes are unchanged during recovery; no full-game v2
  outcome has been read. Main remains exact 4ee; no Kaggle access or upload.
  Evidence: `diagnostics/opening_probe_20260928/RESULTS.md` and
  `diagnostics/opening_probe_v2_20260928/PLAN.md`.

- **2026-09-27 20:03 UTC — V43 full saved-loss screen establishes a
  useful opening basis.** The previously started benchmark completed 60/60
  DONE/DONE/720 games: 26 wins, 34 losses, zero draws; 13/30 both-seat
  sweeps versus current 4ee's 0/30. Summed seat margin improves 944,525
  coins (+236,280 versus −708,245). Exact candidate/manifest hashes verify.
  **Pass its ten-sweep basis gate, not promotion:** the prior top-20 pilot
  still loses all three targets and regresses Majkel. A separate common
  first-investment fork now passes 20/20 first-three-turn physical checks,
  preserving each parent farm/private state except two inert V43 hands,
  and gives both arms identical public step-1 observations. Full 50-entry
  both-arm testing is pending. Evidence:
  `diagnostics/v43_loss_screen_20260928/RESULTS.md` and
  `diagnostics/opening_probe_20260928/{PLAN.md,physical.json}`.

- **2026-09-27 19:34 UTC — broad WHEAT purchase cap rejected at
  feasibility.** Exact successful market-event accounting across the 30
  saved public losses finds 90,882 BUY_PRODUCT WHEAT fills costing
  3,315,483 and 97,981 WHEAT sales receiving 3,577,635, a positive
  262,152 net trade book (positive in every loss). A narrower same-step
  bought-then-resold subset loses 114,824 directly, but also occurs in the
  current Majkel winning control. DECEM's corresponding −6,858 direct
  loss is far below its −62,163 game gap. These flows do not predict the
  rival market response to a cap. **Reject a broad or untested narrow cap;
  no candidate outcomes, main edit or upload.** Evidence:
  `diagnostics/wheat_roundtrip_20260928/FEASIBILITY.md`.

- **2026-09-27 19:25 UTC — early MELON opening rejected as a bounded
  patch.** The current policy first plants MELON on day 6/7/8/9/13/16 in
  4/6/1/14/2/3 of the 30 saved losses, and day 9/10/10 in the DECEM/Boey/
  Vadim top-20 failures. Read-only scan of all 145 complete routes and the
  common 72-step opening found no MELON planting on days 0–5; the earliest
  is step 152/day 6 in five routes. At day 6 the three top-20 failure
  captures fill all 25 NW tiles, hold no MELON seed, and have only 357–860
  cash; the day-0 market queue already uses all ten slots. A day 0–5
  planting requires a new funded whole-opening schedule with displaced
  crop/pasture work, not an additive order. Prior day-six swaps failed
  their margin gates. **Reject an early-MELON overlay; no candidate, main
  edit or upload.** Evidence:
  `diagnostics/early_melon_opening_20260928/FEASIBILITY.md`.

- **2026-09-27 19:24 UTC — single-day MELON harvest/delivery planner
  rejected at feasibility.** Across 30 saved-loss traces and four top-20
  traces, 492 MELON batches reached maturity; only 19 waited more than 24
  turns before harvest (114 eventual units), in nine loss traces and none
  of the four top-20 traces. Only two batches (at most 12 units) have a
  contiguous PASS-only route/harvest/shed/return window without displacing
  scheduled work. No harvested MELON unit waited more than 24 turns before
  shed delivery (maximum 19 turns). Sale attribution had 691 unmatched units,
  so no cash-effect claim was made. **Reject a generic extra harvest-worker
  or single-day planner; no candidate, main edit or upload.** Evidence:
  `diagnostics/melon_harvest_lag_20260928/RESULTS.md`.

- **2026-09-27 19:19 UTC — V43 DECEM mechanism confirms an incompatible
  opening, not a late transplant.** Four exact both-seat fixed-route trace
  reruns reproduced current 4ee margin −62,163 and V43 margin −14,744.
  Opening orders differ at step 0; observations differ at step 1; by day 3
  shops, crop/animal inventory and 22 of 23 overlapping tile records differ.
  By day 18 V43 owns three quadrants versus 4ee's two. V43 makes more
  state-changing harvests (384/420 versus 293/453) and far fewer worker
  non-PASS no-ops (199/6,006 versus 1,149/5,339), but its own market net
  rises 68,589 while the fixed rival's rises 21,170, leaving a loss. The
  earlier five-fixture screen had zero target-seat wins and regressed both
  Majkel control seats. **Reject V43 branch/suffix; no candidate, main edit
  or upload.** Evidence: `diagnostics/v43_decem_mechanism_20260928/RESULTS.md`.

- **2026-09-27 19:11 UTC — current-4ee land retry rejected on saved top-20
  failures.** The frozen conservative candidate (SHA `675893ed…e51`) was
  screened in both seats against DECEM, Boey and Vadim plus winning DSM and
  Majkel controls, ten DONE/DONE/720 native-engine games on exact saved
  action tapes. DECEM's margin improved from −62,163 to −15,338 in both
  seats, but stayed a loss. Boey/Vadim were unchanged losses; both controls
  remained wins. **Zero target seats flipped**, so the predeclared wider
  panel gate failed. Reacting native eligibility in the separate plan was
  previously absent in its first 64 seed scan; there is no promotion basis.
  Reject the retry as a top-20 fix; `main.py` and Kaggle status unchanged.
  Evidence: `diagnostics/land_retry_top20_20260928/{PLAN.md,RESULTS.md,screen.json}`.

- **2026-09-27 19:00 UTC — blanket earlier MELON/MILK sale rejected at
  feasibility.** The 30 exact loss traces contain 3,594 MILK and 332
  MELON turns with positive shed stock and no sale; four current top-20
  traces contain 317 and 12. At the first held turn, historical quoted
  prices imply only 2,179 MILK and 2,880 MELON aggregate gross coins from
  selling earlier across all 30 losses, before shared-market response;
  MILK favors earlier sale in only 17/30 episodes. Some held turns have a
  full 10-order queue (293 MILK turns) or scheduled purchases (1,755 held
  turns). An older movement-based timing patch improved 211–379 coins but
  rescued no saved loss. **Reject a blanket timing overlay; no candidate
  outcomes, main edit or upload.** Evidence:
  `diagnostics/sale_timing_20260928/FEASIBILITY.md`.

- **2026-09-27 18:55 UTC — three historical complete policies rejected on
  frozen top-20 failures.** Saved standalone decoded V43, full V48 and
  search-v2 were each run in both seats against DECEM, Boey and Vadim plus
  DSM/Majkel winning controls (30 local games, all DONE/DONE/720). None won
  or drew any of the six target seats. V43/V48 gave identical panel results,
  narrowed DECEM from −62,163 to −14,744 per seat but worsened Boey/Vadim
  and lost both Majkel control seats. Search-v2 lost all ten seats. **Reject
  these complete-policy replacements; no new trigger, main edit or upload.**
  These fixed tapes do not validate reacting strength. Evidence:
  `diagnostics/historical_policy_screen_20260928/{PLAN.md,RESULTS.md,screen.json}`.

- **2026-09-27 18:54 UTC — broad melon/milk or early-sale patch rejected
  at feasibility.** Across the 30 local losses, own MELON units sold are
  greater/equal/fewer than the rival in 15/2/13 games and MILK in 16/1/13,
  yet MELON cash trails in 26/30 and MILK in 25/30. In 34 exact traces,
  own first MELON sale is essentially the first shed-stock day; the average
  sale day trails rivals by 13.3 days, pointing to late production rather
  than held stock. Only one strict actionable earlier MELON sale window
  appears, at quote 221 versus the actual next-day 223. Nine comparable
  MILK windows have next-day prices usually higher. Same-turn queue
  position differences are too small to explain the gap. **Reject a
  blanket volume or timing overlay; no candidate outcome test, main edit or
  upload.** A new state-aware physical planner would need verified funding,
  travel, harvest, delivery, feed and market execution. Evidence:
  `diagnostics/dynamic_portfolio_20260928/FEASIBILITY_20260928.md`.

- **2026-09-27 18:42 UTC — compatible day-six melon route screen rejected
  at feasibility.** The exact first-two-shop branches shared the incumbent's
  full action prefix through step 143 and matched all three saved current
  top-20 failures, but occurred in only **1/30** local live losses and
  **3/54** live wins; they also occurred in two winning top-20 controls.
  Compatible replacement routes request only +1/+4/+3 additional MELON
  plants after the switch, with other schedule changes. A generic visible
  melon gap marks 30/30 losses but also 53/54 wins, so it is not a
  selective trigger. Earlier route switches failed their fixed-tape gain
  or native paired-margin gates. **Reject before candidate outcome games;
  no main edit or upload.** Evidence:
  `diagnostics/portfolio_research_20260927/FEASIBILITY.md`.

- **2026-09-27 18:38 UTC — frozen local target baseline complete.** The
  downloaded 30 public-loss replies were replayed with exact 4ee in both
  native seats: **0W/0D/60L**, all DONE/DONE/720. All 30 original-seat
  rewards/margins reproduce the saved public episodes exactly; the opposite
  seat also loses all 30. Only two episodes have seat-dependent margins
  (114252835: −5,282/−3,023; 114274897: −42,560/−41,698). The local
  manifest records these 30 fixtures plus 20 already downloaded current
  top-team entries (17/20 both-seat wins), 50 entries from 48 distinct
  episodes. These are fixed-action regression targets, not reacting-policy
  validation. **Accept baseline audit; no promotion decision or main edit.**
  Evidence: `diagnostics/loss_class_20260927/{RESULTS.md,local_target_manifest_180951.json,live_loss_tape_baseline_180951.json}`.

- **2026-09-27 18:38 UTC — terminal market cleanup rejected at feasibility.**
  In the current Vadim top-20 loss (−400), the final market sells all
  marketable stock; no worker actions fail to change state. In 20 live
  losses under 10,000 coins, 18 also end with no sellable stock. The two
  remaining residual holdings could recover at most 71 and 161 coins,
  below their respective loss margins. **No repeated liquidation defect,
  candidate, main edit or upload.** Evidence:
  `diagnostics/near_margin_20260927/FEASIBILITY_20260928.md`.

- **2026-09-27 18:27 UTC — early worker watering bundle rejected at
  feasibility.** A separate candidate hired four workers for 7 coins on
  day 1 and made 58 valid moves and 20 state-changing WATER actions on 19
  wheat and one strawberry tile in each saved DECEM/Majkel source trace.
  Wheat at crop age 1 gained no yield; the next planned delivery remained
  21 wheat in shed and `SELL WHEAT 18`, with the same 12 wheat plots
  harvested/replanted. Fixed-tape margin changes were **−1,242** and **−7**
  coins. **Reject before native strength testing; no main edit or upload.**
  Reserved seeds 2721000–2721031 remain unused. Evidence:
  `diagnostics/early_workers_20260927/RESULTS.md` and
  `source_tape_replay.json`.

- **2026-09-27 18:16 UTC — same-turn funded land-order candidate rejected.**
  On 16 fresh native seeds in both seats with original shops and reacting
  references, moving an already scheduled `BUY_LAND` after sales activated
  on 12/16 seed pairs versus current main but scored **0W/8D/8L** paired
  outcomes against it, versus 16 draws for self-control (paired margin
  −250). Against the public-market reference it dropped from the incumbent's
  16/16 paired wins to **14/16**, with paired-margin delta **−225,318**;
  candidate cash fell 126,870 while rival cash rose 98,448. Both files
  swept c68 with only +28 candidate paired-margin coins. All 160 games
  across five development blocks completed cleanly. **Reject; no
  confirmation, main edit or upload.** Fixed top-20 tapes did not rescue
  DECEM, Boey or Vadim and were diagnostics only. Evidence:
  `diagnostics/production_bundle_20260927/{PLAN.md,RESULTS.md}` and five
  keyed development JSON files.

- **2026-09-27 18:09:54 UTC — latest official 4ee live snapshot.** Kaggle
  submission 56609430 remains COMPLETE with publicScore **2551.5**,
  uploaded 13:10:15 UTC. The team leaderboard is rank **136**, Score
  **2572.1**; rank 10 Score **2847.2**. The team score currently equals
  the older c68 submission 56602057's publicScore (2572.1), which exceeds
  the new 4ee submission's 2551.5; the team rank must not be attributed to
  a score gain from 4ee. Eight more public games were
  downloaded without outcome filtering (4W/4L), making the complete
  **84-game cohort 54W/30L/0D**. All 85 raw replay hashes including
  validation verify, with zero failed paths; remote validation parity remains
  PASS. New losses were Yaroslav −324, Ghost Rule −4,243, leave you −7,748,
  and Navier-stokes −7,764. No new upload or main edit. Evidence:
  `diagnostics/new_live_56609430_20260927/snapshot_180951/summary.json`,
  `cohort_180951.json`, `delta_180951.json`, and `RESULTS.md`.

- **2026-09-27 17:47:25 UTC — latest official 4ee live snapshot.** Kaggle
  submission 56609430 remains COMPLETE with publicScore **2554.6**,
  uploaded 13:10:15 UTC. The team leaderboard is rank **137**, Score
  **2568.5**; rank 10 Score **2852.4**. Nine additional public games were
  downloaded without outcome filtering (5W/4L), making the complete
  **76-game cohort 50W/26L/0D**. All 77 raw replay hashes including
  validation verify, zero failed paths; remote validation parity remains
  PASS. New losses: THIRD FARM CLUB −42,560, leave you −2,999,
  boominginging −26,613, and fuxi −14,244. No new upload or main edit.
  Evidence: `diagnostics/new_live_56609430_20260927/snapshot_174722/summary.json`,
  `cohort_174722.json`, `delta_174722.json`, and `RESULTS.md`.

- **2026-09-27 17:46 UTC — early hire-only intervention rejected at
  feasibility.** In the fresh DECEM/Majkel source-seed traces, our policy
  has 96–98 coins and only one market order at step 24, while the rival
  hires three or four workers for 4–7 coins. Cash and queue slots permit
  those hires, but our route emits **zero hand commands on steps 25–47**;
  later command lists are sized to existing hires. Rival worker actions
  cannot be transplanted because only 12/25 and 10/25 exact tile states
  match at step 24, falling to 5/25 and 6/25 by step 72. **Reject adding
  HIRE orders without a new state-aware task, feed, crop, harvest and sale
  schedule.** No candidate, native test, main edit or upload. Evidence:
  `diagnostics/market_portfolio_20260927/HIRE_FEASIBILITY.md`.

- **2026-09-27 17:32 UTC — newer official top-20 replies fully checked.**
  A new 17:23–17:25 UTC leaderboard snapshot has 20 current teams,
  including new rank-18 Kaggledew Valley 🏆. Their latest completed public
  episodes were created 16:37–17:17 UTC today; all 20 raw replay and action
  hashes verify, and the 18 distinct episodes have **zero overlap** with
  the earlier 16:35 panel. Exact uploaded 4ee won both native original-shop
  seats against **17/20** teams and **7/10** current top-ten teams (34W/6L
  seats), all 40 DONE/DONE/720. Current two-seat failures: DECEM rank 1
  −62,163, Boey rank 3 −20,873, Vadim Vasilenko rank 5 −400. Majkel1337
  became a win on a *different episode*; this does not show a policy gain.
  Native shops at turn 144 differ from the source replay for 16/20 teams;
  fixed tapes remain diagnostic only. **Accept the complete fresh panel;
  reject an all-top-20 or top-10 claim.** No main edit or upload. See
  `diagnostics/current_top20_20260927_172258/RESULTS.md`, `summary.json`,
  `manifest.json`, and `assessment.json`. A paired c68 counterfactual on the
  exact three current failing tapes also loses all six seats: DECEM −62,163,
  Boey −18,260, Vadim −363 per seat. **Reject simple c68 reversion** as a
  rescue for these new replies; see `prior_top3.json`.

- **2026-09-27 17:23:00 UTC — latest read-only Kaggle check.** Submission
  56609430 is still COMPLETE, uploaded 13:10:15 UTC, with publicScore
  **2551.6**. The team leaderboard is rank **145**, Score **2563.4**, versus
  rank-10 Score **2867.7**. One new public episode, 114271958 versus
  offhand, was downloaded and SHA-256 verified: loss by 7,539 coins. The
  complete 67-game public cohort is **45W/22L/0D**, all 68 raw hashes
  including validation verified, zero failed paths, and remote validation
  parity remains PASS. The current `main.py` still hashes to 4eeac9c3;
  no new upload occurred. Evidence:
  `diagnostics/new_live_56609430_20260927/snapshot_172258/summary.json`,
  `cohort_172258.json`, `delta_172258.json`, and `RESULTS.md`.

- **2026-09-27 17:22 UTC — same-item queue guard rejected.** Candidate
  `f8ba6524...24b873c` retained the purchase-queue order whenever an action
  simultaneously bought and sold the same product; it activated 74–116 turns
  in each of the five targeted fresh top-20 tapes. All ten both-seat native
  original-shop games finished DONE/DONE/720. It still lost both seats to
  DECEM, Boey, Vadim Vasilenko and Majkel1337; Yizhou stayed a win but did
  not recover its earlier c68 margin. **Reject at the frozen targeted gate;**
  do not run the conditional full top-20 or reacting native panels. The
  uploaded `main.py` and Kaggle status remain unchanged. See
  `diagnostics/same_item_queue_guard_20260927/PLAN.md`, `RESULTS.md` and
  `targeted.json`.

- **2026-09-27 17:12:01 UTC — final 4ee live cutoff extended.** Kaggle
  submission 56609430 remains COMPLETE with publicScore **2557.4**; its
  LastSubmissionDate is still 13:10:15 UTC. Team leaderboard rank is **139**,
  team Score **2567.3**; rank 10 Score **2872.8**. Five newly completed
  public games were downloaded without outcome filtering (3W/2L), making
  **66 games: 45W/21L/0D** at this cutoff, all 67 replay hashes including
  validation verified, zero failed paths. Exact current `main.py` and the
  uploaded backup both hash to 4eeac9c3...f783ed; remote validation parity
  still passes. This is the final read-only status check, not a new upload.
  Evidence: `diagnostics/new_live_56609430_20260927/snapshot_171158/summary.json`,
  `delta_171158.json`, `cohort_171158.json`, and `RESULTS.md` there.

- **2026-09-27 17:12 UTC — day-10 third-land response infeasible from the
  saved route library.** The observable rival-installation/cash warning fires
  in 8 live losses and 4 live wins. All 12 already buy our third quadrant
  successfully at steps 241/242/266; by step 312, eight have 25/25 SW
  installations, two have 23/25, and two losses on route 113784024 have
  11/25. Those sparse cases have 14 unbuilt SW tiles, but their existing
  seed, hire, animal care, harvest and delivery schedule lacks a compatible
  saved replacement. Across 145 embedded routes, no *distinct* continuation
  matches any flagged game's first-240 worker actions and investment orders;
  matching IDs are full 719-turn duplicates. The four step-266 land cases
  split 2 wins/2 losses, and the two losing BAKERY/PIZZA cases have only
  1,642/1,541 cash at step 240 before the incumbent's wheat and hire bundle.
  **Reject a blind land order, partial overlay or generic route splice; no
  candidate or independent experiment plan is justified yet.** No main edit
  or upload. Evidence: `diagnostics/third_land_response_20260927/RESULTS.md`,
  `route_and_execution.json` and the hash-verified 4ee live replays.

- **2026-09-27 17:09 UTC — live day-6/day-10 structural trigger rejected
  for policy change.** All 61 hash-verified public replays (42W/19L) show
  day-10 median own installations 50 in both losses and wins, versus rival
  61 in losses and 50 in wins. An observable day-10 rule (rival ≥8 plots
  ahead and rival cash no higher) catches 8/19 losses but also 4/42 wins,
  including rank-100 and rank-105 opponents. The narrower post-hoc Pizza
  plus rival-third-land marker catches 6/19 losses and 0/42 wins against
  five teams, but all six already buy our third land at steps 241/242/266;
  five fill its 25 southwest plots by step 312. A generic extra land or
  simple worker action is not an executable rescue. Preserve the signal as
  exploratory; **reject a candidate/promotion from this audit** pending a
  full funded production and market-response schedule with fresh reactive
  both-seat validation. No `main.py` edit or upload occurred. See
  `diagnostics/new_live_56609430_20260927/structural_audit/RESULTS.md`.

- **2026-09-27 17:01 UTC — guarded 4ee seed-prefund candidate rejected.**
  Exact uploaded 4ee plus a final, simulator-guarded adjacent SELL-before-
  BUY_SEED swap is preserved as isolated `d8b8c293...`; main stays exact
  4ee and no upload occurred. Fresh16:35 top20 replay development completed
  40/40 DONE/DONE/720, zero errors, six activated games, 16/20 both-seat
  sweeps unchanged. Boey worsened -2,819→-6,510 and Vadim -5,821→-7,355
  per seat; neither required loss flipped. DECEM improved -63,151→-11,602
  but still lost. Matched traces show one added seed and identical worker
  action lists, then changed tile occupancy and third native shops. **Reject
  at the frozen first win gate; skip the conditional 300 replays and native
  confirmation.** The previous 7673 funding coverage rejection remains.
  See `diagnostics/seed_prefund_20260927/RESULTS.md` and the independent
  diagnosis in `diagnostics/new_main_failure_diagnosis_20260927/RESULTS.md`.

- **2026-09-27 16:53:09 UTC — 4ee live cohort extended.** Submission
  56609430 remains COMPLETE with publicScore **2550.1**. Four new completed
  public games since 16:41 were downloaded and hash-checked (3W/1L), making
  the cutoff **61 games: 42 wins, 19 losses, no draws**, zero failed paths.
  Team leaderboard: rank **138**, Score **2567.3**, LastSubmissionDate
  13:10:15 UTC; rank 10 Score 2872.5. The leaderboard score continues to
  equal the prior c68 submission's score, not this new submission score.
  Validation parity still passed. No new upload or main edit occurred.
  Evidence: `diagnostics/new_live_56609430_20260927/snapshot_165306/summary.json`,
  `diagnostics/new_live_56609430_20260927/cohort_165306.json`.
- **2026-09-27 16:52 UTC — old c68 does not rescue the 18 new live losses.**
  On the fixed opponent action tapes of all 18 current 4ee live losses,
  c68 and 4ee each lose all 18 original-seat and all 18 swapped-seat games.
  72/72 native games DONE/DONE/720 with zero errors. Exact 4ee reproduces
  both live cash totals in every original-seat loss. Across 36 paired seats,
  4ee has +8,201 total relative margin over c68 (mean +227.8), with mean
  own cash -317.0 and rival cash -544.8. These losses were selected after
  observing 4ee; saved actions are not independent reactive validation.
  **Reject reverting to c68 as a fix for these 18 failures.** Evidence:
  `diagnostics/new_live_56609430_20260927/c68_loss_counterfactual/RESULTS.md`.
- **2026-09-27 16:41:44 UTC — latest 4ee public cohort.** Kaggle
  submission 56609430 remains COMPLETE. Its displayed publicScore is
  **2537.3** after 57 completed public episodes; all 57 replays are
  downloaded and hash-checked: **39 wins, 18 losses, no draws**, zero failed
  replay paths. The final two new episodes since 16:35 both lost: -19,196
  versus pensukesan and -9,211 versus keiz. The team leaderboard still shows
  rank **137**, Score **2572.2** (equal to the earlier c68 submission's
  current score), LastSubmissionDate 13:10:15 UTC; rank 10 is 2872.5.
  Remote validation parity passed. This upload did not meet the top-10 or
  all-opponent goals. Preserve 4ee while diagnosing current live and top-20
  losses; no second upload was made.
  Evidence: `diagnostics/new_live_56609430_20260927/snapshot_164140/summary.json`,
  `diagnostics/new_live_56609430_20260927/cohort_164140.json`, and
  `diagnostics/new_live_56609430_20260927/validation_parity.json`.
- **2026-09-27 16:35:22 UTC — fresh top-20 recorded-action assessment.**
  The official snapshot's 20 teams and latest completed public replays were
  newly downloaded. Source games were created 2026-09-27 15:45:33–16:29:24
  UTC, with zero episode overlap with yesterday's top-20 or today's 11:37
  top-100 panel. Exact uploaded 4ee won both seats against **16/20**,
  including **6/10** top-ten teams; 40/40 games DONE/DONE/720, 32W/8L,
  zero recorded errors. Four current top-ten losses in both seats: DECEM
  (rank 1, -63,151), Boey (rank 3, -2,819), Vadim Vasilenko (rank 5,
  -5,821), Majkel1337 (rank 6, -77,373). Prior uploaded c68 on exactly
  the same tapes and both seats also went 16/20 and 32W/8L, with no outcome
  change; 4ee's total seat cash margin was 40,477 lower. Native shops at
  turn 144 differed from the source recording for 16/20 teams, and none
  of these source episodes overlaps submission 56609430's live episodes,
  so no direct live cash parity case is available in this panel. **Accept
  the complete assessment; reject an all-top-20 sweep or replay-only policy
  promotion claim.** Fixed action tapes do not independently validate
  outcomes against reacting private policies. The Yizhou mechanism audit is
  recorded below; no policy edit or upload. Evidence:
  `diagnostics/current_top20_20260927_163500/RESULTS.md`, `MATCHUPS.md`,
  `summary.json`, and `manifest.json`.
- **2026-09-27 16:49 UTC — Yizhou queue-order regression diagnosed, no fix
  promoted.** On the fresh rank-15 tape, 4ee still wins both seats but loses
  31,655/30,648 margin versus c68: own cash falls 13,787/13,011 and rival
  cash rises 17,868/17,637. Seat-0 traces have identical physical actions
  and market-order multisets for all 719 turns; 75 queue orders differ. The
  first cash effect is day-7 step 170, then a 6-coin rival cash difference
  at day-10 step 251 lets it buy 4,000-coin SE land in 4ee's game while
  c68's rival misses that purchase. A one-turn override restoring c68's
  step-170 queue **did not** prevent that land purchase and reduced 4ee's
  margin by 10 more coins. **Accept the mechanism diagnosis; reject a
  step-170-only fix and any promotion from one fixed tape.** A broader
  same-item buy/sell ordering guard remains untested. Main and Kaggle are
  unchanged. See
  `diagnostics/current_top20_20260927_163500/YIZHOU_MECHANISM.md`.
- **2026-09-27 17:05 UTC — fresh DECEM/Majkel production gap and complete
  tape pilots rejected.** In exact 4ee native seat-0 loss traces, both
  rivals have three land quadrants by the end of day 18 versus our two.
  Through that day, their worker non-PASS no-change counts are 8/59 versus
  our 375/424; terminal counts are 43/65 versus our 1,149/1,043.
  Successful market sale-minus-purchase cash at terminal is 136,444 versus
  our 71,892 against DECEM and 158,772 versus our 78,272 against Majkel.
  Our WHEAT buy/sell recycling spends 145,804/114,695 on product purchases
  with little net gain, while the rivals' crops and animals earn high
  receipts. A frozen native pilot of both complete rival action tapes on
  three fresh original-shop seeds in both seats finished DONE/720 but lost
  **all 12 games** to reacting 4ee. DECEM's tape retained three land and
  productive worker execution, yet its strawberry receipts fell sharply
  under different shops; Majkel's tape lost a land quadrant on two seeds
  and had 1,027 no-change worker commands on the audited new seed. A
  passive 145-route screen found no distinct day-18-to-end suffix
  compatible with either incumbent day-6-to-17 schedule. **Accept the
  funded-production/worker gap as a diagnosis; reject both fixed complete
  tapes and an existing late-route switch for promotion.** Keep main and
  Kaggle unchanged. See
  `diagnostics/current_top20_20260927_163500/STRUCTURAL_AUDIT.md` and
  `diagnostics/current_top20_20260927_163500/FULL_TAPE_PILOT_RESULTS.md`.
- **2026-09-27 17:11 UTC — DECEM/Majkel shop-reveal suffix splices rejected.**
  On each tape's source seed, the first two public shops match the original
  recording, but the 4ee incumbent and taped rival differ from action step 0
  through all 144 pre-second-reveal actions. At first reveal step 72, only
  9/25 DECEM and 11/25 Majkel occupied tile coordinates match our crop or
  animal type; at second reveal step 144, only 8/25 and 5/25 match. Our
  opening has wheat/strawberries and fewer cows, while the rival tapes
  require established melon plots and different pastures. Cash is higher
  for us at both reveals, but does not reconcile tile and worker schedules;
  preceding step-143 hand positions have zero overlap for both opponents.
  Recorded-source and native-replayed target layouts agree. **Reject
  direct shop-conditional tape suffix transplant; no candidate, untouched
  activation panel, main edit or upload.** Evidence:
  `diagnostics/current_top20_20260927_163500/TRANSPLANT_COMPATIBILITY.md`
  and `transplant_compatibility.json`.
- **2026-09-27 16:35:53 UTC — submitted 4eeac9c3 confirmed COMPLETE.**
  Kaggle submission **56609430** was received at 13:10:15 UTC and its
  validation episode **114183268** completed at 13:15:09 UTC. The submission
  page publicScore is **2550.2**. The contemporaneous team leaderboard row
  reports rank **137**, Score **2572.2**, and LastSubmissionDate
  **2026-09-27 13:10:15 UTC**; rank 10 is 2869.5. The leaderboard score
  equals the older c68 submission's current 2572.2, while the new file's
  publicScore is 2550.2. The upload did not improve the displayed rank.
  The screenshot showing c68 from five hours earlier predates this
  upload. The current `main.py` SHA-256 still matches the uploaded 4ee backup.
  All 55 public episodes in the snapshot and the validation replay have been
  downloaded with exact raw hashes. The public outcomes are 39 wins, 16
  losses, no draws; every replay is DONE/DONE over 720 frames with 719
  actions per seat. The remote validation replay exactly matches the uploaded
  4ee backup loaded as `kaggle_purchase_iterated_entrypoint`: both players'
  719 actions and final cash [104134, 104134] agree with local native
  execution, DONE/DONE. No duplicate upload is needed.
  Evidence: `diagnostics/new_live_56609430_20260927/snapshot_163551/summary.json`,
  `diagnostics/new_live_56609430_20260927/cohort_163551.json`,
  `diagnostics/new_live_56609430_20260927/validation_parity.json`, and
  `diagnostics/shunki_purchase_iterated_20260927/promotion_receipt.json`.
- **2026-09-27 13:10 UTC — 4eeac9c3 promoted and uploaded as56609430.**
  Currentmain SHA-256:
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
  All frozen pilot,300 replay,256 native and both-seat file-loader gates
  passed. The final callable is`kaggle_purchase_iterated_entrypoint`.
  Local file/direct execution matches all719actions of both players and both
  cash totals in both seats; runtime budgets remain positive. **Accept promotion
  and this user-authorized upload.** The then-current PENDING status has since
  resolved to COMPLETE, as recorded above. Oldmain backup:
  `main_before_purchase_iterated_20260927_c68fa46f.py`; uploaded backup:
  `main_uploaded_purchase_iterated_20260927_4eeac9c3.py`.
  The one-upload authorization is consumed. Top10/all50 goals remain
  unfinished. Evidence: diagnostics/shunki_purchase_iterated_20260927/
  promotion_receipt.json,loader_parity.json andRESULTS.md.

- **2026-09-27 13:08 UTC — 4eeac9c3 independent confirmation passed.**
  All256 native games DONE/720, zero recorded errors. New candidate124W/4L
  versus old32W/32D/64L across four references. New wins:c68 32/32,
  purchase43d 32/32,iterated3bd 28/32,1f 32/32; no reference regression.
  Pooled paired-seed win-point gain95% bootstrap interval[0.546875,0.625].
  Both included components activate in both seats of all16 seeds against
  every reference. **Accept the frozen independent confirmation.** File
  loader verification is running; main remainsc68 until both seats pass.
  One upload remains authorized. Evidence: diagnostics/
  shunki_purchase_iterated_20260927/confirmation.json.

- **2026-09-27 12:52 UTC — 4eeac9c3 all300 replay regressions passed.**
  All300 fresh candidate games DONE/720, zero recorded errors, no lost
  incumbent winning seat. Recent11:37 external99 remains73sweeps/146wins;
  recent50 remains36sweeps/72wins; original50 remains44sweeps/88wins.
  The separate self-control wins both seats. **Accept the frozen regression
  gate; no replay win-rate improvement is claimed.** The untouched256-game
  native confirmation has started, old/new versus four reacting policies,
  with both seats and original shops. Main remainsc68; upload approval
  unconsumed. Evidence: diagnostics/shunki_purchase_iterated_20260927/
  RESULTS.md and panels.json.

- **2026-09-27 12:43 UTC — 4eeac9c3 recent100 regression subset complete.**
  All200 games against the11:37 panel are DONE/720 with zero recorded errors.
  External results remain73/99 both-seat sweeps,146W/52L; current50 remains
  36/50. No prior winning seat is lost. The own-team self-control wins both
  seats and is reported separately. **Accept this regression subset only**;
  the original50, untouched native confirmation and file-loader checks
  remain required. No promotion/upload yet; main remainsc68. Evidence:
  diagnostics/shunki_purchase_iterated_20260927/panels.json (still running).

- **2026-09-27 12:24 UTC — 4eeac9c3 native development pilot passed.**
  Fresh2712000–7, both seats:16W/0L versus uploadedc68,15W/1L versus43d,
  12W/4L versus3bd. All48DONE/720, zero errors. Both components and second
  search pass activate in every paired case. **Accept pilot, no promotion
  yet.** Running all300 recent100/original50 regressions before the frozen
  independent confirmation. Main staysc68; upload authorization unconsumed.
  Evidence: diagnostics/shunki_purchase_iterated_20260927/PILOT_RESULTS.md.

- **2026-09-27 12:19 UTC — new composition4eeac9c3 built; pilot running.**
  Exact purchase-only43d plus the unchanged two-pass3bd tail is a genuinely
  new composition. Exclude7673's rare funding arm because its coverage gate
  failed. Freeze a new plan before outcomes:48 fresh native pilot games,
  300 recent/original replay regressions,256 independent native confirmation
  games, then both-seat all-action file-loader parity. The earlier43d/3bd/
  7673 rejections remain valid. Main staysc68; root candidate backup saved.
  One new upload is authorized by the user's current explicit update request.
  Evidence: diagnostics/shunki_purchase_iterated_20260927/PLAN.md and
  build_manifest.json. No strength conclusion or upload yet.

- **2026-09-27 12:10 UTC — economics rejection and structural audit complete.**
  Native reconstruction matches both players' cash at all719turns in both
  tomato cases. The fixed-shop/trade-quantity model loses15358 relative cash
  against Driz, turning a win into a modeled loss; gains5466 against liminhai
  but retains a large deficit. Assumed delivery capacity fails by two units
  once in both games. **Reject the broad tomato substitution direction**;
  no full candidate. Separately, all99 latest external tapes offer only two
  normalized early schedule alternatives and none after216. **Accept only
  the structural shortlist**, not state compatibility or strength. Evidence:
  diagnostics/scheduled_tomato_economics_20260927/RESULTS.md and
  diagnostics/fresh_schedule_compatibility_20260927/RESULTS.md.

- **2026-09-27 12:05 UTC — latest78 live games:53W/25L, rank120.**
  c68 remains COMPLETE at score2598.6; rank10score2884.8. Every listed
  completed public episode is audited, allDONE/DONE/720. The seven new
  games are1W/6L. **Accept live audit; goal remains unfinished.** Exact
  localmain still matches uploadedc68backup. Evidence:
  diagnostics/disjoint_live_audit_20260927/RESULTS_1205.md and
  diagnostics/disjoint_upload_20260927/live_120556/summary.json.

- **2026-09-27 11:56 UTC — latest full current100 assessment completed.**
  Frozen11:37 snapshot: all100 team tapes freshly downloaded from87
  distinct episodes created11:05–11:37UTC; zero episode overlap with the
  morning100 or original50 panels. Main exactc68. All200gamesDONE/720,
  zero errors. Excluding our rank98 self-control: top10 7/10sweeps,
  top50 36/50, full current100 73/99 external sweeps and146W/52L/0D.
  The self-control wins both seats+20700 and is excluded from opponent
  performance.26external matchups remain lost; Boey/DECEM/Majkel are the
  top10 losses.54/99 native shop prefixes differ from recording at144.
  Both final cash totals match real Kaggle outcomes in the original seats
  of the two overlapping live episodes (ready or not, Matt Motoki).
  **Accept the complete fresh assessment; reject an all-current100 or
  live-top10 success claim.** Do not interpret different-panel results as
  a policy change. Preserve old77/100 and original44/50 regressions.
  No promotion/upload; no active experiment processes remain. Evidence:
  diagnostics/current_top100_20260927_1137/RESULTS.md, MATCHUPS.md,
  summary.json and assessment.json; root CURRENT_LEADERBOARD_REPORT_20260927.md.

- **2026-09-27 11:50 UTC — earlier harvest fits existing late crop work.**
  A new isolated native recipe retains positions and replaces ripe
  age8–10 FERTILIZE with HARVEST, and age11 WATER with final HARVEST.
  All28 demand-eligible plots produce4tomatoes each before decay using
  two changed commands and no additional fertilizer/workers/land. Their
  original schedules produce8strawberries each. **Accept mechanical
  feasibility only, not economic value or promotion.** Delivery, seed
  procurement, foregone strawberry sales and shared-price effects remain
  untested. The preceding unchanged-schedule rejection remains valid.
  No policy edits during the new100 assessment; main exactc68. Evidence:
  diagnostics/scheduled_tomato_harvest_20260927/RESULTS.md.

- **2026-09-27 11:47 UTC — latest71 live games:52W/19L, rank98.**
  The11:37 official listing is fully audited, allDONE/DONE/720; eight new
  games are3W/5L. Against teams in that snapshot's top100, the cohort has
  23games:7W/16L, including repeats. c68score2623.8; rank10score2876.7.
  **Accept complete live audit; goal remains unfinished.** The new11:37
  top100 collection is complete at100tapes/87distinct episodes. Rank78
  renamed MacCook→MAC; exact same team/submission IDs resolve its original
  latest episode, documented before testing.200native replay games are
  now running on immutable c68, with own rank98 tape a separate control.
  Evidence: diagnostics/disjoint_live_audit_20260927/RESULTS_1137.md and
  diagnostics/current_top100_20260927_1137/identity_receipt.json.

- **2026-09-27 11:38 UTC — two cheaper crop routes rejected mechanically.**
  Nine baseline traces over starts13–18 contain no owned six-cell area
  free for12 days, and every12-day span has a day without a terminal
  four-action PASS window. Reject the proposed free-land/free-labor route;
  broader rescheduling is not tested. An isolated native audit reproduces
  all86 late strawberry plots exactly (8 harvested units each). All28
  plots with two or more visible tomato-demand shops harvest zero tomatoes
  if only the seed/crop is changed: their harvest schedule is too late.
  **Reject simple crop substitution; no candidate or full games.**
  Main remains c68. Evidence: diagnostics/auxiliary_low_cost_audit_20260927/
  RESULTS.md and diagnostics/scheduled_crop_substitution_20260927/RESULTS.md.

- **2026-09-27 11:38 UTC — current100 refreshed again from official snapshot.**
  Official11:37:26UTC snapshot has team rank98, c68 score2623.8, rank10
  score2876.7, and71 completed public episodes. A new complete top100
  collection is starting under a frozen protocol; no prior replay results
  will be reused. Our own rank98 row is a self-control, so external-opponent
  performance will be reported over99 teams. Preserve the07:27 panel and
  original50 regression unchanged. No upload; main exact c68. Evidence:
  diagnostics/current_top100_20260927_1137/PLAN.md and live_113723 receipt.

- **2026-09-27 11:30 UTC — auxiliary tomato 1c1fb72a rejected.**
  Complete nine-game, both-seat development comparison: old10W/8L,
  new8W/10L. Every activated case successfully plants12, harvests48 and
  delivers48 with zero errors; six inactive pairs retain their results.
  Driz margin improves9617→11141, liminhai -38375→-15170, but istinetz
  falls5269→-6680 in both seats. **Reject the original development gate;
  no conditional native pilot, panels, confirmation or upload.** The
  root candidate backup is preserved; main remains exact c68. Passive
  native cash diagnosis matches both totals with zero unexplained cash.
  Delta own/rival is +488/-1036, -19039/-42244, and -15879/-3930
  respectively. Added land/wages cost7804/7804/9689; net tomato gains
  only1687/466/3290. Future shops change in all three, so the margin gain
  is not evidence that the extra crop pays for itself. Accept diagnosis;
  investigate cheaper executable commitments before a new policy.
  Evidence: diagnostics/shunki_auxiliary_tomatoes_20260927/RESULTS.md,
  DIAGNOSIS_RESULTS.md, development.json and diagnosis.json.

- **2026-09-27 11:30 UTC — latest63 live games:49W/14L, rank99.**
  Official11:09 snapshot: c68 COMPLETE, score2630.0, team rank99,
  rank10 score2886.7. All63 completed episodes downloaded, all
  DONE/DONE/720. The12 new games are5W/7L. At this snapshot13 games
  involve current top100 teams:4W/9L, including repeated opponents.
  **Accept the unfiltered audit; top10/all50 remain incomplete.**
  No upload or main change. Evidence: diagnostics/
  disjoint_live_audit_20260927/RESULTS_1109.md and live_110915 receipt.

- **2026-09-27 11:03 UTC — separate crop field passes mechanical delivery audit.**
  The unused SE field can support12 tomatoes with two extra workers after
  baseline hiring. Native mechanics produce48 units. The first midnight-only
  design fails shed capacity in all relevant starts and is rejected. A new
  physical schedule harvests/delivers at ages9 and11 and waters at age10:
  two12-unit drops at worst-case hours17/21, no early weeds, full48 delivered.
  Whole factual baseline cash stress (all added wages/land/seeds, no extra
  revenue) and joint delivery-capacity checks admit starts15–18 in the
  liminhai loss,13–18 in Driz Lo,16–18 in istinetz; other six lack demand.
  **Accept feasibility only; next build a separate observable-state candidate.**
  No future recorded states may enter its rule. Main remains c68. Evidence:
  diagnostics/auxiliary_tomato_feasibility_20260927/RESULTS.md and
  diagnostics/auxiliary_tomato_delivery_20260927/RESULTS.md.

- **2026-09-27 10:47 UTC — actual-opponent queue diagnostic supports physical research.**
  All four selected live games reproduce both players' cash and resources
  at all 719 turns after correcting the audit's midnight phase alignment.
  Two-pass searches with actual recorded rival orders/private stock find
  local relative-cash sums +530 (Driz), +2423 (liminhai), +561 (istinetz),
  +4197 (Joseph). These separate-state sums are not full-game outcomes,
  global bounds or deployable forecasts. **Accept diagnostic only; no
  promotion.** Liminhai's -38375 deficit still points toward production
  under this bounded search. Main remains c68. Evidence: diagnostics/
  market_oracle_diagnostic_20260927/RESULTS.md.

- **2026-09-27 10:43 UTC — two-pass 3bd rejected at current50 gate.**
  All 100 games in the completed current top-50 cohort are DONE/720,
  with zero errors and no lost incumbent winning seat. Results remain
  36/50 sweeps and 72/100 wins; none of the 14 remaining matchups is
  rescued. **Reject the original >36-sweep gate.** Preserve the earlier
  31/32 native pilot pass alongside this failure. No rank51–100 or
  original50 candidate games, native confirmation, loader test or upload.
  Main remains c68. Evidence: diagnostics/
  shunki_iterated_queue_20260927/RESULTS.md. An offline, explicitly
  non-deployable actual-opponent-order diagnostic is now checking local
  trade-order opportunities in the four cash-audited live top100 games.

- **2026-09-27 10:35 UTC — two-pass3bd pilot passes; combined7673 rejected.**
  New root-backed-up3bd78d06 keeps c68 farm work/quantities and searches
  two passes over existing SELL/BUY_PRODUCT order positions against fixed
  passive/post-c68/raw-schedule forecasts. Frozen2708000–07 pilot:16/16
  wins vsreactingc68,15/16 vsreacting43d; all32DONE/720,zero errors.
  Both passes active in both seats for all8pairs per reference. **Pilot
  pass only; current100/original50 panels now run under frozen gates.**
  Evidence: diagnostics/shunki_iterated_queue_20260927/PILOT_RESULTS.md.
  Combined7673 completed all1280 prefix checks:zero funding-eligible cases.
  **Reject its mandatory coverage gate; no range extension, conditional
  ablation, loader test, promotion or upload.** Its earlier256-game native
  pass and79/100 panel result remain recorded. Evidence: diagnostics/
  shunki_funded_purchase_20260927/RESULTS.md. Main remains exactc68.

- **2026-09-27 10:35 UTC — every new10:22 live game reconciled.**
  Allfive games match both final cash totals and719ownactions, with zero
  failed own purchases or unexplained cash. Newliminhai loss is mostly
  melon(-19091) andcarrot(-8110), by is melon(-9645), THUNDER THUNDER is
  wool(-15430). **Accept diagnosis; reject failed-purchase explanation.**
  Do not treat all losses as the earlier tomato deficit. No candidate
  qualification change. Evidence: diagnostics/disjoint_live_cash_1022_20260927/RESULTS.md.

- **2026-09-27 10:24 UTC — latest51 live games:44W/7L, rank86.**
  Official10:22 snapshot has c68 COMPLETE, score2648.0, rank86, rank10
  score2889.7. All51 listed games downloaded and verified DONE/DONE/720.
  Five new games: two Orbital Terraformer wins (+610,+45), losses to
  liminhai(-10568), by(-8590), THUNDER THUNDER(-10094). Eight games are
  against teams currently top100:4W/4L; Joseph is outside this newer
  cutoff. **Accept the unfiltered audit; top10/all50 remain incomplete.**
  No new upload; main exactc68. Evidence: diagnostics/
  disjoint_live_audit_20260927/RESULTS_1022.md.

- **2026-09-27 10:22 UTC — later library switch cannot repair liminhai.**
  Passive 203-source catalogue audit (known bad113445495 excluded): at
  turns216–576, both liminhai and the Driz Lo winning control have only
  source113840386 with an exact complete action prefix; it is already the
  incumbent continuation. Removing adjacent balanced cash round trips
  still leaves no alternative after216 (24 alternatives exist at144).
  **Reject existing-later-route selection for this deficit.** No candidate
  or games run, no promotion; main remains c68. Evidence: diagnostics/
  current_late_schedule_audit_20260927/RESULTS.md.

- **2026-09-27 10:18 UTC — all four current top-100 live games reconciled.**
  Exact c68 reproduced all 719 own actions and both final cash totals in
  every game: three wins, one loss, zero unexplained cash and zero failed
  own purchases. Liminhai's -38375 loss has net tomato -35542 and melon
  -17409 differences; rival/ours tomato plots are 27/10 at turn576.
  Driz Lo shares the first two shops but is a +9617 win, so an opening-pair
  switch alone is not supported. **Accept descriptive diagnosis; reject
  missing-purchase explanation.** Inspect complete compatible later plans
  before proposing an intervention. Main remains c68; combined7673's
  frozen funding recruitment continues. Evidence: diagnostics/
  disjoint_live_top100_cash_20260927/RESULTS.md.

- **2026-09-27 10:06 UTC — all46 public c68 games audited:42W/4L.**
  Every12 new10:05-listing game downloaded without outcome filtering:
  11wins,1loss. Full cohort42wins/4losses/0draws, allDONE/DONE/720.
  New loss:liminhai -38375, episode114103869. Prior34 raw hashes verified
  before reuse. **Accept full live audit; top10/all50 remain incomplete.**
  Latest rank84/2651.8; currentmain exactc68, no new upload. Evidence:
  diagnostics/disjoint_live_audit_20260927/RESULTS_1005.md. Combined7673
  funding qualification is still running; publicb137 and weed4b578a18
  candidates are rejected under their frozen gates.

- **2026-09-27 10:05 UTC — live top100 reached; weed transfer rejected.**
  Official snapshot: c68 submission56602057 COMPLETE, rank84 /2651.8,
  rank10 2890.2,46 completed public episodes. Twelve new replays are
  being audited before reporting their outcomes; prior34 are31W/3L.
  No top10 completion claim. Main remains exactc68. Receipt: diagnostics/
  disjoint_upload_20260927/live_100503/summary.json.
  Passive all34-game weed scan:8543 plant requests,3 weed-blocked (all
  in the Dayi Zhang win), zero strict repair windows, none in any loss.
  **Reject copying an inactive weed repair into main.** Evidence:
  diagnostics/c68_live_weed_audit_20260927/RESULTS.md. Combined7673's
  frozen native funding recruitment remains running.

- **2026-09-27 10:03 UTC — weed-window4b578a18 rejected: zero activation.**
  Fresh2707000–07 native block:12W/4L, all16 DONE/720, zero errors,
  but zero weed repairs across all eight paired seeds. Outcomes equal
  the parent policy, so do not compare them causally with its earlier
  0/16 different-seed block. **Reject the frozen activation gate; no
  conditional panels/confirmation or promotion.** Exact mechanism repair
  and root backup remain research artifacts; parentdd420938 remains
  rejected. Main stays c68. Evidence: diagnostics/
  dsm_weed_window_20260927/RESULTS.md. A passive all34-live-game scan is
  checking whether this defect occurs in the uploaded policy at all.

- **2026-09-27 09:59 UTC — precise weed repair restores DSM endpoint.**
  Separate root-backed-up candidate4b578a18 replaces guarded same-day
  PLANT/WATER/PASS with DIG/PLANT/WATER on a visible weed and existing
  seed. All four development games DONE/720, zero errors. Both target
  seats restore exact source state143, improving -96740 to -27326/-28778.
  Both comparison seats unchanged -30720, zero repairs. **Mechanism pass
  only; zero wins, no promotion.** Frozen fresh2707000–07 pilot now runs.
  Keep dd420938 rejected and main c68. Evidence: diagnostics/
  dsm_weed_window_20260927/MECHANISM_RESULTS.md.

- **2026-09-27 09:54 UTC — DSM failure starts with a weed, not missing cash.**
  Passive four-game audit reproduces both old cash totals. First/worst
  paired seeds only, not fresh validation. Seed2693100 physical/private
  state matches selected source at every turn72–144 despite failed buys.
  Seed2693103 matches through119; a weed at(0,0) is its only resource
  difference through140, then blocks scheduled strawberry planting.
  Actor4 has PLANT/WATER/PASS/PASS at140–143, allowing a candidate
  same-day DIG/PLANT/WATER sequence with no productive slot removed.
  **Accept diagnosis; reject generic purchase-queue repair explanation.**
  Exact endpoint restoration and native strength remain untested. Keep
  dd420938 rejected and main c68. Evidence: diagnostics/
  dsm_continuation_audit_20260927/RESULTS.md.

- **2026-09-27 09:50 UTC — published forecast4/routefix b137 rejected.**
  Reconstructed the exact final leoprovorov notebook artifact from verified
  4f8637a3 plus its two literal ten-pair router edits. No cells executed;
  licenses and root backup preserved. Correct final callable verified.
  Fresh 2706000–07 native pilot: 2W/14L, all DONE/720, zero errors,
  mean margin -9613.125. Its complete 12-melon opening does not beat
  c68 in this block. **Reject >=12/16 gate; no conditional panels,
  confirmation, promotion or upload.** See diagnostics/
  public_forecast4_routefix_20260927/RESULTS.md. Main remains c68.

- **2026-09-27 09:38 UTC — new live losses are not failed-purchase cases.**
  All five new 09:29 episodes reconstructed with exact c68: all 719 own
  actions and both cash totals match in every game; zero unexplained cash.
  All five have zero failed own purchases. Evil Mango loss -1172 combines
  -4722 net carrot receipts and -1386 hiring differential with offsetting
  gains. Omar loss -7159 has -24972 net melon receipts: ours 90 units/3323
  coins from day21, rival143/29015 from day11. Own tomato +11279, milk+5496
  and lower hire/land spend+5451 offset much of that difference.
  **Accept descriptive diagnosis; reject missing-purchase explanation.**
  A new opening intervention must compare complete schedules and reactive
  market effects. No policy edit/promotion. Evidence: diagnostics/
  disjoint_live_cash_0929_20260927/RESULTS.md. Combined 7673 conditional
  funding recruitment remains running; main remains c68.

- **2026-09-27 09:32 UTC — 34 public games audited: 31W/3L.**
  All five newly listed games downloaded; full cohort has 31 wins, three
  losses, no draws, all DONE/DONE/720. New losses: Evil Mango -1172
  (114097679), Omar Althobaiti -7159 (114101302). Three new wins.
  **Accept full unfiltered live outcome audit; no promotion claim.**
  Rank159 /2540.5 at 09:29. Exact main remains c68. Rare funding
  recruitment is running for combined 7673; early prefixes have no
  activations. Evidence: diagnostics/disjoint_live_audit_20260927/RESULTS_0929.md.

- **2026-09-27 09:30 UTC — combined 7673 native confirmation passes.**
  All 256 frozen native games DONE/720, zero errors. Candidate 32/32
  wins versus reacting c68; old self-play 16 points from 32 draws.
  Other reference points unchanged: 1f 32/32, 489 24/32, C95 30/32.
  Paired-seed pooled point-gain bootstrap interval [0.125,0.125].
  Funding activations zero. **Pass broad gate only; no promotion.**
  Run the separately frozen conditional funding ablation, then loader
  parity if passed. Exact candidate and root backup remain 7673; main c68.
  Evidence: diagnostics/shunki_funded_purchase_20260927/CONFIRMATION_RESULTS.md.
  Latest official snapshot 09:29:26: rank159 / 2540.5, submission COMPLETE,
  34 completed public episodes. Prior 29 audited 28W/1L; five newly listed
  games still need audit. Receipt: diagnostics/disjoint_upload_20260927/
  live_092924/summary.json. Top10 remains unachieved.

- **2026-09-27 09:23 UTC — live-loss leftover hypothesis rejected.**
  Passive audit of 114082874: c68 ends with zero shed goods, worker cargo,
  seeds and field yield. It trails by 16588 at frame 264 before closing to
  -13. Physical command dictionaries differ on all 719 turns (including
  worker-count differences); market queues differ on 581. **Reject a simple
  terminal-leftover explanation; no candidate or new strength test.**
  Preserve the earlier six counterfactuals and both standalone rejections.
  See diagnostics/disjoint_live_loss_114082874/RESULTS.md. Combined 7673
  native confirmation is still running; main remains c68.

- **2026-09-27 09:18 UTC — 29 public c68 games verified, 28 wins.**
  All eight new 09:15-listing episodes are wins. Full live cohort: 28 wins,
  one loss (-13 versus Paarthpowa), no draws; all DONE/DONE/720. Reused
  prior 21 only after raw hash verification; no outcome filtering.
  **Accept live outcome audit, no top10 claim or policy promotion.**
  Main c68 remains rank 174 / 2528.5 as of 09:15. Evidence:
  diagnostics/disjoint_live_audit_20260927/RESULTS_0915.md.
  Combined 7673 independent native confirmation remains running.

- **2026-09-27 09:15 UTC — live c68 rises to rank 174 / 2528.5.**
  Submission 56602057 remains COMPLETE and now has 29 completed public
  episodes. Rank 10 is 2897.7. The 21-game audit remains 20 wins/1 loss;
  eight newly listed games are being downloaded before reporting outcomes.
  **Accept current live status; top10 remains unachieved.** Main remains
  exact uploaded c68. Candidate 7673 is still in its frozen 256-game native
  confirmation; no promotion or new upload. Live receipt:
  diagnostics/disjoint_upload_20260927/live_091515/summary.json.

- **2026-09-27 09:13 UTC — combined full replay gates pass.**
  All 300 seats DONE/720, zero errors; 46 explicit development reuses plus
  254 additional runs. 7673 scores current100 79/100 sweeps and 159/200
  wins; current50 37/50 and 74/100; original50 44/50 and 88/100. No old
  winning seat is lost on either panel. **Coverage gate pass only; all50
  remains unmet.** Frozen broad native confirmation (256 games, fresh
  2704000–2704015) is now running. The separate funding ablation and
  loader gates remain mandatory before promotion. Main is c68; no upload.
  Evidence: diagnostics/shunki_funded_purchase_20260927/PANEL_RESULTS.md.

- **2026-09-27 09:09 UTC — combined current100 finishes 79/100.**
  Exact 7673 completes all 200 current-team seats: 79/100 sweeps and
  159/200 wins versus c68 77/100 and 155/200. No old winning seat lost;
  all DONE/720, zero errors. Current50 remains 37/50 and 74/100.
  **Pass current-panel coverage only.** Original50 regression is running;
  broad native confirmation, rare-funding ablation and loader parity remain
  required before promotion. Evidence: diagnostics/
  shunki_funded_purchase_20260927/current100_completed.json.

- **2026-09-27 09:06 UTC — combined current50 gate passes 37/50.**
  Exact 7673 finishes every current top50 seat: 37/50 both-seat sweeps,
  74/100 wins, versus c68 36/50 and 72/100. No old win lost; all DONE/720,
  zero errors. **Pass this completed coverage gate only.** Remaining
  current100 and original50 regression games are running; no larger-panel
  completion or promotion claim. Evidence: diagnostics/
  shunki_funded_purchase_20260927/current50_completed.json.

- **2026-09-27 09:01 UTC — combined 7673 native pilot passes 15/16.**
  Fresh seeds 2702000–2702007, both seats versus reacting c68: 15 wins,
  one loss (-112, seed 2702002 seat 1), all DONE/720, zero errors. Purchase
  order behavior activates in all eight pairs; funding remains unactivated.
  **Pass pilot only; separate funding qualification still required.**
  Full unchanged-candidate current100/original50 panels are running with
  46 documented development reuses plus 254 remaining games. Main is c68,
  no upload. See diagnostics/shunki_funded_purchase_20260927/PILOT_RESULTS.md.

- **2026-09-27 08:59 UTC — new combined 7673 candidate passes development.**
  Exact 43d purchase-order policy plus unchanged 31ce funding tail is
  separately frozen and root-backed-up as 7673acfe. All 46 development
  games DONE/720, zero errors, 5 wins versus c68's 1. New sweeps: rank 7
  Unknown Mother-Goose (+570) and rank 100 AkiraOnojp (+1 each seat). It
  loses 31ce's recovered redblackbst sweep; effects are not additive.
  **Pass the declared aggregate development gate only.** The two earlier
  standalone candidates remain rejected. Fresh native pilot 2702000–07
  is running. Whole-policy confirmation and separate prospective native
  funding ablation are required before any promotion. See diagnostics/
  shunki_funded_purchase_20260927/PLAN.md and DEVELOPMENT_RESULTS.md.
  Main remains c68; no new upload permission.

- **2026-09-27 08:52 UTC — first live loss reproduced; no tested repair.**
  All six both-seat fixed-tape diagnostics DONE/720, zero reported errors.
  Original c68 exactly matches the live source-seat cash, margin -13 in
  both seats. Rejected purchase-queue 43d worsens it to -24; rejected
  planned-funding 31ce leaves -13. **Reject a repair claim; retain both
  prior rejection decisions and keep main at c68.** Evidence:
  diagnostics/disjoint_live_loss_114082874/RESULTS.md. All current test
  processes are complete. Fresh current100 baseline remains 77/100 sweeps
  and 155/200 wins; live latest 08:48 is rank 621 / 2299.1, 20/21 audited
  public wins. The fresh four-turn-forecast notebook upstream source was
  statically extracted at verified hash 4f8637a3 with LICENSE/NOTICE for
  later comparison; its separate final-cell route remap was not applied,
  and no import, strength test or promotion is claimed for it.

- **2026-09-27 08:50 UTC — 21 live c68 games audited; first loss is 13 coins.**
  All 21 completed public episodes in the 08:48 listing are preserved:
  20 wins, one loss, zero draws, all DONE/DONE/720. Reused the first 13
  downloaded replays only after hash verification; downloaded all eight
  new episodes without outcome filtering. Paarthpowa episode 114082874
  beats c68 seat 1 by 13 coins, 155412 versus 155399. The cohort's opposing
  teams rank 724–5775 at 08:48; none is then top100. **Accept live outcomes;
  no top-10 claim.** A six-game fixed-tape counterfactual diagnosis is
  running on the first loss, with unchanged c68, rejected 43d purchase
  queue, and rejected 31ce funding. Their rejection gates remain binding.
  No main change/upload. Evidence: diagnostics/disjoint_live_audit_20260927/
  RESULTS_0848.md and diagnostics/disjoint_live_loss_114082874/PLAN.md.

- **2026-09-27 08:48 UTC — planned funding rejected; c68 now carries team score.**
  All 128 frozen native screening games DONE/720, zero errors. Candidate
  31ce35e9 activates on zero of 32 paired seed/reference cases. Old/new
  cash and win points are identical; activation and positive-gain gates
  fail. **Reject for promotion; do not run its conditional panels or
  confirmation, and do not extend this cohort.** The two development
  sweeps remain useful mechanism evidence, not independent qualification.
  Main stays c68. See diagnostics/shunki_planned_funding_20260927/RESULTS.md.
  Latest live: team rank **621 / 2299.1**, now carried by c68 submission
  56602057 itself, COMPLETE with 21 completed public episodes. Rank 10
  is 2899.2. The first 13 are verified wins; eight newly listed episodes
  are being downloaded before reporting their outcomes. Evidence:
  diagnostics/disjoint_upload_20260927/live_084816/summary.json.

- **2026-09-27 08:41 UTC — planned funding passes development.**
  31ce35e9 wins 5/46 versus 1/46 baseline on all 23 previously non-swept
  current teams, both seats. New sweeps: current rank 7 Unknown Mother-Goose
  and rank 77 redblackbst; no previously won seat lost. All DONE/720 and
  zero errors. **Development pass only; no full-panel score or promotion.**
  Correct final file callable verified. The frozen 128-game fresh native
  screen now compares old/new versus four reacting references, both seats.
  Main remains c68. Evidence: diagnostics/shunki_planned_funding_20260927/
  DEVELOPMENT_RESULTS.md, development.json, PLAN.md.

- **2026-09-27 08:38 UTC — planned-purchase funding mechanism confirmed.**
  Passive hooks reproduce all 46 previously non-swept current-top100 cash
  pairs. Rank-7 turn 171 misses an existing cow purchase by six coins,
  then sells wheat; advancing an existing sale funds the cow in both
  one-turn forecasts, which the current identical-resource guard rejects.
  **Accept mechanism for a separate experiment, not promotion.** The
  prior procurement candidate remains rejected. Instrumentation loading
  and seat-1 identity mistakes were repaired with preserved receipts and
  23 explicit affected reruns. See current_top100_funding_audit_20260927/
  under diagnostics. New backed-up 31ce35e9 tests only earlier existing
  sales that complete planned animal/seed purchases with guarded resources
  and cost-adjusted cash. Frozen development/native/panel/confirmation
  gates: diagnostics/shunki_planned_funding_20260927/PLAN.md. Development
  is running; main stays c68, no upload authorized.

- **2026-09-27 08:29 UTC — all 13 initial public c68 games won.**
  Downloaded every completed public episode in the frozen 08:22 listing,
  without outcome filtering: 13 wins, zero losses/draws, all DONE/DONE
  over 720 frames. Replays and SHA receipts preserved. **Accept as live
  descriptive evidence; no top-10 or all-opponents claim, no promotion.**
  No loss mechanism can be inferred from this all-winning cohort. Continue
  diagnosis of the fresh top-100 local development losses. See
  diagnostics/disjoint_live_audit_20260927/RESULTS.md and cohort.json.

- **2026-09-27 08:22 UTC — public Step1009 rejected; live status updated.**
  Exact backed-up public 55be5d5f wins 4/16 fresh native games versus c68,
  mean seat margin -5655.75, all DONE. Its S839 component catches 80 errors;
  other reported counters are zero. **Reject under the original pilot
  gates; no conditional panels, promotion or upload.** Two recent public
  notebooks supplied this same policy, not independent agents. See
  diagnostics/public_step1009_native_20260927/RESULTS.md.
  Live Kaggle: team rank 743 / 2241.8 (older active submission); new c68
  submission 56602057 COMPLETE, 1886.3 after 13 completed public episodes.
  Rank 10 is 2895.7. These episode listings do not establish 13 wins.
  Download and audit the full recent cohort before quoting outcomes.
  Evidence: diagnostics/disjoint_upload_20260927/live_0822/summary.json.
  Main remains c68fa46f; the previous upload authorization is consumed.

- **2026-09-27 08:16 UTC — purchase queue fails current-top50 promotion gate.**
  43d6f448 completes all 100 current-top50 games at unchanged 36/50
  sweeps and 72/100 wins, failing the original strict-improvement gate.
  **Reject; keep c68.** Its earlier 15/16 native pilot pass remains valid
  development evidence, but no full confirmation is justified. The planned
  300-game run was stopped for futility after 127 actual completed games;
  full current100/legacy50 candidate results are not claimed. Zero errors
  in recorded games. Exact rejection and owned-process termination receipts
  are in diagnostics/shunki_purchase_queue_20260927/RESULTS.md.

- **2026-09-27 08:07 UTC — purchase-order candidate passes native pilot.**
  Separate backed-up 43d6f448 preserves c68 sale ordering, then tests
  earlier slots for existing BUY_PRODUCT orders under the same exact
  market/resource guards. Fresh seeds 2695000–2695007: 15/16 wins,
  all eight paired seeds active, all DONE, zero errors. The one seat-1
  loss on seed 2695006 (-1146) remains recorded. **Pass development only.**
  Full unchanged-candidate current-100 and older-50 panels (300 games)
  are now running under original gates; independent native and file
  checks would follow only if those pass. No main edit or upload.
  Evidence: diagnostics/shunki_purchase_queue_20260927/PILOT_RESULTS.md.

- **2026-09-27 08:01 UTC — funded DSM state bank rejected.**
  dd420938 moves only its existing turn-zero wheat purchase first. All
  16 fresh native games reach exact turn-72 compatibility and switch
  schedules; ten also match turn 144, none later. All DONE and zero
  errors, but 0/16 wins versus reacting c68. **Reject under original
  strength gate; no further panel, promotion or upload.** This isolates
  portability from competitive strength: solving the 13-coin opening
  deficit does not validate the subsequent recorded-policy continuation.
  Prior d634 rejection remains. Both root backups are preserved.
  See diagnostics/dsm_frontloaded_bank_20260927/RESULTS.md.

- **2026-09-27 07:53 UTC — exact-state DSM bank rejected in native pilot.**
  Separate d634bed3 (122 sources, 968 exact state/shop keys) wins only
  2/16 fresh native games versus reacting c68. All DONE and zero errors,
  but no state match or schedule switch activates. All eight seat-0
  turn-72 captures show the intended farm with five shed wheat, while
  the dominant source boundary requires seven. **Reject unchanged; no
  full replay rerun, promotion or upload.** Preserve the backed-up file.
  A targeted already-used-seed prefix diagnostic is checking exact
  differences before any separate revision. Evidence:
  diagnostics/dsm_state_matched_20260927/RESULTS.md and pilot.json.

- **2026-09-27 07:46 UTC — fresh current top-100 assessment complete.**
  Exact uploaded c68 was frozen for all 200 newly played games. All
  DONE/DONE, 720 frames, zero queue/quantity/gate/farmice errors. Current
  top-10: 7/10 sweeps and 14/20 wins; top-50: 36/50 and 72/100; top-100:
  77/100 and 155/200, with 45 losses and no draws. Twenty-three teams
  remain non-swept. **Reject all-opponents completion claim; keep c68 as
  the unchanged uploaded baseline, no new promotion or upload.**
  Sources cover all 100 teams in the official 07:27:24 UTC snapshot,
  84 distinct episodes created 06:57–07:29 today, none reused from the
  prior 50-team panel. Eight top-50 members changed and sixteen of the
  overlapping teams use a different selected submission. At turn 144,
  native shops differ from their source recording for 65/100 teams,
  emphasizing that fixed tapes are development evidence, not independent
  reacting-policy validation. Exact losses, source context and reproduction:
  diagnostics/current_top100_20260927_0730/RESULTS.md, MATCHUPS.md,
  manifest.json, assessment.json and non_swept_context.json.
  Latest live 07:45: team rank 785 / 2226.4, c68 rating 809.3 after two
  public games, rank 10 at 2896.0. Main SHA remains c68fa46f; the approved
  upload authorization was consumed by 56602057. Read the concise root
  CURRENT_LEADERBOARD_REPORT_20260927.md before quoting older panel scores.
  Next: address observed weaknesses with a separately backed-up candidate;
  DSM state-compatible source research is available but no candidate/pilot
  has yet been built. Fresh reacting-policy games remain necessary.

- **2026-09-27 07:40 UTC — first live c68 game wins; rating still immature.**
  Public episode 114059688 is DONE/DONE over 720 frames: c68 (seat 1)
  149660 versus Taha Alselwi 97457, margin +52203, 604 active farmer
  commands. One public game is descriptive, not a strength estimate.
  New submission rating is 705.3. Team rank is now 790 / 2226.4, carried
  by the remaining older active submission after 1f retirement. Rank 10
  is 2896.0. **Runtime and upload accepted; no top-10 claim.**
  Fresh top-50 slice now completes at 36/50 both-seat sweeps and 72/100
  wins, all DONE; remaining top-100 tests still running. Different panel
  composition and seeds prevent attributing the older 44/50 difference
  solely to policy strength. Evidence: diagnostics/disjoint_upload_20260927/
  live_0740/ and diagnostics/current_top100_20260927_0730/assessment.json.

- **2026-09-27 07:36 UTC — current top-100 collection complete.**
  All 100 snapshot teams have fresh public sources, 84 distinct completed
  episodes; none reuses yesterday's episode or action tape. Selection used
  fresh active-submission scores and latest completed public games without
  outcome filtering. Exact uploaded c68 is frozen for 200 new both-seat
  tests. No unavailable teams or collection errors. **Pass collection
  coverage; strength assessment running.** Evidence:
  diagnostics/current_top100_20260927_0730/manifest.json and PLAN.md.

- **2026-09-27 07:33 UTC — c68 exact remote parity passes.**
  Both local file loading and two freshly imported direct agents reproduce
  every action of validation episode 114057799 in both seats, with exact
  104128/104128 cash, 720 frames and DONE/DONE. Correct final callable is
  kaggle_disjoint_integrated_entrypoint. **Accept upload validation.**
  Competitive score/rank still needs public games; the current fresh
  top-100 assessment is independent of this self-play runtime check.
  Evidence: diagnostics/disjoint_upload_20260927/validation_parity.json.

- **2026-09-27 07:31 UTC — c68 remote validation complete; fresh top 100 requested.**
  Submission 56602057 is COMPLETE, with initial score 600.0 and no public
  competitive games yet. Validation episode 114057799 is 720 frames,
  DONE/DONE, 104128/104128 cash, and 644 non-PASS farmer actions per seat.
  User now explicitly requests testing against the current top 100, not
  yesterday's panel. The official 07:27:24 UTC leaderboard is frozen in
  diagnostics/current_top100_20260927_0730/. Its new PLAN.md specifies
  fresh active-submission/episode selection and 200 paired-seat games.
  Collection is running; no new strength result is claimed yet. The DSM
  state-matched candidate is deferred while completing this request.

- **2026-09-27 07:26 UTC — approved c68 uploaded as submission 56602057.**
  Exact promoted main.py and uploaded root backup have SHA-256
  c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad.
  Kaggle accepted main.py at 07:25:37 UTC and reports PENDING. The user
  authorization "Yes, promote and upload c68fa46f" is consumed by this ID.
  Prior a2 remains preserved. Local development result is 44/50 both-seat
  sweeps, 88/100 seats; six losses remain and live top 10 is unproven.
  Remote validation is pending. See diagnostics/disjoint_upload_20260927/.

- **2026-09-27 07:25 UTC — authorized c68 promoted locally.**
  User explicitly approved: Yes, promote and upload c68fa46f. Exact main.py
  SHA-256 c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad
  is promoted after completed native and both-seat loader qualification.
  Prior a2 is preserved as main_before_disjoint_integration_20260927_a2d2869c.py.
  Upload is now being attempted; no submission ID is claimed before acceptance.
  Evidence: diagnostics/disjoint_upload_20260927/promotion_receipt.json.

- **2026-09-27 07:14 UTC — combined c68 candidate fully qualified, not uploaded.**
  SHA-256 c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad
  composes the two passed components under their disjoint step-144 gates.
  All 34 actual integration games DONE, zero errors: 16 exact component
  cash matches and 18 explicitly rerun changed cases. Both original native
  win-rate requirements remain satisfied. Four file-path games cover both
  behaviors and both seats, selecting the correct final callable and matching
  direct cash. **Qualified for promotion/upload direction; main remains a2.**
  Replay result is 44/50 sweeps, 88/100 seats, with explicitly reused
  identical-policy results. Root backup:
  main_candidate_disjoint_integrated_20260927_c68fa46f.py.
  Evidence: diagnostics/shunki_disjoint_integration_20260927/RESULTS.md.
  The updated upload proposal names c68 and supersedes the earlier a2
  proposal; neither is an upload authorization until the user responds.
  Latest live 07:12: rank 112 / 2608.9, carried by 56590642; uploaded 3cc
  scores 2219.6 and rank 10 is 2895.4. No Kaggle mutation occurred.

- **2026-09-27 07:01 UTC — both pending native experiments completed.**
  Their old process handles are no longer live; authoritative result files
  show complete 128-game runs each, all DONE and zero errors. f66 preserves
  24/24 wins versus each 489 and C95, activates every external seat, and
  exactly matches inactive a2 mirror controls. 2765 improves a2 head-to-head
  points 8 to 16 out of 16 and preserves the three other reference scores
  (16, 12, 16). **Both pass their original numerical gates.** Main is still
  exact a2; neither experimental file was uploaded. Follow the previously
  frozen `diagnostics/shunki_disjoint_integration_20260927/PLAN.md` for
  conditional composition and file checks, without substituting bytes for
  the pending a2 upload request.

- **2026-09-27 07:01 UTC — DSM endpoint compatibility audit completed.**
  Twelve previously downloaded leader episodes have one identical complete
  public farm state (excluding cash) and one identical private-supply state
  at turn 72, despite different action prefixes. Turn 144 has two occupied
  layouts and three complete public-state variants. **Pass feasibility for
  state-compatible schedule research only; no policy promotion.** See
  `diagnostics/dsm_conditional_opening_20260927/RESULTS.md`. Prior fixed DSM
  route rejections stand; source cash and market differences still matter.

- **2026-09-27 03:05 UTC — restricted quantity pilot passes.**
  New backed-up 2765aed9 preserves a2 through turn 143 and enables the
  unchanged quantity optimizer only after observing identical public farm
  layouts and unlocked quadrants at turn 144. This excludes all 100 saved
  a2 panel states, preserving 43/50 sweeps by branch proof. The fresh
  2686000–2686007 native pilot is 15/16 wins, all DONE, zero errors, all
  eight pairs active. **Pass development only.** A separate 128-game
  four-reference confirmation is frozen before its fresh seeds are played.
  See `diagnostics/shunki_mirror_quantity_20260927/`. Main remains a2;
  f66's independent exposure scan and the a2 upload request remain pending.

- **2026-09-27 02:55 UTC — observed-production schedule passes development.**
  f66be305 changes only the complete FARMERS/ICE schedule, selected at
  turn 144 when rival melon plants are visible. It preserves a2's market
  optimizer and opening, and excludes the rejected quantity experiment.
  DECEM becomes +13510/+46307, both DONE and zero errors. The other 49
  panel routes cannot reach the new branch; 98 unchanged a2 results are
  reused with a recorded prefix/exclusion proof. **44/50 sweeps, 88/100
  seats; pass development only.** A fresh outcome-blind exposure scan and
  128-game native confirmation are frozen and running. See
  `diagnostics/shunki_farmice_observed_20260927/DEVELOPMENT_RESULTS.md`.
  Main and its pending upload request remain exact a2, 43/50.

- **2026-09-27 02:52 UTC — quantity candidate rejected at full-panel gate.**
  All 100 games DONE, zero quantity/queue errors. 6e09adf8 still totals
  43/50 sweeps and 86/100 wins: it gains ymg_aq (+164/+1517) but loses
  Boey (-8815 both). **Reject under the frozen no-lost-sweep rule**;
  no external confirmation, promotion or upload. Exact evidence:
  `diagnostics/shunki_trade_quantity_20260927/RESULTS.md`.
  Main remains a2, with a fresh explicit upload request pending. A new
  separate f66be305 schedule candidate changes only FARMERS/ICE against
  visible melon production; its frozen development test is separate from
  the rejected quantity policy.

- **2026-09-27 02:45 UTC — trade quantities pass native development.**
  Separate backed-up 6e09adf8 wins 16/16 seats against reacting a2 on
  frozen fresh seeds 2674000–2674007. All DONE, zero quantity/queue errors,
  all eight pairs activate; margins range 72–1061. **Pass development,
  advance to full top-50 regression; no promotion or upload.** Exact
  evidence: `diagnostics/shunki_trade_quantity_20260927/DEVELOPMENT_RESULTS.md`.
  Qualified local main remains a2; uploaded main remains 3cc.

- **2026-09-27 02:44 UTC — market queue promoted locally after loader parity.**
  `main.py` is now SHA-256
  `a2d2869c1d53bcfcedc8514d004f73bbab27ec6ef22b34d23241e718e4c1bf47`.
  Exact file loading selected `kaggle_market_queue_entrypoint`; both seats
  matched direct execution on seed 2672015, with cash 119533/112005 and
  120120/111419, all DONE and zero queue errors. The 256-game fresh review
  and 43/50 top-panel gates passed. **Promote locally; not uploaded.**
  Prior 3cc bytes are preserved at
  `main_before_market_queue_20260927_3cc0f69f.py`; candidate backup is
  `main_candidate_market_queue_20260927_a2d2869c.py`. Exact receipts are in
  `diagnostics/shunki_queue_winrate_review_20260927/promotion_receipt.json`.
  Kaggle's latest upload remains 56591314 (3cc); its previous permission
  is consumed. Fresh explicit approval is required for any a2 upload.

- **2026-09-27 02:43 UTC — unchanged a2 passes fresh overall-points review.**
  All 256 prospectively specified games DONE, zero queue errors. New wins
  32/32 against each current 3cc and leading 1f; old scores 16 and 15.5
  points. Both versions score 26/32 against 489 and 30/32 against C95.
  Pooled points rise 87.5 to 120 out of 128; whole-seed bootstrap interval
  for the difference is [0.25, 0.26171875]. All new numerical gates pass;
  the original 384-game external-gain failure remains recorded unchanged.
  **Pass numerical qualification; file-loader parity pending before local
  promotion.** Evidence: `diagnostics/shunki_queue_winrate_review_20260927/`.
  Latest live snapshot 02:41:50: rank 126 / 2589.5 carried by 56590642;
  uploaded 3cc is 2090.6 and rank 10 is 2889.3. Another upload still needs
  fresh permission. Separate quantity candidate 6e09adf8 is backed up and
  has not played its frozen native pilot; it is not part of qualified a2.

- **2026-09-27 02:29 UTC — original a2 native protocol completed without
  promotion.** All 384 games DONE, zero queue errors. Head-to-head wins are
  64/64 against each current version; historical controls tie exactly at
  54/64 each for old and new. The required positive external-only win gain
  is absent, so the original gate fails. A null-telemetry aggregation error
  was repaired from saved results without rerunning games or changing gates.
  A separate prospective overall win-rate review now freezes untouched seeds
  2672000–2672015 and old/new controls against all four references. No source
  changes, main promotion or upload. See `NATIVE_RESULTS.md` in the a2 folder
  and `diagnostics/shunki_queue_winrate_review_20260927/PLAN.md`.

- **2026-09-27 02:20 UTC — live snapshot rank 105 / 2,620.8**, carried
  by active 56590642 (1f). Current-main 56591314 is at 2,058.0; rank 10
  is 2,885.4. The eight latest completed public games, selected without
  outcome filtering for each artifact, are 8/8 wins for 3cc and 4/8 for 1f;
  all DONE with at least 604 and 520 non-PASS farmer commands respectively.
  Different opponents and small samples do not establish relative strength
  or a final score. These checks confirm ongoing remote execution.
  Receipts: `diagnostics/shunki_promotion_20260927/live_0220/`.

- **2026-09-27 02:20 UTC — market ordering passes both native head-to-head
  blocks.** Frozen a2d2869c wins 64/64 seats against reacting 3cc and 64/64
  against best-active 1f, on the same 32 fresh paired seeds. All DONE and
  zero queue errors. The two external old/new comparisons are still running;
  **qualification is incomplete and main remains unchanged.** A separate
  missing PIZZA/ICE coverage addition a4d0a896 failed its six-game development
  win gate and is rejected. The read-only refresh downloaded four new source
  schedules without outcome selection or errors, including 113940892.

- **2026-09-27 02:13 UTC — market ordering passes the full replay gate.**
  a2d2869c wins 43/50 sweeps and 86/100 seats, adding marwar22 and losing
  no old sweep. All 100 games DONE, zero queue errors. The independent
  32-seed, four-policy protocol is running, beginning with reacting 3cc;
  the plan and candidate were frozen before these outcomes. **No promotion
  or upload yet.** Seven candidate replay losses remain. Exact full-panel
  comparison: `diagnostics/shunki_market_queue_20260927/top50_decision.json`.

- **2026-09-27 02:08 UTC — current-turn market ordering passes native
  development.** Candidate a2d2869c preserves the parent's orders and
  quantities, evaluates earlier SELL slots with exact 1.32.7 market
  semantics, and guards forecast resources and cash. It wins all 16 fresh
  native games against reacting 3cc on the frozen eight seed pairs, all
  DONE and zero errors; all eight pairs activate (67–116 changed turns per
  seat). **Pass development only; full-50 regression is running.** Main
  remains 3cc. Source, root backup and protocol are in
  `diagnostics/shunki_market_queue_20260927/`.

- **2026-09-27 02:00 UTC — opening candidate rejected independently.**
  c90d992d raised saved replay results to 44/50 sweeps (88/100 wins) with
  no old sweep lost, but won only 1/64 fresh native seats against 3cc.
  All DONE, 0.5/32 paired points; the mandatory 20-point gate failed.
  The other 320 conditional games were not run. Complete public f6a756cf
  also lost all eight fresh native pilot games to 3cc. Procurement ce165545
  completed four development games without errors, recovering one cow
  in each Majkel seat but adding no wins. All three artifacts are rejected;
  root backups and dated results are preserved in their diagnostic folders.
  Main and the active Kaggle submissions remain unchanged.

- **2026-09-27 01:47 UTC — live rank 104 / 2,612.8.** The leading active
  submission is still 56590642 (visible repair 1f). Current-main submission
  56591314 (3cc) is at 1,980.8; rank 10 is 2,889.1. Read-only receipts are
  in `diagnostics/shunki_promotion_20260927/live_0147/`. Main remains 3cc,
  42/50 replay sweeps. Procurement candidate ce165545 improved both known
  losses but won neither matchup and is rejected at its development gate.

- **2026-09-27 01:15 UTC — live rank 163 / 2,539.4.** That score belongs
  to active submission 56590642 (`1f221922...`, visible repair). Younger
  current-main submission 56591314 (`3cc0f69f...`) is at 1,849.1. Rank 10
  is 2,893.1. The 94f replay improvement was rejected by native games.
  New unpromoted `db981415...` removes its regressing bakery branch and
  has 44/50 sweeps / 89 seat wins from four fresh changed-branch checks
  plus 96 unchanged-policy prior results. Fresh-terminal confirmation is
  concluded with rejection at 01:29 after 0/48 head-to-head wins versus
  current main. All prior terminal seeds were excluded. Main and Kaggle
  artifacts remain unchanged.
  `diagnostics/shunki_shop_pruned_20260927/PLAN.md` and `BEST_ACTIVE_GATE.md`
  freeze the new checks, including the actual leading active artifact.

- **2026-09-27 00:39 UTC — live team rank 400 / 2,409.6.** The downloaded
  leaderboard has rank 10 at 2,893.6. The preceding 00:33 submission check
  found new 56591314 COMPLETE / 1,451.9 and active 56590642 / 2,346.6;
  these scores and the later team snapshot have different timestamps.
  Our new submission's first eleven completed public episodes are 10 wins,
  one loss, all DONE/DONE. The experimental 94f selector is at 45/50 replay
  sweeps but failed independent native confirmation at 01:09; **main remains
  uploaded 3cc, with 42/50 replay sweeps.** Current-state entries below
  preserve historical evidence. See `diagnostics/shunki_promotion_20260927/live_0033/`.

- **2026-09-26 23:45 UTC — submission 56591314 validated**, COMPLETE /
  initial score 600.0. Remote episode 113900996 finished DONE/DONE at
  104,125 / 104,125 coins with 644 non-PASS farmer commands in each seat.
  Exact local file-loader self-play reproduces rewards and first actions
  using `replay.info.seed = 0`; the separate configuration seed is null.
  This confirms remote execution, not competitive leaderboard strength.
  See `diagnostics/shunki_promotion_20260927/validation_parity.json` and
  `UPLOAD.md`. No all-50 or top-10 claim; eight replay opponents remain.

- **Kaggle upload 56591314 accepted at 23:38:58 UTC**, exact `3cc0f69f...`
  bytes from current main. First read-only status PENDING, score blank.
  Uploaded snapshot: `main_uploaded_shunki_schedule_20260927_3cc0f69f.py`.
  The CLI reported zero submissions remaining today. Authorization consumed.
  The submission listing also revealed an intervening upload **56590642**
  at 23:01:42 UTC, file `exp_shunki_visible_repair_20260927.py`, COMPLETE /
  1315.5 at this check. Its action was not part of this promotion sequence;
  the older 22:45 active-submission assumptions are stale. Determine current
  rank and active submissions from a new live snapshot. Receipt:
  `diagnostics/shunki_promotion_20260927/submissions_after_upload.json`.

- **2026-09-26 23:39 UTC — locally promoted `3cc0f69f...`**, the observed-shop
  route selector with the independently confirmed ICE/BRUNCH schedule repair.
  Current `main.py` SHA-256 is
  `3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603`.
  It wins 42/50 fresh top-team replay matchups in both seats, versus 31/50
  for prior main, with all games DONE/DONE. The four-policy review was on
  its original `68aad090...` source; the changed branch has separate native
  confirmation, C95 regression checks and exact both-seat file-loader parity.
  Old main is preserved as `main_before_shunki_promotion_20260927_489fe8e4.py`;
  promoted bytes as `main_candidate_shunki_schedule_20260927_3cc0f69f.py`.
  The later wheat, land-only and early-sale candidates were not promoted.
  Kaggle still has the previous artifact until the pending authorized upload.
  See `diagnostics/shunki_promotion_20260927/package.json`. Historical current
  state entries below describe the previous artifact and are superseded here.

- The 22:45 UTC read-only refresh found latest submission 56572390 COMPLETE /
  **2132.7** and older active submission 56569042 COMPLETE / **2225.4**.
  The team is **rank 813 / 2225.4**, with rank 10 at **2902.0** and rank 100
  at **2629.1**. Snapshot: `diagnostics/winrate_review_20260927/live_before/kaggriculture.zip`.
  This supersedes the earlier rank/score snapshots below. No upload yet.
  A fresh root backup `main_before_winrate_review_20260927_489fe8e4.py`
  matches current main byte-for-byte. The independent win-rate evaluation
  has passed; repaired candidate `3cc0f69f...` also passed conditional native
  confirmation and wins 42/50 fresh top-team replay matchups in both seats.
  Eight matchups remain losses; main and Kaggle are still unchanged. See
  `diagnostics/top50_refresh_20260927_2303/RESULTS.md`.
- Separate research `kaggriculture_search_agent.py` is now the
  supply-aware worker scheduler, SHA-256
  `e2cc564fde5c3a61a856f2a985b76fde360e68b904b0ff5f1cde267aede53469`.
  Its prior v2 is preserved byte-for-byte in
  `kaggriculture_search_agent_v2_20260926.py` (SHA-256 `5e4023df...`).
  This is not the Kaggle submission or a proven stronger opponent policy;
  see the 18:32 UTC finding and `diagnostics/public_supply_inspiration_20260926/FEED_RESULTS.md`.
- Local `main.py` SHA-256:
  `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
  The tested strawberry-only 24-turn physical-mirror sale lookahead was
  promoted locally on 2026-09-26. Other products retain 12 turns and
  non-mirror behavior remains at four turns. The previous local revision,
  which remains the older tracked Kaggle submission, is backed up byte-for-byte as
  `main_before_mirror_straw24_20260926_08aa268a.py` and
  `main_uploaded_entrypoint_fix_20260926_08aa268a.py` (SHA-256 `08aa268a...`).
  It has the unique final callable for Kaggle's file loader. The earlier revision,
  which was uploaded but selected the wrong callable, is backed up byte-for-byte
  as `main_before_entrypoint_fix_20260926_0e2c30f4.py` and
  `main_uploaded_mirror12_20260926_0e2c30f4.py` (SHA-256 `0e2c30f4...`).
  The prior eight-turn local revision is backed up as
  `main_before_mirror12_20260926_6b5529fe.py` (SHA-256
  `6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`).
  The previous submitted artifact is separately backed up byte-for-byte as
  `main_before_top10_goal_20260926_04b0bdc3.py` (SHA-256
  `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`).
  See `diagnostics/top10_goal_20260926/MIRROR12_RESULTS.md` and
  `diagnostics/top10_goal_20260926/ENTRYPOINT_FAILURE_FIX.md`, plus
  `diagnostics/top10_goal_20260926/MIRROR_STRAW24_RESULTS.md` for the
  newer local policy. The newer local `489fe8e4...` source was uploaded as
  Kaggle submission 56572390 after the user's fresh approval; an exact
  snapshot is `main_uploaded_mirror_straw24_20260926_489fe8e4.py`.
- Kaggle submission **56572390** uploaded the current local `489fe8e4...`
  bytes at 2026-09-26 07:01:20 UTC following the user's separate fresh
  approval. The 07:04 UTC read-only status was `COMPLETE`, initial score
  600.0. Validation episode 113604202 ended both agents `DONE`, with 71,657
  / 72,326 coins and hundreds of real farm and market actions in each seat.
  Local seed-0 self-play via Kaggle's file-path loader reproduced both cash
  totals and first actions exactly. A 17:07 UTC read-only audit of 100 public
  games found 71 wins and 29 losses, all `DONE`/`DONE`. The latest submission's
  displayed score was 2168.3 at 17:54 UTC, below the older corrected
  submission's 2206.8. The leaderboard used the older, higher score and
  ranked the team 927, versus rank 10 at 2888.7. All 29 audited losses had
  at least one turn meeting the
  visible physical-mirror gate; this is an association, not evidence that the
  longer strawberry lookahead caused them. See
  `diagnostics/live_submission_56572390_20260926/RESULTS.md` and
  `diagnostics/top10_goal_20260926/UPLOAD_56572390.md`.
- The read-only 18:23 UTC Kaggle check found both recent submissions still
  `COMPLETE`: 56572390 displayed 2164.6 and 56569042 displayed 2210.7.
  The leaderboard used the older higher score and ranked Lakshmanan R
  **918 / 2210.7**, versus rank 10 at **2885.5**. This supersedes the earlier
  17:54 score/rank snapshot. Export:
  `diagnostics/leaderboard_20260926_1823/kaggriculture.zip`. The local
  `main.py` still has SHA-256 `489fe8e4...`; no new Kaggle upload occurred.
- The read-only 19:12 UTC Kaggle check found submission 56572390
  `COMPLETE` / **2166.7** and the older active submission 56569042
  `COMPLETE` / **2200.6**. The public leaderboard uses the older active
  score and ranks Lakshmanan R **930 / 2200.6**, versus rank 10 at
  **2891.8**. This supersedes the 18:23 status. Exact exported snapshot:
  `diagnostics/leaderboard_20260926_1912/kaggriculture.zip`. If unchanged
  current `main.py` is submitted again, the latest-two rule would retire
  the older 56569042; at this snapshot the remaining 56572390 score
  2166.7 maps to indicative rank **1005** until a new submission accrues
  games. This is not a prediction of a new submission's final rating.
  Local `main.py` remains SHA-256 `489fe8e4...`; no new upload occurred.
- The read-only 19:59 UTC Kaggle refresh found submission 56572390
  `COMPLETE` / **2149.4** and older active submission 56569042
  `COMPLETE` / **2202.1**. The leaderboard uses the older active score and
  ranks Lakshmanan R **911 / 2202.1**, versus rank 10 at **2896.0**.
  This supersedes the 19:12 snapshot. Export and submission-list receipt:
  `diagnostics/leaderboard_20260926_2000/kaggriculture.zip` and
  `submissions.json`. The local file still hashes `489fe8e4...`; no new
  Kaggle upload occurred. These scores are dynamic and do not forecast a
  fresh submission's future rating.
- The read-only 20:14 UTC Kaggle refresh found current-file submission
  56572390 `COMPLETE` / **2140.1** and older active submission 56569042
  `COMPLETE` / **2200.7**. The leaderboard uses the older score and ranks
  Lakshmanan R **915 / 2200.7**, versus rank 10 at **2890.8**. This
  supersedes the 19:59 snapshot. Exact leaderboard and submission receipts:
  `diagnostics/leaderboard_20260926_2014/kaggriculture.zip` and
  `submissions.json`. Local `main.py` still hashes `489fe8e4...` and
  matches submitted 56572390; no new upload occurred. Reuploading identical
  bytes would not provide a trustworthy score/rank forecast and may retire
  the stronger older submission under Kaggle's latest-two rule. If 2140.1
  were the leaderboard score in this fixed snapshot, it would correspond to
  indicative rank **1073**; this is not a prediction of a new upload.
- The read-only 20:53 UTC Kaggle refresh found current-file submission
  56572390 `COMPLETE` / **2137.8** and older submission 56569042
  `COMPLETE` / **2214.1**. The leaderboard uses the older score and ranks
  Lakshmanan R **861 / 2214.1**, versus rank 10 at **2887.2**. In that
  fixed snapshot, 2137.8 would correspond to indicative rank **1069** if it
  became the displayed score. This is not a forecast of a fresh upload's
  rating. The identical local `main.py` still hashes `489fe8e4...`; no upload
  occurred. Exact leaderboard CSV: `diagnostics/leaderboard_20260926_2053/kaggriculture.zip`.
- A read-only 20:27 UTC public-episode refresh for current-file submission
  56572390 froze 17 completed games with IDs later than the previous
  100-game audit, excluding three older backfills. They ended seven wins,
  ten losses; this is a new chronological sample, not a causal comparison
  between versions. Exact IDs and replays are in
  `diagnostics/physical_sale_predictor_20260927/selection.json` and
  `audit_new.json`. At collection time, submission score/rank had last been
  checked at 20:14 UTC; the later 20:53 snapshot above supersedes it;
  local `main.py` remains hash `489fe8e4...`, with no new upload.
- Kaggle submission **56569042** uploaded the older `08aa268a...`
  corrected-entrypoint source at 2026-09-26 04:27:35 UTC following the user's
  explicit fresh authorization. It is `COMPLETE`. Its validation ended
  72,078/72,747 with both agents `DONE`, each taking hundreds of real
  farm/market actions; local file-path self-play on seed 0 reproduced both
  cash totals and opening actions exactly. A 06:53 UTC audit of 36 public
  episodes found **28 wins and 8 losses**, with both players `DONE` in every
  game. The seven latest public games included losses of -1,006 versus
  Konstantin Zorin and -767 versus kaggle Osaka; five were wins. Our agent
  took real farm and market actions. The 06:58 UTC leaderboard ranked
  Lakshmanan R 837 / 2278.6, versus rank 10 at 2900.9. The rating
  has moved but does not establish
  top-10 strength. See
  `diagnostics/live_submission_56569042_20260926/RESULTS.md`.
- Kaggle submission **56568576** uploaded the *broken-entrypoint*
  `0e2c30f4...` source at 2026-09-26 04:00:32 UTC. Kaggle's loader selected
  `_clone_physical_match` instead of the policy. Four public games available
  at 04:22 UTC each showed our agent making only `PASS` actions, no market
  orders and ending at the starting 3,000 coins; all four were losses. The
  displayed public score was 250.6. The local `08aa268a...` fix passed
  Kaggle file-path loading in both seats and is now submitted as 56569042.
  Another upload requires a fresh explicit user request. Prior submissions
  56529771, 56530281 and 56547116 were `COMPLETE` with the older working
  `04b0bdc3...` source. The competition README says only the latest two
  submissions remain tracked.
- A read-only 2026-09-26 06:32 UTC leaderboard download showed Lakshmanan R
  at rank 994 / 2211.4 and rank 10 at 2907.1, after 29 audited public games
  (23 wins, 6 losses). Snapshot:
  `diagnostics/leaderboard_20260926_0632/kaggriculture.zip`.
  The later 06:58 UTC snapshot shows rank 837 / 2278.6 versus rank 10 at
  2900.9; see `diagnostics/leaderboard_20260926_0658/kaggriculture.zip`.
  The 07:35 UTC snapshot showed rank 900 / 2248.8 versus rank 10 at
  2897.8; see `diagnostics/leaderboard_20260926_0736/kaggriculture.zip`.
  The earlier 2026-09-26 06:11 UTC download showed Lakshmanan R
  at rank 869 / 2269.0 and rank 10 at 2902.4, after 24 audited public games
  (21 wins, 3 losses). Snapshot:
  `diagnostics/leaderboard_20260926_0611/kaggriculture.zip`.
  The earlier 2026-09-26 05:46 UTC download showed Lakshmanan R
  at rank 1256 / 2110.9 and rank 10 at 2904.5, after seventeen games of the
  corrected 56569042 submission. The rating is still early and moving.
  Snapshot: `diagnostics/leaderboard_20260926_0548/kaggriculture.zip`.
  At 05:42 UTC it was rank 1569 / 1981.5 after sixteen games; snapshot:
  `diagnostics/leaderboard_20260926_0545/kaggriculture.zip`.
  At 05:16 UTC, the corrected submission was rank 2949 / 1381.8 after ten
  games; that earlier snapshot is in
  `diagnostics/leaderboard_20260926_0515/kaggriculture.zip`.
  An earlier 03:02 UTC snapshot showed rank 977 / 2229.6, but that preceded
  the bad entrypoint submission and reflects the older artifact, not the
  current corrected submission's strength.
- The frozen refreshed top-50 public **fixed-action** panel contains 100
  captured opponent routes, each tested with both seats: the previously
  submitted `main.py` won
  **67/100 route pairs, 133/200 seat-games**, all `DONE`. This panel does not
  model how opponents respond to changed actions and is now development data,
  not an untouched holdout. Evidence and commands:
  `diagnostics/top50_current_2026-09-24/RESULTS.md` and
  `diagnostics/top50_current_2026-09-24/main_100routes.json`.
- The September 25 current top-100 saved-action panel has 100 distinct route
  tapes, each tested in both seats. The submitted prior hash and current local
  `main.py` each won 59/100 by positive summed paired margin and 118/200 seat
  games; their 400 runs were `DONE` and no result flipped. This repeatedly used
  development panel is a regression screen, **not** a live win-rate estimate.
  The prior eight-turn local policy also won 14/14 activated games on a fresh
  eight-seed reactive near-mirror check. See
  `diagnostics/top10_goal_20260926/CLONEGATE_RESULTS.md`.
- A separate September 26 top-100 panel contains 100 fresh public action
  hashes from 90 episodes, all disjoint from the September 25 action hashes
  and episodes (83 team IDs overlap). The previous eight-turn and 12-turn
  policies won 69/100 paired routes and 137/200 seats, all `DONE`, with no
  outcome flips. The current local strawberry-only 24-turn policy retained
  these counts on an exact branch-eligibility regression screen; the older
  September 25 panel also stayed 59/100 and 118/200 without flips. Native
  12-versus-8 near-mirror testing on 16 fresh
  seeds, both seats, yielded 32/32 wins for 12 turns, +28,930 total margin;
  matched public H6 and Haide reactive checks kept 16/16 control wins, with
  Haide margin delta -342 total. See
  `diagnostics/top10_goal_20260926/MIRROR12_RESULTS.md` and
  `diagnostics/top10_goal_20260926/MIRROR_STRAW24_RESULTS.md`.
- A third September 26 top-100 public fixed-action panel sampled at 07:08
  UTC has 100 distinct action hashes from 88 episodes, disjoint by hash
  from both earlier panels and by episode from the preceding September 26
  panel. Uploaded/current hash `489fe8e4...` won **66/100 paired routes and
  132/200 seat-games**, all `DONE`; top-ten saved routes were 9/10 wins, with
  Boey the loss (−2,890 per seat). Twenty-one of 34 losses had rivals with
  at least seven strawberry tiles at day six, but this is associative.
  This is a new regression/diagnosis panel, not live opponent adaptation.
  See `diagnostics/top100_refresh_2026-09-26_0708/RESULTS.md`.
- A separately refreshed top-20 public replay panel from the 2026-09-25
  21:46 UTC leaderboard snapshot has 20 distinct action tapes. Both the
  previous eight-turn local and previously submitted hashes won 17/20 positive paired
  margins and 34/40 seat-games, with every terminal cash pair identical and
  all 80 games DONE. The losses were Boey, TheEggman and 吃白饭的大肥鱼. This is
  newer fixed-action evidence, not an adaptive-agent rating prediction; see
  `diagnostics/top20_refresh_2026-09-26/RESULTS.md`.
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
- A newer, disjoint 40-episode public live slice for uploaded submission
  56530281 had **9 wins / 31 losses**, all `DONE`. Nineteen losses were under
  1,000 coins, and 24/31 losses matched the rival farmer on at least 718 turns.
  Exact local replay parity of both cash values and statuses was 40/40. In
  both-seat fixed-tape reruns, the uploaded backup and previous eight-turn
  unuploaded local gate each won 11/40 paired routes and 21/80 seats; the
  gate rescued three paired losses and reversed three wins. This is a newer
  diagnosis, **not** adaptive validation. See
  `diagnostics/live_refresh_56530281_20260926/RESULTS.md`.
- For those 24 actual seed/seat combinations, the then-local policy versus the
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
| 2026-09-25 | A new `main_research.py` shadow-price sale planner lowered own cash 108 across its two pilot activations. A guarded idle-animal yield-rescue planner added 110 own coins in the 12-route pilot, then 895 own coins over 488 seat-games from an archived 100-team panel, with 148 substitutions. Its 167/244 route and 329/488 seat wins were exactly the frozen `main.py` counts; no loss was rescued. | Reject sale preemption and do not promote yield rescue; retain both as research modes. `diagnostics/main_research_plan_20260925.md`. |
| 2026-09-26 | The complete route-12 sheep schedule on observed yarn shops improved saved-route paired wins from 13/22 to 16/22, rescuing four and reversing one, but lost 0/16 fresh reactive seat-games to `main.py` across eight preselected yarn seeds. Own cash rose 78,186 total while the reacting rival's cash rose 326,480. | Reject; saved-action gain did not generalize. `diagnostics/top10_goal_20260926/YARN12_RESULTS.md`. |
| 2026-09-26 | Eight-turn sale advance won 16/16 reactive near-mirror seat-games on eight fresh seeds, but the complete saved current top-100 panel stayed at 59/100 positive paired margins (one rescue, one reversal), 118→119/200 seat wins, and reduced own cash 21,101 across 200 games. | Reject unconditional lookahead; mirror gain did not yield broad saved-route improvement. `diagnostics/top10_goal_20260926/LOOK8_RESULTS.md`. |
| 2026-09-26 | Gating the eight-turn lookahead on equal public farm states held saved top-100 wins at 59/100 routes and 118/200 seats with no flips; it won 14/14 activated games on an independent eight-seed reactive mirror block and preserved wins versus two public reactive agents. | Promote exact candidate to local `main.py` as a small near-mirror improvement, **not** a top-ten or 100/100 result. No Kaggle upload. `diagnostics/top10_goal_20260926/CLONEGATE_RESULTS.md`. |
| 2026-09-26 | Swapping thirteen day-11 strawberry plants to tomato under two Farmers Markets improved one saved loss slightly but worsened another and reversed a large win. It suppressed the existing late V219 tomato branch; with original shops pinned, the seat-0 win still reversed. An additive variant preserved that win but narrowed its paired margin +48,319→+11,089 and rescued neither loss. | Reject both early-tomato variants; no `main.py` change or upload. `diagnostics/top10_goal_20260926/FARMERS_TOMATO13_RESULTS.md`. |
| 2026-09-26 | Replaying the saved first-place Boey action history as a complete agent against reacting local `main.py` lost all six games on three fresh native seeds, both seats, by 7,259–37,693 coins per seat. | Reject direct tape transfer; its original-episode win did not generalize. `diagnostics/top10_goal_20260926/BOEY_RAW_TRANSFER.md`. |
| 2026-09-26 | A smoothie-shop-gated day-11/12 swap of 19 wheat plants to strawberry added 65 executed strawberry sales (+8,489 receipts) on a fresh top-20 loss but reduced carrot/wheat receipts and increased seed/feed spending; own cash fell 6,819 and paired margin worsened -21,358→-26,796. | Reject; partial crop conversion omitted the value of later crop cycles. `diagnostics/top10_goal_20260926/SMOOTHIE_STRAW_RESULTS.md`. |
| 2026-09-26 | Restoring the complete preexisting R108 route 125 on observed Pizza Shop/Yarn Store improved two saved-action losses slightly but rescued neither, narrowed a winning control, and won 2/lost 2 distinct fresh native seeds against reacting `main.py`; mean native margin was -795.5 and the worst loss was -10,867. | Reject unconditional restoration; no `main.py` edit or Kaggle upload. `diagnostics/top10_goal_20260926/PIZZA_YARN_ROUTE125_RESULTS.md`. |
| 2026-09-26 | The exact public C95 artifact from Rayk Kretzschmar's notebook passed its published source hash and completed 16 native reactive games against local `main.py` on eight predeclared seeds, both seats, but lost 0/16 wins by mean margin -34,386.8 coins. | Reject direct replacement; historical public scores are not local current strength evidence. No `main.py` edit or Kaggle upload. `diagnostics/top10_goal_20260926/PUBLIC_C95_RESULTS.md`. |
| 2026-09-26 | Broadened the complete V219 day-18 tomato bundle from three to exactly two observed Pizza Shop/Farmers Market shops. It activated and confirmed ten tomato plants on each of three predeclared losing routes in both seats, but worsened every paired loss (-15,716→-16,696, -41,703→-42,759, -5,722→-9,776); three winning controls were exact. | Reject; no loss rescued, no `main.py` edit or Kaggle upload. `diagnostics/top10_goal_20260926/TOMATO2_RESULTS.md`. |
| 2026-09-26 | A fresh, disjoint 40-episode public live audit of the uploaded policy found 9 wins and 31 losses; 19 losses were below 1,000 coins and 24/31 matched the rival farmer on at least 718 turns. Local backup replay reproduced both cash totals/statuses in all original seats. The local eight-turn mirror gate exchanged three saved paired losses for three saved wins with no aggregate win gain. | Retain as diagnosis; no policy promotion from these fixed tapes. `diagnostics/live_refresh_56530281_20260926/RESULTS.md`. |
| 2026-09-26 | A six-turn version of the physical-mirror sale gate gained one paired win on the 40 live-opponent development tapes (12/40 vs 11/40), but held the saved current top-100 at 59/100 and 118/200 seats, with lower own cash. Both six- and eight-turn gates won all 16 fresh reactive near-clone games on eight new seeds, but six turns had 6,404 less aggregate margin, 1,678 less own cash, and 4,726 more rival cash than the eight-turn local policy. | Reject six-turn candidate; keep local `main.py` hash `6b5529fe...`, no Kaggle upload. `diagnostics/top10_goal_20260926/MIRROR6_RESULTS.md`. |
| 2026-09-26 | Exact executed-cash ledgers for eight smallest near-mirror live losses and three close wins reproduced final cash with zero unexplained remainder. All eight losses had lower net strawberry receipts (-2,151 total), although seven sold equal strawberry units; three also sold 13–20 fewer carrots. In one -13 loss the rival twice sold strawberry batches two turns ahead of ours. Winning controls and other offsetting items prevent attributing a win to this timing alone. | Retain as diagnosis; test a narrow candidate separately before any promotion. `diagnostics/live_refresh_56530281_20260926/CASH_LEDGER_CLOSE.md`. |
| 2026-09-26 | Permitting sale advance of the first protected future sale only when already selling the same item rescued one of 40 fresh live-opponent fixed routes (12/40 vs 11/40), but left the current top-100 at 59/100 paired and 118/200 seats with no flips, lowering own cash 2,283. It won 14/16 fresh reactive near-clone games, but lost both seats of one seed by 641, with own cash -966 across the block. The originally diagnosed -13 Squirrel loss remained a loss. | Reject; do not edit `main.py` or upload. `diagnostics/top10_goal_20260926/SAMEITEM_UNPROTECT_RESULTS.md`. |
| 2026-09-26 | The existing cow-to-goose layer on Boey's saved first-place route valued goose at +1,216 versus cow -379 in both seats, but returned `noplan@169`: matching pastures at `(5,2)` and `(6,4)` were already built at steps 153/159 before cow buys at 169/176 and placements at 177/182. A telemetry-only wrapper preserved the exact -7,858 outcome in both seats. | Diagnose an early structure-to-animal scheduling bottleneck; changing value thresholds alone cannot activate the bundle. No policy promotion or upload. `diagnostics/top10_goal_20260926/CS_PREBUILD_DIAGNOSIS.md`. |

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

- **Current priority after 2026-09-26 21:09 UTC:** `main.py` remains
  `489fe8e4...` (submission 56572390, 2137.8 at the 20:53 read-only
  check). The older active submission 56569042 was 2214.1 and ranked the
  team 861; rank 10 was 2887.2. The newest saved top-100 panel is only
  **66/100** paired route wins and **132/200** seat wins, with 34 paired
  losses. The 17 later public games were seven wins/ten losses. Exact
  ledgers point to broad tomato and wool production/delivery deficits;
  the isolated late wool carrier interrupt activated in only one of 16
  fresh paired seeds and is rejected. A full 40-route double-Yarn library
  screen found no complete tape that improved margin on all three major
  losses. Develop a **new** funded production and worker-delivery schedule,
  compare full terminal own/rival cash
  against reacting opponents, then run the full saved panel only if the
  fresh native gate passes. Earlier bullets below record historical
  hypotheses and older snapshots, not current scores.
- User-authorized submission 56572390 contains the current strawberry-only
  24-turn local policy. Remote validation and local file-path parity passed;
  the first seven public games were wins but did not establish a stable rating
  or the new branch's live value. Its predecessor 56569042 had 28 wins and eight
  losses across 36 audited public episodes; the 06:58 UTC leaderboard ranked
  it 837 / 2278.6, still far below rank 10 at 2900.9. The later 07:35
  snapshot ranked the team 900 / 2248.8 versus rank 10 at 2897.8. See
  `diagnostics/live_submission_56569042_20260926/RESULTS.md` and
  `diagnostics/top10_goal_20260926/UPLOAD_56572390.md`. No further upload
  without a new explicit request.
- The September 25 saved top-100 regression count remains 59/100 positive
  paired margins; a separately refreshed September 26 panel is 69/100. The
  new strawberry-only 24-turn mirror gate improves direct near-clone reactive
  matchups but does not improve either saved-route win count. Broader 16-turn
  all-product lookahead reversed one saved-route win and remains rejected.
  Small crop/route edits have failed to make a broad gain.
  A complete early cow-to-goose bundle also failed to generalize: one site
  reached 60/100 on that reused panel but lost margin in fresh reactive
  activations, and two sites reversed a saved-route win. See
  `diagnostics/top10_goal_20260926/EARLY_GOOSE_RESULTS.md`. Value the
  opponent's induced cash and unknown future shop mix, not just own output.
  Prioritize a complete, funded production-bundle decision at one genuine
  resource conflict: include purchase, worker travel/care, harvest, delivery,
  sale, future crop occupancy and market impact. Compare incumbent,
  alternative and no-new-commitment with reactive terminal rollouts; freeze
  an observation-only selector before fresh-seed testing. The proposed
  measurement design is in
  `research_dynamic_planner_20260925/PRO_STRATEGY.md`. Do not repeat the
  rejected independent v1–v5 planner or infer live wins from fixed tapes.
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
- **2026-09-26 — eight-turn sale advance full-panel and reactive audit.** A
  separate candidate won all 16 fresh reactive near-mirror seat-games versus
  `main.py`, but held at 59/100 positive paired route margins on the saved
  current top-100 panel, with one rescue, one reversal, and 21,101 fewer own
  coins across 200 seat-games. The broad treatment was rejected. Production
  `main.py` and Kaggle submission remain unchanged; see
  `diagnostics/top10_goal_20260926/LOOK8_RESULTS.md`.
- **2026-09-26 — physical-mirror sale gate promoted locally.** The gate uses
  equal public farm tiles and worker positions to choose an eight-turn sale
  lookahead, retaining four turns otherwise. Saved current top-100 results
  stayed at 59/100 paired route wins and 118/200 seat wins, with no flips.
  On eight fresh reactive mirror seeds, it won all 14 games where it activated;
  the two inactive games exactly reproduced the matched control's seat effect.
  An earlier eight-seed mirror block won 16/16; public H6 controls were exact
  and public Haide controls kept all six wins. `main.py` now has SHA-256
  `6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`.
  The older Kaggle submissions remain at the previous hash; no upload.
  Full evidence and caveats: `diagnostics/top10_goal_20260926/CLONEGATE_RESULTS.md`.
- **2026-09-26 — early tomato replacement rejected.** A route-104 candidate
  changed thirteen day-11 strawberry seeds/plants to tomato. On the three
  current saved-action routes with double Farmers Markets, it kept two losses
  as losses and reversed a +48,319 paired-margin winning control to -1,696.
  Three other-shop controls were exact. Native event traces showed the early
  cohort prevented the incumbent V219 late tomato commitment in the reversed
  control; pinning the baseline shops still reversed its seat-0 win. **Reject;
  no local `main.py` edit or Kaggle upload.** See
  `diagnostics/top10_goal_20260926/FARMERS_TOMATO13_RESULTS.md`.
- **2026-09-26 — additive tomato follow-up rejected.** Relaxing V219's
  own-tomato exclusion only on route 104 restored its late investment in the
  winning control: the exact trace planted 23 tomato units and sold 131, but
  tomato receipts of 16,468 were still below the incumbent's 17,021 while
  strawberry receipts fell 43,651→27,208. The winning control narrowed from
  +48,319 to +11,089 paired margin, and neither of the two target losses was
  rescued. All 12 panel games finished DONE; **reject**, no `main.py` edit or
  Kaggle upload. Same report as the early-cohort pilot.
- **2026-09-26 — saved Boey tape transfer rejected.** The single first-place
  public action tape beat local `main.py` on its captured seed, but lost all
  six reactive games on three fresh native seeds in both seats when replayed
  as a complete candidate. This is evidence against direct reuse of those
  actions, not a test of Boey's adaptive policy. No `main.py` change or upload;
  see `diagnostics/top10_goal_20260926/BOEY_RAW_TRANSFER.md`.
- **2026-09-26 — refreshed public top-20 panel.** Downloaded one new episode
  action tape per team from the recent top-20 snapshot and ran both local
  hashes in both seats. Current and submitted files each won 17/20 routes and
  34/40 seats, all DONE, with identical terminal cash in all 40 matched
  games. The three losses have different realized product gaps. No upload;
  `diagnostics/top20_refresh_2026-09-26/RESULTS.md`.
- **2026-09-26 — smoothie crop-cycle pilot rejected.** A conditional 19-plant
  WHEAT→STRAWBERRY swap activated only on the target fresh top-20 loss. Its
  65 extra strawberry sales gained 8,489 receipts but displaced 115 carrot
  and 128 wheat sales, increased wheat purchases and seed costs, and reduced
  own final cash 6,819. The target loss worsened and five controls were exact.
  Shops matched exactly in the traced target seat. `main.py` and Kaggle were
  unchanged; `diagnostics/top10_goal_20260926/SMOOTHIE_STRAW_RESULTS.md`.
- **2026-09-26 — complete Pizza/Yarn route pilot rejected.** The standalone
  candidate restored the existing route 125 instead of V92 route 9 on the
  observed matching shop pair. Two saved losses improved slightly but stayed
  losses, one win narrowed, and two other-shop controls were exact. On four
  preselected fresh native seeds against reacting local `main.py`, in both
  seats, it won two distinct games and lost two; mean margin was -795.5 and
  one seed lost 10,867 coins despite own cash increasing 27,599 because the
  rival gained 38,466. All 16 reactive runs were DONE. No main-file change or
  upload; `diagnostics/top10_goal_20260926/PIZZA_YARN_ROUTE125_RESULTS.md`.
- **2026-09-26 — public C95 direct replacement rejected.** Downloaded the
  public Kaggle notebook read-only, decoded its 75,098-byte C95 source through
  an AST-literal extractor, and verified the notebook-declared SHA-256. On
  eight predeclared fresh native seeds, both seats, it lost all 16 DONE
  reactive games to local `main.py` by mean margin -34,386.8. Do not infer
  present head-to-head strength from the notebook's historical public score.
  No main-file change or upload;
  `diagnostics/top10_goal_20260926/PUBLIC_C95_RESULTS.md`.
- **2026-09-26 — two-shop complete late tomato bundle rejected.** Broadened
  the existing V219 qualification without changing its funded land, seed,
  worker, harvest and sale schedule. Three high-ranked saved losses with two
  observed tomato-demand shops each activated, committed, and confirmed ten
  plants in both seats, but every paired loss worsened. Three winning controls
  reproduced the incumbent exactly. All 12 games were DONE. The frozen
  loss-rescue gate failed, so no full-panel or reactive promotion test was run.
  No main-file change or upload;
  `diagnostics/top10_goal_20260926/TOMATO2_RESULTS.md`.
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
- **2026-09-25 — two additional final-action planners screened.**
  `main_research.py` loads the frozen `main.py` and exposes `rival_shadow` and
  `spare_yield` overlays, plus an exact-control mode. The control matched
  native main self-play terminal cash in both seed-0 seats. The rival-shadow
  planner reduced own cash 108 total on its two activated pilot seats and
  rescued no route: **reject**. The corrected spare-yield planner abstains
  on market purchase turns, passed five unit checks, and increased own cash
  110 total across a 12-route/two-seat development screen, with unchanged
  9/12 route wins. The archived 100-team fixed-action panel was then run on
  all 244 routes and both seats for both agents: `main_research.py` and frozen
  `main.py` each won 167/244 route pairs and 329/488 seat-games, with all
  976 runs `DONE`. The candidate made 148 substitutions, gaining 895 own
  coins and 991 paired-margin coins in aggregate, but rescued zero losses and
  reversed zero wins. A low-load two-seat check measured 1.87 ms mean and
  70.75 ms max per candidate call; the parallel full run's max was 8.97 s
  under CPU contention. **Do not promote either mode; no Kaggle submission
  occurred.** See `diagnostics/main_research_plan_20260925.md` and the
  complete matched comparison JSON.
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

- **2026-09-25 — dated leaderboard coverage expanded, not a first-place claim.**
  A September 24 top-100 snapshot supplied 50 new public action histories for
  ranks 51–100; frozen `main.py` won 23/50 route pairs and 44/100 seat games,
  all DONE. Alongside the older top-50 development set, that is 90/150 sampled
  route pairs from 100 distinct teams, **not** 90/100 live agent wins. A fresh
  September 25 replay per team from the old top-50 snapshot gave 33/49 route
  wins and 66/98 seat wins, all DONE; one mislabeled public episode was excluded.
  Today's live leaderboard has only 73 of yesterday's top-100 teams. A new
  current-top-100 fixed-action panel with 100 distinct action hashes finished
  all 200 seat games: 118 wins / 82 losses, or 58 both-seat route wins, 2
  splits, and 40 both-seat route losses. Top-ten routes were 8 both-seat wins
  and 2 both-seat losses, including a 7,858-coin loss in each seat versus #1.
  The dated leaderboard snapshot showed Lakshmanan R at rank 742 / 2370.5
  and first place at 3051.6. Ratings and ranks can change. No submission.
  Evidence: `diagnostics/top100_extension_2026-09-25/`,
  `diagnostics/top50_fresh_2026-09-25/`, and
  `diagnostics/top100_current_2026-09-25/RESULTS.md`.
- **2026-09-25 — low-headroom interventions rejected.** Reapplying the clone
  sale reorder after H6 kept 13/24 recent live routes and 26/48 seats; an idle
  fertilizer collector added 204 actions but zero terminal-cash change because
  the baseline collected the same fertilizer later. A broad yarn-shop route
  override made 2 old top-50 losses into wins but reversed another win. On 9
  fresh yarn-shop routes it rescued zero losses and worsened one paired margin
  by 11,266. Its narrower `ICE_CREAM_SHOP,YARN_STORE` gate had no activation in
  49 fresh old-top-50 routes nor 100 current-top-100 routes, and a conditional
  reactive check versus one public agent reversed a win. H6 demand alpha 0.5
  held the recent panel at 13/24 wins but changed 10 margins, worsening 7 and
  improving 3. **None was promoted.** The first-place team's one public raw
  action tape won only 4/8 reactive seed/seat games against `main.py`, with
  mean margin −4,405; do not mistake a strong episode for a general policy.
- **2026-09-25 — H6 engine-price mismatch isolated.** The
  installed 1.32.7 engine uses hinge scarcity curves for CARROT, TOMATO and
  EGG, whereas frozen `main.py`'s H6 sell-slot scorer still uses log/linear
  approximations. `exp_h6_engine_price_20260925.py` corrects only that scorer;
  its 9,009 sampled item/inventory quotes matched the engine exactly. On 24
  recent live-loss fixed tapes it kept 13/24 route wins, with paired margin
  improving on 13 changed routes, worsening on 4, and no result flips. The
  fresh top-50 holdout result and rejection are recorded immediately below.
  Formula correctness alone was not a promotion criterion. No upload.
- **2026-09-25 — H6 engine-price correction rejected for promotion.** The
  independent fresh 49-route panel remained 33 wins / 16 losses (66/98 seat
  wins), all DONE, with no rescued losses or reversed wins. Of 16 changed
  route margins, 7 improved and 9 regressed; total paired-margin change was
  −228 coins. The 24 recent live-loss fixed routes likewise held 13/24 wins
  with no result flips. The correction is mechanically accurate but has no
  demonstrated win-rate benefit in these screens. A redundant current-top-100
  treatment run was stopped after the holdout failed the promotion gate; its
  partial stdout is not an outcome estimate. `main.py` stays at frozen hash;
  no Kaggle submission.
- **2026-09-25 — user-authorized repeat upload.** The user explicitly asked to
  upload the current `main.py` once. Local `py_compile` passed, and SHA-256
  matched `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
  Kaggle CLI reported `Successfully submitted to Kaggriculture`; the new
  submission ID is **56547116**, message `Current tested main.py 2026-09-25`.
  Its first status query returned `PENDING` with no score. No code change was
  made for this upload, and it does not authorize any later submission.
- **2026-09-25 21:02 UTC — read-only live status check.** Submission 56547116
  is now `COMPLETE` at 2116.4; the other active same-hash submission 56530281
  displayed 2279.2. The downloaded leaderboard showed Lakshmanan R at rank
  907 / 2279.2, with first place at 3054.0. This is a changing rating snapshot,
  not an experiment or a code comparison. `main.py` was unchanged and no
  upload occurred.
- **2026-09-25 21:46 UTC — read-only live status refresh.** Latest two
  same-hash submissions now display 2269.1 and 2121.4; the downloaded
  leaderboard ranks Lakshmanan R 925 (2269.1) and first place 3060.3.
  Snapshot: `diagnostics/top10_goal_20260926/leaderboard_2145utc/kaggriculture.zip`.
  No code change or upload occurred.
- **2026-09-26 — complete yarn route-12 experiment rejected.** Before making
  any candidate change, copied the submitted `main.py` byte-for-byte to
  `main_before_top10_goal_20260926_04b0bdc3.py` in the workspace root. The
  route-12 candidate won 16/22 versus 13/22 yarn fixed-action route pairs,
  with four rescues and one reversal; six non-yarn controls were unchanged.
  Eight freshly preselected yarn-shop seeds, both seats, then gave 0/16
  reactive wins versus `main.py`, all DONE and all activations confirmed.
  Total own cash increased 78,186 while the reacting rival increased 326,480.
  **Reject for promotion.** See
  `diagnostics/top10_goal_20260926/YARN12_RESULTS.md` and the exact JSON
  artifacts. `main.py` and Kaggle were unchanged.
- **2026-09-26 — complete early goose bundle rejected.** The existing
  cow-to-goose planner could not rewrite pastures already built before its
  turn-169 decision, so separate candidates moved the decision to turn 153
  and converted all dependent build, buy, pickup, placement, and sale actions.
  A public-state gate selected 10 of the current top-100 saved routes. The
  two-site version held 59/100 paired route wins, rescuing Hikaru Umeda but
  reversing lingxiaojun. One site reached 60/100 and 120/200 seats with no
  reversal, but a newer top-20 saved panel stayed 17/20 and its fresh reactive
  block lost 2,020 total margin over 32 games; four activated games lost
  despite increasing own cash because rival cash rose more. A separate fresh
  two-site block gained 4,678 total margin but activated in only two games,
  and cross-testing the same adverse seeds showed two sites magnified losses.
  All games were DONE, both seats were checked, and the original shop schedule
  was retained in the saved-route tests. **Reject both for promotion.** See
  `diagnostics/top10_goal_20260926/EARLY_GOOSE_RESULTS.md` and linked JSON
  artifacts. `main.py` and Kaggle remain unchanged.
- **2026-09-26 — egg/yarn complete-route switches rejected.** A new DSM
  top-100 saved-route loss used Brunch Spot/Yarn Store; the rival earned
  11,921 from 203 eggs while our forced yarn route sold no eggs. Three
  observation-legal mixed-herd route schedules were tested on DSM and four
  older original-shop routes, both seats. Route 101 rescued Gleb Tumanov but
  worsened DSM, ShunkiKyoya and keiz; routes 100 and 117 rescued none. The
  winning Matin Urdu control also narrowed under routes 101 and 117. All
  games ended DONE. **Reject all three; no broad/reactive treatment run or
  promotion.** See `diagnostics/top10_goal_20260926/EGG_YARN_HYBRID_RESULTS.md`.
  `main.py` and Kaggle remain unchanged.
- **2026-09-26 — mirror-gated 12-turn sale advance promoted locally.** An
  exact one-expression change from eight to twelve turns beat the prior local
  policy in all 32 reactive seat-games on 16 new native seeds (+28,930 total
  margin, zero errors). On complete old and fresh top-100 saved-action panels,
  paired wins stayed 59/100 and 69/100 respectively with zero flips; the
  fresh panel's 100 action hashes and 90 source episodes are disjoint from
  the old panel.
  Matched reactive checks kept 8/8 wins versus public H6 with identical cash
  and 8/8 versus Haide with a small -342 total margin change. **Promote the
  exact candidate** to local `main.py` SHA-256 `0e2c30f4...` after a
  byte-for-byte backup of the eight-turn local revision as
  `main_before_mirror12_20260926_6b5529fe.py`. Syntax and a two-seat
  promoted-file identity run passed. **No Kaggle upload.** See
  `diagnostics/top10_goal_20260926/MIRROR12_RESULTS.md`.
- **2026-09-26 — Yarn Store/Pizza Shop full-route alternatives rejected.**
  Three new current-top-100 saved-route losses shared the visible ordered
  pair `YARN_STORE,PIZZA_SHOP`. Complete routes 100, 123 and 125 improved
  some margins but rescued none of the three losses; all kept two older wins.
  Route 100 had the best fixed-action margins, yet on the first eight native
  seeds preselected by that public shop pair it won only 3/8 distinct seeds
  against reacting `main.py` and lost five, worst -6,670 per seat. Own cash
  fell 12,377 across the 16 treatment seat-games while rival cash fell
  20,139. **Reject all three;** local `main.py` and Kaggle unchanged. See
  `diagnostics/top10_goal_20260926/YARN_PIZZA_REVERSE_RESULTS.md`.
- **2026-09-26 — mirror-gated 16-turn sale lookahead rejected.** The exact
  one-expression candidate beat current 12-turn `main.py` in 27/32 native
  reactive seat-games on 16 fresh seeds (+11,960 margin), but it lost three
  and drew two. Matched reactive H6 checks were identical; Haide retained
  all eight wins but treatment margin fell 217. On the complete September 26
  100-hash saved-action development panel, paired wins fell 69 to 68 and
  seat wins 137 to 135; `len8487` reversed from +914 to -36 paired margin,
  with no rescued loss and -1,824 aggregate margin. All games were `DONE`.
  **Reject for broad promotion.** The local 12-turn `main.py` SHA-256 remains
  `0e2c30f4...`; no Kaggle upload. Full evidence:
  `diagnostics/top10_goal_20260926/MIRROR16_RESULTS.md`.
- **2026-09-26 04:00 UTC — user-requested current-source upload.** The user
  explicitly requested uploading the current `main.py`. Python AST parsing
  passed; the 12-turn local source and its new byte-identical workspace backup
  `main_uploaded_mirror12_20260926_0e2c30f4.py` both hash to
  `0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a`.
  Kaggle CLI reported successful upload; the first submissions query showed
  new ID **56568576** at `PENDING`, with no score. By 04:08 UTC it was
  `COMPLETE` and displayed 600.0, but the episode list still held only a
  validation game and no public games. **Upload this exact hash only once
  under this request.** See
  `diagnostics/top10_goal_20260926/UPLOAD_56568576.md`.
- **2026-09-26 — small reacting public-agent panel retained as diagnosis.**
  On four predeclared native seeds in both seats, the current 12-turn source
  beat each of three runnable saved public agents 8/8: Thomas 2945 source
  +12,814 total margin, Aurax7 router v6 +41,474, and Foysal 2727 source
  +58,068. All 24 games were `DONE`. A fourth source lacked its required
  `settings.json` and supplied no strategy evidence. **No policy promotion:**
  this small panel does not address the 31 fresh top-100 saved-route losses or
  establish live rank. `main.py` and Kaggle unchanged. See
  `diagnostics/top10_goal_20260926/PUBLIC_NATIVE_PANEL_RESULTS.md`.
- **2026-09-26 — saved DSM opening transplant rejected.** Replacing all
  experimental route prefixes with the first 144 actions of a top-ten DSM
  public episode failed a fresh native seed in both seats: 50,303 candidate
  coins versus 149,113 for reacting current `main.py`, all `DONE`. At day six
  it had only two strawberry tiles, three empty pastures and two weeds,
  rather than DSM's nine-strawberry source farm. **Reject before the broader
  panel:** the recorded actions did not transfer their funding and worker
  state to a new game. `main.py` and Kaggle unchanged. See
  `diagnostics/top10_goal_20260926/DSM_OPENING_RESULTS.md`.
- **2026-09-26 — Kaggle callable selection failure fixed locally.** The
  uploaded `0e2c30f4...` source's validation replay and first four public
  episodes issued only `PASS` and no market orders; all public episodes
  ended at 3,000 own coins. At 04:22 UTC its displayed score was 250.6.
  Installed Kaggle `get_last_callable` selected the newly defined Boolean
  `_clone_physical_match`, while the direct research harness selected
  `module.agent`. Appending a unique final `kaggle_main_entrypoint` fixes the
  loader without changing strategy logic. File-path versus direct-callable
  native results matched exactly in both seats on seed 2610901; after local
  promotion, final `main.py` versus candidate path matched in both seats on
  seed 2610902, with nonempty first market actions and all games `DONE`.
  **Promote the exact local fix** SHA-256 `08aa268a...` after byte-for-byte
  backup of `0e2c30f4...`. **Do not upload without a fresh explicit user
  request.** See `diagnostics/top10_goal_20260926/ENTRYPOINT_FAILURE_FIX.md`.
- **2026-09-26 04:27 UTC — user-authorized corrective upload.** The user
  explicitly approved a new upload of corrected `main.py` after being shown
  the all-`PASS` failure and exact local fix. AST parsing and Kaggle
  `get_last_callable` check passed immediately before submission; SHA-256 was
  `08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863`.
  A byte-identical backup is
  `main_uploaded_entrypoint_fix_20260926_08aa268a.py`. Kaggle CLI reported
  successful submission; new ID **56569042** was initially `PENDING`. At
  04:36 UTC it was `COMPLETE`, with one validation replay that took real
  actions and ended 72,078/72,747, exactly matching local file-path
  self-play; zero public episodes had started.
  **No further upload is authorized.** See
  `diagnostics/top10_goal_20260926/UPLOAD_56569042.md`.
- **2026-09-26 — public-source alternative opening screen rejected.** Six
  complete saved public sources (Flexonafft, Ahmed early yarn, Sunil, Municef,
  Guru and Lynn) all built essentially the same day-six farm as `main.py` on
  one native seed: four strawberries, four cows, two sheep and mostly twelve
  melons. Each lost that seed to current `main.py`; no source supplied the
  nine-to-ten-strawberry opening seen in several large top-100 losses.
  Mzcao7 never produced a day-six capture, and a slow RL source was stopped
  without a completed result. **Reject direct opening transplant from this
  screen;** no `main.py` edit or upload. See
  `diagnostics/top10_goal_20260926/OPENING_SOURCE_SCAN_RESULTS.md`.
- **2026-09-26 — partial funded strawberry opening rejected.** An isolated
  `08aa268a...`-based candidate converted six early melon seed buys and
  matching planting actions where the parent action matched the route plan.
  Its day-six farm had eight strawberries and four melons; one of six target
  turns failed the exact-action guard, so it did not realize the intended ten
  strawberries. Against reacting current `main.py` on two fresh native seeds,
  both seats, all four games ended `DONE` and all four lost by 13,221–15,013
  coins. **Reject this candidate;** it does not test a redesigned strawberry
  life-cycle policy. Local `main.py` and Kaggle submission 56569042 remain
  unchanged. See `diagnostics/top10_goal_20260926/STRAWBERRY6_RESULTS.md`.
- **2026-09-26 04:44 UTC — corrected upload first public games.** A read-only
  audit downloaded both completed public replays of submission 56569042.
  Both were wins, by 77,365 versus Shivam Kushwaha and 108,586 versus
  smileMAN13912339850. Both sides ended `DONE`; our recorded actions include
  thousands of non-`PASS` farm actions and many real market orders. Displayed
  public score was 753.2 after these two games. **Retain current submitted
  source; no new promotion or upload.** See
  `diagnostics/live_submission_56569042_20260926/RESULTS.md` and the raw
  downloaded replays.
- **2026-09-26 — DSM opening interpretation corrected.** The first DSM
  route-patch pilot was confounded because `_alt_install()` overwrote the
  first 96 patched route-0 actions at step 0. A new direct-action candidate
  actually executed all 144 saved opening actions and reproduced DSM's
  nine-strawberry, eight-melon, five-cow, three-sheep day-six farm on the
  original and a fresh native seed, both seats. But handing back to current
  `main.py` lost by 61,713 and 37,531 coins per seat, respectively. The full
  raw DSM route won by 17,199 per seat on its original
  `BRUNCH_SPOT,YARN_STORE` seed but lost by 18,802 per seat on a fresh
  `PET_CAFE,PET_CAFE` seed. All games `DONE`. **Reject both as a general
  replacement;** the portable opening needs a matching adaptive continuation.
  No `main.py` change or upload. See
  `diagnostics/top10_goal_20260926/DSM_OPENING_RESULTS.md` correction.
- **2026-09-26 — full raw DSM route broader native screen rejected.** On
  eight fresh predeclared seeds, both seats, the complete saved DSM action
  schedule beat reacting current `main.py` only 1/8 seed pairs and 2/16
  seat-games; aggregate margin was −160,296, all games `DONE`. **Reject the
  raw schedule as a general replacement.** Its source-episode +17,199 win
  did not carry over. No `main.py` edit or upload; see
  `diagnostics/top10_goal_20260926/DSM_OPENING_RESULTS.md`.
- **2026-09-26 — five high-strawberry raw schedules rejected.** Complete
  saved action routes from mtmr_s1, YumeNeko, Lucas Boesen, Matt Motoki and
  marwar22 transferred their nine-to-ten-strawberry day-six farms but won
  only 0, 2, 2, 4 and 0 of eight fresh reactive seat-games against current
  `main.py`, respectively. Every route had negative aggregate margin; all
  40 games were `DONE`. **Reject as general replacements;** a state-aware
  continuation remains untested. No `main.py` change or upload. See
  `diagnostics/top10_goal_20260926/HIGH_STRAW_RAW_RESULTS.md`.
- **2026-09-26 — complete route-ID search and route-10 rejection.** The
  experimental route override preserved the shared opening, with route 9
  reproducing the DSM baseline exactly. None of 41 route IDs beat DSM's
  `BRUNCH_SPOT,YARN_STORE` saved tape in seat 0. On the three largest
  `YARN_STORE,PIZZA_SHOP` losses, route 10 rescued YumeNeko in paired
  replay (+2,041 versus −41,408) and narrowed mtmr_s1, but one same-shop
  winning control lost 15,174 paired-margin coins. Most decisively, route
  10 lost all 16 reactive seat-games to current `main.py` on eight selected
  shop-matched seeds, all `DONE`, aggregate −43,866. **Reject route 10 and
  retain existing routing;** no `main.py` change or upload. See
  `diagnostics/top10_goal_20260926/ROUTE_ID_SEARCH_RESULTS.md`.
- **2026-09-26 — remaining public-source opening scan rejected.** Seventeen
  of 19 remaining public source files ran to `DONE` on one native seed;
  two lacked `settings.json`. Every runnable source had four strawberries
  and the same core day-six farm as current `main.py`, and lost this one
  reactive game. **No source transplant** or upload; see
  `diagnostics/top10_goal_20260926/PUBLIC_REMAINING_OPENING_RESULTS.md`.
- **2026-09-26 — relaxed physical-mirror gates rejected.** Separate exact-tile
  and crop/animal-layout gates were screened against all 31 September 26
  saved-action losses in both seats, original shops, all `DONE`. Neither
  rescued a loss; tile gate changed four routes for −62 aggregate paired
  margin, and layout gate changed five for −326. **Reject before wider
  promotion;** local `main.py` and Kaggle upload unchanged. See
  `diagnostics/top10_goal_20260926/RELAXED_MIRROR_GATE_RESULTS.md`.
- **2026-09-26 04:58 UTC — five corrected-upload public wins.** The read-only
  Kaggle replay audit now covers five completed public episodes of submission
  56569042. All five are wins by 28,938–108,586 coins, all agents `DONE`,
  and displayed score 1013.2. **Retain uploaded source and continue measuring;**
  this small early sequence does not demonstrate top-10 rank or resolve the
  31 top-100 saved-route losses. See
  `diagnostics/live_submission_56569042_20260926/RESULTS.md` and
  `audit_latest_5.json`.
- **2026-09-26 05:15 UTC — ten corrected-upload public wins.** The read-only
  Kaggle replay audit expanded to ten completed public episodes of 56569042.
  All ten are wins by 3,581–108,586 coins, all agents `DONE`, and displayed
  score 1381.8. **Retain submitted source and continue measuring;** this
  early sequence has not reached or established top-10 rank and does not
  erase the 31 saved-route losses. See
  `diagnostics/live_submission_56569042_20260926/RESULTS.md` and
  `audit_latest_10.json`.
- **2026-09-26 05:20 UTC — eleventh corrected-upload public win.** The
  read-only Kaggle replay audit added a `DONE`/`DONE` win by 8,014 coins versus
  yurunougyou!, bringing the available public sample to 11/11 wins. The
  displayed score was 1475.9. The closest existing win remains +3,581
  versus シュークリーム. **Retain submitted source;** no policy promotion or
  upload. This still provides no top-10 evidence. See
  `diagnostics/live_submission_56569042_20260926/audit_latest_11.json`.
- **2026-09-26 05:28 UTC — thirteen corrected-upload public wins.** Two more
  read-only public replays ended `DONE`/`DONE`: +2,958 versus Juste Me
  (●'◡'●) and +3,656 versus Gorgulu Fried Chicken Wings. All thirteen
  available games are wins; the displayed score was 1707.8. **Retain the
  submitted source;** no promotion or upload. See
  `diagnostics/live_submission_56569042_20260926/audit_latest_13.json`.
- **2026-09-26 — Joseph Adamski close-loss endgame diagnosis.** The
  refreshed top-100 saved-action route lost by only 369 coins per seat. A
  native engine 1.32.7 event trace reproduced seat 0 exactly at 106,388
  versus 106,757, both `DONE`. At step 718, the only two workers still
  carrying goods were already on shed-access tiles; both issued `DROP`, and
  the final market orders sold their wool, carrot and wheat. The final
  liquidation did not strand that cargo. **Reject a terminal-cargo-only
  rescue for this route;** its small deficit needs an earlier production or
  market improvement. No `main.py` edit or upload. Trace:
  `diagnostics/top10_goal_20260926/loss_trace_Joseph_s0.json.gz`.
- **2026-09-26 — 14-turn mirror sale lookahead rejected.** Isolated candidate
  `27ff9808...` won 32/32 reactive seat-games versus current 12-turn
  `main.py` on 16 new native seeds (+17,290 total margin), all `DONE`, but
  repeated the prior 16-turn candidate's saved `len8487` win-to-loss
  reversal: baseline +457 versus candidate −18 per seat. It also narrowed
  the `xi luo` control by 118 per seat. **Reject for promotion;** no full
  route panel, `main.py` edit or upload. See
  `diagnostics/top10_goal_20260926/MIRROR14_RESULTS.md` and raw JSON.
- **2026-09-26 05:42 UTC — sixteen corrected-upload public wins and rank
  snapshot.** Three more `DONE`/`DONE` public games were wins: +1,184 versus
  Toshiki Narushima, +1,376 versus Yuta Eiki, and +19,687 versus Lin.
  Displayed score was 1981.5; a contemporaneous public leaderboard export
  ranked Lakshmanan R 1569, while rank 10 scored 2904.1. **Retain current
  submitted source;** no promotion or upload. The 16 wins do not establish
  top-10 strength. See `diagnostics/live_submission_56569042_20260926/audit_latest_16.json`
  and `diagnostics/leaderboard_20260926_0545/kaggriculture.zip`.
- **2026-09-26 — day-six portfolio association quantified.** Of the 31
  September 26 saved-action losses, 20 rivals had more than our four
  strawberry tiles at day six; their median seat loss was 10,700.5 coins,
  versus 3,558 across the ten losses against exactly-four rivals. All twelve
  largest deficits had rivals with at least seven strawberries. This is a
  loss-only association, not a causal estimate; simple early strawberry
  swaps and full raw high-straw schedules already failed reactive checks.
  **No promotion or upload.** See
  `diagnostics/top10_goal_20260926/LOSS_PORTFOLIO_PATTERN.md`.
- **2026-09-26 — public replay audit availability guard.** Kaggle marked
  three new public episodes complete before quiet CLI downloads returned
  replay bytes, leaving zero-byte placeholders. The read-only audit helper
  now retries those placeholders on later runs and summarizes only nonempty
  replays. Manual sequential downloads subsequently returned full payloads,
  and the resulting 16-game audit parsed normally. This is an audit-tool
  correction, not a policy change; `main.py` and Kaggle submission unchanged.
- **2026-09-26 05:46 UTC — seventeenth corrected-upload public win.**
  Submission 56569042 beat jasonyoung by 20,489 coins, both agents `DONE`.
  The available sample is 17/17 wins and displayed score 2110.9. A public
  leaderboard export ranked Lakshmanan R 1256 while rank 10 scored 2904.5.
  **Retain current source;** no policy promotion or upload. See
  `diagnostics/live_submission_56569042_20260926/audit_latest_17.json` and
  `diagnostics/leaderboard_20260926_0548/kaggriculture.zip`.
- **2026-09-26 — high-strawberry sale-timing gate rejected.** A separate
  candidate enabled twelve-turn sales after a visible day-six rival lead of
  at least three strawberry tiles (rival at least seven). On all 31 saved
  September 26 loss routes, both seats, 17 route margins changed, but zero
  losses were rescued. Aggregate paired margin fell 4,414 coins; Joseph
  Adamski widened from −738 to −3,536 paired. All 62 games `DONE`.
  **Reject before reactive testing;** the structural farm disadvantage is
  not cured by this simple sale timing. No `main.py` edit or upload. See
  `diagnostics/top10_goal_20260926/HIGHSTRAW_SALE12_RESULTS.md`.
- **2026-09-26 — unused-coop one-goose pilots rejected.** On the saved DSM
  Brunch Spot route, current `main.py` lost by 17,199 in seat 0. Merely
  buying a goose left it in the shed and widened the loss to 17,489. A
  dedicated daily hand placed and serviced it, but higher labor and wheat
  costs exceeded 1,729 coins of added egg sales; loss widened to 19,602.
  Assigning an existing planned hand disrupted crop care and widened the
  loss to 51,711. All three native pilots finished `DONE`/`DONE`.
  **Reject all three before broader testing;** the single saved route is
  development evidence, not independent or reactive validation. No `main.py`
  edit or upload. See `diagnostics/top10_goal_20260926/EMPTY_COOP_RESULTS.md`.
- **2026-09-26 06:11 UTC — corrected submission reached rank 869, with three
  narrow losses.** A read-only audit found 21 wins and 3 losses across 24
  public `DONE`/`DONE` episodes; losses were -277, -276, and -131 coins against
  Igor V, Atakan Aldemir, and GanadorPlusUltra. The contemporaneous public
  leaderboard ranked Lakshmanan R 869 / 2269.0, with rank 10 at 2902.4.
  **Retain submitted source while investigating;** this rank is far short of
  top 10 and the score remains volatile. See
  `diagnostics/live_submission_56569042_20260926/RESULTS.md` and
  `diagnostics/leaderboard_20260926_0611/kaggriculture.zip`.
- **2026-09-26 — three live near-mirror losses reproduced and sale-length
  alternatives rejected.** The public loss action tapes reproduced the exact
  live cash on the original seed and seat; Igor and Atakan also had the same
  losses after swapping seats. The old eight-turn and experimental 14-turn
  sale lookaheads rescued zero of three losses in either seat. Original-seat
  margins for current 12 turns were -277/-276/-131; eight turns gave
  -837/-530/-127 and 14 turns -192/-228/-101. All games `DONE`.
  Native executed-cash ledgers exactly reconciled all three games and found
  our net strawberry cash lower by 668, 131, and 281 coins, despite selling
  the same units as Igor and Atakan and ten more than Ganador. Fixed action
  routes are development diagnostics, not independent validation, and 14
  turns already has a separate win-to-loss saved-route reversal. **Reject
  both sale-length alternatives;** no `main.py` edit or upload. See
  `diagnostics/live_submission_56569042_20260926/RESULTS.md` and raw ledgers.
- **2026-09-26 — single high-strawberry donor plans rejected.** Isolated
  candidates fed complete public DSM, Lucas Boesen and Matt Motoki schedules
  through the existing adaptive layers. They reproduced nine or ten day-six
  strawberry tiles. Lucas and Matt rescued their own saved source losses in
  both seats (+2,581 and +5,071 per seat), but on predeclared fresh native
  seeds versus reacting `main.py`, Lucas won only 1/8 seed pairs (2/16 seats;
  mean margin -21,884) and Matt 0/4 (0/8 seats; mean margin -14,192). DSM
  lost its own source route by 45,849 per seat. All games `DONE`.
  **Reject all three;** fixed-action source wins did not generalize. No
  `main.py` edit or upload. See
  `diagnostics/top10_goal_20260926/ADAPTIVE_DONOR_RESULTS.md`.
- **2026-09-26 — public Matt shop-family selector rejected.** Eight recent
  public routes from one submission covered seven first-two-shop pairs, with
  four first-day and six first-four-day action hashes. A candidate started
  from the common opening and selected a complete plan by observed shops,
  while keeping existing adaptive wrappers. It beat its own saved source
  route by 12,850 per seat but lost all eight fresh reactive seat-games on
  four new native seeds (mean margin -12,938), all `DONE`. **Reject;** even
  a small observed-shop route family did not generalize. No `main.py` edit or
  upload. See `diagnostics/top10_goal_20260926/MATT_FAMILY_RESULTS.md`.
- **2026-09-26 06:32 UTC — corrected submission public rating slipped.** The
  read-only audit expanded to 29 `DONE`/`DONE` episodes: 23 wins, six losses.
  New wins were +102 and +40; new losses were -65, -690 and -4,666. The
  leaderboard ranked Lakshmanan R 994 / 2211.4 versus rank 10 at 2907.1,
  below the prior 24-game rank 869 / 2269.0. K.Piro was an exact physical
  mirror throughout; wei chang and datatuu had later farm divergences.
  **Retain submitted source while diagnosing;** the latest sample does not
  support a top-10 claim or promotion of the rejected donor candidates.
  No upload. See `diagnostics/live_submission_56569042_20260926/RESULTS.md`
  and `diagnostics/leaderboard_20260926_0632/kaggriculture.zip`.
- **2026-09-26 06:53 UTC — 36-game live audit and refreshed rank.** A read-only
  audit found 28 wins and eight losses over 36 public episodes of submitted
  hash `08aa268a...`, all players `DONE`. The seven newest games comprised
  five wins and two losses (−1,006 versus Konstantin Zorin and −767 versus
  kaggle Osaka). The 06:58 UTC leaderboard showed rank 837 / 2278.6, with
  rank 10 at 2900.9. **Retain submitted source as current live baseline;**
  this is neither top-10 rank nor evidence the newer local policy has been
  tested live. See `diagnostics/live_submission_56569042_20260926/RESULTS.md`
  and `diagnostics/leaderboard_20260926_0658/kaggriculture.zip`.
- **2026-09-26 06:59 UTC — strawberry-only mirror lookahead promoted locally.**
  Frozen isolated candidate `489fe8e4...` lets strawberry sales inspect up
  to 24 turns when the farms physically mirror, keeping other mirrored sales
  at 12 and non-mirrored sales at four. On two predeclared 16-seed native
  reacting-opponent blocks against `08aa268a...`, both seats, paired seed
  outcomes were 12/1/3 and 10/0/6 positive/negative/tied; all 64 games
  `DONE`, total margin +18,792. Six development live-loss tapes yielded two
  rescues; seven later public tapes retained five wins and two losses, with
  +1,110 margin over 14 seat-games. Exact eligible September 25/26 top-100
  regression screens found zero flips; full-panel paired wins remain 59/100
  and 69/100. The previously sensitive `len8487` route retained +457 per
  seat. An activated Kaggle file-path game selected the intended final
  callable and matched direct-call +690 in both seats. **Promote exact bytes
  to local `main.py` only;** old source backed up as
  `main_before_mirror_straw24_20260926_08aa268a.py`. This is an incremental
  near-mirror improvement with one negative reactive seed and no top-10 or
  all-100 proof. At the time of local promotion, submission 56569042 remained
  the older `08aa268a...` bytes. See
  `diagnostics/top10_goal_20260926/MIRROR_STRAW24_RESULTS.md` and
  `mirror_straw24_promoted_parity.json` in that folder.
- **2026-09-26 07:01 UTC — user-authorized mirror24 upload.** After a fresh
  explicit user approval, exact local hash `489fe8e4...` was snapshotted and
  uploaded to Kaggle as submission **56572390**. CLI reported success; the
  first read-only query returned `PENDING`, with remote validation and public
  score not yet available. **Promote to uploaded candidate; do not claim
  competitive improvement until live games run.** This authorization is
  consumed; another upload needs a new explicit request. See
  `diagnostics/top10_goal_20260926/UPLOAD_56572390.md`.
- **2026-09-26 07:04 UTC — mirror24 remote validation passed.** Submission
  56572390 became `COMPLETE`. The seed-0 self-play replay ended 71,657 /
  72,326, both `DONE`, with 649 non-`PASS` farmer actions and 415/416
  market-action turns. Local Kaggle file-path self-play with the uploaded
  hash reproduced both cash totals and first actions exactly. **Retain
  submitted candidate for live evaluation;** no public competitive episodes
  existed at this check. See `diagnostics/top10_goal_20260926/UPLOAD_56572390.md`
  and `diagnostics/live_submission_56572390_20260926/validation_parity.json`.
- **2026-09-26 07:12 UTC — first mirror24 public games.** Read-only replay
  audit found two `DONE`/`DONE` wins: +119,616 versus BalaVignesh and
  +102,011 versus Julio Cesar Filho. **Continue observing;** two early
  opponents do not support a top-10 conclusion or a new policy promotion.
  No upload. See
  `diagnostics/live_submission_56572390_20260926/audit_latest_2.json`.
- **2026-09-26 07:14 UTC — local v32 fallback rejected.** The local
  `main_v32_observable_portfolio.py` hash `9cb69949...` lost all four fresh
  native reactive seed pairs (eight seat-games) against current `main.py`,
  mean seat margin −47,765.75; every game ended `DONE`. **Reject as a
  replacement;** an old leaderboard score does not outweigh the current
  paired evidence. No `main.py` change or upload. See
  `diagnostics/top10_goal_20260926/V32_REACTIVE_SCREEN.md`.
- **2026-09-26 07:19 UTC — 36-turn strawberry mirror pilot rejected.** An
  isolated one-constant extension from submitted 24 to 36 turns rescued
  zero additional losses on six older live-loss routes in both seats; total
  margin fell 192 coins. It preserved five wins and two losses on seven
  later public routes but lost 810 aggregate margin over 14 seat-games.
  The `len8487` risk control stayed +457 per seat; all 28 games `DONE`.
  **Reject at the predeclared development gate;** no need to expose the
  repeatedly used top-100 panels or fresh reactive seeds to this weaker
  pilot. No `main.py` change or Kaggle upload. See
  `diagnostics/top10_goal_20260926/MIRROR_STRAW36_RESULTS.md`.
- **2026-09-26 07:20 UTC — first four public mirror24 wins did not activate
  the new branch.** The four read-only public replays of 56572390 all ended
  `DONE`/`DONE` wins (+119,616, +102,011, +36,710, +41,000). In each, the
  two visible farms never met the exact physical-mirror gate during turns
  144–717. **Treat these as execution evidence, not proof of the new sale
  rule's live value;** continue monitoring stronger matches. No policy
  change or upload. See
  `diagnostics/live_submission_56572390_20260926/audit_latest_4.json` and
  `mirror_exposure.json` in that folder.
- **2026-09-26 07:23 UTC — a new top-100 public route panel was captured.**
  A fresh leaderboard snapshot supplied 100 teams. The collector initially
  skipped the second team when two appeared in one episode; the read-only
  collector was corrected and rerun. The resulting panel has exactly 100
  team routes, 100 distinct action hashes from 88 public episodes, with no
  action-hash or episode overlap with the preceding September 26 panel and
  no action-hash overlap with the September 25 panel. **Accept as a fresh
  fixed-action regression/diagnosis panel, not reactive validation.** The
  current-agent both-seat benchmark is running. See
  `diagnostics/top100_refresh_2026-09-26_0708/route_audit.json` and
  `routes/summary.json` in that folder.
- **2026-09-26 07:33 UTC — strawberry-tile reaction is too late for opening
  melon choices in four traced rival scenarios.** All twelve incumbent
  melon seeds were bought by turn 17 and planted by 18. The first visible
  rival strawberry lead appeared at turn 14 for Lucas, 63 for DSM and Arda,
  and 87 for Boey. **Do not promote a strawberry-tile-gated opening swap**
  from this diagnosis; most early melon commitments predate the signal.
  An earlier observation-legal signal, better default opening, or funded
  later expansion needs separate testing. No `main.py` edit or upload. See
  `diagnostics/top10_goal_20260926/OPENING_SIGNAL_TIMING.md`.
- **2026-09-26 07:35 UTC — new top-100 route benchmark contradicts all-100
  goal.** Current uploaded/local hash `489fe8e4...` completed 200 fixed-route
  seat-games, all `DONE`, winning 66/100 paired routes and 132/200 seats.
  It won 9/10 saved top-ten routes, losing Boey by 2,890 per seat. Of 34
  total losses, 21 rivals had at least seven day-six strawberry tiles.
  The contemporaneous public leaderboard ranked the team 900 / 2248.8,
  versus rank 10 at 2897.8. **Retain current policy while diagnosing and
  testing complete production changes;** neither the fixed panel nor the
  early live score justifies claiming top-10 or all-100 success. No upload.
  See `diagnostics/top100_refresh_2026-09-26_0708/RESULTS.md` and
  `diagnostics/leaderboard_20260926_0736/kaggriculture.zip`.
- **2026-09-26 07:42 UTC — largest new loss is a wool gap, not a strawberry
  sales gap.** An exact native mhw trace reproduced −45,791 in seat 0,
  both `DONE`. The rival earned 159,937 from wool versus our 99,516, while
  our strawberry sales exceeded theirs 7,028 to 3,908. At day 18 it had
  36 sheep versus our 17; its extra 9,500 sheep cost was much smaller than
  the 60,421 wool-receipt lead. **Use complete production and net-cash
  accounting for this route;** day-six strawberry count alone misdiagnoses
  it. No policy promotion or upload. See
  `diagnostics/top100_refresh_2026-09-26_0708/MHW_LOSS_DIAGNOSIS.md`.
- **2026-09-26 07:45 UTC — double-Yarn, high-sheep route-12 pilot rejected.**
  A new observation-legal gate selected the complete route 12 against
  rivals with at least three sheep on two visible Yarn Stores. On three
  fresh-panel target losses, both seats, mhw's fixed paired margin flipped
  −92,486 to +9,218, but own cash fell 37,386 and the fixed rival's cash
  fell 139,090. ShunkiKyoya and AI是我的豆包 worsened by 13,296 and 6,246
  paired-margin coins. The two-sheep control was exact, all eight games
  `DONE`, and gate errors were zero. **Reject at the predeclared own-cash
  and no-material-regression gate;** a replay flip driven by rival cash
  suppression is not a live-strength result. No `main.py` edit or upload.
  See `diagnostics/top10_goal_20260926/DOUBLE_YARN_HIGHSHEEP_RESULTS.md`.
- **2026-09-26 07:37 UTC — day-11 sheep commitment controller rejected.**
  An isolated observation-only wrapper compared the incumbent's normal
  continuation with the inherited complete six-sheep executor under three
  modeled shop futures. After fixing an empty-order parser bug and rerunning
  the frozen 16-seed, both-seat native block against trusted reacting
  `main.py`, the controller activated on three seeds, lost all six activated
  seats, and reduced summed paired margin by 60,686 coins; the simpler
  always-expand control gave exactly the same outcomes. All 96 A/B/C games
  ended `DONE`; no current-source edit or upload occurred. A full engine-event
  cash ledger on one activated seat reconciled every coin. Native future
  shops changed and its margin fell 9,850; forcing the baseline shop sequence
  while retaining a reactive rival changed the margin to +8,659, mainly
  through reduced rival wool receipts. **Reject the overlay**: its optimistic
  forecast omitted route opportunity costs and future-shop uncertainty.
  Matched-shop evidence is one controlled diagnostic, not independent
  validation. See `diagnostics/commitment_controller_20260926/PLAN.md`,
  `RESULTS.md`, `abc_fixed_dev16_comparison.json`, and
  `ledger_2612002_s0.json` there.
- **2026-09-26 17:09 UTC — mirror24 live sample and rank.** Read-only Kaggle
  audit of the latest 100 public games from submission 56572390 found 71 wins
  and 29 losses, every player `DONE`. The median loss was 460 coins and the
  largest was 4,462; all 29 losses had visible physical-mirror exposure during
  turns 144–717. Of 71 wins, 38 had that exposure and 33 did not. This
  identifies a close mirror-match problem, not the causal effect of the 24-turn
  strawberry branch. The latest submission scored 2165.0, below the older
  08aa submission's 2221.0. A 17:07 UTC leaderboard snapshot ranked the team
  876 on its better score, versus rank 10 at 2881.7. **Retain 489fe8e4 as
  the uploaded/local artifact while diagnosing; do not claim it improved live
  strength or submit again without a fresh explicit request.** See
  `diagnostics/live_submission_56572390_20260926/RESULTS.md`,
  `audit_latest_100.json`, `mirror_exposure.json`, and
  `diagnostics/leaderboard_20260926_1707/kaggriculture.zip`.
- **2026-09-26 17:22 UTC — pure-sale mirror relaxation rejected.** A frozen
  isolated candidate released the first-future-sale protection only when the
  visible farms matched and the future market turn contained sales only. Its
  39-route panel contained all 29 latest live losses plus ten closest wins;
  current `main.py` exactly reproduced all 39 original-seat public cash pairs.
  Across both seats, all 156 baseline/candidate games ended `DONE`. The pilot
  rescued two losses, reversed zero control wins, and raised own cash 2,163
  and fixed-rival cash 518 across original seats. The predeclared development
  gate required five rescues, so **reject before reactive testing or main-file
  promotion**. Saved actions cannot establish a live advantage; no upload.
  See `diagnostics/top10_goal_20260926/PURE_SALE_MIRROR_RESULTS.md` and
  `pure_sale_dev_comparison.json` there.
- **2026-09-26 17:29 UTC — fresh reactive check supports mirror24 retention.**
  Current uploaded/local `489fe8e4...` played the prior uploaded `08aa268a...`
  source on predeclared fresh native seeds 2612600–2612623, both seats. All
  48 games ended `DONE`; 18 paired seeds favored current, five favored old,
  and one tied; summed margin was +14,326, with zero candidate telemetry
  errors. **Retain current local source**, despite its lower Kaggle displayed
  score, because those public scores use different rival samples and this
  controlled new block favors the current version. This is self-play, not
  proof of top-10 strength or all-100 route success. No file change/upload.
  See `diagnostics/top10_goal_20260926/MIRROR24_RETENTION_RESULTS.md` and
  `reactive_mirror24_retention24.json` there.
- **2026-09-26 17:33 UTC — refreshed Boey loss is a funded-portfolio gap.**
  An exact native event trace reproduced the fresh saved first-place Boey
  route's −2,890 seat-0 loss, both `DONE`. Our strawberry and tomato net cash
  led by 15,494 and 12,054, but we trailed net wheat, wool, egg and carrot
  by 13,180, 5,281, 5,133 and 4,784; land/hiring cost another 7,553 more.
  Market wheat turnover included large buys as well as sells, so gross sales
  do not imply a risk-free arbitrage. The physical-mirror gate never opened.
  **Diagnose only**; a complete funded production route and later-shop risk
  matter more than another mirror-sale tweak here. No `main.py` edit/upload.
  See `diagnostics/top100_refresh_2026-09-26_0708/BOEY_LOSS_DIAGNOSIS.md`
  and `boey_trace_s0.json.gz` there.
- **2026-09-26 17:44 UTC — 34 exact fresh-panel loss ledgers identify the
  wider portfolio deficit.** Current source reproduced both original-seed,
  seat-0 terminal cash values against every one of the 34 paired losing
  public routes, all `DONE`; the route join was corrected to use action hash,
  seed, and source seat when an episode held two top teams. Summed net cash
  trailed fixed rivals by 175,114 in tomato (30 routes negative) and 143,782
  in wool (23 negative), versus leads of 75,106 melon, 68,742 milk and 49,400
  fertilizer. We spent 21,741 less on hires and 8,000 less on land overall;
  a production addition must fund its labor and market impact. **Diagnose
  only:** these are selected fixed-action losses, not causal proof that a crop
  or herd increase improves live play. No `main.py` edit/upload. See
  `diagnostics/top100_refresh_2026-09-26_0708/ALL34_LOSS_LEDGER_RESULTS.md`
  and `all34_loss_ledgers_s0.json` there.
- **2026-09-26 17:53 UTC — complete day-16 tomato bundle rejected.** The
  frozen pilot used the 12 largest net-tomato deficits and eight high-rank
  winning controls. Five targets and four controls met the proposed day-16
  observable gate in both seats. The isolated candidate committed a complete
  ten-tomato/worker/land bundle on all nine activated routes, confirming 180
  plants and 1,200 harvest units across the two seats, with zero errors and
  all 80 baseline/candidate games `DONE`. Snorlax flipped −7,618 to +15,890
  paired margin, but the other four activated targets worsened. Across active
  routes own cash fell 2,582, fixed-rival cash rose 28,808, and paired margin
  fell 31,390. **Reject at the predeclared development gate** (one rescue vs
  two required, aggregate cash/margin negative), without reactive promotion
  testing or any `main.py` edit/upload. See
  `diagnostics/top10_goal_20260926/EARLY_TOMATO16_RESULTS.md` and
  `early_tomato16_comparison.json` there.
- **2026-09-26 17:54 UTC — live scores and rank remain below target.** Kaggle
  submissions 56572390 (`489fe8e4...`) and 56569042 (`08aa268a...`) were
  both `COMPLETE`, displaying 2168.3 and 2206.8 respectively. The leaderboard
  used the older higher score and ranked Lakshmanan R 927, versus rank 10 at
  2888.7. Exact `main.py` hash still matched the uploaded 489fe8e4 snapshot
  and the 08aa backup was present. **No new upload or local promotion** after
  the rejected pilots. See
  `diagnostics/leaderboard_20260926_1754/kaggriculture.zip` and
  `diagnostics/live_submission_56572390_20260926/RESULTS.md`.
- **2026-09-26 17:30 UTC — day-six complete-route controller rejected.** The
  second predeclared challenger compared two coherent existing route tapes
  (route 9 incumbent, route 0 alternative) at step 144 using legal visible
  state, time-indexed resource/sale forecasts and three future Yarn scenarios.
  OFF parity matched native `main.py` in both seats on two seeds. In the
  frozen 16-seed, both-seat reacting-main development block, only two seeds
  qualified. B forecast route 0 unfavorably and retained the incumbent in
  all 32 games: zero new paired wins, 16 draws. C always switched on those
  two seeds and lost four seats; own cash rose 5,392 but rival cash rose
  17,686, reducing paired margin 12,294. All 96 A/B/C games ended `DONE`.
  Exact engine-event ledgers for seat 0 on both activated seeds reconcile every
  cash delta; future shops stayed identical in these two controls, and rival
  wool receipts rose by 8,046 and 4,005. **Reject B/C at the predeclared
  development gate**, retain `main.py`, and stop variant tuning after the
  two distinct challenger mechanisms. No saved-route or untouched native
  panel was exposed to this rejected candidate; no upload. See
  `diagnostics/commitment_controller_20260926/PLAN2.md`,
  `ROUTE_RESULTS.md`, `route_abc_dev16_comparison.json`, and
  `route_ledger_activated_s0.json` there.
- **2026-09-26 18:04 UTC — public v48 route-data transplant rejected.**
  Statically decoded the public notebook's verified compressed agent and six
  719-turn action routes without importing or executing downloaded Python.
  A locally written, data-only visible-shop router ran the complete routes
  from turn zero on predeclared native seeds 2614000–2614007 in both seats
  against reacting current `main.py`, with original endogenous shops. All
  16 games ended `DONE`/`DONE`; the transplant lost all eight paired seeds and
  all 16 seats, total paired margin −429,770 (candidate cash 1,494,918 vs
  rival 1,924,688). It omits the public full agent's weed repair, market
  scoring, clone preemption and terminal handling, so this is a route-data
  rejection, not a claim about the author's full policy. **Reject data-only
  transplant; retain `main.py` unchanged.** No saved top-100 screen or Kaggle
  upload. See `diagnostics/public_kaito_v48_20260926/RESULTS.md` and
  `reactive_screen.json` there.
- **2026-09-26 18:08 UTC — no terminal stored cargo in 29 current live
  losses.** Read-only check of all original Kaggle replays from the frozen
  100-game audit found zero goods in our shed or worker inventories after the
  final settled action in every one of the 29 losses. Installed engine 1.32.7
  does not clear those inventories at match termination. **Reject a final
  stored-cargo-only fix** for these losses; earlier production or market
  timing remains possible. No `main.py` edit/upload. See
  `diagnostics/live_submission_56572390_20260926/terminal_inventory_losses.json`
  and the appended `RESULTS.md` section there.
- **2026-09-26 18:17 UTC — exact late-game ledger of all 29 current live
  losses.** Native replay of every original-seed, original-seat public loss
  reproduced both terminal cash values with `main.py` hash `489fe8e4...` and
  reconciled all executed cash by item and day. After day 19 the 29-game
  aggregate margin was +589, with 19 games ahead; days 20–29 cost 24,062
  margin coins, and 28 games eroded. Late net cash gaps were strawberry
  −9,640 (23/29 games negative, only four fewer sale units), wool −9,268
  (23/29, six fewer units), milk −9,519 (19/29; Tavuk −6,271), and carrot
  −5,170 (19/29), partly offset by wheat +7,039. Other late cash difference
  was zero. **Diagnose only; no promotion.** Saved rival actions do not adapt
  to a policy change. Prioritize an isolated late price/timing experiment;
  no `main.py` edit/upload. See
  `diagnostics/live_submission_56572390_20260926/LATE_LOSS_LEDGER_RESULTS.md`
  and `late_loss_ledgers_29.json`.
- **2026-09-26 18:23 UTC — half-base strawberry mirror quote guard rejected.**
  The isolated `exp_mirror_straw_quote60_20260926.py` hash `6c1d9501...`
  suppressed only extra 24-turn strawberry sale advances on physical mirrors
  when the visible quote was below 60. On the frozen 29 current public losses
  plus ten close wins, original seeds and both seats, the 78 candidate games
  were `DONE`/`DONE` with zero errors; the existing baseline reproduced all
  39 original-seat Kaggle cash pairs. In those original seats the guard
  rescued **0/29** losses, reversed the +163 FinalSunFlower win to −190,
  reduced own cash 405, raised fixed-rival cash 2,000, and reduced paired
  margin 2,405. **Reject at the predeclared five-rescue and cash gates**;
  no reactive/top-100 promotion testing, main edit, or Kaggle upload.
  See `diagnostics/late_quote_guard_20260926/RESULTS.md` and raw comparison.
- **2026-09-26 18:08 UTC — independent forward-search agent rejected for
  promotion.** Created standalone `kaggriculture_search_agent.py` (retained
  v2 SHA-256 `5e4023df...`) using a bounded beam search over full observed
  production commitments, three future shop/rival scenarios, paired-margin
  evaluation, and observation-driven worker execution. It has no seed,
  future-shop lookup, hidden rival inventory, or incumbent route tape.
  Native engine 1.32.7 v1 lost all eight paired seeds 0–7 (16 seats; mean
  margin −106,011 per seat). Retained v2 lost all four later seeds 8–11
  (eight seats; mean margin −88,281, mean own cash 59,863); timed-fertilizer
  v5 also lost all four later seeds (mean margin −88,435, own cash 53,576).
  Trace diagnosis showed v1 invested too slowly and later variants' forecast
  portfolios were not reliably funded and served. In a v3 seed-0 trace, our
  worker `PASS`/fertilizer-collection/feed counts were 1,579/86/83 versus
  418/375/349 for reacting `main.py`. V4 raised own cash on seed 0 to
  67,746 but worsened paired margin to −96,693 as rival cash rose to
  164,439. The retained v2 file beat a passive agent on seed 42, 71,813 to
  3,000, and Kaggle's file-path loader selected its final `agent` callable;
  direct and path games matched terminal cash and first action. **Reject
  promotion and Kaggle upload; retain current `main.py` unchanged.** This
  fresh file is a research candidate, not a winning leaderboard claim.
  Evidence and reproduction commands:
  `diagnostics/search_agent_20260926/RESULTS.md` and linked native JSON.
- **2026-09-26 18:26 UTC — published scheduler wheat-reserve idea rejected.**
  Statically reviewed Evelyn3976's public worker-owned feed scheduling and
  Ahmed Berat Ozer's public physical shed guards. `main.py` already has
  related V43 overflow and atomic planting safeguards. An isolated search-agent
  candidate set the wheat SELL reserve equal to its `2*animal_count+3` BUY
  target. On predeclared native seeds 2615000–2615003, both seats against
  reacting `main.py` and original shops, all 16 A/B games were `DONE`;
  B lost all four paired seeds to `main.py` and reduced aggregate A/B paired
  margin by 2,936 coins (two seeds improved, two worsened). **Reject at the
  predeclared development gate; retain search v2 and `main.py`.** No untouched
  confirmation seeds or Kaggle upload. See
  `diagnostics/public_supply_inspiration_20260926/PLAN.md`, `RESULTS.md`,
  `baseline_dev4.json`, and `candidate_dev4.json`.
- **2026-09-26 18:30 UTC — late mirror first-sale advance rejected.** The
  isolated `exp_late_first_sale_mirror_20260926.py` hash `cf016e23...`
  removed first-future-sale protection only during steps 480–717 on a
  visible physical mirror. On the frozen 29 live losses and ten close wins,
  original seeds and both seats, all 78 candidate games ended `DONE`/`DONE`
  with zero errors; the reused exact baseline matched every original-seat
  Kaggle cash pair. Original-seat margin rose 1,389 (own cash +983, fixed
  rival −406), one loss flipped (−374→+64), and no close win reversed. Full
  panel route wins rose 12→13/39. **Reject at the predeclared five-rescue
  gate**; the small fixed-action gain is insufficient to expose fresh
  reactive/top-100 panels. No `main.py` edit or upload. See
  `diagnostics/late_first_sale_20260926/RESULTS.md` and raw comparisons.
- **2026-09-26 18:35 UTC — live strawberry/wool gaps are mainly per-turn
  pacing.** Exact engine transaction traces of all 29 current live losses,
  original seeds/seats and saved rival actions, reproduced both Kaggle cash
  totals. From day 20 onward, strawberry sales totaled 4,999 versus 5,003
  rival units but yielded 9,640 fewer coins. On 388 turns with equal positive
  sale-unit counts, our receipt difference was **+155**; on 658 turns with
  unequal counts it was **−9,795**. Wool sold 2,179 versus 2,185 units, with
  −1,963 on 291 equal-unit turns and −7,305 on 371 unequal turns. Unequal
  turns include different batch sizes or one-sided timing, not proof of a
  specific counterfactual. **Diagnose only:** simple quote and first-sale
  variants failed; a future inventory/market pacing controller needs native
  reactive validation. No `main.py` edit/upload. See
  `diagnostics/live_submission_56572390_20260926/PRICE_GAP_DECOMP_RESULTS.md`
  and `price_gap_cases_29.json`.
- **2026-09-26 18:32 UTC — published feed ownership idea promoted only to
  separate research agent.** Adapted Evelyn3976's physical wheat-carrier
  ownership concept in our standalone search-agent scheduler: suppress
  unavailable FEED jobs, prefer workers holding wheat, and serve CARE before
  abandoning an empty shed trip. No public source was imported or copied.
  Against reacting `main.py` with original shops, development seeds
  2615010–2615013 improved three of four paired margins and aggregate margin
  by 45,468 coins; missing-supply events fell 366→281. Untouched confirmation
  seeds 2615014–2615017 improved three of four paired margins but aggregate
  margin by only **449 coins**; missing-supply fell 352→304. All 32 A/B games
  ended `DONE`, yet the candidate lost every seat to `main.py`. It passed the
  frozen A/B research-file gate and Kaggle's path loader selected `agent`, so
  **promote only to `kaggriculture_search_agent.py`; reject `main.py`
  promotion and Kaggle upload.** The small confirmation gain and own-cash
  decline limit confidence. V2 remains backed up. See
  `diagnostics/public_supply_inspiration_20260926/FEED_PLAN.md`,
  `FEED_RESULTS.md`, and the four native JSON files there.

- **2026-09-26 18:45 UTC — observed-stock sale race, first gate rejected.**
  The isolated `exp_mirror_stock_frontload_20260927.py` passed a native
  two-seat smoke on saved episode 113642505 with all games `DONE`, but its
  exact current physical-mirror condition was false during the 20-unit
  strawberry missed-sale window. It fired zero times and changed neither
  final cash pair. The public replay has 283 earlier exact-match turns, but
  late farm tiles differ. **Reject this gate as a mechanism failure before
  the frozen 39-route screen; no main edit or Kaggle upload.** Measure
  observable earlier-match streaks before a revised rule. See
  `diagnostics/mirror_stock_frontload_20260927/MECHANISM_SMOKE.md`.

- **2026-09-26 18:53 UTC — persistent mirror stock-sale candidate rejected.**
  Isolated `exp_mirror_stock_frontload_latched_20260927.py` (SHA-256
  `73aa0150...`) latched only after 24 consecutive visible physical matches,
  then frontloaded observed strawberry shed stock after late tile divergence
  while workers remained aligned. It activated in the documented 20-unit
  missed-sale trace and improved its fixed-rival margin −900→+85 in both
  seats. On the frozen 29 public losses and ten close wins, both seats and
  original shops, all 78 candidate games ended `DONE` with zero errors.
  Original seats rescued eight losses and reversed one control win, but own
  cash fell **845** while fixed-rival cash fell 11,440, for paired margin
  +10,595. **Reject at the predeclared positive-own-cash gate; no reactive
  promotion screen, main edit or Kaggle upload.** Fixed tapes do not adapt.
  See `diagnostics/mirror_stock_frontload_20260927/LATCHED_RESULTS.md` and
  `latched_dev_comparison.json`.

- **2026-09-26 19:00 UTC — half-base latched sale passes fixed routes but
  fails the predeclared reactive gate.** `exp_mirror_stock_frontload_halfbase_20260927.py`
  (SHA-256 `e9517dae...`) sells observed stock only when the strawberry
  quote is at least 60, half of the native 120-coin base. On 29 frozen live
  losses plus ten controls in both seats, all 78 games were `DONE`, with
  zero errors. Original seats rescued five losses, reversed no control win,
  gained own cash 1,874 and paired margin 5,759 against fixed rival actions.
  Fresh reactive seeds 2614300–2614315 against `main.py` in both seats
  produced **one positive pair, one negative pair and 14 ties** (+546
  aggregate margin); only four of 32 games triggered the rule. This fails
  the predeclared positive paired-seed majority. **Reject promotion; no
  main edit or upload.** See
  `diagnostics/mirror_stock_frontload_20260927/HALF_BASE_RESULTS.md` and
  linked JSON.

- **2026-09-26 19:04 UTC — reacting Haide near-clone diagnostic failed.**
  On fresh native seeds 2614350–2614357, both seats, the unchanged half-base
  candidate and current `main.py` separately faced the saved public Haide
  policy with matched original seed/seat and endogenous shops. All 32 A/B
  games were `DONE`; the candidate triggered in 8/16 treatment games and
  flipped both incumbent losses, raising wins 14→16/16. Yet paired-seed
  deltas were two positive, two negative and four tied; own cash fell 44,
  Haide cash fell 2,416 and paired margin rose 2,372. It failed the
  predeclared ≥5/8 improving pairs and positive-own-cash diagnostic gates.
  **Retain the earlier rejection; no `main.py` edit or Kaggle upload.** See
  `diagnostics/mirror_stock_frontload_20260927/HAIDE_REACTIVE_RESULTS.md`
  and raw JSON.

- **2026-09-26 19:08 UTC — near-clone sale race needs rival timing evidence.**
  First-action native traces of four changed reacting-Haide seeds reproduced
  the A/B cash pairs. In the +1,444-margin seed, our frontloaded sale at
  step 637/quote64 beat Haide's step639 sale; the incumbent waited until
  step643/quote32. In two margin regressions, the incumbent would have
  sold first at a higher quote (steps643/74 and 613/72), while the
  frontloaded rule sold at quotes66 and64. A similar visible price jump
  preceded both gain and regression. **Diagnose only; retain rejection of
  the simple quote rule.** Future rival sale actions are not available to
  the live policy; an opponent-timing forecast would need independent
  predictive and reactive validation. No main edit/upload. See
  `diagnostics/mirror_stock_frontload_20260927/HAIDE_TIMING_DIAGNOSIS.md`.

- **2026-09-26 19:20 UTC — public-history sale-race predictor lacks data.**
  A frozen observation-only extractor scanned all 100 current-submission
  live replays, keeping one half-base stock-sale opportunity per own stock
  batch. The 39 pre-used loss/close-win episodes supplied 45 opportunities
  with eight positive rival-before-own sale labels. The remaining 61
  episodes supplied only 25 opportunities and **five positives**, below the
  predeclared minimum 20 positive holdout examples. **Reject before model
  fitting or policy testing; no main edit/upload.** This narrow mirror
  problem is too sparse for a reliable fitted timing rule with these public
  observations. Redirect to the larger production gaps in the top-100 loss
  ledgers. See
  `diagnostics/mirror_stock_frontload_20260927/PREDICTOR_RESULTS.md` and
  `sale_race_dataset.json`.

- **2026-09-26 19:29 UTC — generic failed-worker-command repair rejected.**
  An exact native event census of all 34 lost refreshed top-100 routes and
  ten deterministic winning controls used original seeds, candidate seat 0,
  native shops and unchanged `main.py` hash `489fe8e4...`. All 44 games were
  `DONE`/`DONE` and reproduced both frozen terminal cash totals. Our 34 losses
  had 1,443 failed non-`PASS` commands out of 217,606 (0.663%), with no
  route reaching 100 failures (max 80); controls had 471/63,992 (0.736%).
  Both predeclared concern thresholds failed. **Reject a generic invalid-
  command repair; no main edit or Kaggle upload.** `PASS` turns are not
  proof of reachable funded work, and fixed rivals do not react. See
  `diagnostics/top100_refresh_2026-09-26_0708/WORKER_EFFICIENCY_PLAN.md`,
  `WORKER_EFFICIENCY_RESULTS.md`, and `worker_efficiency_44.json`.

- **2026-09-26 19:36 UTC — public V35 whole-policy replacement rejected.**
  The Apache-2.0 Kaggle V35 notebook yielded exact source hash
  `294e7e4d...` and reports public score 2692.9 on its own account. After a
  static top-level and embedded-code check, its unmodified `agent` faced
  current `main.py` on fresh native seeds 2615600–2615615 in both seats,
  original shops. All 32 games were `DONE`/`DONE`; V35 lost **all 16 paired
  seeds and all 32 seats**, mean margin −7,815.4 coins/game, aggregate
  −250,094. Its separate two-seat smoke seed also lost. **Reject wholesale
  replacement at the predeclared reactive gate; no top-100 conditional panel,
  local main edit or Kaggle upload.** Its published rating is not a prediction
  for our policy. See `diagnostics/public_ahmed_v35_20260927/PLAN.md`,
  `RESULTS.md`, `reactive_dev16.json`, and exact source.

- **2026-09-26 19:44 UTC — same-tile idle feed candidate rejected.**
  Corrected native Boey/mhw traces showed 50/34 distinct animal/day
  opportunities where our worker `PASS`ed with carried wheat on an unfed
  animal and the baseline never fed that tile later that day. All had zero
  prior consecutive unfed days; raw repeated `PASS` counts and immature crop
  `yield_units` were not interpreted as lost output. Isolated candidate
  `exp_pass_feed_20260927.py` hash `067f2854...` fed a cow/sheep on parent
  `PASS` during days 12–28 with worker wheat≥2. Original seeds, both seats,
  native shops: all four Boey/mhw smoke games `DONE`/`DONE`, 198 triggers,
  zero errors, own cash **−7,175**, rival −1,874, paired margin **−5,301**.
  **Reject at the predeclared positive-own-cash smoke gate; no extended fixed
  panel, reactive promotion, main edit or Kaggle upload.** See
  `diagnostics/top100_refresh_2026-09-26_0708/PASS_OPPORTUNITY_RESULTS.md`
  and `diagnostics/pass_feed_20260927/PLAN.md`, `RESULTS.md`, raw JSON.

- **2026-09-26 19:51 UTC — read-only top-20 refresh diagnoses two current
  leading losses.** Twenty newest completed public routes from the 19:46 UTC
  leaderboard snapshot had 20 distinct action hashes and 18 source episodes,
  with zero hash/episode overlap with the 07:08 top-100 panel. Unchanged
  `main.py` hash `489fe8e4...` won **18/20 paired routes and 36/40 seats**,
  all `DONE`/`DONE`, original seeds and shops. The losses were first-place
  Boey (−16,062/seat, Ice Cream/Bakery) and DECEM (−9,876/seat,
  Bakery/Pizza). Exact native seat-0 ledgers reproduced both cash pairs:
  Boey's main net deficits were wheat −8,990, egg −7,635, milk −4,830;
  DECEM's were egg −11,037, carrot −9,864, wheat −8,866. **Diagnose only;
  no main edit or Kaggle upload.** Fixed action routes are not reactive
  evidence. See `diagnostics/top20_refresh_2026-09-26_1946/RESULTS.md`,
  `main_20routes.json`, `two_loss_ledgers.json`, and saved traces.

- **2026-09-26 19:59 UTC — complete route remappings miss their frozen
  improvement gate.** Four separate full-source candidates changed only
  Ice Cream/Bakery route 105→110 or123, or Bakery/Pizza 107→110 or101,
  preserving complete existing funded tapes. New Boey/DECEM targets and all
  three known same-shop-pair 07:08 comparators ran original seeds, both
  seats and native shops; all 20 games `DONE`/`DONE`. Best target gains were
  Boey +1,558 margin/seat with **own cash −2,495** (route123), and DECEM
  +2,688 margin/seat with own +3,634 (route101). Bakery/Pizza route101 also
  improved RS Turley and Yizhou fixed routes, but it fell below the
  predeclared +5,000 target margin per seat. **Reject all four for
  promotion; no conditional reactive stage, main edit or Kaggle upload.**
  The positive route101 fixed deltas remain a development lead, not a live
  claim. See `diagnostics/route_portfolio_20260927/PLAN.md`, `RESULTS.md`,
  `fixed_screen.json`, `variants.json`.

- **2026-09-26 19:41 UTC — terminal tiles and execution-gap screen found no
  promotable module.** Three full native self-play traces (seeds 0–2, seat 0
  analyzed) had zero failed PLANT, every HIRE/BUY_LAND succeeded, and the
  last hand did 12–23 non-PASS commands on all 90 days. Exact day-end animal
  replay found seven clipped units in five events across three games; a
  pilot enabling the disabled seed-prefund switch on seed 0 changed neither
  terminal cash pair.
  Among all 29 original live losses, only two had any saleable terminal tile
  yield, one COW/milk unit each, with the rival also holding one. Separate
  full-policy two-seat native pilots on familiar seed 0 saw public V43 and
  v48 lose to current `main.py` by paired margins −16,012 and −89,581.
  These familiar-seed screens are mechanism checks, not strength estimates.
  **Reject terminal-cargo, generic no-op, trailing-hire, seed-prefund and
  wholesale public-policy promotion from this evidence; keep `main.py`
  unchanged and do not upload.** Focus future work on a complete funded
  production commitment evaluated with fresh reactive opponents. Evidence:
  `diagnostics/physical_gap_20260927/RESULTS.md` and raw traces/JSON.

- **2026-09-26 20:03 UTC — complete day-26 route-2 transition rejected.**
  An isolated candidate advanced all 22 executable step-648 route/forecast
  thresholds to step 624, keeping compressed tapes intact. The route-2 day-26
  schedule differs on every turn from the current specialized route; all
  compared routes match from day 27. On new native seeds 2617000–2617003,
  both seats against reacting current `main.py` with original shops, all
  eight games ended `DONE`/`DONE`. Candidate paired margins were −446,
  +1,148, −58 and +252; aggregate own cash rose 112 per game, but only
  **two of four** paired seeds improved, below the predeclared three-of-four
  gate. **Reject without extended testing, main edit or Kaggle upload.**
  See `diagnostics/late_route_transition_20260927/PLAN.md`, `RESULTS.md`,
  `reactive_dev4.json` and candidate SHA-256 `86e83251...`.

- **2026-09-26 20:06 UTC — multi-product rival sale-race predictor rejected.**
  A read-only extractor found 11,478 stock-batch sale opportunities in 100
  completed current-submission replays. The 61-episode holdout had 568
  positive rival-before-own sale events across 55 episodes, passing the
  predeclared sample-size gate. One frozen L2 logistic model fit on 39
  development episodes reached development AUC 0.799. Holdout AUC was
  **0.654**, below the required 0.70, although top-quartile precision 0.1516
  was 1.887 times the 0.0803 prevalence. **Reject the predictive module and
  do not tune on this holdout, build an action candidate, edit `main.py` or
  upload from this evidence.** The target also conditions on future own-sale
  timing that a deployed policy would need to forecast. See
  `diagnostics/multigood_sale_race_20260927/PLAN.md`, `RESULTS.md`,
  `opportunities.json` and `model_result.json`.

- **2026-09-26 20:10 UTC — compatible day-18 shop retarget rejected.**
  Seven EXP240 routes (105, 108, 120, 121, 122, 124, 125) have identical
  complete action tapes through step 431, allowing a state-compatible day-18
  switch when the two newest visible shops map to another route in that
  family. The isolated candidate compiled and ran against reacting unchanged
  `main.py` on fresh native seeds 2617300–2617315, both seats, original
  shops: all 32 games `DONE`/`DONE`, zero router errors. Nine seeds entered
  the compatible family, but only **one** actually switched; that seed lost
  177 own cash per seat (paired margin −354), and the other 15 paired margins
  were zero. **Reject at the predeclared four-activation gate; no main edit
  or Kaggle upload.** See `diagnostics/day18_shop_retarget_20260927/PLAN.md`,
  `RESULTS.md`, `reactive_dev16.json` and candidate SHA-256 `3a4ceb6a...`.

- **2026-09-26 20:13 UTC — Bakery/Pizza complete route-101 reactive gate
  rejected.** An outcome-blind native scan selected the first six exact
  Bakery/Pizza openings among 299 sequential new seeds. Frozen candidate
  `exp_route_bakpizza_101_20260927.py` changed the visible day-6 route 107
  to existing fully funded route 101. Control and candidate faced reacting
  unchanged `main.py` on each seed in both seats with original shops; all 24
  games ended `DONE`/`DONE`. Across the 12 seat comparisons, candidate own
  cash rose **36,718**, but rival cash rose **52,104**, so paired margin fell
  **15,386**. Only **3/6** seed pairs improved margin and the worst regressed
  **16,862**, failing the frozen 4/6, positive-total-margin and −5,000-floor
  gates. **Reject without confirmation block, main edit or Kaggle upload.**
  The earlier fixed-route own gain did not generalize to margin against a
  reacting opponent. See `diagnostics/bakpizza_reactive_20260927/PLAN.md`,
  `RESULTS.md`, `seed_selection.json` and `reactive_dev6.json`.

- **2026-09-26 20:21 UTC — Pizza/Bakery route-library search rejected.**
  Three distinct top-100 fixed-action routes with this first-two-shop pair
  were all paired losses. Thirty-nine day-six-prefix-compatible alternate
  complete route IDs were each screened in seat 0 on all three original
  seed/shop cases; all 117 games ended `DONE`/`DONE`. The predeclared
  maximum-minimum selector chose route 124, the only alternative that
  improved margin on all three, but its total margin gain was just **939**
  against a required **15,000**, and its own-cash delta was **−135**, with
  one case negative. **Reject the library switch without both-seat or
  reactive escalation, main edit or Kaggle upload.** The incumbent route
  library appears inadequate for this loss cluster; fixed tapes remain
  diagnostic only. See
  `diagnostics/pizzabakery_route_search_20260927/PLAN.md`, `RESULTS.md`,
  `variants.json` and `fixed_screen.json`.

- **2026-09-26 20:39 UTC — public physical-state milk-sale pilot rejected;
  model interpretation superseded by 20:48 correction below.**
  A revised observation-only sale-race model added visible rival harvest
  readiness and worker geometry. It trained on 100 existing public episodes
  and passed a **17 later-episode** temporal holdout: 2,051 opportunities,
  137 positives across 16 episodes, AUC **0.835**, top-quartile precision
  **2.889×** the 0.0668 prevalence. The single-file candidate embedded its
  frozen coefficients and advanced at most eight milk units only with
  high risk, public ready milk, a same-day own planned sale and modeled
  receipt drop. Five-episode feature parity and both-seat Kaggle file-path
  parity passed. On fresh seeds 2623000–2623015, control and candidate
  versus reacting `main.py` in both seats yielded all 64 games `DONE/DONE`,
  zero branch errors, but only **3/16** paired seeds activated, below the
  frozen four-seed minimum. Six sales/32 units improved paired margin by
  only **194** total (own +80, rival −114). **Reject action promotion as too
  sparse for the top-10 goal; the predictor evidence was later withdrawn
  after the replay-index correction below. No main edit or Kaggle upload.** See
  `diagnostics/physical_sale_predictor_20260927/PLAN.md`, `RESULTS.md`,
  `model_result.json`, `file_parity_seed0.json`, `reactive_dev16.json`.

- **2026-09-26 20:48 UTC — replay-index correction and corrected milk pilot
  rejected.** Kaggle replay frame `t` pairs observation `t` with the action
  from turn `t-1`; the original extractor accidentally used that action for
  the current decision. Thus the 20:39 model counts/AUC and offline/deployed
  feature-parity claim were invalid as deployment evidence, although its
  exact native terminal-cash result remains real. Corrected observation `t`
  plus action frame `t+1` yields 5,997 development opportunities/708
  positives, 1,108 later-holdout opportunities/112 positives, holdout AUC
  **0.844** and top-quartile lift **2.964**; the **same 17-game holdout** was
  reused and provides no second independent confirmation. Corrected
  five-episode feature parity and both-seat Kaggle file-loader parity
  passed. An isolated corrected candidate on fresh native seeds
  2624000–2624015 against reacting unchanged `main.py`, both seats and
  original shops, ended all 64 games DONE/DONE, zero branch errors, but
  **0/16 seed pairs activated**. **Reject model/action promotion; no main
  edit or Kaggle upload.** See
  `diagnostics/physical_sale_predictor_20260927/RESULTS.md`,
  `model_result_corrected.json`, and `reactive_corrected_dev16.json`.

- **2026-09-26 20:53 UTC — exact cash diagnosis of 17 later public games.**
  All 17 frozen rival routes reproduced both live terminal cash totals
  exactly with unchanged `main.py` and original seed/seat, all DONE/DONE.
  Seven were wins and ten losses (loss margin sum **−30,651**); six losses
  were ahead on day 19. Loss aggregate net item deficits were MILK
  **−13,800**, CARROT **−13,293**, and WOOL **−10,117**. The Takahiro
  Someya loss (−7,097) was almost entirely a WOOL timing/price gap:
  each agent sold 367 units, yet ours received 48,313 vs 55,322 coins;
  days 21 and 27 alone had −4,497 receipt gap at equal daily unit totals.
  The rival's wool carriers placed and sold 24 units at turns 666–667;
  ours stayed at the sheep tiles for care/harvest/fertilizer work, then
  placed and sold later into quotes as low as 1. At turn 666 ours carried
  41 wool but had zero in the shed, so an extra market SELL alone could
  not have captured that early price. **Diagnostic only; no policy
  promotion, main edit or upload.** A carrier-delivery schedule candidate
  would need fresh reacting opponents in both seats. See
  `diagnostics/new_live17_diagnosis_20260927/RESULTS.md` and exact JSON.

- **2026-09-26 21:09 UTC — late wool-carrier delivery interrupt rejected.**
  An isolated wrapper advanced a loaded sheep worker's harvest, shed trip,
  placement and wool sale, holding the worker until its original parent
  delivery command. A first raw-route lookahead was corrected before fresh
  testing because the raw tape omitted two later-controller hands. The
  corrected rule passed both-seat Kaggle file-loader parity. On the saved
  Takahiro route it improved paired margin 5,769, but that fixed rival
  cannot validate the policy. Fresh native seeds 2625000–2625015 versus
  reacting unchanged `main.py`, both seats and original shops, all 64 games
  DONE/DONE with zero errors. Only **1/16 paired seeds activated**; its
  own cash rose 960, rival cash fell 944 and paired margin rose 1,904.
  The other 15 pairs were unchanged. **Reject at the frozen four-activation
  gate; no top-100 escalation, main edit or Kaggle upload.** See
  `diagnostics/wool_delivery_interrupt_20260927/RESULTS.md`,
  `reactive_fresh16.json`; candidate SHA-256 `33b63056...`.

- **2026-09-26 21:19 UTC — complete double-Yarn route-library remapping
  rejected.** An isolated runtime map tested all 40 complete route tapes
  with the incumbent's first-144-turn prefix against three major saved
  double-Yarn losses plus the same-shop dodsters control, original seeds
  and seat 0: all 160 games DONE/DONE, with exact incumbent cash parity.
  No route improved paired margin on all three losses. Route 126 was the
  only alternative that increased own cash on all three (+6,142/+1,679/
  +4,956), but its paired margin changed +5,312/−2,512/+2,576, and none
  of the losses flipped. **Reject all remappings at the frozen development
  gate; no both-seat or reactive escalation, main edit or Kaggle upload.**
  Fixed rival tapes remain diagnostic only. The route library cannot
  supply the broadly improved funded schedule needed for these losses.
  See `diagnostics/double_yarn_route_library_20260927/RESULTS.md` and
  `fixed_screen.json`.

- **2026-09-26 21:32 UTC — recorded public route general replacement
  rejected, double-Yarn specialist remains unconfirmed.** An outcome-blind
  scan selected the first eight new double-Yarn seeds after 704 seed-only
  shop checks; the 512→1,024 scan-budget extension preceded all treatment
  outcomes. Three complete public rival action tapes faced reacting local
  `main.py`, both seats and native shops. ShunkiKyoya's route passed the
  frozen development gate: 8/8 positive paired seeds, 16/16 seats, own
  cash +282,072 and paired margin +369,941; the other two tapes failed.
  Its exact 719 actions were packaged as a 14 KB single-file candidate
  (source action SHA-256 `a72f6711...`, candidate `39d39bfd...`) with
  raw-route and both-seat Kaggle file-loader parity. On untouched
  arbitrary-shop seeds 2629000–2629015, all 64 control/treatment games
  DONE/DONE with same first-two shops within each comparison, but it
  improved only **5/16 paired seeds and 10/32 seats**, own cash
  **−294,178**, rival cash **+381,348**, margin **−675,526**, worst
  paired regression **−105,092**. **Reject general replacement; no main
  edit or Kaggle upload.** A double-Yarn specialist would need an
  independent double-Yarn block and a state-compatible opening selector;
  investigate same-opponent public route variants rather than cherry-pick
  this tape. See
  `diagnostics/public_route_native_screen_20260927/RESULTS.md`,
  `reactive_screen.json`, and `reactive_confirm16.json`.

- **2026-09-26 21:45 UTC — exact Shunki route portfolio feasibility
  rejected.** All 203 completed public episodes for submission 56553856
  yielded verified 719-action route artifacts, covering all eight first
  shops and 61/64 shop pairs. All first 72 actions match, but four
  first-shop groups diverge before turn 144 and 45 same-pair groups have
  multiple full action hashes. Same-pair turn-79 wheat trades differ by
  visible price/money (16 versus 15 units); same-pair turn-132 farmer
  DIG versus PASS corresponds to a visible weed under the farmer.
  **Reject exact shop-key route assembly under the frozen feasibility
  plan; no `main.py` edit or Kaggle upload.** A separate coarse lookup
  probe needs fresh reacting tests. See
  `diagnostics/shunki_portfolio_20260927/RESULTS.md`, `route_manifest.json`,
  `component_analysis.json`.

- **2026-09-26 21:51 UTC — coarse Shunki shop lookup rejected at frozen
  development gate, despite broad gains.** A 61-route single-file lookup
  passed both-seat Kaggle file-loader parity. On untouched native seeds
  2630000–2630015 versus reacting `main.py`, all 64 games DONE/DONE,
  14/16 positive paired seeds, 28/32 positive seats, own cash +361,264,
  and paired margin +263,664. Yet PET_CAFE/ICE_CREAM_SHOP seed 2630001
  regressed 17,906 paired margin, breaching the predeclared −10,000 floor.
  **Reject exact coarse artifact; no main edit, top-100 escalation, or
  Kaggle upload.** An untouched 32-seed descriptive robustness block is
  planned separately without changing candidate bytes. See
  `diagnostics/shunki_shop_lookup_20260927/RESULTS.md`,
  `ROBUSTNESS_PLAN.md`, and `reactive_dev16.json`.

- **2026-09-26 21:57 UTC — frozen coarse lookup robustness check exposed
  later-shop tail risk.** Candidate bytes unchanged; fresh seeds
  2630100–2630131 versus reacting main, both seats, all 128 games
  DONE/DONE. Margin improved on 29/32 seed pairs, aggregate +389,962,
  but ICE_CREAM_SHOP/BRUNCH_SPOT seed 2630130 regressed −191,290 paired
  margin. Its third shop was YARN_STORE; the chosen source route's third
  shop was FARMERS_MARKET, and same-pair public routes diverge near that
  turn. First-two shops matched only 62/64 seat comparisons because one
  other seed's second shop changed under treatment. **Keep exact
  two-shop candidate rejected; no `main.py` edit or Kaggle upload.**
  Explore later-shop routing as a separate experiment. See
  `diagnostics/shunki_shop_lookup_20260927/RESULTS.md` and
  `reactive_robust32.json`.

- **2026-09-26 22:02 UTC — later-shop public route compatibility audit
  supports an isolated candidate.** All 203 source replay hashes and seats
  were reverified while extracting visible shop sequences. There are 164
  distinct three-shop prefixes; 127 have an exact first-216-action match
  to the current two-shop route, giving 66 possible compatible switches.
  The ICE_CREAM_SHOP/BRUNCH_SPOT/YARN_STORE failure case can switch from
  source episode 113445495 to 113347600 at turn 216. **Proceed to a
  separately tested candidate only; no `main.py` edit or Kaggle upload.**
  See `diagnostics/shunki_portfolio_20260927/THIRD_SHOP_RESULTS.md`,
  `shop_sequences.json`, and `later_shop_analysis.json`.

- **2026-09-26 22:09 UTC — exact-compatible later-shop candidate rejected
  at fresh development gate.** A 145-route single-file selector passed
  both-seat Kaggle file-loader parity. On the previously examined
  ICE_CREAM_SHOP/BRUNCH_SPOT/YARN_STORE failure, it reduced one-seat
  margin loss from −95,645 to −577, but this is only a mechanism check.
  On untouched native seeds 2630200–2630215 versus reacting main, both
  seats, all 64 games DONE/DONE; 13/16 paired seeds improved and aggregate
  margin rose 276,773. BRUNCH_SPOT/PIZZA_SHOP seed 2630211 regressed
  −15,838 paired margin, breaching the predeclared −10,000 floor.
  **Reject exact artifact; no main edit, top-100 escalation, or Kaggle
  upload.** See `diagnostics/shunki_later_lookup_20260927/RESULTS.md`,
  `reactive_dev16.json`.

- **2026-09-26 22:12 UTC — negative-tail cash ledger did not support a
  local action patch.** Seed 2630211 exact native trace reproduced
  main self-play 96,306/96,306 and later-shop candidate versus main
  104,535/112,454. Candidate own cash rose 8,229 but reacting rival
  cash rose 16,148; rival relative net MILK +9,371 and STRAWBERRY +7,289
  were partly offset by TOMATO −9,027. Candidate had no failed market
  orders. **Diagnostic only; no main edit or Kaggle upload.** See
  `diagnostics/shunki_later_lookup_20260927/loss_2630211_ledger.json`.

- **2026-09-26 22:26 UTC — full saved top-100 route diagnostic: candidate
  improved 66→80 wins but missed all-100 target.** Unchanged later-shop
  candidate SHA-256 `68aad090...` and incumbent played the exact same
  100-team panel in both seats, all 400 games DONE/DONE. Candidate won
  80/100 paired routes and 160/200 seats, versus incumbent 66/100 and
  132/200. It flipped 27 incumbent losses to wins but 13 incumbent wins
  to losses; total paired margin improved 1,843,902. First-two shops
  matched in only 134/200 seat comparisons due native action-dependent
  RNG. Four of the five largest losses opened ICE_CREAM_SHOP/BRUNCH_SPOT;
  the incumbent won all four. Exact day-nine captures show third shops
  FARMERS_MARKET, BRUNCH_SPOT, PET_CAFE, SMOOTHIE_SHOP, all using source
  113445495 at that point. **Retain candidate rejection; no main edit
  or Kaggle upload.** Fixed tapes are diagnostic, not independent policy
  validation. See `diagnostics/shunki_later_lookup_20260927/TOP100_DIAGNOSTIC_RESULTS.md`
  and `top100_analysis.json`.

- **2026-09-26 22:31 UTC — exact Shunki imitation has a production
  ceiling on major loss cases.** Cash ledgers for two ICE/BRUNCH losses
  show candidate own late MILK/STRAWBERRY deficits versus incumbent on
  Dipam and large WOOL deficits on mtmr_s1. In the Dipam case, the
  candidate emitted all 719 actions of selected public source episode
  113445495 exactly; crop/animal tile counts matched at nine sampled
  checkpoints. Candidate earned 62,963 versus incumbent 134,683 on
  the same saved opponent route. **Stop exact Shunki route imitation as
  the primary path to top ten or all 100 wins; no main edit or upload.**
  Improve the incumbent's adaptive production/market schedule instead.
  See `diagnostics/shunki_later_lookup_20260927/TOP100_DIAGNOSTIC_RESULTS.md`,
  `ice_brunch_cash_ledgers.json`, and
  `ice_brunch_source_state_comparison.json`.

- **2026-09-26 22:30 UTC — Shunki visible-worker repair rejected.** A new
  self-contained candidate `exp_shunki_visible_repair_20260927.py` (SHA-256
  `1f221922...`) retained the exact 145-route later-shop selector and added
  observed PASS-on-weed DIG plus safe next-PASS replay for work blocked by
  weeds. It compiled; Kaggle file-path selection and terminal cash matched
  direct calls in both seats. A controlled weed observation triggered DIG.
  On fresh native seeds 2630400–2630415, three arms (main control, original
  Shunki selector and repaired selector) faced reacting unchanged `main.py`
  in both seats with original shops: all 96 games DONE/DONE, first-two shops
  matched in all 32 candidate/main comparisons, zero repair errors, but
  **zero repair activations**. Candidate cash exactly equaled the original
  selector in all 32 games. It improved 15/16 paired seeds versus main and
  +169,030 paired margin overall, yet seed 2630408 regressed −171,270;
  ICE_CREAM_SHOP/BRUNCH_SPOT/BAKERY had no recorded three-shop route.
  **Reject at the predeclared activation and tail-risk gates; no main edit
  or Kaggle upload.** See
  `diagnostics/shunki_visible_repair_20260927/PLAN.md`, `RESULTS.md`,
  `reactive_dev16.json`, and `candidate_parity.json`.

- **2026-09-26 22:54 UTC — ICE/BRUNCH complete-schedule repair passes its
  saved-route development gate.** New candidate
  `exp_shunki_ice_schedule_20260927.py`, SHA-256 `3cc0f69f...`, replaces
  seven references to source episode 113445495 with 113383763. The two
  routes share their first 241 actions exactly; all nine affected route-map
  transitions pass exact-prefix checks. Four unrelated earlier prefix
  mismatches remain recorded. The old source bought 112 wheat seeds after
  turn 216 but scheduled only 54 plantings, versus 112 in the replacement;
  strawberry plantings were 2 versus 10 from the same ten-seed purchase
  plan. All five saved ICE/BRUNCH routes ran both seats, DONE/DONE: four
  losses became wins and the existing win was unchanged. **Advance this
  isolated candidate to prospective native reactive confirmation; no main
  edit or upload yet.** Outcome-blind seed selection and the clarified
  pre-confirmation win-rate gate are recorded in
  `diagnostics/shunki_ice_schedule_20260927/PLAN.md`; development evidence
  is `development.json`. These familiar routes are development data, not
  independent validation. The unchanged earlier candidate's separate
  512-game win-rate review is still running.

- **2026-09-26 23:05 UTC — fresh win-rate reassessment passes.** Unchanged
  later-shop candidate `68aad090...` won 248/256 fresh native seat games
  against current main, previous main, public V35 and public C95, versus
  incumbent 175 wins / 76 draws / 5 losses on the same 256-game panel.
  Candidate W/L was 62/2, 62/2, 64/0 and 60/4 respectively. All 512 games
  DONE/DONE; maximum candidate call 463.2 ms. Pooled win-score improvement
  +13.67 percentage points, paired whole-seed bootstrap 95% interval
  +9.38 to +17.58 points. **Candidate earns promotion consideration under
  the prospectively changed win-rate objective**, while previous cash-tail
  rejection findings remain intact. This does not validate changed
  `3cc0f69f...` bytes, whose separate confirmation is still running. No
  main edit or upload. See `diagnostics/winrate_review_20260927/RESULTS.md`.

- **2026-09-26 23:08 UTC — repaired ICE/BRUNCH schedule passes independent
  native confirmation and both-seat file loading.** Outcome-blind scans
  found eight fresh target openings in 160 sequential seeds. Candidate
  `3cc0f69f...` won all 16 seats against current main and all 16 against
  previous main; original `68aad090...` won 6/16 against each. All 80 games
  including controls DONE/DONE, five/eight current-main pairs exposed the
  change, first three shops identical in all 16 old/new paired comparisons.
  The Kaggle file loader selected the unique final entrypoint and exactly
  matched direct-call cash in both seats. **Pass branch confirmation; await
  full fresh top-50 comparison before promotion.** All 50 requested source
  replays have downloaded (50 distinct action hashes, 43 public episodes,
  no errors). No main edit or upload. See
  `diagnostics/shunki_ice_schedule_20260927/RESULTS.md` and
  `diagnostics/top50_refresh_20260927_2303/download_result.json`.

- **2026-09-26 22:56 UTC — current top-50 public-route comparison favors
  the visible-worker candidate descriptively, but it remains rejected.**
  Froze Kaggle leaderboard ranks 1–50 at 22:35 UTC. For each team, selected
  the recent submission closest to that leaderboard score (the displayed
  submission date can point to a newer, lower-scoring upload), and extracted
  one completed public action history. The 50 histories have distinct
  action hashes. Current `main.py` SHA-256 `489fe8e4...` and separate
  `exp_shunki_visible_repair_20260927.py` SHA-256 `1f221922...` each faced
  every fixed route on its original seed in both seats: all 200 games
  DONE/DONE. Main won 40/50 two-seat route margins; candidate won 42/50,
  flipping six losses to wins and four wins to losses. Total paired margin
  changed +513,474 coins; own cash +675,602, rival cash +162,128. Main
  first-two shops matched candidate in 65/100 seat comparisons. Four main
  wins became candidate losses, including Anton Tikhonov (margin change
  -211,794) and Victor @ Tufa Labs (-83,476). The candidate recorded 11
  idle-weed DIG repairs and zero repair errors; without a same-route
  ablation, the gain cannot be attributed to the repair. **No promotion or Kaggle
  upload.** Fixed replay actions cannot react to a changed policy, and the
  candidate had zero repair activations plus a severe fresh native reactive
  regression in its predeclared gate. See
  `diagnostics/top50_live_compare_20260927/COMPARISON.md`,
  `comparison.csv`, both 100-game JSON panels, and the frozen routes.

- **2026-09-26 23:29 UTC — fresh requested top-50 panel completed.** All 50
  source routes downloaded with distinct action hashes. Both policies completed
  100 games DONE/DONE. Repaired candidate `3cc0f69f...` won 84/100 seats and
  42/50 both-seat matchups; current main won 64/100 seats and 31/50 sweeps.
  Fifteen losses became sweeps, four old sweeps became losses. **Regression
  comparison passes, but all-50 target remains incomplete; no promotion or
  upload yet.** See `diagnostics/top50_refresh_20260927_2303/RESULTS.md`.

- **2026-09-26 23:29 UTC — downstream wheat-purchase v0 stopped.**
  `f21e0cfd...` improved DECEM margin by 3,718 in both seats but still lost
  by 78,474, with six extra wheat units across three turns. Stock projection
  had incorrect shed geometry. Native tracing then identified the upstream
  problem: attempted wheat harvests on locked southern land. HIRE creates
  empty inventories regardless of extra arguments. **Reject v0; investigate
  failed expansion before another supply patch.** See
  `diagnostics/shunki_feed_supply_20260927/RESULTS.md`.

- **2026-09-26 23:35 UTC — funded land retry fixes execution, not yet wins.**
  `5002b442...` retries a 2,000-coin southwest purchase that failed at turn
  217 with 1,936 coins. DECEM margin improves -82,192 to -3,104 in both
  seats and later feed failures disappear. Full 50-team comparison remains
  42/50 sweeps and 84/100 seat wins, all DONE/DONE, no win flips. **Fails
  strict sweep-improvement gate; do not promote this artifact alone.**
  Retain as a causal component for a separately frozen candidate. Five
  remaining losses had no audited physical failures, and terminal stock
  is already largely sold. See `diagnostics/shunki_land_retry_20260927/RESULTS.md`.

- **2026-09-26 23:38 UTC — four-turn early-sale package rejected.**
  `d25562cd...` completed all 16 seats against the remaining eight losses
  but won none; marwar22 worsened -114 to -2,270. **Reject at development
  gate; no full-panel or reactive escalation.** See
  `diagnostics/shunki_sale_advance_20260927/RESULTS.md`.

- **2026-09-26 23:40 UTC — four-turn early-sale transplant rejected.**
  Candidate `d25562cd...` ran both seats of all eight known replay losses,
  sixteen games DONE/DONE; none became a win. Three margins improved
  slightly and five worsened; marwar22 fell from -114 to -2,270 per seat.
  **Fail development gate; no promotion or upload.** The user explicitly
  requested farming methods, timings and logic experiments next. See
  `diagnostics/shunki_sale_advance_20260927/RESULTS.md`.

- **2026-09-26 23:45 UTC — user-requested farming variants screened.**
  Fertilizer-before-water `e46194f0...` had zero eligible swaps in sixteen
  known-loss games and identical cash: **stop at activation gate**. Coherent
  carrot-to-wheat crop-chain substitution `72ba0715...` activated throughout
  and flipped marwar22 from -114 to +3,818 per seat, while worsening margins
  in the other seven matchups. All 32 games DONE/DONE. **Advance only the
  crop variant to the frozen full-50 regression gate; no promotion yet.**
  See `diagnostics/shunki_farming_methods_20260927/development_decisions.json`.

- **2026-09-26 23:46 UTC — promoted candidate uploaded and remote parity verified.**
  Exact `3cc0f69f...` main is submission **56591314**, COMPLETE / initial
  600.0. Remote validation 113900996 and local file-loader seed-0 self-play
  both finish 104,125/104,125, DONE/DONE, first actions identical. Root old
  and uploaded backups are preserved. The one renewed upload authorization
  is consumed, and CLI reported zero remaining uploads today. A separately
  visible intervening submission 56590642 is also active; use live status
  rather than the old 22:45 snapshot. **Promotion executed; goal still
  active, with 42/50 sweeps and no live top-10 claim.** See
  `diagnostics/shunki_promotion_20260927/UPLOAD.md` and the reviewable
  `diagnostics/top50_refresh_20260927_2303/SCORECARD.md`.

- **2026-09-26 23:46 UTC — relaxed-prefix audit is diagnostic only.**
  Four old prefix mismatches are one-unit differences in same-turn wheat
  buy/sell round trips, with identical worker actions. Ignoring only
  adjacent quantity-balanced buy/sell pairs exposes 50 possible later route
  transitions (20 at the third shop). None activates on the eight remaining
  top-50 loss histories. Market cash can still differ, so this is not a
  proof of full state compatibility. **Do not implement or promote from
  this audit alone.** Evidence: `diagnostics/shunki_promotion_20260927/wash_prefix_audit.json`.

- **2026-09-26 23:50 UTC — full farming crop-chain comparison rejected.**
  `72ba0715...` completed all 100 fresh top-50 seat games DONE/DONE, with
  84 wins and 42/50 sweeps. It gained marwar22 but lost Kaggledew Valley;
  **fails strict net-win gate, no promotion**. First-investment price audit
  shows wheat/carrot quotes 22/53 in Snorlax and 38/47 in We wanna be tomatos,
  explaining why seed savings alone are insufficient. Timing variant had
  zero eligible swaps. See `diagnostics/shunki_farming_methods_20260927/RESULTS.md`.

- **2026-09-26 23:54 UTC — farming fork completed its comparisons.**
  Preserved both root experimental scripts and the complete crop 100-game
  comparison. Neither farming variant earned promotion. Concurrent primary
  task promotion of `3cc0f69f...` to main/submission 56591314 was detected
  by hash and confirmed against its upload and remote-parity receipts;
  no additional upload was attempted here. Future use of the rejected
  variants' confirmation recipe must use frozen `489fe8e4...`, not the
  changed main path. See `diagnostics/shunki_farming_methods_20260927/RESULTS.md`.

- **2026-09-26 23:54 UTC — refreshed public source schedules collected.**
  All eleven newly completed public episodes of source submission 56553856
  were downloaded without outcome selection. Sixteen new exact-prefix
  compatible lookup keys were identified; no policy change was built or
  validated from them. **Research data only; no promotion.** Raw replays,
  compressed actions, hashes and prefix audit are preserved under
  `diagnostics/shunki_refresh_farming_20260927/manifest.json`.

- **2026-09-26 23:53 UTC — late fertilizer cut rejected before implementation.**
  Native marwar22 ledger spends only 54 coins on seven final-day fertilizer
  units, and the observed fertilizer commands target age-two/three carrots
  before their final watering and harvest. These are productive inputs;
  removing them would not be justified by the -114 margin. **No candidate
  change.** Evidence: `diagnostics/shunki_promotion_20260927/last_day_fertilizer_audit.json`.

- **2026-09-26 23:53 UTC — budget-model correction required for future land-retry derivatives.**
  Engine `_fib(0)=1` and `_fib(1)=1`; the unpromoted `5002b442...` helper
  starts with 0,1 and undercounts labor cost. The configuration key is
  `farmHandCostMult`, not `farmHandCostMultiplier`. Its successful DECEM
  retry is measured evidence, but the 500-coin reserve does not make the
  forecast formula exact. **Preserve frozen experiments; correct these
  formulas in a separately hashed future candidate before promoting any
  land-retry derivative.** Current submitted 3cc has no such helper.

- **2026-09-26 23:53 UTC — weed preparation experiment started separately.**
  New `e8583cee...` on submitted 3cc replaces a no-op on a visible weed
  with DIG only when the next same-day command plants/builds there. This
  covers HARVEST-before-PLANT as well as PASS-before-PLANT, unlike the
  older visible-repair experiment. Frozen development and independent
  gates: `diagnostics/shunki_preplant_weed_20260927/PLAN.md`. Main unchanged.

- **2026-09-26 23:56 UTC — pre-plant weed repair fails its win gate.**
  `e8583cee...` completed sixteen known-loss games, DONE/DONE, zero errors.
  One actual repair improved ymg_aq seat 0 by 816 to -4,222; all other
  outcomes remained unchanged. **Reject for promotion; no full-panel or
  native escalation.** See `diagnostics/shunki_preplant_weed_20260927/RESULTS.md`.

- **2026-09-26 23:56 UTC — late policy switching lacks a shared physical opening.**
  A direct native seed-0 trace of submitted 3cc versus old 489 main found
  physical/unit mismatch throughout the first 217 turns. Hiring and animals
  already diverge at the first two turns. **Do not splice these policies
  after a shop reveal based only on replay win counts.** Evidence:
  `diagnostics/shunki_expert_switch_20260927/opening_compatibility_seed0.json`.

- **2026-09-27 00:01 UTC — scheduled-sale land prefunding is not enough.**
  `25ad35be...` advances one fertilizer unit already earmarked for sale,
  funding the original turn-217 land purchase without waiting for a retry.
  DECEM finishes 145,082 versus 147,976 in both seats (-2,894), DONE/DONE.
  **Fails required both-seat-win gate; no promotion or native escalation.**
  See `diagnostics/shunki_land_prefund_20260927/RESULTS.md`.

- **2026-09-27 00:06 UTC — broader complete-schedule search frozen.**
  The remaining eight losses occupy six two-shop histories. PIZZA/ICE has
  no original two-shop map entry and uses a first-shop fallback. A new
  evaluator `eefbb176...` considers 17–30 source schedules per affected
  history, each preserving the first 144 actions after removing only
  adjacent inventory-neutral product buy/sell round trips. 220 one-seat
  development games include every top-50 case in those histories. The
  selected table will depend only on the first two observed shops, then
  face full both-seat regression and prospective independent native
  confirmation. **Search only; no main edit or upload.** Plan and frozen
  source hashes: `diagnostics/shunki_route_search_20260927/PLAN.md`,
  `search_manifest.json`.

- **2026-09-27 00:26 UTC — complete schedule selector passes replay regression.**
  All 220 development games finished DONE/DONE. Frozen shop-only candidate
  `94f0602f...` changes four observed two-shop branches, with the original
  144-turn opening preserved. It then wins **45/50 matchups in both seats,
  91/100 seat games**, versus submitted 3cc at 42/50 and 84/100. DECEM,
  Snorlax and marwar22 become sweeps; no prior sweep is lost. ymg_aq remains
  split (+1,190/-1,167), so the positive total margin is not a both-seat win.
  **Advance to independent native confirmation only; no promotion.** The
  source filtering's neutral-inventory trade differences do not establish
  cash equivalence. Separate outcome-blind first-144-turn panels per rival
  were specified before scans at 00:23 UTC, then the exact candidate and
  all inputs were frozen in `diagnostics/shunki_route_search_20260927/native/manifest.json`.
  448 reactive games are planned; see that directory's PLAN.md and RESULTS.md.

- **2026-09-27 00:26 UTC — current leader opening diversity audited.**
  Twelve latest completed public DSM episodes from submission 56582621
  were downloaded without outcome selection. They contain six distinct
  physical openings by turn 72 and twelve by turn 144. **Research only;
  do not blindly concatenate these adaptive action tapes.** Sources and
  hashes: `diagnostics/dsm_opening_audit_20260927/audit.json`.

- **2026-09-27 00:39 UTC — coherent dairy conversion rejected.**
  `d5663505...` replaces five future geese with cows on the observed
  PIZZA/ICE branch, including animal orders, structures, PICKUP/PLACE,
  three explicit product drops, and egg-to-milk sales. All six games DONE
  with changes active. Breaking1800 improves from -12,594 to -3,288 in
  both seats, but ymg_aq worsens from +1,190/-1,167 to -12,441/-19,857.
  Arda stays a win, so sweeps remain 1/3 and one prior seat win is lost.
  **Reject; no full-panel/native escalation or promotion.** Milk's higher
  visible price is insufficient evidence of a profitable whole investment.
  `diagnostics/shunki_dairy_conversion_20260927/RESULTS.md` preserves the
  exact implementation and results; 94f confirmation continues unchanged.

- **2026-09-27 00:57 UTC — public-movement sale timing rejected.**
  Passive eight-turn worker-history matching predicted the saved opponents'
  sales correctly and found 5–24 timing opportunities per loss trace. This
  is replay-trained evidence, not independent validation. Candidate
  `ad5902a9...` encodes 8,791 consensus-sale keys, uses no identity/seed,
  and advances held, planned cash goods only when predicted rival sales
  exceed observed town consumption before the scheduled sale. All ten
  known-loss games DONE, all sale debts settled, 3–14 active turns each.
  Every margin rises by 211–379 coins, but no new both-seat win is earned.
  **Reject; no escalation or promotion.** See
  `diagnostics/shunki_sale_model_20260927/RESULTS.md`. The unchanged 94f
  native protocol is still running. Main remains 3cc.

- **2026-09-27 00:57 UTC — six passive loss ledgers completed.**
  The 94f top-50 loss traces all reproduce their benchmark rewards exactly.
  Breaking1800 and seek inspiration have no failed own market purchases or
  failed productive worker commands, so their deficits are not generic
  execution crashes. Majkel's missing cow purchase at 171 lacks 51 coins;
  the next turn's planned sales create enough purchase cash, but funding
  later feed remains a separate constraint. No retry was implemented from
  that observation alone. Evidence:
  `diagnostics/shunki_shop_optimized_losses_20260927/ledger.json` and raw
  event traces. **Diagnostics only; no promotion.**

- **2026-09-27 01:01 UTC — dairy failure traced through cash and shared shops.**
  In ymg_aq seat 1, `d5663505...` raises own cash by 12,331 but rival cash
  by 31,021, losing 18,690 relative margin. Extra animal spending causes
  unfunded wheat buys from turn 152, missed seeds, then numerous failed
  productive actions; the third/fourth native shops change PET/BRUNCH to
  BRUNCH/ICE. **Rejection stands.** Do not attribute this solely to final
  milk prices or assume unchanged town RNG after an investment change.
  `diagnostics/shunki_dairy_conversion_20260927/causal_summary.json`.

- **2026-09-27 01:01 UTC — root backups preserved before qualification.**
  `main_before_shop_optimized_20260927_3cc0f69f.py` equals current main;
  `main_candidate_shop_optimized_20260927_94f0602f.py` equals the frozen
  45/50 selector. No main edit or additional upload. Outcome-blind native
  selection completed after 672/896/800/992 prefix scans for old489,
  old08aa, public C95 and submitted3cc respectively. Each panel has eight
  seeds per changed branch. Full native games are running.

- **2026-09-27 01:05 UTC — later compatible switching audit completed.**
  The BAKERY/PET candidate uses source 113474010 from BAKERY/SMOOTHIE,
  but none of the other four schedules in that source family matches its
  executed 144–215 prefix. They differ in seed/animal purchases and worker
  commands from 171/172, not merely balanced trade quantities. **Do not
  splice them after the third shop without a new state-reconciliation
  controller.** Other selected families have one or two compatible tapes,
  but compatibility alone is not evidence of a win. No candidate change.
  `diagnostics/shunki_route_search_20260927/late_compatibility_audit.json`.

- **2026-09-27 01:09 UTC — 45/50 selector rejected by independent games.**
  `94f0602f...` completed 352 of the planned 448 native games, all DONE.
  The parent wins 182/192 external seat games; the candidate had 144 points
  in 160 external games, so its best possible final external result is
  176/192. **The frozen pooled non-regression gate is impossible; reject.**
  Stop only this runner and its four workers; the all-50/top-10 goal remains
  active. Candidate scores are 60/64 versus 64/64 against 489, and 52/64
  versus 54/64 against 08aa. C95/new was partly completed; head-to-head was
  not run. Do not represent this as a 448-game result or promote on the
  45/50 trained replays. Main remains 3cc, both root backups are preserved.
  `diagnostics/shunki_route_search_20260927/native/early_rejection.json`.

- **2026-09-27 01:17 UTC — pruned selector advances to fresh confirmation.**
  `db98141542b90eb84441a42070c0e9679e3733f46fb811dd85d6e2a5c9be439f`
  removes only BAKERY/PET from rejected 94f. Four new two-seat branch games
  exactly reproduce submitted 3cc there. The other 96 games have identical
  policies/openings to prior 94f, yielding 44/50 sweeps and 89/100 seat wins
  by explicit compositional verification. **Advance, not promote.** New
  terminal samples exclude every previously completed seed per rival;
  the original head-to-head panel remains unplayed and outcome-unseen.
  Main protocol is 240 games, followed only on a pass by a separately
  frozen 48-game comparison with highest active 1f. All native and loader
  gates must pass before promotion. `diagnostics/shunki_shop_pruned_20260927/`.

- **2026-09-27 01:29 UTC — pruned selector also rejected.**
  `db981415...` completes all 240 fresh native games DONE/DONE. New and old
  both win 46/48 versus frozen 489 and 48/48 versus public C95. However,
  the candidate loses **0 wins / 48 games head-to-head** to reacting 3cc:
  zero of 24 paired points against the required 16. All retained branches
  activated in both seats. **Reject; no promotion/upload.** The conditional
  highest-active comparison and loader gates are deliberately not run.
  The 44/50 compositional replay result is training evidence only. See
  `diagnostics/shunki_shop_pruned_20260927/native/confirmation.json`.

- **2026-09-27 01:29 UTC — six new public source schedules collected.**
  All newly listed completed public episodes of source 56553856 were
  downloaded without reward/outcome filtering, zero errors. Their two-shop
  histories do not include the missing PIZZA/ICE combination. **Research
  data only; no change to either tested candidate or main.** Manifest:
  `diagnostics/shunki_source_refresh_20260927_0126/manifest.json`.

- **2026-09-27 01:34 UTC — demand-aware crop feasibility traces completed.**
  Unchanged 3cc reproduces all three saved seat-0 losses DONE/DONE. Late
  strawberry plantings / three-slot same-tile work windows are: Snorlax 15/55, We wanna be tomatos 15/55, Majkel1337 10/32.
  **Feasibility data only; no candidate or promotion.** A future melon
  controller must fund seeds, mature correctly, and execute harvest,
  replant and same-day watering as a coherent chain. It must also measure
  rival benefits from changed supply. Next work: inspect these traces and
  engine crop rules, then freeze a separate experimental plan if feasible.
  `diagnostics/shunki_crop_demand_20260927/audit.json`.


## 2026-09-29 05:49 UTC — uploaded257 Pizza production guard pilot passed

Candidate `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb` keeps the exact uploaded257 repairs and skips the optional Goose4 Pizza route when the existing public source leaf has at least 12 rival melon plots. The prospective four-case/eight-game both-seat pilot reproduced baseline margins and improved both Pensukesan seats from -53,956 to -8,665 (+45,291 each), while Dieter exactly retained both +27,854 wins and both rewards. All games completed DONE/DONE/720 with zero policy errors; trigger/route telemetry passed. W/D/L remains two wins and two losses. Decision: retain for the frozen full saved panel and fresh reacting screen, not research promotion or an upload. Threshold is a sparse fitted hypothesis. Root research main remains exact4ee. Receipt: `diagnostics/combined_agent_257f_20260929/pizza_pilot/comparison_manifest_receipt.json`, SHA256 `1d8d4bd5a34afd6200e5f8e9ddd2cfcb1c87f52adf1fd8d70898a9571f65a820`; assessment and full case table are beside it. Kaggle was not contacted.


## 2026-09-29 06:05 UTC — ae349d83 saved panel passed; reactive screen pending

The separate root file `main_candidate_improved_20260929.py` (SHA256 `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`) completed102 fresh saved games against exact uploaded257 reference rows, after four baseline pilot reproductions. Result remains94W/0D/8L including two public controls; the100 goal seats remain92W/0D/8L,27/30 loss sweeps and19/20 top20 sweeps. Only both Pensukesan margins improve, by45291 each; all other100 rows preserve rewards/results/margins, and no prior win or margin regresses. All games DONE/DONE/720, zero errors. Decision: accept the narrow saved margin repair for the predeclared fresh reacting/loader checks, not research promotion. Full per-case table and assessment: `diagnostics/combined_agent_257f_20260929/SAVED_RESULTS.md`; saved receipt SHA256 `218297125b45a782f903b2a7aaa178597b708a53f0ffac4f196b404f7b95ce2d`. The mirror-gated Brunch/Pizza route swap was rejected before any games for incompatible schedules; see `diagnostics/reactive_repair_257f_20260929/RESULTS.md`. No Kaggle contact and root main unchanged. Native diagnostic instrumentation was isolated in this experiment folder, and the shared qualify.py was restored byte-exactly to its prior frozen hash c4bae3c9.


## 2026-09-29 06:33 UTC — ae349d83 fresh reacting screen shows no gain

All 48 predeclared original-shop native games completed cleanly across seeds 2026092981–2026092984, three reacting policies and both seats. Uploaded257 and new ae349d83 each scored 8 wins / 14 draws / 2 losses in the 24 matched scenarios; every own/rival reward and margin is identical. Against root4ee: 0W/6D/2L (both losses on seed2026092983 at -10,646); against uploaded257: 0W/8D/0L; against AhmedV35: 8W/0D/0L. The new Pizza guard activated in zero candidate games. All whole-seed point deltas are zero, so the predeclared strict pooled win-rate gain gate fails. Decision: reject research promotion; keep the standalone candidate only as the measured saved-margin repair, with no online score/top10 claim. Minimum native overage and full per-case evidence are recorded in `diagnostics/combined_agent_257f_20260929/reactive/`; receipt SHA256 `53e0968303b1e26c4ec6dfc0681edb2f939d156b9635c5a1aaca5fb99233479e`. The final file-loader check initially stopped with zero games because its checker omitted the workspace import path; the error/source were archived, the checker fixed, and the candidate unchanged. Loader verification is now running. Root main remains exact4ee; no Kaggle contact.


## 2026-09-29 06:36 UTC — tested standalone ae349d83 delivered; no research promotion

Created `main_candidate_improved_20260929.py`, SHA256 `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`, plus exact uploaded backup `main_uploaded_backup_257f941d_20260929.py`. All eight operational native direct/file runs passed on Pensukesan and Dieter in both seats: Kaggle selected `kaggle_a44_pet_market_gate_entrypoint`; all 719 action frames for both players, rewards and complete policy telemetry matched; DONE/DONE/720, zero native/policy errors, and minimum remaining overage 58.670028 seconds. All eight also exactly reproduced the new saved-panel rewards and telemetry. Loader receipt SHA256 `e6925bec83e3afa55c8339d02224fac1d2c0802fe9c788200c84bb96dc69915c`; corrected checker SHA256 `b6d1fc4aa0a8b117c823058cb36104d4652c6c7a5acb28f5c5436194959975d5`. Its earlier import-path preparation failure started zero games and remains archived.

Across this request, 166 full game executions comprise 8 focused pilot games, 102 saved candidate games, 48 fresh native comparison games and 8 file-loader games. The new file improves both Pensukesan saved margins by 45,291, preserves all saved wins (27/30 archived-loss sweeps and 19/20 top20), and exactly ties uploaded257 in all 24 fresh scenarios (8W/14D/2L; zero new-guard activations). Final decision: retain the separate file as an experimental saved-margin repair, reject research promotion and any asserted online win-rate/score/top10 gain. Root `main.py` remains exact4ee; no Kaggle access/upload occurred. Full results for every case, including rejected ideas and the final checks: `NEW_MAIN_TEST_REPORT_20260929.md`, SHA256 `7c7a648354f4e1ffdb1786f59fcbbc978cf3002941e3985e7f7f81f943b39cb8`; machine-readable summary `diagnostics/combined_agent_257f_20260929/FINAL_SUMMARY.json`.


## 2026-09-29 09:02 UTC — opponent-agnostic execution review: no new supported candidate

Reviewed exact ae349d83 source and the existing reactive, terminal, delivery and physical-gap evidence. The source already has partial-plant, failed-hire catch-up, funded animal and physical bridge guards; absence of a general scheduler does not establish a profitable intervention. Exact ae349 reactive comparisons have zero paired outcome/margin delta; exact DECEM terminal recovery is only 44. The prior delivery repair gained 24,746 own cash but 24,342 rival cash (+404 paired), and the older physical audit is not exact-ae evidence. Decision: no-go for a new execution/resource-allocation candidate until a repeated funded-but-missed task on exact ae349 has an executable repair with its whole commitment accounted for. No policy changes, new games, route/market screens or Kaggle access occurred. Review: `diagnostics/opponent_agnostic_execution_review_ae349_20260929/REVIEW.md`, SHA-256 `2cfecae7953a73281c91b7e5df42a8a02f7fbcede5c2a26868ceee26fefb854c`; bound evidence is in `review_receipt.json`. This is a review of existing evidence, not a new outcome experiment or a claim that improvement is impossible.
