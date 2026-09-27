# September 25 current top-100 Kaggriculture replay audit

`leaderboard_snapshot.json` comes from a read-only Kaggle leaderboard download
on 2026-09-25. It names 100 teams; `summary.json` contains one latest public
episode action tape for each (100 distinct action hashes). The local simulator
is `kaggle-environments` 1.32.7. This is **fixed-action replay testing**:
opponents do not adapt to our changed actions, so the results are not live
head-to-head wins, a skill rating, or a first-place prediction.

The frozen production `main.py` SHA-256 is
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
`main_100routes.json` tested each route with our agent in both seats. All 200
games finished DONE. It won 118 seat games and lost 82. By team, **58 routes
were won in both seats, 2 split, and 40 were lost in both seats**. If a route
is judged by the *sum* of its two seat margins, the count is 59 positive and
41 negative. These are different definitions and must not be conflated.

| Leaderboard ranks | Both-seat wins | Split | Both-seat losses |
| --- | ---: | ---: | ---: |
| 1–10 | 8 | 0 | 2 |
| 11–25 | 9 | 0 | 6 |
| 26–50 | 15 | 0 | 10 |
| 51–100 | 26 | 2 | 22 |

The current #1, Boey, beat our agent by 7,858 coins in each saved-action seat.
The other top-ten loss was Fourth Quadrant by 4,266 coins in each seat. Five
both-seat losses were below 1,000 coins per seat, including one by 35 coins.
The downloaded leaderboard snapshot showed Lakshmanan R at rank 742 / 2370.5
and first place at 3051.6; those ratings can move with new live games. A replay
win cannot be read as a promised rating gain because the opponent's submitted
policy is not executing live in this harness.

`shop_pair_probe.json` identified the first two public shops after 144 turns in
both tested seats for each route. No current-top-100 route showed the ordered
pair `ICE_CREAM_SHOP,YARN_STORE`; therefore the narrow route-switch candidate
from older development replays was not validated on this holdout.

Reproduce the rank-band breakdown:

```powershell
python -X utf8 diagnostics/summarize_rank_panel.py `
  --summary diagnostics/top100_current_2026-09-25/summary.json `
  --results diagnostics/top100_current_2026-09-25/main_100routes.json `
  --leaderboard diagnostics/top100_current_2026-09-25/leaderboard_snapshot.json
```

The isolated H6 exact-engine price-scoring candidate was mathematically
verified against 9,009 simulator quotes. It did **not** clear the promotion
gate: on the 24 recent live-loss fixed routes it remained 13 wins / 11 losses;
on a separate fresh 49-route panel it remained 33 wins / 16 losses. In the
fresh panel, 7 of 16 changed route margins improved, 9 regressed, and the sum
was −228 coins. It did not rescue a loss. A redundant full current-top-100
candidate rerun was stopped after this independent gate failure; do not quote
an incomplete 100-route treatment result. The production `main.py` remains
unchanged. No Kaggle submission was made as part of this audit.
