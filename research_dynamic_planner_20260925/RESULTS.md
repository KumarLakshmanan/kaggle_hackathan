# Independent planner experiment — 2026-09-25

## Decision

**Reject for promotion.** The independently authored, observation-driven
planner is valid and fast enough in local full games, but it is much weaker
than the current `main.py`. Neither `main.py` nor Kaggle was changed by this
experiment. Fixed opponent tapes are a development screen, not independent
validation or a claim about live opponents.

## Implementation and mechanical checks

- `candidate.py` constructs worker jobs from the current observed farm and
  validates movement, supplies and task prerequisites at every turn.
- `economics.py` implements the installed 1.32.7 price and town-demand
  mechanics exactly where observable, plus explicit approximate future
  production/shop scenarios. The generated `standalone_v*.py` files are
  readable one-file agents, with no incumbent imports, replay IDs or encoded
  action tapes.
- Ten engine-backed economy/scheduler unit tests passed. A full 720-frame
  smoke episode against `pass` returned `DONE` and 131,774 final coins, with
  zero unit no-ops and zero deaths; two cargo units overflowed in that smoke
  game. Actual strength was tested separately.

## Strength evidence

| Candidate | Reactive versus `main.py` | Mean own final coins | Mean margin | Seed-0 matched-shop margins versus `main.py` (seats 0, 1) |
| --- | ---: | ---: | ---: | --- |
| v1, horizon-profit ranking | 0/8 wins, four seeds, both seats | 62,037 | −61,743 | −64,415, −64,894 |
| v2, opening-animal and slow-crop quotas | 0/4 wins, two seeds, both seats | 51,092 | −49,106 | −86,017, −85,987 |
| v3, later slow-crop cap and staple bonus | 0/4 wins | 58,516 | −54,442 | −68,853, −69,658 |
| v4, late staple bonus alone | 0/4 wins | 56,966 | −51,280 | −64,115, −70,328 |
| v5, cash/worker-throughput ranking | 0/4 wins | 44,311 | −79,501 | −107,073, −107,073 |

The native games let the engine draw future shops naturally, so the opponent's
cash also changes when a policy changes the random-event path. The matched-shop
screen pins the *observed* v1 native shop sequence locally to diagnose the
intervention; it is not the submitted environment and does not prove
performance across other shop schedules. The v1 native run on seed 0 seat 0
matched its pinned-shop rerun exactly (80,665 versus 145,080).

On the 12-route evenly spaced top-50 saved-action development screen, v1 won
1/12 paired routes and 2/24 seat games; `main.py` won 9/12 routes and
18/24 seats on those same saved actions. The tapes do not react to new policy
behavior, so this is only a negative screen. The gap was already too large to
justify a full 100-route run of a rejected candidate.

The v1 seed-0 audit found zero unit no-ops, deaths or discarded cargo. Day-1
assets were three cows and three sheep, while `main.py` had eight wheat,
twelve melons, two sheep and two cows. By day 12, the candidate's cash was
2,581 versus 19,740. It later overplanted strawberries (38 by day 15) and
bought 487 wheat units over the game, so production and purchasing did not
convert into enough final cash. This is a portfolio/throughput failure, not
an action-schema failure.

The v5 throughput objective shifted opening assets to 18 melons, four
strawberries, one sheep and one cow, and improved day-12 cash to 12,741
versus the corresponding opponent's 17,575. But it then expanded to 41
strawberries by day 15, had 44,036 coins by day 29 versus 117,589, and lost
more severely overall. Penalizing committed capital and worker time was not
sufficient to handle complete harvest-to-sale cycles or future market
feedback. Its seed-0 audit showed zero no-ops, one crop death, and `DONE` for
both agents.

## Reproduction

```powershell
python -X utf8 -m unittest discover -s research_dynamic_planner_20260925 -p 'test_*.py' -v
python -X utf8 paired_benchmark.py --candidate research_dynamic_planner_20260925\standalone_v1.py --opponent main.py --seeds 0 1 42 20260925 --json-out research_dynamic_planner_20260925\planner_v1_main_4seeds.json
python -X utf8 research_dynamic_planner_20260925\fixed_shop_compare.py --candidate research_dynamic_planner_20260925\standalone_v1.py research_dynamic_planner_20260925\standalone_v5_throughput.py --opponent main.py --seed 0 --schedule-audit research_dynamic_planner_20260925\planner_v1_main_seed0_audit.json --output research_dynamic_planner_20260925\fixed_shop_recheck_seed0.json
```

The smoke, paired, audit and fixed-shop JSON artifacts in this directory are
the exact local result records. A separate GPT-6 Pro strategy critique was
requested with aggregate-only findings. Its specific proposal is documented
in `PRO_STRATEGY.md`; its advice is a hypothesis until independently tested.
