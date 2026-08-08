# V35 generalization-first replay report

V35 returns to V32, the stronger live-leaderboard baseline (2826.9 versus
V34's 2727.9), and adds only three narrow adaptations selected from public
state. It removes V34's broad industrial-opening and shop-pair expansion.

## New public-failure corpus

- Replays supplied: 22
- Unique opponent routes: 22
- V32 result: 19 wins / 3 losses (38/44 game wins)
- V34 result: 16 wins / 6 losses (32/44 game wins)
- V35 result: **22 wins / 0 losses (44/44 game wins)**
- V35 mean margin per game: **+4,452.4**
- All games: `DONE/DONE`

The three repaired V32 matchups are:

| Episode | Opponent | V32 margin/game | V35 margin/game |
|---:|---|---:|---:|
| 90835915 | MD. Nazmus Sakib Anik | -710 | +1,779 |
| 90839236 | I_luv_magick | -614 | +1,384 |
| 90920242 | ConnieCodes | -147 | +1,328 |

The highest-reward supplied opponent route, Akhilesh godugu in episode
90878133 (141,966 original reward), loses to V35 by 4,447 in both candidate
seats.

## Generalization sanity check

V35 versus V32 across four paired seeds produced four paired draws and zero
paired losses. This confirms the new signatures did not activate broadly in
the sanity set.

## Missing best-replay input

At validation time `best_replay/` contained no JSON replay files. The prior
tracked best files are currently deleted in the worktree, and the newly
mentioned best JSON is not present anywhere else in the project. Therefore no
claim is made that V35 passed a file that was not available.

Evidence:

- `benchmark_results/v32_vs_v34_public_failures.json`
- `benchmark_results/v34_vs_v34_public_failures.json`
- `benchmark_results/v35_all_22_public_failures.json`
- `benchmark_results/v35_vs_v32_sanity.json`

Promoted artifact SHA-256:

`4ab8b2f1497e5bc63753a5e261b23e96b76314d6840c02fdf1c361d355ab678c`
