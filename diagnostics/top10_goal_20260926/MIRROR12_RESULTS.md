# Mirror-gated 12-turn sale lookahead — 2026-09-26

## Hypothesis and exact change

The locally promoted 8-turn sale advance already beat near-mirror reactive
controls. A prior 6-turn ablation was weaker. I froze a 12-turn candidate
before evaluating the new September 26 action panel and 16 new native seeds.
It changes exactly `_ADV_LOOK = 8 if matched else 4` to
`_ADV_LOOK = 12 if matched else 4`. The physical farm equality gate, normal
4-turn behavior, sale safeguards, route planner, and all other source bytes
are unchanged. The candidate SHA-256 is
`0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a`.

## Reactive evidence

`reactive_mirror12_fresh.py` ran the candidate against the previous local
`main.py` on predeclared seeds 2610300–2610315, both seats, with the engine's
native shop draws and both policies responding normally. All 32 games ended
`DONE`. The 12-turn candidate won **32/32 seat-games**, positive in each of
the 16 seeds, gaining 28,930 coins of aggregate terminal margin (6–1,686
per seat). It advanced a sale in all 32 games and recorded zero sale/gate
errors; maximum candidate call was 225 ms in this run. Both seat outcomes
were identical for each seed, so the 32 seats are not 32 independent seeds.

A separate matched test used two locally saved public agent implementations,
four new seeds each, both seats, with the previous local hash as control:

| Reacting opponent | Control wins | 12-turn wins | Margin change over 8 games | Advanced games |
| --- | ---: | ---: | ---: | ---: |
| Public preempt H6 | 8/8 | 8/8 | 0 | 0 |
| Haide | 8/8 | 8/8 | -342 | 8 |

Haide's reacting cash increased 1,140 while our cash increased 798; this
small negative margin signal limits the claim to the tested near-mirror
matchup. No win was reversed in these public-agent checks.

## Saved-action regression panels

Every game below ended `DONE`; each of 100 distinct routes was tested in both
seats with its original shop sequence. The September 25 panel was reused for
development. The September 26 panel was downloaded read-only from the
03:02 UTC leaderboard snapshot, with 100 distinct action hashes from 90 episodes;
83 team IDs overlap the older panel, but zero action hashes or episode IDs do.
The new panel is still a fixed-action regression screen, not an adaptive
opponent win-rate estimate.

| Panel | Previous local route/seat wins | 12-turn route/seat wins | Result flips | Changed routes | Paired-margin change | Worst paired regression |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| September 25 top 100 | 59/100, 118/200 | 59/100, 118/200 | 0 | 16 | +730 | -180 |
| September 26 top 100 | 69/100, 137/200 | 69/100, 137/200 | 0 | 8 | +578 | -234 |

The new panel's 69/100 baseline versus 59/100 on the older panel is sampling
variation across public episodes, not evidence that the local agent's live
rating rose. At this snapshot the *uploaded older artifact* displayed rank
977 / 2229.6, versus rank 10 / 2900.6; no submitted code was changed here.

## Promotion decision

**Promote the exact 12-turn candidate to local `main.py`.** It provides a
consistent direct near-mirror advantage on the new reactive seeds, has no
saved-route outcome reversal in either complete panel, and retains all wins
against the two checked public reactive agents. Its small Haide margin
regression and unchanged saved-route win counts mean it is not evidence of a
top-ten or 100/100 policy.

The previous local `main.py` was copied byte-for-byte to
`main_before_mirror12_20260926_6b5529fe.py` (SHA-256
`6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`)
before replacement. The promoted `main.py` exactly matches candidate SHA-256
above, compiled successfully, and reproduced the seed-2610300 +1,070
per-seat direct result against the backup. **No Kaggle upload occurred.**

Reproduction and evidence: `build_sale_mirror12.py`,
`reactive_mirror12_fresh.py` / `.json`, `reactive_mirror12_public.py` / `.json`,
`mirror12_top100_old_routes.json`,
`diagnostics/top100_refresh_2026-09-26/main_local_100routes.json`,
`diagnostics/top100_refresh_2026-09-26/mirror12_100routes.json`, and
`mirror12_promoted_identity_seed2610300.json`.
