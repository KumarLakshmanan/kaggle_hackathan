# Refreshed public top-100 routes — 2026-09-26

At about 03:02 UTC, a read-only Kaggle leaderboard download showed
Lakshmanan R at rank 977 / 2229.6 and tenth place at 2900.6. One recent
public action history per top-100 team was downloaded. `summary.json`
contains 100 distinct action hashes from 90 episodes; none of its action
hashes or episode IDs occurs in the September 25 top-100 panel, although 83
team IDs overlap. The routes are **fixed actions**, not executing opponents.

The previous eight-turn local agent and the now-promoted 12-turn local agent
were tested on every route in both seats under Kaggriculture engine 1.32.7.
All 400 games ended `DONE`. Each policy won **69/100 route pairs and 137/200
seat-games**, with no route or seat outcome flips between them. Positive
paired margin means the sum of both seat margins is positive; the two seat
results are correlated and must not be counted as independent opponents.

| Rank band | Saved routes lost by current local agent |
| --- | ---: |
| 1–10 | 1 |
| 11–20 | 3 |
| 21–50 | 7 |
| 51–100 | 20 |

The one top-ten saved loss was DSM (-17,199 per seat); Boey was a win on this
particular saved episode, unlike an older Boey episode. Of the 31 current
saved-route losses, the median per-seat deficit was 7,337 and the largest
was 25,022. Only one paired loss was within 2,000 coins. These are sampling
and scenario results, not a live win rate or evidence that the team climbed
the leaderboard.

`losses_31_summary.json` freezes the 31 losses, and
`losses_31_capture144.json` records both-seat public observations at the
day-6 route decision. Three of the largest losses (mtmr_s1, YumeNeko, Lucas
Boesen) shared `YARN_STORE,PIZZA_SHOP`; the complete-route and reactive
screen of that pattern was negative. See
`../top10_goal_20260926/YARN_PIZZA_REVERSE_RESULTS.md` and
`../top10_goal_20260926/MIRROR12_RESULTS.md`.

**Decision:** retain this panel as a current regression screen and loss
diagnosis. It cannot by itself justify a policy change or a Kaggle upload.
