# Completed results as of October 1, 2026 IST

Validated incumbent: bbffbe65. Experimental survivor: 4ea1d89a. No Kaggle submission was made in this task.

| Completed panel | Validated incumbent W/D/L | New candidate W/D/L | Meaning |
|---|---:|---:|---|
| Fresh reacting development, 32 games/version | 24/8/0 | 30/0/2 | Candidate gains two win points; independent confirmation still required |
| Saved top20, both seats | 32/0/8 | 32/0/8 | 80% wins, identical outcomes |
| Saved top100, both seats | 136/0/64 | 136/0/64 | 68% wins, identical outcomes |

The physical-enabled full candidate also scores 30/0/2, but its physical planner never activates and its peak call is 12.63 seconds versus 2.10 seconds for the selected market-only candidate. The cheaper market-only candidate advances under the frozen tie rule.

All 96 development games and all 400 top100 version/seat games complete cleanly. Top20 rows are reused in the top100 ledger and must not be counted as additional independent evidence. The saved snapshot is September 29, not a fresh live leaderboard. Candidate mean coin margin on top100 is 30,295.51 versus incumbent 30,409.175, a decrease of 113.665 coins, with no changed wins/losses.

Engineering: 216 native/cache parity checks pass, plus focused scheduling, hidden-seed independence, mutation isolation and empty-order checks. These validate execution, not competitive strength.

Fitted terminal evaluator: episode-group heldout coin RMSE 5,053 versus 5,939 for cash-only; Brier score 0.164 versus 0.240 for the declared heuristic. This is not calibrated live win probability.

Expanded full-season offline forecast: 22,425 native transitions, 39 complete hypothetical seasons, all five crops, all three animals and animal/wheat bundles. No expansion meets the robust selection gates. This is one state under hypothetical reacting scenarios, not 39 competitive wins.

Prior independent qualification of bbffbe65: 121/0/7 in 128 games (94.5% wins), compared with its older 4eeac9c3 baseline at 67/54/7. Both-seat native/file-loader parity passed. This result belongs to bbffbe65, not the new candidate.

Recommendation now: upload `upload_ready_bbffbe65/main.py`. Retain 4ea1d89a as experimental until its independent confirmation and loader gates complete. No tested version establishes greater than 90% wins against saved top20/top100 or a top10 Kaggle rank.

Every completed top100 matchup and both seats: `TOP100_PAIRED.md` and `TOP100_PAIRED.csv`. Raw development cases: `screen_results.jsonl`. Raw saved cases: `top100_results.jsonl`. Receipts bind source and result hashes.
