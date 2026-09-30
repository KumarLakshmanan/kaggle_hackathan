# Fresh top-20 recorded-action assessment — 27 September 2026

Official leaderboard snapshot: **2026-09-27T17:25:20.090613+00:00**.
The 20 latest completed source episodes were created from **2026-09-27T16:37:25.102000** to **2026-09-27T17:17:27.905000** UTC. All 20 raw replay and action hashes verify; the 18 distinct episodes have **zero overlap** with the earlier 16:35 panel. Kaggledew Valley 🏆 entered the top 20 in place of My second life.

Exact uploaded 4ee `main.py`, native engine 1.32.7, original shops, both seats: **17/20** both-seat sweeps and **7/10** top-ten sweeps. All 40 games are DONE/DONE/720 with no failed seats. The native second-shop state differs from the source replay for 16/20 teams. Fixed opponent action tapes cannot establish results against their reacting private policies.

| Rank | Team | Episode | Seat 0 margin | Seat 1 margin | Both seats won |
|---:|---|---:|---:|---:|---|
| 1 | DECEM | 114267880 | -62,163 | -62,163 | no |
| 2 | DSM | 114267880 | +33,114 | +33,114 | yes |
| 3 | Boey | 114266440 | -20,873 | -20,873 | no |
| 4 | M & M & P & Q | 114265030 | +21,007 | +21,007 | yes |
| 5 | Vadim Vasilenko | 114265033 | -400 | -400 | no |
| 6 | Majkel1337 | 114263239 | +17,814 | +17,814 | yes |
| 7 | Fourth Quadrant | 114267646 | +4,844 | +4,844 | yes |
| 8 | Unknown Mother-Goose | 114272024 | +22,493 | +22,493 | yes |
| 9 | Just A game on your lips | 114259211 | +179,188 | +179,188 | yes |
| 10 | Anton Tikhonov | 114270638 | +36,989 | +36,989 | yes |
| 11 | KawattaTaido | 114272232 | +75,403 | +75,403 | yes |
| 12 | kigasudayooo | 114273655 | +195,167 | +195,167 | yes |
| 13 | TheEggman | 114273215 | +41,122 | +41,122 | yes |
| 14 | Azat Akhtyamov | 114264626 | +61,529 | +65,141 | yes |
| 15 | Yizhou | 114273553 | +105,667 | +104,903 | yes |
| 16 | atsushi11o7 | 114273553 | +186,413 | +186,413 | yes |
| 17 | 有辣条有权 | 114262952 | +86,320 | +86,320 | yes |
| 18 | Kaggledew Valley 🏆 | 114273541 | +11,432 | +11,432 | yes |
| 19 | Arda Ceylan | 114271761 | +85,825 | +81,300 | yes |
| 20 | Densike | 114270616 | +50,887 | +50,887 | yes |

Current losses in both seats are DECEM (rank 1), Boey (rank 3), and Vadim Vasilenko (rank 5). Majkel1337 is a win in this new source episode; it was a loss on the earlier, different episode. The changed sample is not evidence of a policy improvement.

A separate c68 counterfactual on exactly these three failing tapes and both
seats also loses all six native games: DECEM −62,163, Boey −18,260, Vadim
−363 coins per seat. Current 4ee margins are −62,163, −20,873, and −400.
Reverting the whole file does not rescue any of these saved failures.
This is a selected fixed-tape diagnostic, not a reacting-policy comparison.
See `prior_top3.json` and `prior_top3.py`.

**Decision:** Accept the complete fresh assessment. The requested all-top-20 and top-10 goals remain unmet. No `main.py` change or Kaggle upload occurred.

Evidence: `snapshot.json`, `manifest.json`, `routes/summary.json`, `assessment.json`, `source_context.json`, `summary.json`, `raw_archive/*`, and `PLAN.md`.
