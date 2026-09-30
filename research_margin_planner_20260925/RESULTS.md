# Rival-aware planner results — 2026-09-25

This is a research candidate, **not** a Kaggle-ready submission or a replacement
for `main.py`. It uses only current public observations and the frozen v1
worker executor. The treatment changes investment valuation, not the executor.
The separate `control` mode reproduced the frozen v1 seed-0 results in both
seats. Four mechanism unit tests passed.

## Tested strategic alternatives

| Mode | Decision rule | Reactive result vs `main.py`, seeds 0 and 42, both seats | Decision |
| --- | --- | --- | --- |
| `terminal_margin` | Price-curve forecast of incremental own **minus rival** terminal cash, with two future demand/rival scenarios | 0/4 wins, all `DONE`; mean own 64,941; mean margin -56,078; mean agent call 6.23 ms, max 65.85 ms | Reject for promotion; retain as a research model |
| `short_cycle` | Same opponent-aware forecast, but require a complete project cycle within 12 days | 0/4 wins, all `DONE`; mean own 47,804; mean margin -75,065; mean agent call 3.75 ms, max 54.49 ms | Reject |

The terminal-margin mode showed a modest paired-margin signal against the
*frozen v1 planner*, not against `main.py`. To separate policy changes from
future-shop random-number drift, the A/B harness pinned only the exogenous
shop-unlock schedule from the frozen control. Both agents and the opponent
still reacted to their own observations; market stock, trades, weeds, and
opponent choices were not replayed.

| Matched-shop seeds | Seats | Margin improvements | Mean own-cash change vs v1 | Mean paired-margin change vs v1 | Result flips |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0, 42, 17, 101 | 8 | 6/8 | -2,180 | +1,593 | 0; all remained losses |

The strongest positive margin change (+6,633) was still a loss. Seed 17
showed the risk in the objective: own cash fell 9,369 in each seat while the
rival fell 10,622, creating only a +1,253 margin gain. Seed 101 regressed
2,731 margin in each seat. An engine audit of native seed 17 seat 0 found
zero unit no-ops, but four plants died; the new mix can overburden the worker
schedule. The rival-cash externality is also only a forecast; its future
shop and sale timing assumptions are not exact engine continuations.

**Promotion decision:** Neither mode is in `main.py`. A 100-route saved-action
panel would not establish that a policy with 0/4 reactive wins can beat the
incumbent, so the predeclared gate to run it was not met. No Kaggle upload
was made. This experiment gives a reusable investment model and a measurable
opponent-aware margin signal, but not a stronger agent.

## Reproduction

```powershell
python -X utf8 -m unittest discover -s research_margin_planner_20260925 -p 'test_*.py' -v
python -X utf8 paired_benchmark.py --candidate research_margin_planner_20260925\agent.py --opponent main.py --seeds 0 42 --json-out research_margin_planner_20260925\margin_seed0_42.json
python -X utf8 research_dynamic_planner_20260925\terminal_rollout.py --control research_dynamic_planner_20260925\standalone_v1.py --treatment research_margin_planner_20260925\agent.py --opponent main.py --seeds 17 --shop-audit research_margin_planner_20260925\control_seed17_audit.json --json-out research_margin_planner_20260925\matched_seed17.json
```

Raw `margin_seed0_42.json`, `short_seed0_42.json`, `matched_seed*.json`, and
`margin_seed17_audit.json` are in this directory. The experimental mode is
selected with the local benchmark's candidate override `MODE=short_cycle` or
`MODE=control`; the default is `terminal_margin`.
