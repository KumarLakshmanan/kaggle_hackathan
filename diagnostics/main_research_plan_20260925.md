# Separate main-research planners — 2026-09-25

`main_research.py` imports the frozen `main.py` in a distinct module namespace
and applies only an optional final-action overlay. It is **not** a standalone
Kaggle submission file. The inherited policy is SHA-256
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
`main.py` was not edited or uploaded for this experiment.

## Falsifiable hypotheses

1. `rival_shadow`: sell up to eight already-held premium units before a
   visibly ready rival harvest, provided the inherited tape planned to sell
   that item within 5–24 turns and the public price curve predicts a material
   post-rival drop. This is a price-preemption test; it never reads the rival's
   private shed, replay identity, seed, or future shop draw.
2. `spare_yield`: turn only an otherwise `PASS` farmer/hand action on an
   observed, full animal tile into `HARVEST` when its next scheduled output
   would clip at the held-output cap. Reserve shed room for all current
   output and do not displace a productive action or another worker's harvest.
   This is a task-capacity/yield-loss test, distinct from the incumbent's
   existing one-per-day `CARE` replacement.

The exact-control `MODE=baseline` wrapper matched `main.py` terminal cash in
both seats of reactive self-play seed 0 (72,290 / 72,959). Five synthetic
mechanism tests for the research overlays passed.

## Initial fixed-action development screen

Both candidates were tested on the same 12 evenly spaced routes selected
from the later 2026-09-24 top-50 manifest, both seats. Baseline route results
were joined by exact opponent path to the separately measured full control.

| Mode | Route wins | Changed seats | Own-cash change over 24 seats | Margin change | Conclusion |
| --- | ---: | ---: | ---: | ---: | --- |
| `rival_shadow` | 9/12 | 2 | -108 | -108 | Reject: it acted twice and worsened both |
| `spare_yield` initial | 9/12 | 12 | +338 | +490 | Continue only after capacity review |
| `spare_yield` safe (final full-panel source) | 9/12 | 8 | +110 | +174 | Continue: no win reversal and positive cash, but too small to claim strength |

The initial `spare_yield` treatment made 26 unit-action substitutions. A
capacity review found that same-turn product/animal purchases could fill the
shed after an added harvest; the safe version abstains on those turns. It made
16 substitutions on the same pilot. All simulations finished `DONE`, and its
minimum per-seat margin change was zero. The **pre-safety** version's small
reactive self-play check against `main.py` on seeds 0 and 42 produced one win,
one loss and two draws, all `DONE`; the aggregate paired-margin gain was only
22 coins on seed 0 and zero on seed 42. The final safe source was rerun on
the same reactive seeds: again one win, one loss and two draws, all `DONE`,
with paired-margin changes of +14 and zero. Neither result is evidence of a
higher Kaggle rating.

## Top-100-user comparison protocol

The archived 2026-09-22 manifest
`live_top_leaderboard_routes_2026-09-22_round3_top100_3ep/summary.json`
contains 244 action tapes from 100 distinct team IDs, with 1–3 saved routes
per team. Run each route twice, candidate in each seat: 488 games per agent.
Report route-pair wins/losses (sign of the two-seat summed margin), individual
seat-game wins/losses/draws, team coverage, every game's status, and candidate
versus the frozen incumbent **on the same manifest**. Do not call the 244
fixed-action routes 244 adaptive opponents or extrapolate this score to a
live Kaggle rank. This archived panel overlaps the later top-50 panel for 33
team IDs and is development evidence, not a blind holdout.

Run commands:

```powershell
python -X utf8 route_panel_benchmark.py --candidate main.py --summary live_top_leaderboard_routes_2026-09-22_round3_top100_3ep\summary.json --workers 8 --json-out diagnostics\main_research_top100_baseline_20260925.json
python -X utf8 route_panel_benchmark.py --candidate main_research.py --summary live_top_leaderboard_routes_2026-09-22_round3_top100_3ep\summary.json --workers 8 --json-out diagnostics\main_research_top100_candidate_20260925.json
```

Promotion gate: require a meaningful route-win gain over the matched baseline,
no material own-cash or winning-control regressions, valid actions and `DONE`
statuses, and separate reactive-agent confirmation. Do not promote on the
fixed-action panel alone. No Kaggle upload without a new explicit request.

## Completed top-100 archived panel

The audited comparison is
`diagnostics/main_research_top100_comparison_20260925.json`, generated from
the two full runner outputs above. It matched every route by path, seed,
source seat and action hash; the manifest SHA-256 was identical for both
agents. `main_research.py` tested SHA-256 was
`45632992521689a4dc68bf58411f369faed5bf0529802eb6e4a589ca9b7e76cb`.

| Agent | Route-pair wins / losses / draws | Route win / loss % | Seat-game wins / losses / draws | Seat win / loss % |
| --- | --- | --- | --- | --- |
| Frozen `main.py` | 167 / 77 / 0 of 244 | 68.44 / 31.56 | 329 / 159 / 0 of 488 | 67.42 / 32.58 |
| `main_research.py` safe `spare_yield` | 167 / 77 / 0 of 244 | 68.44 / 31.56 | 329 / 159 / 0 of 488 | 67.42 / 32.58 |

All 976 baseline-plus-candidate simulated seat-games returned `DONE` for both
players. The candidate made 148 idle-action harvest substitutions. It gained
895 own coins and 991 paired-margin coins in aggregate over 488 games (about
1.83 and 2.03 per game), with 0 loss→win and 0 win→loss flips at either route
or seat level. Worst route margin change was -292; best was +168. Because teams
contributed 1–3 routes each, an equal-weight-per-team mean of the candidate's
sampled route-win rates is **68.17%**; team route majorities were 62 win, 25
loss and 13 split/draw. These are descriptive fixed-tape scores, not a live
win probability or leaderboard rank.

Efficiency: the parallel 488-game candidate run had mean 6.61 ms per agent
call and a 8.97-second maximum under heavy concurrent CPU load; every game
still completed. A separate low-load two-seat seed-0 run averaged 1.87 ms
per call with a 70.75 ms maximum and both seats `DONE`. The parallel maximum
is a stress observation, not an expected Kaggle call time.

**Promotion decision: reject for `main.py` and do not submit.** The safe
yield-rescue rule is a valid experimental micro-optimization but increased
no wins on the 100-team development panel, and it does not justify changing
the competition artifact. The `rival_shadow` mode was rejected at the pilot
screen. Preserve `main_research.py` as research code; it depends on `main.py`
and cannot be submitted as a single file without bundling and new validation.
