# Refreshed top-50 public replay panel — 2026-09-24

## Provenance and scope

- A fresh Kaggle leaderboard snapshot supplied ranks 1–50. For each team, the downloader selected its highest-public-score accessible submission and its two most recent completed public episodes.
- The panel contains 50 teams, 100 distinct 719-action team routes, and 91 distinct episode IDs (some top-50 teams played each other in one episode). The exact selected route metadata is in `routes/summary.json`; the leaderboard and public submission snapshots are alongside it.
- A post-download integrity check recomputed every route's action hash and decision count: 100/100 passed.
- This is an **offline fixed-action replay** test: opponent actions were captured in past games, not recomputed in response to our agent. It is neither 100 independent adaptive opponents nor a Kaggle rating or expected leaderboard rank.
- Because these results have now been inspected, this exact panel is development/regression evidence for future changes, not an untouched validation holdout. A future candidate needs fresh routes or reactive live-agent tests for independent confirmation.

## Frozen `main.py` benchmark

`main.py` SHA-256: `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.

Command:

```powershell
python route_panel_benchmark.py --candidate main.py --summary diagnostics\top50_current_2026-09-24\routes\summary.json --workers 8 --json-out diagnostics\top50_current_2026-09-24\main_100routes.json
```

| Snapshot ranks | Route wins | Route losses | Seat wins / games |
| --- | ---: | ---: | ---: |
| 1–10 | 18 | 2 | 36 / 40 |
| 11–20 | 15 | 5 | 30 / 40 |
| 21–30 | 13 | 7 | 26 / 40 |
| 31–40 | 12 | 8 | 23 / 40 |
| 41–50 | 9 | 11 | 18 / 40 |
| **Total** | **67** | **33** | **133 / 200** |

All 200 simulated games returned `DONE`. By seat, 66 routes were W/W, one was W/L, and 33 were L/L; the W/L route had a positive summed margin and counts as a route-pair win. At the team level, our agent won both sampled route pairs against 26 teams, split 1–1 against 15, and lost both against 9. The route-pair calculation uses each route separately; the benchmark's seed-grouped `paired_results` should **not** be used here because two selected routes can share an episode seed.

The largest paired-margin deficits were: Excluding (rank 25, −78,392), Boey (rank 35, −53,424 and −39,954), Sida Zuo (rank 27, −37,371), ShunkiKyoya (rank 34, −36,348), ActiveMusyoku (rank 49, −32,066), Planned Economy (rank 31, −31,212), and Majkel1337 (rank 4, −27,560). These are diagnostic replay results, not predicted live match scores.

Measured local agent execution averaged about 3.70 ms per action call; the largest observed call was about 702 ms. Local parallel game wall time averaged 12.42 seconds per game, which is not the competition's per-turn runtime measure.

## Strategy consultation and decision

The [GPT‑6 Pro consultation](https://chatgpt.com/c/6ab4f501-73e0-83ee-92a4-6283e49dd350) recommended a small, observation-legal crop-cycle planner: commit at most four already-owned tiles; reserve funded seeds and protected worker slots; water after every planting or replant on that same day; reserve harvest, delivery, shed and market-order capacity; value output at feasible sale time under conservative supply cases; and test original fixed-shop, native, and reactive continuations separately. It cautioned that the 4–6k-per-seat gap is a **falsifiable scale target**, not a promised benefit from four tiles.

The standalone four-tile pilot is experimental. Its [findings](../block_planner_findings_20260924.md) show that it certified only one rotating lane, not a complete four-tile scheduler. On one target loss it improved the original fixed-shop margin by only 280 coins while still losing, and its native result was vulnerable to changed shop draws. Its final 40-route top-20 check changed frozen main's 37/40 route wins and 74/80 seat wins to 36/40 and 72/80, including one prior winning route reversed. It is **not promoted**. The existing `main.py` was not changed in this run, and nothing was submitted to Kaggle.

## Follow-up diagnosis and bounded screens

The [loss clusters](loss_clusters.md) and [24-game daily ledger](LEDGER_12_ROUTE.md)
separate severe low realized prices at equal strawberry units from smaller
sheep/cow cohorts and one route where the fixed rival's public cash dominates.
All 24 ledgers reconcile to the frozen benchmark. They do not identify a
universal production or service fix.

A forced existing [day-6 cohort-route screen](ROUTE_COHORT_SCREEN.md) rescued two
of six selected losses but reversed three previously winning controls, so it
was rejected. A separate [early-tomato pilot](../early_tomato_report_20260924.md)
ran 48 bounded native/fixed-shop games. It changed two plots on one selected
loss but recovered only 7.2% of that paired deficit under fixed shops; our own
cash fell, and a native winning control flipped to a loss. It also failed its
predeclared promotion gate. **Neither candidate changed `main.py`; the tested
100-route baseline remains 67/100 route-pair wins and 133/200 seat wins.**

Further local [crop-cohort and H6 price screens](CROP_COHORT_SCREENS_20260924.md)
tested day-11 carrot replacement, tomato-project timing/demand thresholds,
a day-11 strawberry-to-tomato swap on all 100 routes, an exact engine
scarcity-curve correction, and a targeted day-6 tomato substitution. The
day-6 rule failed both eligible native seats and reduced our cash despite a
fixed-shop gain; its 12-route predeclared loss/control screen never activated.
An additional bounded [Full/Half/Omit late-tomato
ablation](CROP_COHORT_SCREENS_20260924.md) activated on one of three pilot
routes; both reduced arms lowered our terminal cash and rescued no loss.
None increased the 67/100 route or 133/200 seat
win count, so none was promoted to `main.py`. The [Luna/max loss
stratification](LOSS_STRATIFICATION_LUNA.md) records an exact 11-route
development panel for focused follow-up. No Kaggle submission was made.

An additional [four-route near-tie audit](NEAR_TIE_AUDIT_20260925.md) found no
stranded final-turn shed stock or undelivered cargo on the checked losing
seats. The [early strawberry demand screen](DEMAND_OBSERVABILITY_20260925.md)
found that seed purchases start on day 5 before the second shop is known.
Omitting the cohort helped one loss only modestly (+1,845 own coins) under
matched shops but cost a winning control 19,251 own coins and reversed its
outcome. Native results were strongly confounded by changed future shop draws;
that candidate was also rejected and `main.py` remains frozen.

## Full-panel route-9 counterfactual (2026-09-25)

The earlier sheep-heavy route-9 screen was expanded to the exact 100-route,
both-seat panel using `exp_route_cohort_selector_20260924.py` with
`_EXP_ROUTE=9` from step 144 through 647. All 200 native games finished `DONE`.
It won **58/100 route pairs and 113/200 seats**, versus the frozen `main.py`'s
67/100 and 133/200. Four baseline losses became wins, but **13 baseline wins
became losses**. Mean own final cash fell by 5,975.01 per seat-game; replay
opponent cash rose by 101.74. The four rescues all had positive own-cash
changes, but this unconditional route choice is a net regression. Its full
output is `route_force_9_100routes_20260925.json`. It remains a diagnostic,
not a promoted or submitted candidate. The next question is whether public
state at the day-6 decision distinguishes rescues from reversals without
using replay IDs, future shops, or opponent private inventory.

The [day-6 public-state selector screen](ROUTE9_PUBLIC_SELECTOR_20260925.md)
captured all 100 incumbent routes at the decision point and exactly
reproduced their final outcomes. No coarse one-feature threshold passed the
full-panel rescue-versus-reversal gate; whole-team leave-one-out selection
fell to 64/100 routes and 127/200 seats, with zero rescued held-out losses and
three reversed wins. This route-switch mechanism remains rejected.

A separate [worker-consolidation bound](WORKER_CONSOLIDATION_BOUND_20260925.md)
checks GPT-6 Pro's task-preserving hire proposal on four near-tie losing
traces. Avoiding one final hire on every day has enough *theoretical* wage
scale to cover each deficit, but no replacement schedule has yet been proven;
the prior blunt hire-cap screen still stands as a negative control.
