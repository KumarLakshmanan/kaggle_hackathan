# Public scheduler inspiration: feed reserve, 2026-09-26

Sources reviewed statically: Evelyn3976's public *Kaggriculture Adaptive
Market Scheduler v1* (worker ownership of wheat feed and shed pickups) and
Ahmed Berat Ozer's public *Kaggriculture V43: Recovering Lost Harvests*
(physical shed and market guards). Their source was not imported or executed.
The current `main.py` already has related V43 overflow and atomic planting
guards, so this first experiment changed only the separate search agent.

## Predeclared wheat-reserve experiment

`PLAN.md` froze the mechanism, seeds 2615000–2615003, both seats, reacting
`main.py`, native engine 1.32.7 and original endogenous shops. A was the
retained `kaggriculture_search_agent.py` v2. B was
`exp_public_supply_reserve_20260926.py`, which changed only the wheat SELL
reserve from `animal_count` to `2*animal_count+3`, matching the existing buy
target. The candidate is an independent implementation of a reserve concept;
no public source was copied.

| Seed | A paired margin | B paired margin | B minus A |
| --- | ---: | ---: | ---: |
| 2615000 | -197,969 | -200,869 | -2,900 |
| 2615001 | -257,034 | -224,164 | +32,870 |
| 2615002 | -248,382 | -226,690 | +21,692 |
| 2615003 | -215,262 | -269,860 | -54,598 |
| **Total** | **-918,647** | **-921,583** | **-2,936** |

All 16 games ended `DONE` for both agents and opponent. Each candidate lost
all four seed pairs and all eight seat games to `main.py`. A mean seat margin
was -114,830.875 and mean own cash 60,414.125; B was -115,197.875 and
59,285.125. B improved two seeds, but its aggregate paired margin and own
cash worsened. **Reject B at the predeclared development gate.** No untouched
confirmation seeds were opened, no `main.py` promotion and no Kaggle upload.

Raw files: `baseline_dev4.json`, `candidate_dev4.json`. Reproduce with
`python paired_benchmark.py --candidate kaggriculture_search_agent.py --opponent main.py --seeds 2615000 2615001 2615002 2615003 --json-out diagnostics/public_supply_inspiration_20260926/baseline_dev4.json`
and substitute `exp_public_supply_reserve_20260926.py` for the B run.
