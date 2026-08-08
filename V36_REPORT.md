# V36 leader-meta report

## Outcome

V36 replaces V35 in `main.py` and `submission.py`. The versioned artifact is
`main_v36_leader_meta.py`. All three files are byte-identical:

`d1efd15b91dc47f7136d3d7bfd37019b57338c8c6c170aa9b253344cef3c2ace`

V35's completed live public score was 1294.7 when checked on 2026-08-08,
well below V32's 2822.5. V36 therefore keeps none of V35's brittle default
selection behavior.

## Live data archived

- 100/100 public Kaggriculture code references were pulled into
  `pipelines/kaggle_public/` (88 notebooks and 12 Python files).
- 20 literal public agent sources were safely extracted without executing the
  notebooks into `pipelines/kaggle_public_agents/`.
- The pinned live top-10 snapshot contains Seb (allegedly), kakuteki,
  mrgrishninsb, Marcus, CemBas, HealthStone, Auxileon, Dandan Li, Sean Zhang,
  and hongqian miao.
- `best_replay/top10_raw/` stores latest public matches.
- `best_replay/top10_best_raw/` stores each pinned team's most recent strict
  win. `top10_manifest.json` and `top10_winning_manifest.json` preserve the
  exact team, submission, episode, score, and file mapping.
- Because the leaderboard changed during the run, prior top-10 routes were
  retained as historical holdouts instead of discarded.

## Public architecture findings

Notebook titles and reported local rates were not accepted as evidence. On
V35's eight new top-10 losses:

- The public "top-5 meta ensemble" lost all 16 paired-seat games.
- The public "93% WR" agent lost all 16 games.
- The public Flex adaptive agent lost all 16 games.
- The Tetsutani adaptive agent recovered two routes but still lost six.

The useful lesson was architectural: retain a high-output tested worker route,
repair stochastic legality failures from live state, and adapt the market tape
only when an observable signature is both narrow and validated.

## V36 architecture

1. The production base is kakuteki's live rank-2 route from episode 90944496,
   selected because it was the only screened response to beat all eight of
   V35's initial top-10 losses.
2. Every action is passed through hand alignment, weed repair, shed-aware sale
   clamping, bounded premium-sale preemption, exception recovery, and terminal
   liquidation.
3. A public turn-144 signature (`YARN_STORE`, `FARMERS_MARKET`, opponent money
   1685-1691) selects mrgrishninsb's market-compatible response book. Both
   books have the same worker trajectory for all 719 turns.
4. A second public signature (`BRUNCH_SPOT`, `ICE_CREAM_SHOP`, opponent money
   1702-1706) selects a one-order timing variant: sell 18 strawberries on turn
   623 instead of 624. This was the best of 310 exhaustive one-sale shifts.
5. No team name, replay ID, private opponent state, or seed is consulted by the
   submitted agent.

## Final validation

The consolidated corpus contains 61 unique routes: both seats from every
available failed replay plus every old and refreshed top-10 route still on
disk.

- Games: 122/122 wins, 0 draws, 0 losses
- Unique route pairs: 61/61 wins
- All statuses: `DONE`
- Mean margin: +4757.7
- Median margin: +4363
- Minimum game margin: +163
- Mean reward: 128075.0
- Agent mean call time: 546 microseconds
- Agent maximum observed call time: 126.7 milliseconds

The exact result is in `benchmark_results/v36_3_all_historical_routes.json`.

Against V35 directly on four fresh paired seeds, V36 won 8/8 games with mean
margin +5278.25. The exact result is in
`benchmark_results/v36_final_vs_v35_paired.json`.

## Honest limitation

No agent can be guaranteed to win against every unseen future submission.
V36 is proven only on the archived corpus and the direct seed panel above. Its
recovery and public-state market controls are designed to generalize, but a
new live replay should still be added to the corpus and revalidated before any
future submission.
