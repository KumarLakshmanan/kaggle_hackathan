# Refreshed top-20 public replay panel — 2026-09-26

One recent public action history for each of the first 20 teams in the 2026-09-25 21:46 UTC Kaggle leaderboard snapshot was downloaded read-only. `summary.json` has 20 distinct action SHA-256 hashes, with source submission, episode, seed and seat. These are **fixed opponent actions**, not executing submitted agents, and do not estimate live leaderboard win rate.

The current local `main.py` SHA-256 `6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076` and the previous submitted backup SHA-256 `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1` were each tested against all 20 routes in both candidate seats under engine 1.32.7. All 80 games were DONE. Both agents had **17/20 positive paired margins and 34/40 seat wins**; every terminal candidate/rival cash pair matched exactly between the two agents. The physical-mirror sale gate did not demonstrate benefit on this separate replay set.

The three both-seat losses for current `main.py` were Boey (-2,861 per seat), TheEggman (-7,956), and 吃白饭的大肥鱼 (-10,679). Exact seat-0 event traces are `top20_Boey_trace_s0.json.gz`, `top20_Eggman_trace_s0.json.gz`, and `top20_team_trace_s0.json.gz`. Their realized revenue gaps differ: Boey sells much more fertilizer and eggs; TheEggman more eggs and strawberries; 吃白饭的大肥鱼 more strawberries and milk. Gross wheat sales conceal large product purchases and should not be read as net income.

This panel improves freshness and locates targets, but the saved actions and correlated seats cannot prove that the local file will beat these teams live. No Kaggle upload occurred.

Reproduce the benchmark from the workspace root:

```powershell
python -B -X utf8 route_panel_benchmark.py --candidate main.py --summary diagnostics\top20_refresh_2026-09-26\summary.json --workers 6 --json-out diagnostics\top20_refresh_2026-09-26\main_local_20routes.json
python -B -X utf8 route_panel_benchmark.py --candidate main_before_top10_goal_20260926_04b0bdc3.py --summary diagnostics\top20_refresh_2026-09-26\summary.json --workers 6 --json-out diagnostics\top20_refresh_2026-09-26\submitted_backup_20routes.json
```
