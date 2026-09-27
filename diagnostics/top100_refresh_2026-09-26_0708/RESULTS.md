# Refreshed top-100 public routes — 2026-09-26 07:08 UTC

The read-only leaderboard snapshot listed 100 teams (rank-10 score 2904.1).
One recent public action history from each selected scored submission was
captured. A collector bug that skipped the second team in a shared episode
was fixed before the final run. The frozen panel has **100 team routes, 100
distinct action SHA-256 hashes and 88 source episodes**. It has no action
hash or episode overlap with the preceding September 26 top-100 panel and
no action-hash overlap with the September 25 panel. See `route_audit.json`,
`leaderboard_snapshot.json`, and `routes/summary.json`.

The current uploaded `main.py` SHA-256 `489fe8e4...` played all routes in
both seats under engine 1.32.7, with original seeds and shops. All 200 games
ended `DONE`. It won **66/100 positive paired routes and 132/200 seat-games**.
Paired route margin is the sum of the two seat margins; seats of one route
are correlated. The full result, including day-six captures, is
`main_100routes.json`; the exact rank and portfolio joins are in
`main_panel_analysis.json` and `main_loss_manifest.json`.

| Snapshot ranks | Paired wins | Paired losses |
| --- | ---: | ---: |
| 1–10 | 9 | 1 |
| 11–20 | 8 | 2 |
| 21–50 | 23 | 7 |
| 51–100 | 26 | 24 |

The top-ten saved loss is Boey, −2,890 coins in each seat. The largest
paired losses are mhw (−92,486), ShunkiKyoya (−45,570), AI是我的豆包
(−39,652), Lucas Boesen (−39,170), and chungkuangwen (−32,132).
Among the 34 lost routes, 21 rivals had at least seven strawberry tiles at
day six, with median loss 8,313 coins per seat; twelve lost-route rivals had
at most four, with median loss 3,693.5. This is an association, not proof
that copying strawberry counts would improve the agent. A prior complete
DSM ledger found that goose, wheat and other net-cash differences dominated
despite our later farm having more strawberries.

The public leaderboard at 07:35:40 UTC ranked Lakshmanan R **900 / 2248.8**,
versus rank 10 at **2897.8**; see
`diagnostics/leaderboard_20260926_0736/kaggriculture.zip`. The newly
uploaded submission had seven early public wins by 07:31 UTC but had not
reached a stable comparable rating. Fixed replay wins are not live head-to-head
wins because rivals do not react to our changed actions.

**Decision:** retain this as a fresh regression and loss-diagnosis panel.
The 66/100 result contradicts the requested all-100 outcome. No policy
promotion or Kaggle upload follows from this fixed-action result alone.
Investigate complete funded production bundles against major losses and
test candidates against reacting opponents on new seeds before promotion.
