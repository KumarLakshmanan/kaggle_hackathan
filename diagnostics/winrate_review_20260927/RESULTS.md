# Fresh win-rate reassessment — completed 2026-09-26 23:05 UTC

Unchanged candidate SHA-256 `68aad090...` played 32 untouched native seeds
(2631000–2631031), both seats, against four complete reacting policies.
Incumbent `489fe8e4...` played the same panel as controls. All 512 games
finished DONE/DONE under engine 1.32.7, with original endogenous shops.

| Reacting opponent | Candidate W/D/L | Incumbent W/D/L |
| --- | ---: | ---: |
| Current main | 62 / 0 / 2 | 1 / 62 / 1 |
| Previous uploaded main | 62 / 0 / 2 | 46 / 14 / 4 |
| Public Ahmed V35 | 64 / 0 / 0 | 64 / 0 / 0 |
| Public C95 | 60 / 0 / 4 | 64 / 0 / 0 |
| Total | **248 / 0 / 8** | **175 / 76 / 5** |

With a draw worth half a win, the candidate improved pooled win rate by
**13.67 percentage points**. A paired bootstrap resampling whole seed blocks
gave a descriptive 95% interval of **+9.38 to +17.58 points**. The maximum
measured candidate call was 463.2 ms. It passed every prospectively recorded
criterion, including the per-opponent guard against excessive C95 regression.
This panel contains four policies, not a representative sample of the entire
live leaderboard. C95 results regressed by four seat wins and are not hidden.

**Decision: the unchanged candidate now earns promotion consideration under
the new, independently validated win-rate objective.** Earlier cash-tail
rejections remain recorded under their original criteria. Do not describe
this new result as a retroactive pass of those earlier experiments.

A separate `3cc0f69f...` candidate repairs the incomplete ICE/BRUNCH schedule.
These 512 games did not run that changed artifact; its native confirmation,
fresh top-50 panel and loader checks are separate requirements. No main edit
or upload occurred at this decision. Current main has an exact root backup.

Evidence: `PLAN.md`, `manifest.json`, `reactive_panel.json`.
Reproduce: `python -B -X utf8 diagnostics\winrate_review_20260927\run_panel.py`.
