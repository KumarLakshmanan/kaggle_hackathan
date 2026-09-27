# Kaggriculture agent research memory

Submission status checked: 2026-09-27 12:05 UTC; leaderboard snapshot checked:
2026-09-27 12:05 UTC. This is a living research log,
not a claim that the agent beats every opponent. Update the dated findings below after each
completed experiment, with the artifact and a clear promotion/rejection decision.
`AGENTS.md` points future workspace work to this file.

## Mission and operating constraints

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
  authorizes ONE new upload of a qualified update. This authorization is
  unconsumed at12:19UTC. The preceding conditional request to upload if
  not already uploaded did not trigger a duplicate c68 submission.
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
